from typing import List
from pydantic import BaseModel, Field

class ClassifierResponse(BaseModel):
    subjects: List[str] = Field(
        ..., 
        description="Lista de assuntos do documento"
    )
    
    class Config:
        use_enum_values = True