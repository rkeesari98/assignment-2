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
        existing_taskboards = (
            firestore_db.collection('task_board')
            .where('title', '==', task_board.title)
            .get()
        )
        if len(existing_taskboards)>0:
            raise Exception("name already exists.please use a different one")
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
            data = doc.to_dict()
            data['id'] = doc.id  # add document id to the data
            return data
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
    @staticmethod
    def do_user_have_access(email: str, taskboard_id: str) -> bool:
        try:
            doc_ref = firestore_db.collection('task_board').document(taskboard_id)
            doc = doc_ref.get()
            if not doc.exists:
                raise Exception("Invalid Taskboard Id")

            data = doc.to_dict()
            created_by = data.get("created_by")
            users = data.get("users", [])

            if email == created_by or email in users:
                return True
        except Exception as e:
            raise Exception("You don't have permission")
        
    @staticmethod
    def remove_user_from_tasks(users: list, taskboard_id: str):
        try:
            matching_tasks = (
                firestore_db.collection("tasks")
                .where("board_id", "==", taskboard_id)
                .get()
            )

            for task_doc in matching_tasks:
                task_data = task_doc.to_dict()
                assigned_users = task_data.get("assigned_to", [])

                updated_assignees = [user for user in assigned_users if user in users]

                firestore_db.collection("tasks").document(task_doc.id).update({
                    "assigned_to": updated_assignees
                })

        except Exception as e:
            raise Exception(f"Error while updating task assignments: {str(e)}")
        
    @staticmethod
    def update_taskboard(taskboard_id: str, email: str, taskboard: TaskBoard):
        try:
            doc_ref = firestore_db.collection('task_board').document(taskboard_id)
            snapshot = doc_ref.get()
            
            if not snapshot.exists:
                raise Exception("Taskboard does not exist")

            taskboard_doc = snapshot.to_dict()

            if email != taskboard.created_by:
                raise Exception("Only the creator can edit the board")

            existing_taskboards = (
                firestore_db.collection('task_board')
                .where('title', '==', taskboard.title)
                .get()
            )

            for doc in existing_taskboards:
                if doc.id != taskboard_id:
                    raise Exception("Name already exists. Please use a different one")

            # Validate each user
            for user_email in taskboard.users:
                user_check = firestore_db.collection('users').where('email', '==', user_email).limit(1).get()
                if len(user_check) == 0:
                    raise Exception(f"User {user_email} not found. Please assign only existing users.")

            doc_ref.update({
                "title": taskboard.title,
                "users": taskboard.users
            })

            updated = doc_ref.get().to_dict()

            
            updated_taskboard = {
                "users": taskboard.users,
                "created_by": taskboard.created_by,
                "title": taskboard.title,
                "id": taskboard_id
            }
            print("in service method")
            print(updated_taskboard)
            TaskBoardService.remove_user_from_tasks(updated_taskboard['users'],taskboard_id)
            return updated_taskboard

        except Exception as e:
            raise Exception(f"Error updating taskboard: {str(e)}")
        
    @staticmethod
    def delete_taskboard(taskboard_id: str, email: str):
        try:
            doc_ref = firestore_db.collection('task_board').document(taskboard_id)
            snapshot = doc_ref.get()

            if not snapshot.exists:
                raise Exception("Taskboard does not exist")

            taskboard_data = snapshot.to_dict()

            if taskboard_data.get("created_by") != email:
                raise Exception("Only the creator of the taskboard can delete the board")

            if len(taskboard_data.get("users"))>1:
                raise Exception("Remove all users from the taskboard before deleting it")

            doc_ref.delete()
            return {"message": "Taskboard deleted successfully", "id": taskboard_id}

        except Exception as e:
            raise Exception(f"Error deleting taskboard: {str(e)}")
