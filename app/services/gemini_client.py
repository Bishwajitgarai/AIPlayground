from app.core.config import settings
from google.genai import Client

from pydantic import BaseModel

class GeminiResponse(BaseModel):
    message:str




google_client= Client(
    api_key=settings.GEMINI_API_KEY
)