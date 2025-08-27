from pydantic_settings import SettingsConfigDict,BaseSettings

class Settings(BaseSettings):

    REDIS_HOST:str
    REDIS_PORT:int
    REDIS_DB:int
    REDIS_PASSWORD:str

    GEMINI_API_KEY:str
    
    GEMINI_CHAT_MODEL:str
    GEMINI_LIVE_MODEL:str


    model_config=SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

settings=Settings()