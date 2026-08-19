import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.models import Sinistro
from app.db.session import get_db
from app.schemas.sinistro import SinistroOut

router = APIRouter(prefix="/sinistros", tags=["sinistros"])


@router.get("", response_model=list[SinistroOut])
def list_sinistros(
    tipo_registro: str | None = None,
    data_inicio: dt.date | None = None,
    data_fim: dt.date | None = None,
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[Sinistro]:
    """Consulta paginada dos sinistros ingeridos — pensada para o time de
    análise de dados puxar lotes conforme a base cresce, sem acesso direto ao banco.
    """
    query = db.query(Sinistro)
    if tipo_registro:
        query = query.filter(Sinistro.tipo_registro == tipo_registro)
    if data_inicio:
        query = query.filter(Sinistro.data_sinistro >= data_inicio)
    if data_fim:
        query = query.filter(Sinistro.data_sinistro <= data_fim)

    return (
        query.order_by(Sinistro.data_sinistro, Sinistro.id_sinistro)
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/{id_sinistro}", response_model=SinistroOut)
def get_sinistro(id_sinistro: int, db: Session = Depends(get_db)) -> Sinistro:
    obj = db.get(Sinistro, id_sinistro)
    if obj is None:
        raise HTTPException(status_code=404, detail="Sinistro não encontrado")
    return obj
