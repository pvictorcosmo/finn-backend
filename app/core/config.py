from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    groq_api_key: str
    my_phone: str = ""
    port: int = 3000
    render_external_url: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"



settings = Settings()
