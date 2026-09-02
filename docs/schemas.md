# `src/app/schemas/`

Schemas Pydantic que definem os contratos de entrada/saída da API — a
"fronteira" entre o model ORM interno (`db/models.py`) e o JSON exposto pelos
endpoints.

## `sinistro.py`

### `SinistroOut`

```python
class SinistroOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source_name: str
    source_row_id: str
    id_sinistro: int | None
    ...
```

Representa um sinistro na saída da API (`GET /sinistros`, `GET
/sinistros/{id}`). `from_attributes=True` permite construir o schema
diretamente a partir de uma instância do model ORM `Sinistro`
(`SinistroOut.model_validate(obj)`, feito implicitamente pelo FastAPI via
`response_model`).

Não é um espelho 1:1 do model ORM: é um **subconjunto curado** dos campos —
por exemplo, inclui `tp_sinistro_colisao_frontal` mas não todas as ~13 flags
de tipo de sinistro do model (`tp_sinistro_colisao_transversal`,
`tp_sinistro_choque`, `tp_sinistro_atrop_animal` etc. ficam de fora). Ou
seja, ao adicionar um novo campo relevante ao model `Sinistro`, ele **não**
aparece automaticamente na API — precisa ser adicionado aqui também.

### `IngestionSummary`

```python
class IngestionSummary(BaseModel):
    source_file: str
    total_rows: int
    inserted: int
    updated: int
    skipped_other_municipio: int
    skipped_invalid: int
    colunas_nao_mapeadas: list[str] = []
    avisos: list[str] = []
```

Resposta de `POST /ingest/csv` (ver [`api.md`](./api.md)). Dá visibilidade
completa de qualidade de dados a cada ingestão: quantas linhas o arquivo
tinha ao todo, quantas viraram inserts/updates, quantas foram puladas por
serem de outro município, quantas por terem dado erro de parsing
(`LinhaInvalidaError`), quais colunas do CSV não bateram com nenhum campo
conhecido (`colunas_nao_mapeadas`), e uma lista de avisos linha a linha
(`avisos`, prefixados com o número da linha, truncada em 50 itens — ver
[`services.md`](./services.md)). É construído e retornado por
`services/ingestion_service.ingest_csv_bytes`.

## `auth.py`

### `Token`

```python
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
```

Resposta de `POST /auth/login` (ver [`api.md`](./api.md)). `token_type`
sempre `"bearer"` — é o valor que o cliente usa para montar o header
`Authorization: Bearer <access_token>` nas chamadas seguintes.
