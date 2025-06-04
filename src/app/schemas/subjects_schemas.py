from pydantic import BaseModel, Field

class SubjectResponse(BaseModel):
    id: int = Field(..., description="ID do assunto")
    name: str = Field(..., description="Nome do assunto")
    class Config:
        from_attributes = True