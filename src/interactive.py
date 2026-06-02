"""
interactive.py
--------------
Genera dashboards HTML interactivos (autoejecutables, sin servidor).

- affective_map_html(): mapa de calor con filtros por tipo y zona.
- network_map_html(): mapa con lista de personajes que filtra el mapa.
"""

import json
from pathlib import Path
from typing import List, Dict


def _affective_map_template(data_json: str, title: str = 'Mapa afectivo') -> str:
    return r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>__TITLE__</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<style>
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,sans-serif;color:#1A1A1A}
.layout{display:grid;grid-template-columns:1fr 380px;height:100vh}
#map{height:100%}
.panel{border-left:1px solid #ddd;padding:20px;overflow-y:auto;background:#FAFAFA}
.panel h1{font-size:18px;margin:0 0 4px;color:#1F4E78}
.subtitle{font-size:12px;color:#666;font-style:italic;margin-bottom:18px}
.controls{background:white;border:1px solid #e3e3e3;border-radius:6px;padding:14px;margin-bottom:14px}
.controls label{display:block;font-size:11px;font-weight:600;color:#444;text-transform:uppercase;margin-bottom:4px;letter-spacing:.04em}
.controls select{width:100%;padding:6px 8px;border:1px solid #ccc;border-radius:4px;font-size:13px;margin-bottom:10px;background:white}
.gradient-bar{height:12px;border-radius:4px;background:linear-gradient(to right,#2E7D32,#FFFFFF,#C62828);margin:6px 0}
.detail{background:white;border:1px solid #e3e3e3;border-radius:6px;padding:14px;font-size:12px;line-height:1.5}
.detail h2{font-size:16px;color:#1F4E78;margin:0 0 4px}
.detail .empty{color:#999;font-style:italic;padding:18px 0;text-align:center}
.stat{background:white;border:1px solid #e3e3e3;border-radius:6px;padding:8px 12px;margin-bottom:8px;font-size:12px}
.stat .value{font-weight:700;color:#1F4E78}
</style></head><body>
<div class="layout">
<div id="map"></div>
<div class="panel">
<h1>__TITLE__</h1>
<div class="subtitle">Sin remedio · Antonio Caballero · Bogotá 1972</div>
<div class="controls">
<label>Tipo de lugar</label>
<select id="ftipo"><option value="">Todos</option></select>
<label>Zona</label>
<select id="fzona"><option value="">Todas</option></select>
<label>Mínimo de menciones afectivas</label>
<select id="fmin"><option value="0">Mostrar todos</option><option value="2">≥2</option><option value="4" selected>≥4</option><option value="6">≥6</option></select>
</div>
<div class="stat">Lugares mostrados: <span class="value" id="stat">—</span></div>
<div class="controls" style="font-size:11px;line-height:1.5">
<b style="color:#1F4E78">Leyenda</b>
<div>Tamaño = total de menciones · Color = índice de desencanto</div>
<div class="gradient-bar"></div>
<div style="display:flex;justify-content:space-between;font-size:10px;color:#666"><span>−1 alegría</span><span>0</span><span>+1 desencanto</span></div>
</div>
<div class="detail" id="detail"><div class="empty">Haga clic o pase el cursor sobre un punto.</div></div>
</div>
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const lugares = __DATA__;
const map = L.map('map').setView([4.65,-74.07],13);
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',{attribution:'© OpenStreetMap © CARTO'}).addTo(map);
function colorFor(idx){
  if(idx===null||idx===undefined) return '#bbb';
  const t=(idx+1)/2;
  if(t<0.5){const k=t/0.5;return `rgb(${Math.round(46+(255-46)*k)},${Math.round(125+(255-125)*k)},${Math.round(50+(255-50)*k)})`}
  const k=(t-0.5)/0.5;
  return `rgb(${Math.round(255-(255-198)*k)},${Math.round(255-(255-40)*k)},${Math.round(255-(255-40)*k)})`;
}
const tipos=[...new Set(lugares.map(l=>l.tipo))].sort();
const zonas=[...new Set(lugares.map(l=>l.zona))].sort();
document.getElementById('ftipo').innerHTML+=tipos.map(t=>`<option>${t}</option>`).join('');
document.getElementById('fzona').innerHTML+=zonas.map(z=>`<option>${z}</option>`).join('');
let layer=L.layerGroup().addTo(map);
function render(){
  layer.clearLayers();
  const ft=document.getElementById('ftipo').value, fz=document.getElementById('fzona').value, fm=parseInt(document.getElementById('fmin').value);
  let cnt=0;
  for(const l of lugares){
    if(ft&&l.tipo!==ft) continue;
    if(fz&&l.zona!==fz) continue;
    const aff=(l.negativas||0)+(l.positivas||0);
    if(aff<fm) continue;
    const c=L.circleMarker([l.lat,l.lon],{radius:5+4*Math.log(1+l.menciones_total),fillColor:colorFor(l.indice_desencanto),color:'#222',weight:1,fillOpacity:0.85});
    const idx=l.indice_desencanto!==null?l.indice_desencanto.toFixed(2):'—';
    c.bindPopup(`<b>${l.lugar}</b><br><i>${l.tipo} · ${l.zona}</i><br>Menciones: <b>${l.menciones_total}</b><br>Neg: <b>${l.negativas}</b> · Pos: <b>${l.positivas}</b><br>Idx: <b>${idx}</b>`);
    c.on('mouseover',()=>show(l));c.on('click',()=>show(l));
    c.addTo(layer);cnt++;
  }
  document.getElementById('stat').textContent=cnt;
}
function show(l){
  const idx=l.indice_desencanto!==null?l.indice_desencanto.toFixed(2):'—';
  const cats=Object.entries(l.categorias||{}).sort((a,b)=>b[1]-a[1]).map(([c,n])=>`<span style="background:#EAF1F8;color:#1F4E78;padding:2px 7px;border-radius:10px;margin:2px 3px 2px 0;font-size:11px;display:inline-block">${c}·${n}</span>`).join(' ');
  document.getElementById('detail').innerHTML=`<h2>${l.lugar}</h2><div style="color:#666;font-style:italic;font-size:12px;margin-bottom:10px">${l.tipo} · ${l.zona}</div><div style="font-size:11px;color:#666;margin-bottom:8px">Supuesto histórico:</div><div style="margin-bottom:8px">${l.supuesto_real||'—'}</div><div style="font-size:11px;color:#666;margin-bottom:4px">Categorías afectivas:</div><div>${cats||'<i>Sin clasificación</i>'}</div><div style="margin-top:8px;font-size:11px">${l.menciones_total} menciones · <b style="color:#B71C1C">${l.negativas} neg.</b> · <b style="color:#2E7D32">${l.positivas} pos.</b> · idx <b>${idx}</b></div>`;
}
['ftipo','fzona','fmin'].forEach(id=>document.getElementById(id).addEventListener('change',render));
render();
</script></body></html>""".replace('__TITLE__', title).replace('__DATA__', data_json)


def affective_map_html(places: List[Dict], out_path: str,
                        title: str = 'Mapa afectivo · Sin remedio'):
    """places: lista de dicts con lat, lon, lugar, tipo, zona, menciones_total,
    negativas, positivas, indice_desencanto, supuesto_real, categorias."""
    geo = [p for p in places if p.get('lat') is not None and p.get('lon') is not None]
    html = _affective_map_template(json.dumps(geo, ensure_ascii=False), title)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(html, encoding='utf-8')
    return out_path


def network_map_html(graph_data: Dict, geojson_data: Dict, out_path: str,
                     title: str = 'Red personajes ↔ lugares'):
    """graph_data: {'nodes': [...], 'edges': [{source, target, weight}]}.
    geojson_data: FeatureCollection con properties.name y properties.personajes.
    """
    data = json.dumps({'graph': graph_data, 'geojson': geojson_data},
                       ensure_ascii=False)
    html = r"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"><title>__TITLE__</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
*{box-sizing:border-box}body{margin:0;font-family:-apple-system,sans-serif;color:#1A1A1A}
.layout{display:grid;grid-template-columns:300px 1fr 340px;height:100vh}
#map{height:100%}
.panel{padding:14px;overflow-y:auto;background:#FAFAFA}
.panel.left{border-right:1px solid #ddd}
.panel.right{border-left:1px solid #ddd}
.panel h1{font-size:15px;color:#1F4E78;margin:0 0 6px}
.pers{padding:4px 8px;cursor:pointer;border-radius:4px;font-size:12px;display:flex;justify-content:space-between}
.pers:hover{background:#EAF1F8}
.pers.active{background:#C81F1F;color:white;font-weight:700}
.reset{background:white;border:1.5px solid #C81F1F;color:#C81F1F;padding:5px;border-radius:4px;font-size:11px;cursor:pointer;width:100%;margin:6px 0;font-weight:600}
.reset:disabled{opacity:0.5;cursor:not-allowed}
.group-title{font-size:10px;text-transform:uppercase;margin:10px 0 4px;font-weight:700;letter-spacing:.04em}
.detail{background:white;border:1px solid #e3e3e3;border-radius:6px;padding:14px;font-size:12px}
.detail h2{font-size:14px;color:#1F4E78;margin:0 0 4px}
.detail .empty{color:#999;font-style:italic;padding:18px 0;text-align:center}
</style></head><body>
<div class="layout">
<div class="panel left">
<h1>Personajes</h1>
<button class="reset" id="reset" disabled>Quitar filtro</button>
<div id="plist"></div>
</div>
<div id="map"></div>
<div class="panel right">
<h1>__TITLE__</h1>
<div style="font-size:11px;color:#666;font-style:italic;margin-bottom:10px">Clic en un personaje para filtrar.</div>
<div class="detail" id="detail"><div class="empty">Pase el cursor o haga clic sobre un punto.</div></div>
</div>
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const DATA=__DATA__;
const CAT_COLOR={Élite:'#7B1FA2',Popular:'#F57C00','Tránsito urbano':'#1976D2','Institucional/represivo':'#455A64',Otro:'#888'};
const ELITE=['Jockey Club','Hotel Tequendama','Edificio Avianca','Banco de la Sabana','Banco de la República','Embajada de los Estados Unidos','Embajada de Bélgica','Hipódromo','Club El Unicornio','Iglesia de la Porciúncula','Colegio San Tarsicio','Plazoleta del General San Martín','Teatro Colón','Museo de Arte Moderno (MAMBO)'];
const POPULAR=['La Perseverancia','Suba','Barrio Kennedy','Barrio El Rincón','Barrios de invasión','Bar El Oasis','Music Bar (Comida y Dancing)','Sagrado Corazón (imágenes domésticas)'];
const INST=['Cantón Norte / Remonta de Usaquén','Estación de policía','Capitolio Nacional'];
const TRANS=['Carrera Séptima','Carrera Trece','Carrera Quinta','Carrera Novena','Carrera Quince','Calle 100','Calle 19','Avenida Caracas'];
function catDe(l){if(ELITE.includes(l))return 'Élite';if(POPULAR.includes(l))return 'Popular';if(INST.includes(l))return 'Institucional/represivo';if(TRANS.includes(l))return 'Tránsito urbano';return 'Otro'}
const map=L.map('map').setView([4.65,-74.07],13);
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',{attribution:'© OSM © CARTO'}).addTo(map);
let layer=L.layerGroup().addTo(map);
let activo=null;
const ePers={},eLug={};
for(const e of DATA.graph.edges){
  const p=e.source.replace('P:','');const l=e.target.replace('L:','');
  (ePers[p]=ePers[p]||{})[l]=e.weight;(eLug[l]=eLug[l]||{})[p]=e.weight;
}
function buildList(){
  const personajes=DATA.graph.nodes.filter(n=>n.type==='personaje').sort((a,b)=>b.weight-a.weight);
  document.getElementById('plist').innerHTML=personajes.map(p=>`<div class="pers" data-p="${p.name}"><span>${p.name}</span><span style="opacity:0.6">${p.weight}</span></div>`).join('');
  document.querySelectorAll('.pers').forEach(r=>r.addEventListener('click',()=>{
    const p=r.dataset.p;activo===p?clear():set(p);
  }));
}
function set(p){activo=p;document.querySelectorAll('.pers').forEach(r=>r.classList.toggle('active',r.dataset.p===p));document.getElementById('reset').disabled=false;render()}
function clear(){activo=null;document.querySelectorAll('.pers').forEach(r=>r.classList.remove('active'));document.getElementById('reset').disabled=true;render()}
document.getElementById('reset').addEventListener('click',clear);
function render(){
  layer.clearLayers();
  for(const f of DATA.geojson.features){
    const l=f.properties.name;
    let w=f.properties.total_coocurrencias;
    if(activo){w=(ePers[activo]||{})[l];if(!w) continue;}
    const cat=catDe(l);const r=5+5*Math.log(1+w);
    const c=L.circleMarker([f.geometry.coordinates[1],f.geometry.coordinates[0]],{radius:r,fillColor:CAT_COLOR[cat],color:'#222',weight:1,fillOpacity:0.85});
    c.bindPopup(`<b>${l}</b><br><i>${cat}</i><br>${activo?activo+' aquí: <b>'+w+'</b>':'Total: <b>'+w+'</b>'}`);
    c.on('mouseover',()=>show(f,w));c.on('click',()=>show(f,w));
    c.addTo(layer);
  }
}
function show(f,w){
  const l=f.properties.name;const cat=catDe(l);
  if(activo){
    document.getElementById('detail').innerHTML=`<h2>${l}</h2><div style="color:#666;font-style:italic;font-size:11px;margin-bottom:8px">${cat}</div><b>${activo}</b> aquí en <b>${w}</b> ${w===1?'párrafo':'párrafos'}.`;
  }else{
    const lista=(f.properties.personajes||[]).map(p=>`<li style="padding:4px 0;border-bottom:1px solid #f0f0f0;display:flex;justify-content:space-between"><span><b>${p.nombre}</b></span><span style="color:#888;font-size:11px">${p.apariciones}×</span></li>`).join('');
    document.getElementById('detail').innerHTML=`<h2>${l}</h2><div style="color:#666;font-style:italic;font-size:11px;margin-bottom:8px">${cat} · ${w} coocurrencias</div><ul style="list-style:none;padding:0;margin:0">${lista||'<li><i style="color:#999">Sin personajes detectados.</i></li>'}</ul>`;
  }
}
buildList();render();
</script></body></html>""".replace('__TITLE__', title).replace('__DATA__', data)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(html, encoding='utf-8')
    return out_path
