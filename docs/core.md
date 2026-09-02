# `src/app/core/`

Configuração transversal da aplicação. Hoje contém um único arquivo.

## `config.py`

```python
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg://infosiga:infosiga@localhost:5432/infosiga"
    )
    municipio_alvo: str = os.getenv("MUNICIPIO_ALVO", "RIBEIRAO PRETO")

settings = Settings()
```

Define um objeto `Settings` imutável (`frozen=True`), instanciado uma única
vez como `settings` e importado por todo o resto do app (`db/session.py`,
`services/ingestion_service.py`).

`load_dotenv()` carrega um `.env` na raiz do projeto (se existir) para dentro
de `os.environ` **sem sobrescrever** variáveis já setadas no ambiente — é por
isso que os testes continuam isolados mesmo com um `.env` presente (ver
abaixo).

### Variáveis de ambiente

| Variável | Padrão | Usada em |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://infosiga:infosiga@localhost:5432/infosiga` | `db/session.py`, para criar a `engine` do SQLAlchemy. Casa com os valores padrão do `docker-compose.yml` |
| `MUNICIPIO_ALVO` | `RIBEIRAO PRETO` | `services/ingestion_service.py`, para filtrar as linhas do CSV que serão persistidas |

O projeto usa **Postgres** (imagem `postgis/postgis`, já com PostGIS
disponível para futuras consultas geoespaciais — ver
[`arquitetura.md`](./arquitetura.md)) como banco padrão, subido via
`docker-compose.yml`. Não é mais SQLite por padrão — o driver usado é
`psycopg` (`psycopg[binary]` no `requirements.txt`).

Como os valores são lidos com `os.getenv` no momento da definição da classe,
a variável de ambiente precisa estar setada **antes** do primeiro `import` de
`app.core.config` (direto ou indireto). É por isso que os testes
(`tests/conftest.py`) setam `DATABASE_URL` para um SQLite temporário logo no
topo do `conftest`, antes de qualquer módulo da aplicação ser importado —
mantém a suíte rápida e isolada do Postgres — ver [`tests.md`](./tests.md).

Não há validação de formato nem valores obrigatórios: se `DATABASE_URL`
apontar para uma URL inválida, o erro só aparece quando `create_engine` for
chamado em `db/session.py`.
