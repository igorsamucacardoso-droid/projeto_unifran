# `tests/`

Suíte de testes automatizados (`pytest`).

## `conftest.py`

```python
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

os.environ.setdefault(
    "DATABASE_URL", f"sqlite:///{tempfile.mktemp(suffix='.db')}"
)
```

Executado automaticamente pelo pytest antes de qualquer teste, em duas
responsabilidades:

1. **Path do pacote:** insere `src/` no `sys.path`, para os testes
   conseguirem `import app...` sem instalar o pacote — mesmo padrão usado em
   [`scripts/seed_from_csv.py`](./scripts.md).
2. **Isolamento de banco:** define `DATABASE_URL` para um arquivo SQLite
   temporário (`tempfile.mktemp`) **antes** de qualquer módulo da aplicação
   ser importado. Isso é essencial porque `app.core.config.Settings` lê
   `DATABASE_URL` no momento da definição da classe (ver
   [`core.md`](./core.md)) — se essa variável não fosse setada aqui, os
   testes rodariam contra `sinistros.db` (o banco de desenvolvimento),
   contaminando dados reais com registros de teste.
   `os.environ.setdefault` (não `os.environ[...] =`) respeita uma
   `DATABASE_URL` já setada externamente, caso exista.

## `test_csv_parser.py`

Testa `services/csv_parser.py` isoladamente, sem tocar banco ou API — ver
[`services.md`](./services.md).

### `test_parse_row_converte_tipos_e_encoding`

Linha sintética cobrindo as principais conversões de tipo: `id_sinistro`
(`str` → `int`), `data_sinistro` (`dd/mm/aaaa` → `date`), `hora_sinistro`
(`HH:MM` → `time`), `latitude`/`longitude` (decimal com vírgula → `float`),
`qtd_automovel` (`str` → `int`), e as flags booleanas (`"S"` → `True`,
`""` → `False`).

### `test_csv_real_filtra_ribeirao_preto`

Lê o **dataset real** (`sinistros_12-2025.csv`, na raiz do projeto — ver
[`dados.md`](./dados.md)) direto do disco, decodifica com
`CSV_ENCODING` e faz duas asserções fixas sobre o tamanho do dataset:

```python
assert len(rows) == 16816
assert len(rp_rows) == 447
```

Ou seja, **depende do conteúdo exato do CSV na raiz do repositório** — se o
arquivo for atualizado/substituído por uma nova exportação oficial, esse
teste provavelmente quebra e os números precisam ser atualizados junto. Além
da contagem, garante que `parse_row` não levanta exceção para **nenhuma**
linha real de Ribeirão Preto (`for row in rp_rows: parse_row(row)`) — é o
teste que dá confiança de que o parser aguenta o dado de produção real, não
só casos sintéticos.

## `test_mapa.py`

Testa o endpoint `GET /mapa` de ponta a ponta, via `TestClient` do FastAPI —
ver [`api.md`](./api.md).

```python
def setup_module() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(Sinistro(id_sinistro=999999, municipio="RIBEIRAO PRETO",
                     latitude=-21.1775, longitude=-47.8103,
                     logradouro="Rua Teste", tp_sinistro_primario="COLISAO"))
    db.commit()
```

`setup_module` (hook de nível de módulo do pytest, roda uma vez antes de
todos os testes do arquivo) cria as tabelas no banco temporário (isolado
pelo `conftest.py`) e insere um único sinistro fake, geocodificado, com
`id_sinistro=999999` — um valor alto, deliberadamente fora da faixa dos IDs
reais do CSV oficial, para não colidir com dados reais caso o teste algum
dia rode contra um banco não-vazio.

### `test_mapa_retorna_html_com_ponto_geocodificado`

Faz `GET /mapa` via `TestClient` e verifica:
- Status `200`.
- `content-type` contém `text/html`.
- O HTML retornado contém a string `"leaflet"` (case-insensitive) — confirma
  que a página carrega a lib, sem testar comportamento JS de fato (o
  `TestClient` não executa JavaScript).
- O HTML contém `"Rua Teste"` — confirma que o sinistro inserido no
  `setup_module` foi de fato lido do banco e serializado no popup.

Não testa a lógica de peso de calor, gradiente ou raio anti-sobreposição
descritos em [`api.md`](./api.md) — esses são comportamentos client-side
(JavaScript) não exercitados por este teste.

## Rodando

```bash
.venv/bin/pytest
```
