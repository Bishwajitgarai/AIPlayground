from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.services.gemini_client import google_client,GeminiResponse
from app.core.config import settings
from google.genai.types import Part, GenerateContentConfig



user_router = APIRouter(tags=["User list"], prefix="/user")

@user_router.get("/{query}")
async def get_query(query: str):
    """
    Call Gemini chat model with the given query
    """
    try:
        response = google_client.models.generate_content(
            model=settings.GEMINI_CHAT_MODEL,
            config=GenerateContentConfig(
                temperature=1.0,
                top_k=40,      # must be int
                top_p=0.95,
                response_schema=GeminiResponse,
                response_mime_type="application/json",
                system_instruction="You are a chatbot"
            ),
            contents=[Part.from_text(text=query)],   # ✅ use actual query
        )

        if not response.candidates:
            return JSONResponse(
                status_code=500,
                content={"status_code": 500, "message": "No response from Gemini"},
            )

        # Use instantiated objects.
        response_data: GeminiResponse = response.parsed

        
        return JSONResponse(
            status_code=500,
            content={"status_code": 500, "message": response_data.model_dump()},
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "message": "Error while fetching from Gemini",
                "error": str(e),
            },
        )
