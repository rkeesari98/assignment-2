from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request,Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.oauth2.id_token
from google.auth.transport import requests
from google.cloud import firestore
from pydantic import ValidationError
import starlette.status as status
from fastapi.responses import RedirectResponse
from models import Task, TaskBoard
from taskboard_service import TaskBoardService
from task_service import TaskService
app = FastAPI()

firestore_db = firestore.Client()

firebase_request_adapter = requests.Request()


app.mount("/static", StaticFiles(directory="static"), name="static")


templates = Jinja2Templates(directory="templates")

def is_logged_in(request:Request):
    id_token = request.cookies.get("token")
    if not id_token:
        return False
    try:
        user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
        if user_token:
            return True
    except Exception as e:
        return False

def insert_into_user_firestore(request:Request):
    id_token = request.cookies.get("token")
    if not id_token:
        return None
    try:
        user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
        if user_token:
            user = {}
            user["email"] =  user_token.get("email")
            user["name"]  = user["email"].split("@")[0]
            users_ref = firestore_db.collection("users")
            user_doc = users_ref.where("email", "==", user["email"]).limit(1).stream()
            user_exists = any(user_doc)  
            if not user_exists:
                users_ref.add(user) 
            return user
    except Exception as e:
        return None


def get_user_info(request:Request)->Dict:
    id_token = request.cookies.get("token")
    if not id_token:
        return None
    try:
        user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
        if user_token:
            user = {}
            user["email"] =  user_token.get("email")
            user["name"]  = user["email"].split("@")[0]
            return user
    except Exception as e:
        return None

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        "main.html",
        {"request": request}
    )


def add_user_to_firestore(request:Request):
    user = {
        "email":request.user.email,
        "name":request.user.email.split("@")[0]
    }
    firestore_db.collection('users').add(user)

@app.get("/taskboards",response_class=RedirectResponse)
def get_taskboards(request:Request):
    if not is_logged_in(request):
        return RedirectResponse(url="/")
    try:
        user = insert_into_user_firestore(request)
        taskboards = TaskBoardService.get_taskboards(user["email"])
        return templates.TemplateResponse(
            "taskboards.html",
            {"request":request,"taskboards":taskboards,"user":user}
        )
    except Exception as e:
        print(e)
        return RedirectResponse(
            url=f"/taskboards?error={str(e)}",
            status_code=303
        )

@app.get("/tasksboards/create",response_class=RedirectResponse)
def create_taskboards(request:Request):
    insert_into_user_firestore(request)
    users_ref = firestore_db.collection("users")
    users_docs = users_ref.stream()
    users = [user.to_dict() for user in users_docs]
    user_info = get_user_info(request)
    return templates.TemplateResponse("add-task-board.html", 
            {"request": request,
             "users":users,
             "current_user":user_info,
             "board": None
             })

def taskboard_form(title: str = Form(...), created_by: str = Form(...), users: str = Form(...)):
    users_list = users.split(',') if users else []
    return TaskBoard(title=title, created_by=created_by, users=users_list)
    
@app.post("/taskboards/create",response_class=HTMLResponse)
def create_taskboards(request:Request,task_board:TaskBoard=Depends(taskboard_form)):
    try:
        TaskBoardService.create_task_board(request,task_board)
        return RedirectResponse(
            url="/",
            status_code=303
        )
    except Exception as e:
        print(e)
        return RedirectResponse(
            url=f"/taskboards/create?error={str(e)}",
            status_code=303
        )
    
@app.get("/taskboards/{task_board_id}")
def get_taskboard_details(request: Request, task_board_id: str, error: Optional[str] = None):
    if not is_logged_in(request):
        return RedirectResponse(url="/", status_code=303)
    
    print("it is here")
    try:
        # Decode the error if it exists
        
        task_board = TaskBoardService.get_task_board(task_board_id)
        if not task_board:
            raise ValueError("Invalid task board ID")
        
        users_ref = firestore_db.collection("users")
        users_docs = users_ref.stream()
        users = [user.to_dict() for user in users_docs]
        
        user_info = get_user_info(request)
        tasks = TaskService.get_tasks(task_board_id)
        
        return templates.TemplateResponse("add-task-board.html", {
            "request": request,
            "users": users,
            "current_user": user_info,
            "board": task_board,
            "tasks": tasks,
            "error": error  # Pass the decoded error to the template
        })

    except Exception as e:
        
        return RedirectResponse(
            url=f"/taskboards/create?error={str(e)}",
            status_code=303
        )

