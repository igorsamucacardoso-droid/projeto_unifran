import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg://infosiga:infosiga@localhost:5432/infosiga"
    )
    municipio_alvo: str = os.getenv("MUNICIPIO_ALVO", "RIBEIRAO PRETO")


settings = Settings()
