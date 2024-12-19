from fastapi import FastAPI
from Users.users import router as user_router
from files.file import router as file_router
from config.database import Base,engine

Base.metadata.create_all(bind=engine)
app = FastAPI()

@app.get("/health")
def health():
    return {"message":"Good Health!!!"}


app.include_router(user_router)
app.include_router(file_router)




