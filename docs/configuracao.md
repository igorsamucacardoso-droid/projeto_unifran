# Configuração e arquivos de raiz

## `requirements.txt`

Dependências de runtime:

```
fastapi
uvicorn[standard]
sqlalchemy
pydantic
python-multipart
```

`python-multipart` é necessária especificamente para o FastAPI conseguir
processar o upload `multipart/form-data` de `POST /ingest/csv` (ver
[`api.md`](./api.md)) — sem ela, `UploadFile`/`File(...)` falha em runtime.
Nenhuma versão é fixada (sem pinning) — instalar sempre pega a versão mais
recente compatível de cada pacote.

## `requirements-dev.txt`

```
-r requirements.txt
pytest
httpx
```

Estende `requirements.txt` (via `-r`) e adiciona o necessário para rodar a
suíte de testes: `pytest` (test runner) e `httpx` (dependência do
`fastapi.testclient.TestClient`, usado em `tests/test_mapa.py`).

## `.gitignore`

```
.env
__pycache__/
.venv/
*.db
.pytest_cache/
```

Note que `*.db` cobre `sinistros.db` (o banco gerado em runtime — ver
[`dados.md`](./dados.md)), mas **não** cobre `sinistros_12-2025.csv` (o
dataset bruto, que é versionado propositalmente) nem
`data/municipio_ribeirao_preto.geojson`.

## Variáveis de ambiente

Documentadas com detalhe em [`core.md`](./core.md). Resumo:

| Variável | Padrão | Efeito |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./sinistros.db` | String de conexão do SQLAlchemy |
| `MUNICIPIO_ALVO` | `RIBEIRAO PRETO` | Filtro aplicado na ingestão do CSV |

Não há arquivo `.env` versionado nem `.env.example` — as variáveis são
lidas diretamente do ambiente do processo (`os.getenv`), com os padrões
acima cobrindo o caso de desenvolvimento local sem nenhuma configuração
extra.

## `CLAUDE.md`

Arquivo vazio na raiz do repositório (0 bytes) — reservado para instruções
de projeto ao Claude Code, ainda não preenchido.
