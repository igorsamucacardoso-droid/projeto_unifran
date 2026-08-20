"""Popula a base local a partir de um CSV no formato oficial, sem precisar
subir o servidor HTTP. Útil para bootstrap inicial e para reingestões manuais.

Uso: python scripts/seed_from_csv.py [caminho/para/arquivo.csv]
(padrão: dados/sinistros_12-2025.csv)
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from app.db.session import Base, SessionLocal, engine  # noqa: E402
from app.services.ingestion_service import ingest_csv_bytes  # noqa: E402


def main(csv_path: Path) -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        content = csv_path.read_bytes()
        summary = ingest_csv_bytes(db, content, csv_path.name)
        print(summary.model_dump_json(indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    default_path = ROOT / "dados" / "sinistros_12-2025.csv"
    arg = sys.argv[1] if len(sys.argv) > 1 else str(default_path)
    main(Path(arg))
