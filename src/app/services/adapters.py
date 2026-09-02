"""Mapeamento genérico de linhas de CSV para os campos do model `Sinistro`.

Não assume um schema fixo: cada campo do model tem uma lista de nomes de
coluna aceitos (`_FIELD_MAP`), então CSVs de fontes diferentes (formato
oficial INFOSIGA, extrações parciais de outros sistemas, etc.) alimentam a
mesma base sem precisar de um parser dedicado por formato. O que não é
reconhecido não derruba a linha — vira um aviso e vai para `raw_data`
inteiro (ver `services/ingestion_service.py`), então nenhum dado bruto se
perde mesmo quando o formato é desconhecido.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


class LinhaInvalidaError(ValueError):
    """Linha não tem nenhuma coluna reconhecível — não há o que aproveitar."""


@dataclass
class ParsedRow:
    fields: dict[str, Any]
    source_row_id: str
    unmapped_columns: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    municipio_informado: bool = False


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return s.strip().lower().replace(" ", "_")


def _to_str(value: Any) -> str | None:
    v = str(value or "").strip()
    return v or None


def _to_int(value: Any) -> int | None:
    v = str(value or "").strip()
    if not v:
        return None
    return int(float(v.replace(",", ".")))  # alguns campos vêm como "1.0"


def _to_float(value: Any) -> float | None:
    v = str(value or "").strip()
    if not v:
        return None
    return float(v.replace(",", "."))


def _to_bool_flag(value: Any) -> bool:
    return str(value or "").strip().upper() in {"S", "SIM", "TRUE", "1", "YES"}


_DATE_FORMATS = ("%d/%m/%Y", "%Y-%m-%d")


def _to_date(value: Any) -> dt.date | None:
    v = str(value or "").strip()
    if not v:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return dt.datetime.strptime(v, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"data em formato não reconhecido: {v!r}")


_TIME_FORMATS = ("%H:%M", "%H:%M:%S", "%H%M%S")


def _to_time(value: Any) -> dt.time | None:
    v = str(value or "").strip()
    if not v:
        return None
    for fmt in _TIME_FORMATS:
        try:
            return dt.datetime.strptime(v, fmt).time()
        except ValueError:
            continue
    raise ValueError(f"hora em formato não reconhecido: {v!r}")


# Campo do model -> (nomes de coluna aceitos, já normalizados, função de
# conversão). A primeira alias encontrada no CSV vence.
_FIELD_MAP: dict[str, tuple[tuple[str, ...], Callable[[Any], Any]]] = {
    "id_sinistro": (("id_sinistro", "num_acidente", "id_acidente"), _to_int),
    "tipo_registro": (("tipo_registro",), _to_str),
    "data_sinistro": (("data_sinistro", "data_acidente", "data"), _to_date),
    "ano_sinistro": (("ano_sinistro", "ano_acidente"), _to_int),
    "mes_sinistro": (("mes_sinistro", "mes_acidente"), _to_int),
    "dia_sinistro": (("dia_sinistro",), _to_int),
    "hora_sinistro": (("hora_sinistro", "hora_acidente"), _to_time),
    "ano_mes_sinistro": (("ano_mes_sinistro", "mes_ano_acidente"), _to_str),
    "dia_da_semana": (("dia_da_semana", "dia_semana"), _to_str),
    "turno": (("turno", "fase_dia"), _to_str),
    "logradouro": (("logradouro", "end_acidente", "endereco"), _to_str),
    "numero_logradouro": (("numero_logradouro", "num_end_acidente"), _to_str),
    "tipo_via": (("tipo_via", "tp_rodovia"), _to_str),
    "tipo_local": (("tipo_local", "tp_cruzamento"), _to_str),
    "latitude": (("latitude", "latitude_acidente", "lat"), _to_float),
    "longitude": (("longitude", "longitude_acidente", "lon", "lng"), _to_float),
    "cod_ibge": (("cod_ibge", "codigo_ibge"), _to_int),
    "municipio": (("municipio", "cidade"), _to_str),
    "regiao_administrativa": (("regiao_administrativa",), _to_str),
    "administracao": (("administracao",), _to_str),
    "conservacao": (("conservacao",), _to_str),
    "circunscricao": (("circunscricao",), _to_str),
    "tp_sinistro_primario": (("tp_sinistro_primario", "tp_acidente"), _to_str),
    "qtd_pedestre": (("qtd_pedestre",), _to_int),
    "qtd_bicicleta": (("qtd_bicicleta",), _to_int),
    "qtd_motocicleta": (("qtd_motocicleta",), _to_int),
    "qtd_automovel": (("qtd_automovel",), _to_int),
    "qtd_onibus": (("qtd_onibus",), _to_int),
    "qtd_caminhao": (("qtd_caminhao",), _to_int),
    "qtd_veic_outros": (("qtd_veic_outros",), _to_int),
    "qtd_veic_nao_disponivel": (("qtd_veic_nao_disponivel",), _to_int),
    "qtd_gravidade_fatal": (("qtd_gravidade_fatal", "qtde_obitos"), _to_int),
    "qtd_gravidade_grave": (("qtd_gravidade_grave",), _to_int),
    "qtd_gravidade_leve": (("qtd_gravidade_leve",), _to_int),
    "qtd_gravidade_ileso": (("qtd_gravidade_ileso",), _to_int),
    "qtd_gravidade_nao_disponivel": (("qtd_gravidade_nao_disponivel",), _to_int),
    "tp_sinistro_atrop_pedestre": (("tp_sinistro_atrop_pedestre",), _to_bool_flag),
    "tp_sinistro_atrop_vitima_fora_veic": (
        ("tp_sinistro_atrop_vitima_fora_veic",),
        _to_bool_flag,
    ),
    "tp_sinistro_colisao_frontal": (("tp_sinistro_colisao_frontal",), _to_bool_flag),
    "tp_sinistro_colisao_traseira": (("tp_sinistro_colisao_traseira",), _to_bool_flag),
    "tp_sinistro_colisao_lateral": (("tp_sinistro_colisao_lateral",), _to_bool_flag),
    "tp_sinistro_colisao_transversal": (
        ("tp_sinistro_colisao_transversal",),
        _to_bool_flag,
    ),
    "tp_sinistro_colisao_outros": (("tp_sinistro_colisao_outros",), _to_bool_flag),
    "tp_sinistro_choque": (("tp_sinistro_choque",), _to_bool_flag),
    "tp_sinistro_atrop_animal": (("tp_sinistro_atrop_animal",), _to_bool_flag),
    "tp_sinistro_capotamento": (("tp_sinistro_capotamento",), _to_bool_flag),
    "tp_sinistro_engavetamento": (("tp_sinistro_engavetamento",), _to_bool_flag),
    "tp_sinistro_tombamento": (("tp_sinistro_tombamento",), _to_bool_flag),
    "tp_sinistro_outros": (("tp_sinistro_outros",), _to_bool_flag),
    "tp_sinistro_nao_disponivel": (("tp_sinistro_nao_disponivel",), _to_bool_flag),
}

_MUNICIPIO_ALIASES = _FIELD_MAP["municipio"][0]


def parse_row_generico(raw: dict[str, str]) -> ParsedRow:
    normalized = {_norm(k): v for k, v in raw.items() if k}

    fields: dict[str, Any] = {}
    warnings: list[str] = []
    matched_keys: set[str] = set()

    for campo, (aliases, coercer) in _FIELD_MAP.items():
        for alias in aliases:
            if alias in normalized:
                matched_keys.add(alias)
                bruto = normalized[alias]
                try:
                    fields[campo] = coercer(bruto)
                except ValueError as exc:
                    fields[campo] = None
                    warnings.append(
                        f"campo '{campo}' (coluna '{alias}'): {exc}"
                    )
                break

    if not fields:
        raise LinhaInvalidaError("nenhuma coluna reconhecida nesta linha")

    unmapped = sorted(k for k in normalized if k not in matched_keys and normalized[k])

    id_natural = fields.get("id_sinistro")
    if id_natural is not None:
        source_row_id = str(id_natural)
    else:
        raw_repr = "|".join(f"{k}={v}" for k, v in sorted(raw.items()))
        source_row_id = hashlib.sha1(raw_repr.encode("utf-8")).hexdigest()
        warnings.append(
            "sem coluna de id reconhecida — usando hash do conteúdo da linha "
            "como chave; uma edição no arquivo-fonte gera uma linha nova em "
            "vez de atualizar a existente"
        )

    return ParsedRow(
        fields=fields,
        source_row_id=source_row_id,
        unmapped_columns=unmapped,
        warnings=warnings,
        municipio_informado=any(a in normalized for a in _MUNICIPIO_ALIASES),
    )
