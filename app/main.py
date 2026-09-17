from fastapi import FastAPI

app = FastAPI(title="kris Bank Api")

@app.get("/")
def root():
    return {"Message": "Kris Bank API"}

