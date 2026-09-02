from fastapi.testclient import TestClient

from app.db.models import Sinistro
from app.db.session import Base, SessionLocal, engine
from app.main import app


def setup_module() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.add(
            Sinistro(
                source_name="teste",
                source_row_id="999999",
                id_sinistro=999999,
                municipio="RIBEIRAO PRETO",
                latitude=-21.1775,
                longitude=-47.8103,
                logradouro="Rua Teste",
                tp_sinistro_primario="COLISAO",
            )
        )
        db.commit()
    finally:
        db.close()


def test_mapa_retorna_html_com_ponto_geocodificado():
    client = TestClient(app)
    response = client.get("/mapa")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "leaflet" in response.text.lower()
    assert "Rua Teste" in response.text
