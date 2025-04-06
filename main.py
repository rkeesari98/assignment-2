from typing import Optional
from fastapi import FastAPI, Request,Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.oauth2.id_token
from google.auth.transport import requests
from google.cloud import firestore
import starlette.status as status
from fastapi.responses import RedirectResponse
from models import TaskBoard
from taskboard_service import TaskBoardService

app = FastAPI()

firestore_db = firestore.Client()

firebase_request_adapter = requests.Request()


app.mount("/static", StaticFiles(directory="static"), name="static")


templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        "home.html",
        {"request": request}
    )


def add_user_to_firestore(request:Request):
    user = {
        "email":request.user.email,
        "name":request.user.email.split("@")[0]
    }
    firestore_db.collection('users').add(user)


@app.get("/taskboards/create",response_class=RedirectResponse)
def create_taskboards():
    return templates.TemplateResponse(
        "add-taskboard.html",
        {"request":Request}
    )
    
@app.post("/tasksboards/create",response_class=HTMLResponse)
def create_taskboards(request:Request,task_board:TaskBoard):
    try:
        TaskBoardService.create_task_board(request,task_board)
        return RedirectResponse(
            url="/",
            status_code=303
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/tasksboards/create?error={str(e)}",
            status_code=303
        )