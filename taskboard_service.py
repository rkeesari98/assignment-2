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
        existing_task_board = firestore_db.collection('task_board').where(field_path='name', op_string='==', value=task_board.title).limit(1).get()
        if len(existing_task_board) > 0:
            raise Exception("Task board name already exists please use different one")
        for user in task_board.users:
            user_exist = firestore_db.collection('users').where(field_path='email',op_string='==',value=user).limit(1).get()
            if len(user_exist)<=0:
                raise Exception("User not found please assign users who exists")
        firestore_db.collection('task_board').add(task_board.dict())
    
    @staticmethod
    def get_task_board(task_board_id: str) -> Optional[dict]:
        try:
            doc_ref = firestore_db.collection('task_board').document(task_board_id)
            doc = doc_ref.get()
            if not doc.exists:
                raise Exception("Invalid Taskboard Id")
            return doc.to_dict()
        except Exception as e:
            print(f"Error retrieving taskboard: {e}")
            raise
    
    @staticmethod
    def get_taskboards(user_email: str):
        all_docs = firestore_db.collection("task_board").stream()
        taskboards = []

        for doc in all_docs:
            data = doc.to_dict()
            data["id"] = doc.id
            data["total_mem"] = len(data.get("users",[]))
            # Filter condition
            if data.get("created_by") == user_email or user_email in data.get("users", []):
                taskboards.append(data)

        print(taskboards)
        return taskboards
