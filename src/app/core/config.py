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

    admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
    # Hash bcrypt da senha (gerar com scripts/hash_password.py), nunca a senha em texto puro.
    admin_password_hash: str = os.getenv("ADMIN_PASSWORD_HASH", "")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )


settings = Settings()
