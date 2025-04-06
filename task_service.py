from models import Task
from taskboard_service import TaskBoardService
from fastapi import Request
from google.auth.transport import requests
from google.cloud import firestore


firestore_db = firestore.Client()

firebase_request_adapter = requests.Request()

class TaskService:
    @staticmethod
    def create_task(task:Task):
        try:
            TaskBoardService.get_task_board(task.board_id)
            existing_task = (
                firestore_db.collection('tasks')
                .where(name='board_id', op_string='==', value=task.board_id)
                .where(name='title', op_string='==', value=task.title)
                .limit(1)
                .get()
            )     
            if len(existing_task) > 0:
                raise Exception("tasks in same board must have different name")
            task.status='INCOMPLETE'       
            task.due_date = None
            firestore_db.collection("tasks").add(task.dict())

        except Exception as e:
            raise Exception(e)
        
    @staticmethod
    def update_task(request:Request,task_board_id:str,task_id:str,task:Task):
        try:
            if task.board_id!=task_board_id:
                raise Exception("Task does not belongs to given board id")
            task_ref = firestore_db.collection("tasks").document(task_id)
            task = task_ref.get()
            if not task.exists:
                raise Exception("Invalid task id please enter valid task id")
            task_board_ref = firestore_db.collection("task_board").document(task_board_id)
            task_board = task_board_ref.get()
            if request.user.email not in task_board.users:
                raise Exception("task may not exist or you don\'t have access")
            
            task_ref.update(task.dict())
        except Exception as e:
            raise Exception(e)

