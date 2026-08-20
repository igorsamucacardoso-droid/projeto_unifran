# Arquitetura

## Visão geral

```
src/app/
  main.py            # monta o app FastAPI e registra as rotas
  core/
    config.py         # configuração (variáveis de ambiente)
  db/
    session.py         # engine, sessão, Base declarativa
    models.py           # model ORM Sinistro
  schemas/
    sinistro.py          # schemas Pydantic (I/O da API)
  services/
    csv_parser.py          # parsing do CSV oficial (encoding, tipos)
    ingestion_service.py     # upsert no banco a partir do CSV
  api/routes/
    health.py                 # GET /health
    ingestion.py               # POST /ingest/csv
    sinistros.py                 # GET /sinistros, GET /sinistros/{id}
    mapa.py                        # GET /mapa (visualização Leaflet)
scripts/
  seed_from_csv.py    # popula o banco a partir de um CSV local, sem subir o servidor
data/
  municipio_ribeirao_preto.geojson   # contorno do município (malha IBGE)
tests/                # pytest
sinistros_12-2025.csv  # dataset bruto (estadual, ~16.8 mil linhas)
sinistros.db            # banco SQLite (gerado em runtime, fora do controle de versão)
```

## Camadas e dependências

O projeto segue uma separação simples em camadas, cada uma dependendo apenas
das camadas "abaixo" dela:

```
api/routes  →  services  →  db (models, session)
     ↓             ↓
  schemas       core (config)
```

- **`core`** não depende de nada dentro do app — é a base (configuração).
- **`db`** depende de `core` (para pegar a `DATABASE_URL`).
- **`schemas`** são contratos Pydantic independentes, usados pela camada
  `api` para validar/serializar entrada e saída.
- **`services`** contém a lógica de negócio (parsing de CSV, upsert) e
  depende de `db` (para persistir) e `core` (para saber qual município
  filtrar).
- **`api/routes`** é a camada mais externa: recebe requisições HTTP, chama
  `services` ou consulta `db` diretamente (rotas de leitura simples), e
  serializa a resposta via `schemas`.

## Fluxo de dados ponta a ponta

### 1. Ingestão

```
CSV oficial (estadual, latin-1, ';', decimal com vírgula)
   │
   ▼  scripts/seed_from_csv.py  OU  POST /ingest/csv
   │
services/csv_parser.py     — decodifica, faz parse linha a linha
   │
services/ingestion_service.py  — filtra por MUNICIPIO_ALVO, faz upsert por id_sinistro
   │
   ▼
db (tabela `sinistros`, SQLite)
```

Reingerir o mesmo arquivo é seguro: o `id_sinistro` (chave natural do
dado-fonte) é usado como chave primária, então uma segunda ingestão apenas
atualiza os registros já existentes em vez de duplicá-los. Isso é o que
permite ao time de dados reingerir arquivos incrementalmente conforme
chegam novas exportações do CSV oficial.

### 2. Consulta (API para o time de dados)

```
GET /sinistros[?tipo_registro=&data_inicio=&data_fim=&limit=&offset=]
GET /sinistros/{id_sinistro}
   │
   ▼
db.query(Sinistro) — filtros opcionais, paginação
   │
   ▼
schemas.SinistroOut — serialização para JSON
```

### 3. Visualização (mapa)

```
GET /mapa
   │
   ▼
db.query(Sinistro) — apenas registros com lat/lon não nulos
   │
   ▼
página HTML autocontida (Leaflet + OpenStreetMap via CDN)
  - contorno do município (data/municipio_ribeirao_preto.geojson)
  - camada de calor ponderada por gravidade
  - marcadores individuais coloridos por gravidade, com popup
```

Esse endpoint roda fora de qualquer sandbox de artifacts — precisa que o
navegador do usuário final tenha acesso direto à internet para baixar os
tiles do OpenStreetMap e as libs do CDN (`unpkg.com`).

## Por que SQLite (por enquanto)

O `README.md` do projeto registra a decisão: SQLite via SQLAlchemy foi
escolhido para a primeira versão por simplicidade (zero infraestrutura extra
para rodar localmente), mas a camada de acesso a dados já é abstraída via
SQLAlchemy especificamente para permitir trocar por Postgres/PostGIS depois,
caso as consultas geoespaciais do modelo de predição de zonas de risco
exijam mais do que o SQLite oferece.

## Pendências arquiteturais conhecidas

Registradas desde a primeira versão do projeto (`README.md`):

- **Geocodificação:** parte relevante dos registros de Ribeirão Preto não
  tem latitude/longitude no CSV oficial. Ainda não há decisão tomada entre
  descartar esses registros ou geocodificá-los por logradouro — é apontado
  como crítico para o modelo de predição de zonas de risco, já que reduzir a
  amostra geograficamente enviesa o treinamento.
- **Segurança:** os endpoints não têm autenticação/autorização. Necessário
  antes de expor a API fora da rede local.
- **Migrações:** o schema é criado via `Base.metadata.create_all` (ver
  [`db.md`](./db.md)); não há Alembic configurado. Qualquer mudança de
  schema em produção exigirá migração manual até isso ser resolvido.
- **Postgres/PostGIS:** cogitado como evolução, ainda não implementado.
