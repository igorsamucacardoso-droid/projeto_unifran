"""Parsing do CSV oficial de sinistros.

O arquivo-fonte vem em ISO-8859-1 (latin-1), delimitado por ';' e com números
decimais em vírgula (padrão brasileiro) — isso é tratado aqui, isoladamente,
para o resto do pipeline só lidar com tipos Python já normalizados.
"""

import csv
import datetime as dt
from collections.abc import Iterator
from typing import Any, TextIO

CSV_ENCODING = "latin-1"
CSV_DELIMITER = ";"


class LinhaInvalidaError(ValueError):
    """Linha do CSV não pôde ser convertida para o schema esperado."""


def _to_int(value: str) -> int | None:
    value = (value or "").strip()
    if not value:
        return None
    return int(float(value))  # alguns campos vêm como "1.0"


def _to_coord(value: str) -> float | None:
    value = (value or "").strip()
    if not value:
        return None
    return float(value.replace(",", "."))


def _to_bool_flag(value: str) -> bool:
    return (value or "").strip().upper() == "S"


def _to_date(value: str) -> dt.date | None:
    value = (value or "").strip()
    if not value:
        return None
    return dt.datetime.strptime(value, "%d/%m/%Y").date()


def _to_time(value: str) -> dt.time | None:
    value = (value or "").strip()
    if not value:
        return None
    return dt.datetime.strptime(value, "%H:%M").time()


def parse_row(raw: dict[str, str]) -> dict[str, Any]:
    """Converte uma linha crua do CSV (dict de strings) no formato do model ORM.

    Levanta LinhaInvalidaError se um campo obrigatório estiver ausente/corrompido.
    """
    try:
        return {
            "id_sinistro": int(raw["id_sinistro"]),
            "tipo_registro": raw.get("tipo_registro") or None,
            "data_sinistro": _to_date(raw.get("data_sinistro", "")),
            "ano_sinistro": _to_int(raw.get("ano_sinistro", "")),
            "mes_sinistro": _to_int(raw.get("mes_sinistro", "")),
            "dia_sinistro": _to_int(raw.get("dia_sinistro", "")),
            "hora_sinistro": _to_time(raw.get("hora_sinistro", "")),
            "ano_mes_sinistro": raw.get("ano_mes_sinistro") or None,
            "dia_da_semana": raw.get("dia_da_semana") or None,
            "turno": raw.get("turno") or None,
            "logradouro": raw.get("logradouro") or None,
            "numero_logradouro": raw.get("numero_logradouro") or None,
            "tipo_via": raw.get("tipo_via") or None,
            "tipo_local": raw.get("tipo_local") or None,
            "latitude": _to_coord(raw.get("latitude", "")),
            "longitude": _to_coord(raw.get("longitude", "")),
            "cod_ibge": _to_int(raw.get("cod_ibge", "")),
            "municipio": raw.get("municipio") or None,
            "regiao_administrativa": raw.get("regiao_administrativa") or None,
            "administracao": raw.get("administracao") or None,
            "conservacao": raw.get("conservacao") or None,
            "circunscricao": raw.get("circunscricao") or None,
            "tp_sinistro_primario": raw.get("tp_sinistro_primario") or None,
            "qtd_pedestre": _to_int(raw.get("qtd_pedestre", "")),
            "qtd_bicicleta": _to_int(raw.get("qtd_bicicleta", "")),
            "qtd_motocicleta": _to_int(raw.get("qtd_motocicleta", "")),
            "qtd_automovel": _to_int(raw.get("qtd_automovel", "")),
            "qtd_onibus": _to_int(raw.get("qtd_onibus", "")),
            "qtd_caminhao": _to_int(raw.get("qtd_caminhao", "")),
            "qtd_veic_outros": _to_int(raw.get("qtd_veic_outros", "")),
            "qtd_veic_nao_disponivel": _to_int(raw.get("qtd_veic_nao_disponivel", "")),
            "qtd_gravidade_fatal": _to_int(raw.get("qtd_gravidade_fatal", "")),
            "qtd_gravidade_grave": _to_int(raw.get("qtd_gravidade_grave", "")),
            "qtd_gravidade_leve": _to_int(raw.get("qtd_gravidade_leve", "")),
            "qtd_gravidade_ileso": _to_int(raw.get("qtd_gravidade_ileso", "")),
            "qtd_gravidade_nao_disponivel": _to_int(
                raw.get("qtd_gravidade_nao_disponivel", "")
            ),
            "tp_sinistro_atrop_pedestre": _to_bool_flag(
                raw.get("tp_sinistro_atrop_pedestre", "")
            ),
            "tp_sinistro_atrop_vitima_fora_veic": _to_bool_flag(
                raw.get("tp_sinistro_atrop_vitima_fora_veic", "")
            ),
            "tp_sinistro_colisao_frontal": _to_bool_flag(
                raw.get("tp_sinistro_colisao_frontal", "")
            ),
            "tp_sinistro_colisao_traseira": _to_bool_flag(
                raw.get("tp_sinistro_colisao_traseira", "")
            ),
            "tp_sinistro_colisao_lateral": _to_bool_flag(
                raw.get("tp_sinistro_colisao_lateral", "")
            ),
            "tp_sinistro_colisao_transversal": _to_bool_flag(
                raw.get("tp_sinistro_colisao_transversal", "")
            ),
            "tp_sinistro_colisao_outros": _to_bool_flag(
                raw.get("tp_sinistro_colisao_outros", "")
            ),
            "tp_sinistro_choque": _to_bool_flag(raw.get("tp_sinistro_choque", "")),
            "tp_sinistro_atrop_animal": _to_bool_flag(
                raw.get("tp_sinistro_atrop_animal", "")
            ),
            "tp_sinistro_capotamento": _to_bool_flag(
                raw.get("tp_sinistro_capotamento", "")
            ),
            "tp_sinistro_engavetamento": _to_bool_flag(
                raw.get("tp_sinistro_engavetamento", "")
            ),
            "tp_sinistro_tombamento": _to_bool_flag(
                raw.get("tp_sinistro_tombamento", "")
            ),
            "tp_sinistro_outros": _to_bool_flag(raw.get("tp_sinistro_outros", "")),
            "tp_sinistro_nao_disponivel": _to_bool_flag(
                raw.get("tp_sinistro_nao_disponivel", "")
            ),
        }
    except (KeyError, ValueError) as exc:
        raise LinhaInvalidaError(str(exc)) from exc


def iter_raw_rows(csv_text: TextIO) -> Iterator[dict[str, str]]:
    reader = csv.DictReader(csv_text, delimiter=CSV_DELIMITER)
    yield from reader
