
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create engine
# check_same_thread=False is needed for SQLite in multi-threaded envs like Streamlit
connect_args = {
    "check_same_thread": False} if "sqlite" in settings.SQLALCHEMY_DATABASE_URI else {}

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
