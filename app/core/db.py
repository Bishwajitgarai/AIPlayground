from enum import Enum
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from app.core.config import settings
from collections.abc import Generator



class DBType(str, Enum):
    SQLITE = "sqlite"
    MYSQL = "mysql"
    POSTGRES = "postgres"


def get_database_url() -> str:
    if settings.DB_TYPE == DBType.SQLITE:
        return f"sqlite:///./{settings.DB_NAME}.db"
    elif settings.DB_TYPE == DBType.MYSQL:
        return (
            f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
            f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        )
    elif settings.DB_TYPE == DBType.POSTGRES:
        return (
            f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASSWORD}"
            f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        )
    else:
        raise ValueError(f"Unsupported DB_TYPE: {settings.DB_TYPE}")


SQLALCHEMY_DATABASE_URL = get_database_url()

# SQLite needs check_same_thread
connect_args = {"check_same_thread": False} if settings.DB_TYPE == DBType.SQLITE else {}

# Engine
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# Dependency for FastAPI
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
