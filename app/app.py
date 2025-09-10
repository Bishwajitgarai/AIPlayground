from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse,HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from app.routes.user import user_router
from app.routes.wsconnect import ws_router
from app.routes.gmail import gmail_router
from app.utils.token_verify import verify_token
from app.utils.logger import log_requests
from app.core.db import Base, engine, get_db


app=FastAPI()

# Create tables (for dev; in prod you should use Alembic)
Base.metadata.create_all(bind=engine)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Allow all origins
    allow_credentials=True,   # Allow cookies / auth headers
    allow_methods=["*"],      # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],      # Allow all headers
)

app.middleware("http")(verify_token)
app.middleware("http")(log_requests)
templates = Jinja2Templates(directory="app/templates")


app.include_router(user_router, prefix="/api")
app.include_router(gmail_router, prefix="/api")
app.include_router(ws_router, prefix="/extension")

# @app.get("/")
# async def home():
#     return JSONResponse({
#         "success":True,"message":"Running..."
#     })

# Serve index.html at root
@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})