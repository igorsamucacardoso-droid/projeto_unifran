Estamos desenvolvendo um projeto que é voltado para

"Inteligência Artificial Aplicada à Predição de Zonas de Risco em Sinistros de Trânsito: Estudo de Caso em Ribeirão Preto-SP"

A plataforma será desenvolvida em Python e estamos aqui focados em Back-end, por isso, desenvolva a arquitetura inicial para digestão desses dados no csv no diretório.

## Escopo

Dados restritos ao município de **Ribeirão Preto-SP**. O CSV de origem é estadual (todo SP); o filtro é aplicado na ingestão.

## Arquitetura

API de ingestão (FastAPI) + armazenamento (Postgres/PostGIS via SQLAlchemy, subido com Docker Compose) para que o time de análise de dados consuma os sinistros via HTTP conforme novos arquivos forem chegando. Reingerir o mesmo arquivo é seguro (upsert por `id_sinistro`, idempotente).

```
src/app/
  main.py            # app FastAPI
  core/config.py     # configuração (DATABASE_URL, MUNICIPIO_ALVO)
  db/                # models SQLAlchemy + sessão
  schemas/           # schemas Pydantic (I/O da API)
  services/
    csv_parser.py     # parsing do CSV oficial (encoding latin-1, tipos)
    ingestion_service.py  # upsert no banco
  api/routes/        # endpoints (health, ingest, sinistros)
scripts/seed_from_csv.py  # popula o banco a partir de um CSV local, sem subir o servidor
docker-compose.yml   # sobe o Postgres (postgis/postgis) usado pela API
tests/               # pytest
```

## Rodando localmente

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt

# subir o Postgres
cp .env.example .env
docker compose up -d db

# popular o banco com o CSV local (bootstrap)
.venv/bin/python scripts/seed_from_csv.py

# subir a API
.venv/bin/uvicorn app.main:app --app-dir src --reload
# docs interativas em http://127.0.0.1:8000/docs
```

Endpoints principais:
- `POST /ingest/csv` — upload de um CSV no formato oficial (multipart/form-data, campo `file`)
- `GET /sinistros` — lista paginada, com filtros `tipo_registro`, `data_inicio`, `data_fim`
- `GET /sinistros/{id_sinistro}` — detalhe de um sinistro
- `GET /health`

## Próximos passos conhecidos

- Decidir estratégia para os ~69% dos registros de Ribeirão Preto sem latitude/longitude (descartar vs. geocodificar por logradouro) — crítico para o modelo de zonas de risco.
- Autenticação/autorização nos endpoints antes de expor fora da rede local.
- Migrações de schema (Alembic) quando o CSV oficial mudar de formato.
- Avaliar Postgres+PostGIS se as consultas geoespaciais para o modelo de risco exigirem mais do que SQLite oferece.
