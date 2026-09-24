import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

from urllib.parse import urlparse

if DATABASE_URL:
    parsed_url = urlparse(DATABASE_URL)
    print("DATABASE DEBUG")
    print("  scheme:", parsed_url.scheme)
    print("  username:", parsed_url.username)
    print("  hostname:", parsed_url.hostname)
    print("  port:", parsed_url.port)
    print("  database:", parsed_url.path)
    print("  password_present:", bool(parsed_url.password))

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the .env file")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()