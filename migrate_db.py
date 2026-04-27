from sqlalchemy import text
from backend.db.session import engine, init_db, SessionLocal
from backend.models.models import Base, User
from backend.services.auth import hash_password

def migrate():
    # Drop all tables and recreate them to ensure schema matches exactly
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Recreating all tables...")
    init_db()
    
    db = SessionLocal()
    try:
        new_user = User(
            username="admin",
            password_hash=hash_password("admin@123"),
            ho_ten="Quản trị viên hệ thống",
            role="admin",
            is_active=True,
            must_change_password=False
        )
        db.add(new_user)
        db.commit()
        print("Created admin user with password admin@123")
    except Exception as e:
        db.rollback()
        print(f"Error creating admin user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
