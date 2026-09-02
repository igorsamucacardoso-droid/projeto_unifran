# `src/app/db/`

Camada de acesso a dados: conexão com o banco e o único modelo ORM do
projeto.

## `session.py`

```python
connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- **`engine`** — criado a partir de `settings.database_url` (ver
  [`core.md`](./core.md)), que por padrão aponta para o Postgres subido pelo
  `docker-compose.yml`. O `connect_args={"check_same_thread": False}` só é
  aplicado quando o banco é SQLite: é necessário porque o SQLite por padrão
  proíbe usar a mesma conexão em threads diferentes, e o FastAPI/uvicorn
  atende requisições em threads diferentes por padrão. Para Postgres esse
  `connect_args` fica vazio — a checagem `startswith("sqlite")` continua
  existindo porque os testes (`tests/conftest.py`) usam SQLite para ficarem
  rápidos e isolados, então o código precisa suportar os dois bancos.
- **`SessionLocal`** — factory de sessões SQLAlchemy, com `autocommit=False`
  e `autoflush=False` (padrão explícito, controle total sobre quando
  commitar/flushar).
- **`Base`** — classe declarativa da qual todo model ORM herda (hoje, só
  `Sinistro`, ver `models.py` abaixo). É contra `Base.metadata` que
  `create_all` é chamado em `main.py` para criar as tabelas.
- **`get_db()`** — generator usado como dependência do FastAPI
  (`Depends(get_db)`) nas rotas que precisam do banco. Garante que a sessão
  é sempre fechada (`finally: db.close()`) mesmo se a rota levantar exceção.

## `models.py`

Define um único model, `Sinistro`, mapeado para a tabela `sinistros`.

```python
class Sinistro(Base):
    __tablename__ = "sinistros"
    id_sinistro: Mapped[int] = mapped_column(Integer, primary_key=True)
    ...
```

### Por que `id_sinistro` é a chave primária

`id_sinistro` é a chave natural do dado-fonte (vem assim no CSV oficial) e
foi escolhida como PK deliberadamente para permitir **upsert idempotente**:
ao reingerir um CSV, `services/ingestion_service.py` faz `db.get(Sinistro,
id_sinistro)` para decidir se atualiza um registro existente ou insere um
novo — ver [`services.md`](./services.md).

### Grupos de colunas

| Grupo | Colunas (exemplos) | Observação |
|---|---|---|
| Identificação/registro | `id_sinistro`, `tipo_registro` | `tipo_registro` distingue tipos de registro do boletim |
| Data/hora | `data_sinistro`, `ano_sinistro`, `mes_sinistro`, `dia_sinistro`, `hora_sinistro`, `ano_mes_sinistro`, `dia_da_semana`, `turno` | Campos redundantes com `data_sinistro`/`hora_sinistro`, mas mantidos porque já vêm prontos do CSV oficial (evita recalcular) |
| Localização | `logradouro`, `numero_logradouro`, `tipo_via`, `tipo_local`, `latitude`, `longitude`, `cod_ibge`, `municipio`, `regiao_administrativa`, `administracao`, `conservacao`, `circunscricao` | `municipio` é indexado (`index=True`) — é o principal filtro de ingestão e consulta |
| Classificação do sinistro | `tp_sinistro_primario` | Tipo primário textual (ex.: "COLISAO") |
| Veículos envolvidos | `qtd_pedestre`, `qtd_bicicleta`, `qtd_motocicleta`, `qtd_automovel`, `qtd_onibus`, `qtd_caminhao`, `qtd_veic_outros`, `qtd_veic_nao_disponivel` | Contagens inteiras, todas opcionais |
| Gravidade das vítimas | `qtd_gravidade_fatal`, `qtd_gravidade_grave`, `qtd_gravidade_leve`, `qtd_gravidade_ileso`, `qtd_gravidade_nao_disponivel` | Usadas para colorir/ponderar o mapa de calor — ver [`api.md`](./api.md) |
| Tipo de sinistro (flags) | `tp_sinistro_atrop_pedestre`, `tp_sinistro_colisao_frontal`, `tp_sinistro_colisao_traseira`, `tp_sinistro_capotamento`, `tp_sinistro_tombamento`, etc. | Booleanas, `default=False`; o CSV oficial as codifica como `"S"`/vazio (ver `services/csv_parser.py`) |
| Proveniência | `source_file`, `ingested_at` | Não vêm do CSV: preenchidas pela própria ingestão. Importam porque a ingestão se repete ao longo do tempo — permitem rastrear de qual arquivo e quando cada linha veio |

Todas as colunas de dado (fora `id_sinistro`) são opcionais (`| None`),
refletindo que o CSV oficial tem campos frequentemente vazios.

### Criação de tabelas

Não há migrações (Alembic). As tabelas são criadas via
`Base.metadata.create_all(bind=engine)`, chamado tanto em `main.py` (ao subir
a API) quanto em `scripts/seed_from_csv.py` (ao rodar o seed
standalone). Qualquer mudança de schema em uma base já populada exige
intervenção manual — ver pendências em [`arquitetura.md`](./arquitetura.md).
