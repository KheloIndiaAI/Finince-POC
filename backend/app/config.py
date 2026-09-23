"""Application configuration, loaded from environment / .env.

AWS access keys and the Bedrock token are NOT declared here so they can never be
logged via this object; boto3 reads them from the standard AWS environment
variables. The DB password is needed to build the connection URL, so it lives
here — never log the settings object.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    aws_region: str = "ap-south-1"
    s3_bucket: str = ""
    claude_model: str = "global.anthropic.claude-sonnet-4-6"

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "ai_comparison"
    db_user: str = "app_user"
    db_password: str = ""

    # Comma-separated origins allowed to call the API (React dev server).
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
