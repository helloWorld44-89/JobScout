from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost/jobscout"
    SECRET_KEY: str = "changeme"
    # AI / LiteLLM
    AI_MODEL: str = "gpt-4o-mini"
    AI_BASE_URL: str = ""  # Ollama endpoint, e.g. http://localhost:11434 or http://ollama:11434
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SCORE_THRESHOLD: int = 70

    # Auth
    APP_USERNAME: str = "admin"
    APP_PASSWORD_HASH: str = ""  # generate with: uv run python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('yourpassword'))"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"

    model_config = {"env_file": ".env"}


settings = Settings()
