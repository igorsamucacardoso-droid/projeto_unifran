from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.schemas.auth import Token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    """Autentica o admin do sistema e retorna um token Bearer (JWT) a ser
    usado nos endpoints de importação de dados (`Authorization: Bearer <token>`).
    """
    valid_username = form_data.username == settings.admin_username
    valid_password = verify_password(form_data.password, settings.admin_password_hash)
    if not (valid_username and valid_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=form_data.username)
    return Token(access_token=access_token)
