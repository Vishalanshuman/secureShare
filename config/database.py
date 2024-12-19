from sqlalchemy.orm import declarative_base,sessionmaker
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URI=os.getenv("DATABASE_URI")

engine = create_engine(DATABASE_URI,connect_args={"check_same_thread": False})

Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base=declarative_base()

def get_db():
    db=Session()
    try:
        yield db
    finally:
        db.close()