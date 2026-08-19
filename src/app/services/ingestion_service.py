import datetime as dt
import io

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Sinistro
from app.schemas.sinistro import IngestionSummary
from app.services.csv_parser import (
    CSV_ENCODING,
    LinhaInvalidaError,
    iter_raw_rows,
    parse_row,
)


def ingest_csv_bytes(
    db: Session, file_bytes: bytes, source_filename: str
) -> IngestionSummary:
    """Ingesta um CSV no formato oficial, restrito ao município configurado
    (padrão: Ribeirão Preto). Reingestões fazem upsert por id_sinistro, então
    rodar o mesmo arquivo de novo é seguro (idempotente).
    """
    text = file_bytes.decode(CSV_ENCODING)
    total = inserted = updated = skipped_other_municipio = skipped_invalid = 0

    for raw_row in iter_raw_rows(io.StringIO(text)):
        total += 1

        municipio = (raw_row.get("municipio") or "").strip().upper()
        if municipio != settings.municipio_alvo:
            skipped_other_municipio += 1
            continue

        try:
            data = parse_row(raw_row)
        except LinhaInvalidaError:
            skipped_invalid += 1
            continue

        data["source_file"] = source_filename
        data["ingested_at"] = dt.datetime.utcnow()

        existing = db.get(Sinistro, data["id_sinistro"])
        if existing is not None:
            for key, value in data.items():
                setattr(existing, key, value)
            updated += 1
        else:
            db.add(Sinistro(**data))
            inserted += 1

    db.commit()

    return IngestionSummary(
        source_file=source_filename,
        total_rows=total,
        inserted=inserted,
        updated=updated,
        skipped_other_municipio=skipped_other_municipio,
        skipped_invalid=skipped_invalid,
    )