@app.post("/taskboards/{task_board_id}")
def edit_taskboards(request: Request, task_board_id: str, taskboard: TaskBoard = Depends(taskboard_form)):
    if not is_logged_in(request):
        return RedirectResponse(url="/", status_code=303)
    
    users_ref = firestore_db.collection("users")
    users_docs = users_ref.stream()
    user_info = get_user_info(request)
    users = [user.to_dict() for user in users_docs]
    
    try:
        user = insert_into_user_firestore(request)
        print("in update before service call")
        # Unpack the tuple returned by update_taskboard
        task_board = TaskBoardService.update_taskboard(task_board_id, user['email'], taskboard)
        
        if not task_board:
            raise ValueError("Invalid task board ID")
        
        tasks = TaskService.get_tasks(task_board_id)

        return templates.TemplateResponse("add-task-board.html", {
            "request": request,
            "users": users,
            "current_user": user_info,
            "board": task_board,
            "tasks": tasks
        })

    except Exception as e:
        task_board = TaskBoardService.get_task_board(task_board_id)
        tasks = TaskService.get_tasks(task_board_id)
        return templates.TemplateResponse("add-task-board.html", {
            "request": request,
            "users": users,
            "current_user": user_info,
            "board": task_board,
            "tasks": tasks,
            "error": str(e) 
        })


def task_form(
    title: str = Form(...),
    status: str = Form(...),
    details: str = Form(default=""),
    assigned_to: List[str] = Form(default=[]),
    board_id: str = Form(...),
    due_date: Optional[str] = Form(None),
    due_time: Optional[str] = Form(None)
) -> Task:
    try:
        # Only convert date/time if values are provided
        due_date_obj = None
        if due_date and due_date.strip():
            due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
        
        due_time_obj = None
        if due_time and due_time.strip():
            due_time_obj = datetime.strptime(due_time, '%H:%M').time()
        
        # Create Task object
        return Task(
            title=title,
            status=status,
            details=details,
            assigned_to=assigned_to if assigned_to else [],
            board_id=board_id,
            due_date=due_date_obj,
            due_time=due_time_obj
        )
    except ValidationError as e:
        print(f"Validation error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        print(f"Error in task_form: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/taskboards/{task_board_id}/tasks", response_class=RedirectResponse)
def create_task(
    request: Request,
    task_board_id: str,
    task: Task = Depends(task_form)
):
    try:
        print(f"Creating task for board {task_board_id}")
        print(f"Task data: {task}")
        
        if task.board_id != task_board_id:
            task.board_id = task_board_id
        
        TaskService.create_task(task)
        
        # Fixed URL path
        return RedirectResponse(
            url=f"/taskboards/{task_board_id}",
            status_code=303
        )
    except Exception as e:
        print(f"Error creating task: {e}")
        return RedirectResponse(
            url=f"/taskboards/{task_board_id}?error={str(e)}",
            status_code=303
        )
    
@app.post("/task_boards/{task_board_id}/tasks/{task_id}",response_class=RedirectResponse)
def update_task(request:Request,task_board_id:str,task_id:str,task:Task):
    try:
        TaskService.update_task(request,task_board_id,task_id,task)
        return RedirectResponse(
            url="/",
            status_code=303
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/error={str(e)}",
            status_code=303
        )
    

@app.post("/taskboards/{taskboard_id}/tasks/{task_id}/toggle-complete")
def mark_task_completion(request: Request, taskboard_id: str, task_id: str):
    try:
        if not is_logged_in(request):
            return JSONResponse(status_code=401, content={"error": "Unauthorized"})

        user = insert_into_user_firestore(request)
        if not TaskBoardService.do_user_have_access(user["email"], taskboard_id):
            return JSONResponse(status_code=403, content={"error": "Permission denied"})

        TaskService.mark_task_as_complete(task_id)
        return JSONResponse(status_code=200, content={"message": "Task marked as completed successfully"})

    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"error": str(e)})
        
    
@app.delete("/taskboards/{taskboard_id}/tasks/{task_id}")
def delete_task(request:Request,taskboard_id:str,task_id:str):
    try:
        if not is_logged_in(request):
            return JSONResponse(status_code=401, content={"error": "Unauthorized"})

        user = insert_into_user_firestore(request)
        if not TaskBoardService.do_user_have_access(user["email"], taskboard_id):
            return JSONResponse(status_code=403, content={"error": "Permission denied"})
        TaskService.delete_task(task_id)
        return JSONResponse(status_code=200, content={"message": "Task deleted successfully"})
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@app.post("/taskboards/{taskboard_id}/delete",response_class=RedirectResponse)
def delete_taskboard(request:Request,taskboard_id:str):
    try:
        print("hitttt")
        if not is_logged_in(request):
            return JSONResponse(status_code=401, content={"error": "Unauthorized"})
        user = insert_into_user_firestore(request)
        TaskBoardService.delete_taskboard(taskboard_id,user['email'])
        return RedirectResponse(
            url=f"/taskboards",
            status_code=303
        )
    except Exception as e:
        print("Error while deleting:", str(e))
        return RedirectResponse(
            url=f"/taskboards",
            status_code=303
        )