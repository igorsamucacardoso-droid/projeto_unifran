# `src/app/core/`

Configuração transversal da aplicação: `config.py` (variáveis de ambiente) e
`security.py` (autenticação do admin).

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

    admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
    admin_password_hash: str = os.getenv("ADMIN_PASSWORD_HASH", "")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )

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
| `ADMIN_USERNAME` | `admin` | `api/routes/auth.py`, comparado contra o `username` enviado em `POST /auth/login` |
| `ADMIN_PASSWORD_HASH` | `""` (vazio → login sempre falha) | `core/security.py`, hash bcrypt comparado contra a senha enviada no login. Gerar com `scripts/hash_password.py` — **nunca** colocar a senha em texto puro aqui |
| `JWT_SECRET_KEY` | `""` (vazio → tokens inseguros/previsíveis) | `core/security.py`, chave de assinatura HMAC dos tokens JWT. Gerar com `python -c "import secrets; print(secrets.token_hex(32))"` |
| `JWT_ALGORITHM` | `HS256` | `core/security.py`, algoritmo de assinatura/verificação do JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | `core/security.py`, validade do token emitido em `POST /auth/login` |

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
chamado em `db/session.py`. O mesmo vale para `ADMIN_PASSWORD_HASH`/
`JWT_SECRET_KEY` vazios — a aplicação sobe normalmente, mas login sempre
falha (`admin_password_hash` vazio) ou os tokens ficam assinados com uma
chave trivial (`jwt_secret_key` vazio); ver [`security.py`](#securitypy).

## `security.py`

Autenticação **single-user**: não há tabela de usuários, o sistema só
distingue "admin autenticado" (via as credenciais em `settings`) de "não
autenticado".

```python
def verify_password(plain_password: str, password_hash: str) -> bool:
    ...  # bcrypt.checkpw

def create_access_token(subject: str) -> str:
    ...  # jwt.encode, expira em settings.access_token_expire_minutes

def decode_access_token(token: str) -> str | None:
    ...  # jwt.decode; None se assinatura/expiração inválida
```

- `verify_password` retorna `False` sem sequer chamar `bcrypt.checkpw` se
  `password_hash` estiver vazio (evita `bcrypt` levantar exceção com hash
  malformado quando `ADMIN_PASSWORD_HASH` não foi configurada).
- `create_access_token` codifica `subject` (o username) no claim `sub` e
  `exp` (expiração) — payload mínimo, sem roles/permissões extras porque só
  existe um papel (admin).
- `decode_access_token` engole qualquer `jwt.PyJWTError` (assinatura
  inválida, token expirado, malformado) e retorna `None` uniformemente —
  quem chama (`api/deps.get_current_admin`, ver [`api.md`](./api.md)) não
  precisa distinguir os motivos, só decidir entre autorizar (`401`) ou não.
