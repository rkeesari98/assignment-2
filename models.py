from typing import List

from pydantic import BaseModel
from datetime import date

class TaskBoard(BaseModel):
    title:str
    created_by:str
    tasks:List[str]
    users:List[str]
    
class User(BaseModel):
    name:str
    email:str

class Task(BaseModel):
    name:str
    status:str
    details:str
    assigned_to:List[str]
    due_date:date