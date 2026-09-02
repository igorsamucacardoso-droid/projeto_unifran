# Configuração e arquivos de raiz

## `docker-compose.yml`

Sobe o Postgres usado como banco padrão do projeto (imagem
`postgis/postgis:16-3.4` — Postgres 16 com PostGIS já instalado, pensando na
evolução geoespacial cogitada em [`arquitetura.md`](./arquitetura.md)).

```bash
cp .env.example .env   # ajuste se quiser trocar usuário/senha/porta
docker compose up -d db
```

Lê usuário/senha/banco/porta de variáveis de ambiente (`POSTGRES_USER`,
`POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_PORT`), todas com um valor
padrão embutido no próprio `docker-compose.yml` caso o `.env` não exista.
Os dados persistem no volume nomeado `postgres_data` entre reinícios do
container.

## `.env.example`

Template de variáveis de ambiente — copie para `.env` (gitignorado) e ajuste
se necessário. Cobre tanto as variáveis do `docker-compose.yml`
(`POSTGRES_*`) quanto as da aplicação (`DATABASE_URL`, `MUNICIPIO_ALVO`, ver
[`core.md`](./core.md)). `app/core/config.py` carrega esse `.env`
automaticamente via `python-dotenv` — não é preciso exportar as variáveis
manualmente no shell.

## `requirements.txt`

Dependências de runtime:

```
fastapi
uvicorn[standard]
sqlalchemy
pydantic
python-multipart
psycopg[binary]
python-dotenv
```

`python-multipart` é necessária especificamente para o FastAPI conseguir
processar o upload `multipart/form-data` de `POST /ingest/csv` (ver
[`api.md`](./api.md)) — sem ela, `UploadFile`/`File(...)` falha em runtime.
`psycopg[binary]` é o driver usado pelo SQLAlchemy para falar com o Postgres
(`postgresql+psycopg://...`); `python-dotenv` carrega o `.env` em
`core/config.py`. Todas as versões são fixadas (`==`) — instalar sempre pega
exatamente a versão testada de cada pacote.

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
data/dados_infosiga.zip
```

Note que `*.db` cobre `sinistros.db` (usado apenas quando `DATABASE_URL` é
sobrescrita para SQLite, ex. nos testes — ver [`dados.md`](./dados.md)), mas
**não** cobre `sinistros_12-2025.csv` (o dataset bruto, que é versionado
propositalmente) nem `data/municipio_ribeirao_preto.geojson`.
`data/dados_infosiga.zip` é ignorado por ser um dump bruto grande (>100 MB) —
não deve ser versionado.

## Variáveis de ambiente

Documentadas com detalhe em [`core.md`](./core.md). Resumo:

| Variável | Padrão | Efeito |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://infosiga:infosiga@localhost:5432/infosiga` | String de conexão do SQLAlchemy (Postgres, via `docker-compose.yml`) |
| `MUNICIPIO_ALVO` | `RIBEIRAO PRETO` | Filtro aplicado na ingestão do CSV |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` / `POSTGRES_PORT` | `infosiga` / `infosiga` / `infosiga` / `5432` | Usadas só pelo `docker-compose.yml` para configurar o container do Postgres |

Copie `.env.example` para `.env` (gitignorado) para customizar localmente;
`core/config.py` carrega esse arquivo automaticamente. Sem `.env`, os
padrões acima cobrem o desenvolvimento local assumindo que o Postgres do
`docker-compose.yml` está no ar.

## `CLAUDE.md`

Arquivo vazio na raiz do repositório (0 bytes) — reservado para instruções
de projeto ao Claude Code, ainda não preenchido.
