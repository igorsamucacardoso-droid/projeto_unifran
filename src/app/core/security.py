"""Autenticação do admin: hash de senha (bcrypt) e tokens de acesso (JWT).

Login é single-user (um único admin, credenciais vêm de variáveis de
ambiente via `settings`) — não há tabela de usuários porque o sistema só
precisa distinguir "admin autenticado" de "não autenticado" para liberar a
importação de dados.
"""

import datetime as dt

import bcrypt
import jwt

from app.core.config import settings

TOKEN_SUBJECT_CLAIM = "sub"


def verify_password(plain_password: str, password_hash: str) -> bool:
    if not password_hash:
        return False
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(subject: str) -> str:
    expires_at = dt.datetime.now(dt.timezone.utc) + dt.timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {TOKEN_SUBJECT_CLAIM: subject, "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str | None:
    """Retorna o `subject` do token se válido, ou None (assinatura/expiração inválida)."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except jwt.PyJWTError:
        return None
    return payload.get(TOKEN_SUBJECT_CLAIM)
