import io
from pathlib import Path

from app.services.csv_parser import CSV_ENCODING, iter_raw_rows, parse_row

CSV_PATH = Path(__file__).resolve().parents[1] / "sinistros_12-2025.csv"


def test_parse_row_converte_tipos_e_encoding():
    raw = {
        "id_sinistro": "2725247",
        "data_sinistro": "01/12/2025",
        "hora_sinistro": "12:46",
        "latitude": "-20,0393654",
        "longitude": "-47,7684727",
        "municipio": "IGARAPAVA",
        "qtd_automovel": "1",
        "tp_sinistro_colisao_frontal": "S",
        "tp_sinistro_choque": "",
    }
    parsed = parse_row(raw)

    assert parsed["id_sinistro"] == 2725247
    assert parsed["data_sinistro"].isoformat() == "2025-12-01"
    assert parsed["hora_sinistro"].isoformat() == "12:46:00"
    assert parsed["latitude"] == -20.0393654
    assert parsed["longitude"] == -47.7684727
    assert parsed["qtd_automovel"] == 1
    assert parsed["tp_sinistro_colisao_frontal"] is True
    assert parsed["tp_sinistro_choque"] is False


def test_csv_real_filtra_ribeirao_preto():
    text = CSV_PATH.read_bytes().decode(CSV_ENCODING)
    rows = list(iter_raw_rows(io.StringIO(text)))
    rp_rows = [r for r in rows if r["municipio"].strip().upper() == "RIBEIRAO PRETO"]

    assert len(rows) == 16816
    assert len(rp_rows) == 447

    for row in rp_rows:
        parse_row(row)  # não deve levantar exceção para nenhuma linha real
