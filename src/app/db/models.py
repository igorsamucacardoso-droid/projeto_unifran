import datetime as dt

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Sinistro(Base):
    """Registro de sinistro de trânsito, escopo Ribeirão Preto-SP.

    Colunas espelham o CSV oficial (id_sinistro é a chave natural do dado-fonte,
    por isso é usada como PK para permitir upsert em reingestões).
    """

    __tablename__ = "sinistros"

    id_sinistro: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo_registro: Mapped[str | None] = mapped_column(String(50))

    data_sinistro: Mapped[dt.date | None] = mapped_column(Date)
    ano_sinistro: Mapped[int | None] = mapped_column(Integer)
    mes_sinistro: Mapped[int | None] = mapped_column(Integer)
    dia_sinistro: Mapped[int | None] = mapped_column(Integer)
    hora_sinistro: Mapped[dt.time | None] = mapped_column(Time)
    ano_mes_sinistro: Mapped[str | None] = mapped_column(String(10))
    dia_da_semana: Mapped[str | None] = mapped_column(String(20))
    turno: Mapped[str | None] = mapped_column(String(20))

    logradouro: Mapped[str | None] = mapped_column(String(255))
    numero_logradouro: Mapped[str | None] = mapped_column(String(20))
    tipo_via: Mapped[str | None] = mapped_column(String(50))
    tipo_local: Mapped[str | None] = mapped_column(String(50))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    cod_ibge: Mapped[int | None] = mapped_column(Integer)
    municipio: Mapped[str | None] = mapped_column(String(100), index=True)
    regiao_administrativa: Mapped[str | None] = mapped_column(String(100))
    administracao: Mapped[str | None] = mapped_column(String(50))
    conservacao: Mapped[str | None] = mapped_column(String(50))
    circunscricao: Mapped[str | None] = mapped_column(String(50))

    tp_sinistro_primario: Mapped[str | None] = mapped_column(String(50))

    qtd_pedestre: Mapped[int | None] = mapped_column(Integer)
    qtd_bicicleta: Mapped[int | None] = mapped_column(Integer)
    qtd_motocicleta: Mapped[int | None] = mapped_column(Integer)
    qtd_automovel: Mapped[int | None] = mapped_column(Integer)
    qtd_onibus: Mapped[int | None] = mapped_column(Integer)
    qtd_caminhao: Mapped[int | None] = mapped_column(Integer)
    qtd_veic_outros: Mapped[int | None] = mapped_column(Integer)
    qtd_veic_nao_disponivel: Mapped[int | None] = mapped_column(Integer)

    qtd_gravidade_fatal: Mapped[int | None] = mapped_column(Integer)
    qtd_gravidade_grave: Mapped[int | None] = mapped_column(Integer)
    qtd_gravidade_leve: Mapped[int | None] = mapped_column(Integer)
    qtd_gravidade_ileso: Mapped[int | None] = mapped_column(Integer)
    qtd_gravidade_nao_disponivel: Mapped[int | None] = mapped_column(Integer)

    tp_sinistro_atrop_pedestre: Mapped[bool] = mapped_column(Boolean, default=False)
    tp_sinistro_atrop_vitima_fora_veic: Mapped[bool] = mapped_column(Boolean, default=False)
    tp_sinistro_colisao_frontal: Mapped[bool] = mapped_column(Boolean, default=False)
    tp_sinistro_colisao_traseira: Mapped[bool] = mapped_column(Boolean, default=False)
    tp_sinistro_colisao_lateral: Mapped[bool] = mapped_column(Boolean, default=False)
    tp_sinistro_colisao_transversal: Mapped[bool] = mapped_column(Boolean, default=False)
    tp_sinistro_colisao_outros: Mapped[bool] = mapped_column(Boolean, default=False)
    tp_sinistro_choque: Mapped[bool] = mapped_column(Boolean, default=False)
    tp_sinistro_atrop_animal: Mapped[bool] = mapped_column(Boolean, default=False)
    tp_sinistro_capotamento: Mapped[bool] = mapped_column(Boolean, default=False)
    tp_sinistro_engavetamento: Mapped[bool] = mapped_column(Boolean, default=False)
    tp_sinistro_tombamento: Mapped[bool] = mapped_column(Boolean, default=False)
    tp_sinistro_outros: Mapped[bool] = mapped_column(Boolean, default=False)
    tp_sinistro_nao_disponivel: Mapped[bool] = mapped_column(Boolean, default=False)

    # Metadados de proveniência: importam porque a ingestão é repetida ao longo
    # do tempo (novos arquivos), então precisamos rastrear de onde cada linha veio.
    source_file: Mapped[str | None] = mapped_column(String(255))
    ingested_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=dt.datetime.utcnow
    )
