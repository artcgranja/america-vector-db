from src.app.db.models.subjects import SubjectModel, primary_subjects, secondary_subjects
from src.app.db.models.documents import PrimaryDocumentModel, SecondaryDocumentModel

__all__ = [
    'SubjectModel', 'PrimaryDocumentModel', 'SecondaryDocumentModel',
    'primary_subjects', 'secondary_subjects'
]