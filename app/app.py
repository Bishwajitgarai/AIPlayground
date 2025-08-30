from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routes.user import user_router
from app.routes.wsconnect import ws_router
from app.utils.token_verify import verify_token
from app.utils.logger import log_requests


app=FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Allow all origins
    allow_credentials=True,   # Allow cookies / auth headers
    allow_methods=["*"],      # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],      # Allow all headers
)

app.middleware("http")(verify_token)
app.middleware("http")(log_requests)


app.include_router(user_router, prefix="/api")
app.include_router(ws_router, prefix="/extension")

@app.get("/")
async def home():
    return JSONResponse({
        "success":True,"message":"Running..."
    })
