from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.auth import router as auth_router
from app.routers.accounts import router as accounts_router
from app.routers import rates

import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="kris Bank Api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", os.getenv("CORS_ORIGIN")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(accounts_router)
app.include_router(rates.router)


@app.get("/")
def root():
    return {"Message": "Kris Bank API"}

