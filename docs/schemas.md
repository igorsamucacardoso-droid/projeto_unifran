# `src/app/schemas/`

Schemas Pydantic que definem os contratos de entrada/saída da API — a
"fronteira" entre o model ORM interno (`db/models.py`) e o JSON exposto pelos
endpoints.

## `sinistro.py`

### `SinistroOut`

```python
class SinistroOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_sinistro: int
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
```

Resposta de `POST /ingest/csv` (ver [`api.md`](./api.md)). Dá visibilidade
de qualidade de dados a cada ingestão: quantas linhas o arquivo tinha ao
todo, quantas viraram inserts/updates, quantas foram puladas por serem de
outro município, e quantas por terem dado erro de parsing
(`LinhaInvalidaError`, ver [`services.md`](./services.md)). É construído e
retornado por `services/ingestion_service.ingest_csv_bytes`.
