from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.orm import Session
from src.app.db.models.subjects import SubjectModel
from src.app.schemas.subjects_schemas import (
    SubjectResponse
)
from src.app.db.session import get_db_session
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/subjects",
    tags=["subjects"],
    responses={404: {"description": "Not found"}}
)

@router.get("/", summary="Lista todos os assuntos", response_model=List[SubjectResponse])
async def list_subjects(db: Session = Depends(get_db_session)):
    subjects = db.query(SubjectModel).all()
    return [SubjectResponse.model_validate(subject) for subject in subjects]