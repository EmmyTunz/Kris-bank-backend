from fastapi import FastAPI
from app.routers.auth import router as auth_router

app = FastAPI(title="kris Bank Api")

app.include_router(auth_router)

@app.get("/")
def root():
    return {"Message": "Kris Bank API"}

