from app.core.database import engine, Base
from app.models.models import User, Attendance, Naryad, NaryadBrigade, Leave, Notification

def seed():
    """Initializes empty database tables with zero mock records."""
    Base.metadata.create_all(bind=engine)
    print("Database schema created cleanly. Zero mock data.")

if __name__ == "__main__":
    seed()
