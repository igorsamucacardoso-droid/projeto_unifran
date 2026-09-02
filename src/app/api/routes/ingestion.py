from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.schemas.sinistro import IngestionSummary
from app.services.ingestion_service import ingest_csv_bytes

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/csv", response_model=IngestionSummary)
async def ingest_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
) -> IngestionSummary:
    """Recebe um CSV no formato oficial e ingesta os sinistros do município alvo.

    Restrito ao admin do sistema (Bearer token obtido em POST /auth/login).
    Idempotente: reenviar o mesmo arquivo atualiza os registros existentes
    (upsert por id_sinistro) em vez de duplicar. Pensado para o admin poder
    alimentar a base incrementalmente conforme novos arquivos chegam.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="O arquivo enviado deve ser .csv")

    content = await file.read()
    return ingest_csv_bytes(db, content, file.filename)
