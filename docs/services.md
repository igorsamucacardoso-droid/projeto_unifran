# `src/app/services/`

Lógica de negócio: parsing do CSV oficial e ingestão no banco. Isolada da
camada `api` para que as rotas fiquem finas (validação HTTP + delegação) e
essa lógica seja testável sem precisar subir a aplicação — ver
`tests/test_csv_parser.py` em [`tests.md`](./tests.md).

## `csv_parser.py`

Parsing puro (sem tocar banco) de uma linha crua do CSV oficial para um
`dict` de tipos Python já normalizados.

### Constantes

```python
CSV_ENCODING = "latin-1"
CSV_DELIMITER = ";"
```

O arquivo-fonte (`sinistros_12-2025.csv`) vem em **ISO-8859-1 (latin-1)**,
não UTF-8, e delimitado por `;`. Essas particularidades são tratadas aqui,
isoladamente, para o resto do pipeline só lidar com `str`/`int`/`float`/
`date`/`bool` já normalizados — nenhuma outra parte do código precisa saber
do encoding ou do delimitador.

### Conversores de campo

| Função | Entrada → saída | Detalhe |
|---|---|---|
| `_to_int(value)` | `"1.0"` → `1` | Passa por `float()` antes de `int()` porque alguns campos numéricos vêm com `.0` no CSV |
| `_to_coord(value)` | `"-20,0393654"` → `-20.0393654` | Troca vírgula por ponto (decimal brasileiro) |
| `_to_bool_flag(value)` | `"S"` → `True`, qualquer outra coisa → `False` | Como as flags `tp_sinistro_*` são codificadas no CSV oficial |
| `_to_date(value)` | `"01/12/2025"` → `date(2025, 12, 1)` | Formato `%d/%m/%Y` |
| `_to_time(value)` | `"12:46"` → `time(12, 46)` | Formato `%H:%M` |

Todas tratam string vazia/`None` retornando `None` (exceto `_to_bool_flag`,
que retorna `False`).

### `parse_row(raw: dict[str, str]) -> dict[str, Any]`

Converte uma linha crua (dict de strings, como vem do `csv.DictReader`) no
formato esperado pelo model ORM `Sinistro` — as chaves do dict retornado
batem 1:1 com os nomes das colunas de `db/models.py` (exceto
`source_file`/`ingested_at`, preenchidos depois pelo `ingestion_service`).

`id_sinistro` é o único campo tratado como obrigatório (`int(raw["id_sinistro"])`,
sem fallback); qualquer `KeyError` ou `ValueError` durante o parse da linha
inteira é capturado e relançado como `LinhaInvalidaError`, para o chamador
decidir o que fazer com linhas corrompidas sem que uma linha ruim derrube a
ingestão do arquivo inteiro.

### `iter_raw_rows(csv_text: TextIO) -> Iterator[dict[str, str]]`

Wrapper fino sobre `csv.DictReader(csv_text, delimiter=CSV_DELIMITER)` —
único ponto que sabe o delimitador do arquivo.

## `ingestion_service.py`

### `ingest_csv_bytes(db, file_bytes, source_filename) -> IngestionSummary`

Orquestra a ingestão completa de um CSV:

1. Decodifica `file_bytes` usando `CSV_ENCODING` (`latin-1`).
2. Itera linha a linha via `iter_raw_rows`.
3. Para cada linha, filtra por `settings.municipio_alvo`
   (comparação `.strip().upper()`, ver [`core.md`](./core.md)) — linhas de
   outros municípios são contadas em `skipped_other_municipio` e ignoradas,
   **sem** sequer tentar o parse completo.
4. Faz `parse_row(raw_row)`; se levantar `LinhaInvalidaError`, conta em
   `skipped_invalid` e segue para a próxima linha.
5. Preenche `source_file` e `ingested_at` (`datetime.utcnow()`) no dict
   parseado.
6. **Upsert por `id_sinistro`:** `db.get(Sinistro, data["id_sinistro"])` —
   se existir, atualiza todos os campos do objeto existente
   (`setattr` em loop) e conta em `updated`; senão, cria um `Sinistro(**data)`
   novo e conta em `inserted`.
7. Ao final do loop, `db.commit()` — um único commit para o arquivo inteiro
   (não por linha), então uma ingestão é atômica: ou tudo é persistido, ou
   nada (se uma exceção não tratada ocorrer antes do commit).
8. Retorna `IngestionSummary` com as contagens (`total_rows`, `inserted`,
   `updated`, `skipped_other_municipio`, `skipped_invalid`).

Essa função é o único ponto de entrada de dados no banco, usada tanto por
`api/routes/ingestion.py` (via HTTP) quanto por `scripts/seed_from_csv.py`
(via linha de comando) — ver [`api.md`](./api.md) e [`scripts.md`](./scripts.md).

**Idempotência:** como `id_sinistro` é a PK e o upsert é feito por ela,
rodar `ingest_csv_bytes` duas vezes com o mesmo arquivo produz o mesmo
estado final do banco (a segunda vez, tudo cai em `updated` em vez de
`inserted`) — é essa propriedade que permite reingestões seguras conforme
novos arquivos oficiais chegam.
