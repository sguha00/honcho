import os

from dotenv import load_dotenv

# from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

# from sqlalchemy.orm import sessionmaker

load_dotenv()


connect_args = {}

if (
    os.environ["DATABASE_TYPE"] == "sqlite"
):  # https://fastapi.tiangolo.com/tutorial/sql-databases/#note
    connect_args = {"check_same_thread": False}

engine = create_async_engine(
    os.environ["CONNECTION_URI"], connect_args=connect_args, echo=True
)

SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
