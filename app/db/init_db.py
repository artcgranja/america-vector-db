from app.db.base import Base
from app.db.models import SubjectModel, PrimaryDocumentModel, SecondaryDocumentModel
from app.db.session import engine

def init_db():
    """
    Initialize the database by creating all tables defined in the models.
    """
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    print("Creating database tables...")
    init_db()
    print("Database tables created successfully!") 