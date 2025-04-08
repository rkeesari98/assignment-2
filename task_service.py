from datetime import date, datetime, time
from typing import Any, Dict
from models import Task
from taskboard_service import TaskBoardService
from fastapi import Request
from google.auth.transport import requests
from google.cloud import firestore


firestore_db = firestore.Client()

firebase_request_adapter = requests.Request()

class TaskService:

    @staticmethod
    def create_task(task: Task):
        try:
            TaskBoardService.get_task_board(task.board_id)

            # Using keyword arguments for where queries as recommended
            existing_task = (
                firestore_db.collection('tasks')
                .where(filter=firestore.FieldFilter("board_id", "==", task.board_id))
                .where(filter=firestore.FieldFilter("title", "==", task.title))
                .limit(1)
                .get()
            )

            if len(existing_task) > 0:
                raise Exception("Tasks in the same board must have different names")

            # Use the to_dict method to get Firestore-compatible dict
            task_dict = task.dict(exclude_none=True)
            if task.due_date:
                task_dict['due_date'] = task.due_date.isoformat()
            if task.due_time:
                task_dict['due_time'] = task.due_time.strftime("%H:%M")

            firestore_db.collection("tasks").add(task_dict)

        except Exception as e:
            print(f"Firestore error: {e}")  # Add detailed logging
            raise Exception(str(e))

        
    @staticmethod
    def update_task(task_board_id:str,task_id:str,task:Task):
        try:
            if task.board_id != task_board_id:
                raise Exception("Task does not belongs to given board id")
            task_ref = firestore_db.collection("tasks").document(task_id)
            snapshot = task_ref.get()
            if not snapshot.exists:
                raise Exception("Invalid task id please enter valid task id")
            task_dict = task.dict(exclude_none=True)
            if task.due_date:
                task_dict["due_date"] = task.due_date.isoformat()  # 'YYYY-MM-DD'
            if task.due_time:
                task_dict["due_time"] = task.due_time.strftime("%H:%M")  # 'HH:MM'
            task_ref.update(task_dict)
        except Exception as e:
            raise Exception(e)
        
    @staticmethod
    def get_tasks(task_board_id):
        try:
            tasks_ref = firestore_db.collection('tasks')
            query = tasks_ref.where('board_id', '==', task_board_id)
            tasks = query.stream()
            
            task_list = []
            for task in tasks:
                task_data = task.to_dict()
                task_data['id'] = task.id

                # Convert due_date and due_time safely
                if 'due_date' in task_data:
                    if isinstance(task_data['due_date'], str):
                        try:
                            task_data['due_date'] = datetime.fromisoformat(task_data['due_date']).date()
                        except ValueError:
                            task_data['due_date'] = None
                    elif isinstance(task_data['due_date'], datetime):
                        task_data['due_date'] = task_data['due_date'].date()

                if 'due_time' in task_data:
                    if isinstance(task_data['due_time'], str):
                        try:
                            task_data['due_time'] = datetime.strptime(task_data['due_time'], "%H:%M:%S").time()
                        except ValueError:
                            task_data['due_time'] = None
                    elif isinstance(task_data['due_time'], datetime):
                        task_data['due_time'] = task_data['due_time'].time()
                assigned_to = task_data.get('assigned_to', [])
                task_data['unassigned'] = not assigned_to or len(assigned_to) == 0
                task_list.append(task_data)

            return task_list

        except Exception as e:
            raise Exception(f"Error getting tasks: {e}")

    @staticmethod
    def mark_task_as_complete(task_id: str):
        try:
            doc_ref = firestore_db.collection('tasks').document(task_id)
            task = doc_ref.get()
            if not task.exists:
                raise Exception("Invalid task id")
            current_datetime = datetime.now()
            doc_ref.update({
                "status": "completed",
                "due_date": current_datetime.date().isoformat(), 
                "due_time": current_datetime.time().strftime("%H:%M:%S")  
            })
        except Exception as e:
            raise Exception(str(e))

    @staticmethod
    def delete_task(task_id:str):
        try:
            doc_ref = firestore_db.collection('tasks').document(task_id)
            task = doc_ref.get()
            if not task.exists:
                raise Exception("Invalid task id")
            doc_ref.delete() 
        except Exception as e:
            raise Exception(str(e))
    @staticmethod
    def get_task(task_id):
        try:
            task_ref = firestore_db.collection("tasks").document(task_id)
            task = task_ref.get()
            
            if not task.exists:
                return None
                
            task_data = task.to_dict()
            task_data["id"] = task_id
            
            if task_data.get("due_date"):
                if isinstance(task_data["due_date"], date):
                    task_data["due_date"] = task_data["due_date"].strftime('%Y-%m-%d')
                    
            if task_data.get("due_time"):
                if isinstance(task_data["due_time"], time):
                    task_data["due_time"] = task_data["due_time"].strftime('%H:%M')
                    
            if task_data.get("completed_at"):
                if isinstance(task_data["completed_at"], datetime):
                    task_data["completed_at"] = task_data["completed_at"].strftime('%b %d, %Y at %I:%M %p')
            
            return task_data
        except Exception as e:
            print(f"Error getting task: {e}")
            raise Exception(f"Error retrieving task: {str(e)}")
        
   