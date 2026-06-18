from pydantic import BaseModel
from typing import List

class SourceItem(BaseModel):
    chunk_id:int
    text:str

class QuestionRequest(BaseModel):
    question:str
    

class QuestionResponse(BaseModel):
    answer:str
    sources:List[SourceItem]

    
