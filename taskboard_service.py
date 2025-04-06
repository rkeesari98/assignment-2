from fastapi import Request
from models import TaskBoard
from typing import Dict, List, Optional, Union
from google.auth.transport import requests
from google.cloud import firestore


firestore_db = firestore.Client()

firebase_request_adapter = requests.Request()

class TaskBoardService:
    @staticmethod
    def create_task_board(request:Request,task_board:TaskBoard):
        existing_task_board = firestore_db.collection('task_board').where(field_path='name', op_string='==', value=task_board.name).limit(1).get()
        if len(existing_task_board) > 0:
            raise Exception("Task board name already exists please use different one")
        for user in task_board.users:
            user_exist = firestore_db.collection('users').where(field_path='email',op_string='==',value=user).limit(1).get()
            if len(user_exist)<=0:
                raise Exception("User not found please assign users who exists")
        firestore_db.collection('task_board').add(task_board.dict())
    
    