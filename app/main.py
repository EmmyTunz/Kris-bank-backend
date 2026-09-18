from fastapi import FastAPI
from app.routers.auth import router as auth_router
from app.routers.accounts import router as accounts_router


app = FastAPI(title="kris Bank Api")

app.include_router(auth_router)
app.include_router(accounts_router)


@app.get("/")
def root():
    return {"Message": "Kris Bank API"}

