"""Popula a base local a partir de um ou mais CSVs de sinistros, sem precisar
subir o servidor HTTP. Aceita qualquer schema reconhecível pelo mapeamento
por-alias em `app/services/adapters.py` (formato oficial INFOSIGA e outros) —
não há formato fixo obrigatório. Útil para bootstrap inicial e para
alimentar a base incrementalmente com fontes diferentes.

Uso: python scripts/seed_from_csv.py [arquivo1.csv arquivo2.csv ...]
(sem argumentos: usa dados/sinistros_12-2025.csv)
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from app.db.session import Base, SessionLocal, engine  # noqa: E402
from app.services.ingestion_service import ingest_csv_bytes  # noqa: E402


def main(csv_paths: list[Path]) -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for csv_path in csv_paths:
            content = csv_path.read_bytes()
            summary = ingest_csv_bytes(db, content, csv_path.name)
            print(f"=== {csv_path.name} ===")
            print(summary.model_dump_json(indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    default_path = ROOT / "dados" / "sinistros_12-2025.csv"
    args = sys.argv[1:] or [str(default_path)]
    main([Path(a) for a in args])
