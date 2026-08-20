# `scripts/`

## `seed_from_csv.py`

Popula a base local a partir de um CSV no formato oficial **sem** precisar
subir o servidor HTTP. Útil para bootstrap inicial do banco e para
reingestões manuais durante desenvolvimento.

```bash
python scripts/seed_from_csv.py [caminho/para/arquivo.csv]
# padrão: sinistros_12-2025.csv na raiz do projeto
```

### Como funciona

```python
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from app.db.session import Base, SessionLocal, engine
from app.services.ingestion_service import ingest_csv_bytes

def main(csv_path: Path) -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        content = csv_path.read_bytes()
        summary = ingest_csv_bytes(db, content, csv_path.name)
        print(summary.model_dump_json(indent=2))
    finally:
        db.close()
```

- Insere `src/` no `sys.path` manualmente (o script roda fora do pacote
  `app`, então precisa desse ajuste para conseguir `import app...`) — o
  mesmo padrão usado em [`tests/conftest.py`](./tests.md).
- Cria as tabelas (`Base.metadata.create_all`) — idempotente, então rodar o
  script contra um banco já existente não recria nada.
- Lê o arquivo **em bytes** (`read_bytes()`, não `read_text()`) e delega
  inteiramente para `ingest_csv_bytes` — o mesmo caminho de código usado
  pelo endpoint `POST /ingest/csv` (ver [`services.md`](./services.md) e
  [`api.md`](./api.md)). Ou seja, popular o banco via script ou via upload
  HTTP tem exatamente o mesmo comportamento (mesmo filtro de município,
  mesmo upsert idempotente).
- Imprime o `IngestionSummary` resultante como JSON formatado (`indent=2`)
  no stdout — dá visibilidade imediata de quantas linhas foram inseridas/
  atualizadas/puladas, sem precisar consultar a API depois.

### Quando usar

- **Bootstrap:** primeira vez rodando o projeto localmente, antes de subir a
  API (`Base.metadata.create_all` em `main.py` também criaria as tabelas,
  mas o banco ficaria vazio até alguém chamar `POST /ingest/csv`).
- **Reingestão manual em dev:** mais rápido que montar um upload
  `multipart/form-data` manualmente para testar o pipeline de ingestão.
