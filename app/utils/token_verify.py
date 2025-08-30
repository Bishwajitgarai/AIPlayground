from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


async def verify_token(request: Request, call_next):
    # Skip docs or public routes if you want
    if request.url.path.startswith("/docs"):
        return await call_next(request)

    # token = request.headers.get("Authorization")
    
    # if not token or token != "Bishwajit":
    #     return JSONResponse(
    #         status_code=401,
    #         content={"detail": "Unauthorized - Invalid or missing token"},
    #     )

    # Token is valid -> process request
    response = await call_next(request)
    return response


