import csv
import datetime as dt
import io

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Sinistro
from app.schemas.sinistro import IngestionSummary
from app.services.adapters import LinhaInvalidaError, parse_row_generico

SOURCE_NAME = "csv_generico"
AVISOS_MAX = 50  # não deixa o resumo virar um arquivo de log inteiro


def _sniff_delimiter(sample: str) -> str:
    try:
        return csv.Sniffer().sniff(sample, delimiters=";,\t").delimiter
    except csv.Error:
        return ";"


def _decode(file_bytes: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return file_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    return file_bytes.decode("latin-1", errors="replace")


def ingest_csv_bytes(
    db: Session, file_bytes: bytes, source_filename: str
) -> IngestionSummary:
    """Ingesta um CSV de sinistros de formato arbitrário (ver
    `services/adapters.py`), restrito ao município configurado quando o
    arquivo declara essa coluna (padrão: Ribeirão Preto). Reingestões fazem
    upsert por `(source_name, source_row_id)`, então rodar o mesmo arquivo de
    novo é seguro (idempotente) mesmo sem um `id_sinistro` reconhecível.
    """
    text = _decode(file_bytes)
    delimiter = _sniff_delimiter(text[:4096])
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)

    total = inserted = updated = skipped_other_municipio = skipped_invalid = 0
    avisos: list[str] = []
    avisos_gerados = 0
    colunas_nao_mapeadas: set[str] = set()
    municipio_reconhecido_no_arquivo = False

    def registrar_aviso(msg: str) -> None:
        nonlocal avisos_gerados
        avisos_gerados += 1
        if len(avisos) < AVISOS_MAX:
            avisos.append(msg)

    for row_num, raw_row in enumerate(reader, start=2):  # linha 1 é o cabeçalho
        total += 1
        try:
            parsed = parse_row_generico(raw_row)
        except LinhaInvalidaError as exc:
            skipped_invalid += 1
            registrar_aviso(f"linha {row_num}: {exc}")
            continue

        colunas_nao_mapeadas.update(parsed.unmapped_columns)
        for aviso in parsed.warnings:
            registrar_aviso(f"linha {row_num}: {aviso}")

        if parsed.municipio_informado:
            municipio_reconhecido_no_arquivo = True
            municipio = (parsed.fields.get("municipio") or "").strip().upper()
            if municipio != settings.municipio_alvo:
                skipped_other_municipio += 1
                continue

        data = dict(parsed.fields)
        data["source_name"] = SOURCE_NAME
        data["source_row_id"] = parsed.source_row_id
        data["source_file"] = source_filename
        data["ingested_at"] = dt.datetime.now(dt.timezone.utc)
        data["raw_data"] = {str(k): v for k, v in raw_row.items() if k is not None}

        existing = (
            db.query(Sinistro)
            .filter(
                Sinistro.source_name == data["source_name"],
                Sinistro.source_row_id == data["source_row_id"],
            )
            .one_or_none()
        )
        if existing is not None:
            for key, value in data.items():
                setattr(existing, key, value)
            updated += 1
        else:
            db.add(Sinistro(**data))
            inserted += 1

    db.commit()

    if total and not municipio_reconhecido_no_arquivo:
        avisos.insert(
            0,
            "arquivo sem coluna de município reconhecida — filtro de "
            f"MUNICIPIO_ALVO ('{settings.municipio_alvo}') não foi aplicado, "
            "todas as linhas válidas foram aceitas",
        )

    if avisos_gerados > len(avisos):
        avisos.append(
            f"... e mais {avisos_gerados - len(avisos)} aviso(s) omitido(s) "
            f"(limite de exibição: {AVISOS_MAX})"
        )

    return IngestionSummary(
        source_file=source_filename,
        total_rows=total,
        inserted=inserted,
        updated=updated,
        skipped_other_municipio=skipped_other_municipio,
        skipped_invalid=skipped_invalid,
        colunas_nao_mapeadas=sorted(colunas_nao_mapeadas),
        avisos=avisos,
    )
