from typing import Dict, List, Optional
from fastapi import FastAPI, Request,Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.oauth2.id_token
from google.auth.transport import requests
from google.cloud import firestore
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
    
@app.post("/tasksboards/create",response_class=HTMLResponse)
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
            url=f"/tasksboards/create?error={str(e)}",
            status_code=303
        )
    
@app.get("/taskboards/{task_board_id}")
def edit_taskboards(request: Request, task_board_id: str):
    if not is_logged_in(request):
        return RedirectResponse(url="/", status_code=303)
    print("it is here")
    try:
        task_board = TaskBoardService.get_task_board(task_board_id)
        if not task_board:
            raise Exception("invalid task board id")
        users_ref = firestore_db.collection("users")
        users_docs = users_ref.stream()
        users = [user.to_dict() for user in users_docs]
        user_info = get_user_info(request)
        return templates.TemplateResponse("add-task-board.html", 
                {"request": request,
                "users":users,
                "current_user":user_info,
                "board": task_board
                })

    except Exception as e:
        print("Error while fetching taskboard:", e)
        return RedirectResponse(
            url=f"/tasksboards/create?error={str(e)}",
            status_code=303
        )


@app.post("/task_boards/{task_board_id}/tasks",response_class=RedirectResponse)
def create_task(request:Request,task:Task):
    try:
        TaskService.create_task(task)
        return RedirectResponse(
            url="/",
            status_code=303
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/?error={str(e)}",
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
    