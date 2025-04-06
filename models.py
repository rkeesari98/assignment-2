from typing import List, Optional

from pydantic import BaseModel
from datetime import date, time

class TaskBoard(BaseModel):
    title:str
    created_by:str
    users:List[str]
    
class User(BaseModel):
    name:str
    email:str

class Task(BaseModel):
    title:str
    status:str
    details:str
    assigned_to:List[str]
    board_id:str
    due_date:Optional[date] = None
    due_time: Optional[time] = None