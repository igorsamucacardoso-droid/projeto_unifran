# Dados

Arquivos de dados usados/gerados pelo projeto — não são código, mas fazem
parte do comportamento observável da aplicação.

## `sinistros_12-2025.csv`

Dataset bruto oficial, versionado na raiz do repositório. 16.817 linhas
(16.816 linhas de dados + cabeçalho), cobrindo sinistros de trânsito de
**todo o estado de São Paulo** — o filtro para Ribeirão Preto-SP é aplicado
na ingestão (`MUNICIPIO_ALVO`), não no dado bruto. Do total, 447 linhas são
de Ribeirão Preto (`tests/test_csv_parser.py` fixa essas contagens como
asserção — ver [`tests.md`](./tests.md)).

Formato:
- Encoding **latin-1** (ISO-8859-1).
- Delimitador `;`.
- Decimais em vírgula (padrão brasileiro).
- Datas `dd/mm/aaaa`, horas `HH:MM`.
- Flags booleanas como `"S"`/vazio.

Ver [`services.md`](./services.md#csv_parserpy) para o parser que lida com
essas particularidades.

É também a fonte padrão usada por
[`scripts/seed_from_csv.py`](./scripts.md) quando nenhum caminho é passado
como argumento.

## `sinistros.db`

Banco **SQLite**, gerado em runtime (não versionado — está no `.gitignore`
via `*.db`, ver [`configuracao.md`](./configuracao.md)). Criado
automaticamente na primeira vez que a aplicação sobe (`main.py`) ou que o
script de seed roda, no caminho relativo `./sinistros.db` (padrão de
`DATABASE_URL` em [`core.md`](./core.md)) — ou seja, sua localização depende
de onde o processo é executado.

Contém uma única tabela, `sinistros`, mapeada pelo model ORM `Sinistro` —
ver [`db.md`](./db.md).

## `data/municipio_ribeirao_preto.geojson`

Contorno da malha municipal do **IBGE** para Ribeirão Preto-SP (código de
área `3543402`). Um `FeatureCollection` com uma única `Feature` do tipo
`Polygon`, com 84 pares de coordenadas `[longitude, latitude]` (formato
GeoJSON padrão — ordem invertida em relação ao `latitude, longitude` usado
no resto do projeto, ex. `Sinistro.latitude`/`Sinistro.longitude` e o centro
do mapa em `mapa.py`).

Arquivo pequeno (4 KB), de conteúdo estático — não é gerado nem atualizado
por nenhum script do projeto; foi adicionado manualmente ao repositório.
Usado exclusivamente por [`api.md`](./api.md#mapapy) para desenhar o
contorno azul do município e enquadrar o mapa (`fitBounds`) na área
administrativa inteira, cobrindo além dos pontos onde há sinistros
geocodificados.
