# `src/app/core/`

Configuração transversal da aplicação. Hoje contém um único arquivo.

## `config.py`

```python
@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./sinistros.db")
    municipio_alvo: str = os.getenv("MUNICIPIO_ALVO", "RIBEIRAO PRETO")

settings = Settings()
```

Define um objeto `Settings` imutável (`frozen=True`), instanciado uma única
vez como `settings` e importado por todo o resto do app (`db/session.py`,
`services/ingestion_service.py`).

### Variáveis de ambiente

| Variável | Padrão | Usada em |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./sinistros.db` | `db/session.py`, para criar a `engine` do SQLAlchemy |
| `MUNICIPIO_ALVO` | `RIBEIRAO PRETO` | `services/ingestion_service.py`, para filtrar as linhas do CSV que serão persistidas |

Como os valores são lidos com `os.getenv` no momento da definição da classe,
a variável de ambiente precisa estar setada **antes** do primeiro `import` de
`app.core.config` (direto ou indireto). É por isso que os testes
(`tests/conftest.py`) setam `DATABASE_URL` logo no topo do `conftest`, antes
de qualquer módulo da aplicação ser importado — ver [`tests.md`](./tests.md).

Não há validação de formato nem valores obrigatórios: se `DATABASE_URL`
apontar para uma URL inválida, o erro só aparece quando `create_engine` for
chamado em `db/session.py`.
