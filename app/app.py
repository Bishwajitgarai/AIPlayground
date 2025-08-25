from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routes.user import user_router


app=FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"]
)


app.include_router(user_router, prefix="/api")

@app.get("/")
async def home():
    return JSONResponse({
        "success":True,"message":"Running..."
    })
