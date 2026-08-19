import json

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db.models import Sinistro
from app.db.session import get_db

router = APIRouter(tags=["mapa"])

_SEVERITY_COLORS = {
    "fatal": "#d03b3b",
    "grave": "#ec835a",
    "leve": "#fab219",
    "ileso": "#0ca30c",
    "nao_informado": "#8a94a3",
}

_PAGE_TEMPLATE = """<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<title>Mapa de sinistros — Ribeirão Preto</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<style>
  html, body {{ margin: 0; height: 100%; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }}
  #map {{ position: absolute; inset: 0; }}
  .panel {{
    position: absolute; top: 12px; right: 12px; z-index: 1000;
    background: #ffffffee; border: 1px solid #d8dee2; border-radius: 10px;
    padding: 12px 14px; font-size: 13px; color: #10161c; box-shadow: 0 4px 16px rgba(0,0,0,.15);
    min-width: 200px;
  }}
  .panel h1 {{ font-size: 13px; margin: 0 0 8px; }}
  .panel label {{ display: flex; align-items: center; gap: 6px; margin: 4px 0; cursor: pointer; }}
  .legend-dot {{ width: 9px; height: 9px; border-radius: 50%; display: inline-block; }}
  .stat {{ margin-top: 8px; padding-top: 8px; border-top: 1px solid #dde3e7; color: #4b5763; }}
</style>
</head>
<body>
<div id="map"></div>
<div class="panel">
  <h1>Sinistros de trânsito — Ribeirão Preto</h1>
  <label><input type="checkbox" id="toggle-heat" checked> Mapa de calor</label>
  <label><input type="checkbox" id="toggle-points" checked> Pontos individuais</label>
  <div class="stat">{total_geo} de {total} sinistros com coordenadas</div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>
<script>
const pontos = {pontos_json};
const cores = {cores_json};

const map = L.map('map').setView([-21.1775, -47.8103], 12);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
  maxZoom: 19,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}}).addTo(map);

function severidade(p) {{
  if (p.fatal > 0) return 'fatal';
  if (p.grave > 0) return 'grave';
  if (p.leve > 0) return 'leve';
  if (p.ileso > 0) return 'ileso';
  return 'nao_informado';
}}

const heatPoints = pontos.map(p => [p.lat, p.lon, 0.5]);
const heatLayer = L.heatLayer(heatPoints, {{ radius: 22, blur: 18, maxZoom: 15 }});

const markersLayer = L.layerGroup();
pontos.forEach(p => {{
  const sev = severidade(p);
  const marker = L.circleMarker([p.lat, p.lon], {{
    radius: 6,
    color: '#ffffff',
    weight: 1,
    fillColor: cores[sev],
    fillOpacity: 0.9,
  }});
  const linhas = [
    '<strong>' + (p.logradouro || 'Via não informada') + '</strong>',
    (p.data || 'data não informada') + (p.turno ? ' · ' + p.turno : ''),
    p.tipo_primario || p.tipo_registro || '',
    'Gravidade: ' + sev.replace('_', ' '),
  ].filter(Boolean);
  marker.bindPopup(linhas.join('<br>'));
  markersLayer.addLayer(marker);
}});

heatLayer.addTo(map);
markersLayer.addTo(map);

document.getElementById('toggle-heat').addEventListener('change', e => {{
  if (e.target.checked) heatLayer.addTo(map); else map.removeLayer(heatLayer);
}});
document.getElementById('toggle-points').addEventListener('change', e => {{
  if (e.target.checked) markersLayer.addTo(map); else map.removeLayer(markersLayer);
}});
</script>
</body>
</html>
"""


@router.get("/mapa", response_class=HTMLResponse)
def mapa(db: Session = Depends(get_db)) -> str:
    """Mapa navegável (Leaflet + OpenStreetMap) dos sinistros geocodificados.

    Diferente da prévia estática, esta página carrega tiles reais e por isso
    só funciona servida diretamente (fora do sandbox de artifacts), com o
    navegador tendo acesso à internet para buscar os tiles do OpenStreetMap.
    """
    total = db.query(Sinistro).count()
    rows = (
        db.query(Sinistro)
        .filter(Sinistro.latitude.is_not(None), Sinistro.longitude.is_not(None))
        .all()
    )

    pontos = [
        {
            "lat": r.latitude,
            "lon": r.longitude,
            "data": r.data_sinistro.isoformat() if r.data_sinistro else None,
            "turno": r.turno,
            "logradouro": (r.logradouro or "").title(),
            "tipo_registro": r.tipo_registro,
            "tipo_primario": r.tp_sinistro_primario,
            "fatal": r.qtd_gravidade_fatal or 0,
            "grave": r.qtd_gravidade_grave or 0,
            "leve": r.qtd_gravidade_leve or 0,
            "ileso": r.qtd_gravidade_ileso or 0,
        }
        for r in rows
    ]

    html = _PAGE_TEMPLATE.format(
        pontos_json=json.dumps(pontos, ensure_ascii=False),
        cores_json=json.dumps(_SEVERITY_COLORS, ensure_ascii=False),
        total_geo=len(pontos),
        total=total,
    )
    return HTMLResponse(content=html)
