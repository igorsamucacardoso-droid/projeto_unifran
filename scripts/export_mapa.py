"""Exporta o mapa de sinistros para um arquivo HTML estático e autocontido,
pronto para ser anexado/incorporado em outro site (ex.: via <iframe>).

Diferente do endpoint /mapa, este arquivo não depende do servidor FastAPI
rodando: os dados são embutidos diretamente no HTML no momento da exportação.
Os tiles do OpenStreetMap e as libs Leaflet continuam sendo carregados via
internet no navegador de quem acessa a página.

Uso: python scripts/export_mapa.py [caminho/de/saida.html]
(padrão: dados/mapa_sinistros.html)
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from app.api.routes.mapa import _pontos_from_rows, build_mapa_html  # noqa: E402
from app.db.models import Sinistro  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402


def main(output_path: Path) -> None:
    db = SessionLocal()
    try:
        total = db.query(Sinistro).count()
        rows = (
            db.query(Sinistro)
            .filter(Sinistro.latitude.is_not(None), Sinistro.longitude.is_not(None))
            .all()
        )
        html = build_mapa_html(_pontos_from_rows(rows), total)
    finally:
        db.close()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"Mapa exportado para {output_path} ({len(rows)} de {total} sinistros com coordenadas)")


if __name__ == "__main__":
    default_path = ROOT / "dados" / "mapa_sinistros.html"
    arg = sys.argv[1] if len(sys.argv) > 1 else str(default_path)
    main(Path(arg))
