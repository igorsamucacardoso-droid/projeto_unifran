import io
from pathlib import Path

import pytest

from app.services.adapters import LinhaInvalidaError, parse_row_generico

CSV_OFICIAL_PATH = Path(__file__).resolve().parents[1] / "dados" / "sinistros_12-2025.csv"
CSV_ALTERNATIVO_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "acidentes_ribeirao_preto.csv"
)


def test_parse_row_formato_oficial_infosiga():
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
    parsed = parse_row_generico(raw)

    assert parsed.fields["id_sinistro"] == 2725247
    assert parsed.fields["data_sinistro"].isoformat() == "2025-12-01"
    assert parsed.fields["hora_sinistro"].isoformat() == "12:46:00"
    assert parsed.fields["latitude"] == -20.0393654
    assert parsed.fields["longitude"] == -47.7684727
    assert parsed.fields["qtd_automovel"] == 1
    assert parsed.fields["tp_sinistro_colisao_frontal"] is True
    assert parsed.fields["tp_sinistro_choque"] is False
    assert parsed.source_row_id == "2725247"
    assert parsed.municipio_informado is True
    assert parsed.unmapped_columns == []


def test_parse_row_formato_diferente_e_mapeado_por_alias():
    raw = {
        "num_acidente": "3539713",
        "data_acidente": "2018-01-17",
        "codigo_ibge": "3543402",
        "tp_acidente": "COLISAO",
        "qtde_obitos": "1",
        "coluna_desconhecida": "valor qualquer",
    }
    parsed = parse_row_generico(raw)

    assert parsed.fields["id_sinistro"] == 3539713
    assert parsed.fields["data_sinistro"].isoformat() == "2018-01-17"
    assert parsed.fields["cod_ibge"] == 3543402
    assert parsed.fields["tp_sinistro_primario"] == "COLISAO"
    assert parsed.fields["qtd_gravidade_fatal"] == 1
    assert parsed.source_row_id == "3539713"
    # sem coluna de município reconhecida nesse formato
    assert parsed.municipio_informado is False
    assert "coluna_desconhecida" in parsed.unmapped_columns


def test_parse_row_sem_id_usa_hash_do_conteudo_como_chave():
    raw = {"logradouro": "Rua Teste", "latitude": "-21,17", "longitude": "-47,81"}
    parsed = parse_row_generico(raw)

    assert len(parsed.source_row_id) == 40  # sha1 hex
    assert any("sem coluna de id reconhecida" in a for a in parsed.warnings)

    # mesma linha -> mesma chave (idempotente mesmo sem id nativo)
    assert parse_row_generico(dict(raw)).source_row_id == parsed.source_row_id


def test_parse_row_sem_nenhuma_coluna_reconhecida_levanta_erro():
    with pytest.raises(LinhaInvalidaError):
        parse_row_generico({"coluna_aleatoria_1": "x", "coluna_aleatoria_2": "y"})


def test_csv_oficial_real_todas_as_linhas_sao_mapeaveis():
    import csv

    text = CSV_OFICIAL_PATH.read_bytes().decode("latin-1")
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    rp_rows = [r for r in reader if (r.get("municipio") or "").strip().upper() == "RIBEIRAO PRETO"]

    assert len(rp_rows) == 447
    for row in rp_rows:
        parsed = parse_row_generico(row)
        assert parsed.fields["id_sinistro"] is not None
        assert parsed.municipio_informado is True


@pytest.mark.skipif(not CSV_ALTERNATIVO_PATH.exists(), reason="arquivo de exemplo não presente neste ambiente")
def test_csv_alternativo_real_e_mapeavel_sem_derrubar_linhas():
    import csv

    text = CSV_ALTERNATIVO_PATH.read_bytes().decode("utf-8")
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    rows = list(reader)
    assert rows  # arquivo não está vazio

    for row in rows[:200]:  # amostra: arquivo real é grande, checar tudo é lento
        parsed = parse_row_generico(row)
        assert parsed.fields  # sempre mapeia pelo menos algo
