"""
viz_maps.py
-----------
Mapas estilizados con base configurable por YAML.

La geometría base (cerros, sabana, ejes viales, barrios) se pasa como dict
desde el YAML para que el toolkit sirva con cualquier ciudad.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import Polygon
from matplotlib.lines import Line2D
from matplotlib.cm import ScalarMappable
from matplotlib.colors import LinearSegmentedColormap, Normalize
from pathlib import Path
from typing import Dict, List, Optional


def draw_base(ax, geom: Dict, xlim, ylim):
    """Dibuja contexto geográfico: cerros/montañas, llanura, ejes viales, barrios.

    geom es un dict con claves opcionales:
    - cerros: lista de [lat, lon] que dibuja un polígono
    - sabana: dict {min_lon, color} para zona occidental
    - ejes: dict {nombre: {x: [lon1, lon2], y: [lat1, lat2], orient: 'v'|'h'|'d'}}
    - barrios: lista de {name, lat, lon}
    """
    ax.set_facecolor(geom.get('fondo', '#FBF7EE'))
    dxv = xlim[1] - xlim[0]
    dyv = ylim[1] - ylim[0]

    # Cerros (polígono al oriente)
    cerros = geom.get('cerros')
    if cerros:
        cx = [p[1] for p in cerros]
        cy = [p[0] for p in cerros]
        east = max(xlim[1], cerros[0][1] + 0.03)
        poly_x = cx + [east, east]
        poly_y = cy + [cy[-1], cy[0]]
        ax.add_patch(Polygon(list(zip(poly_x, poly_y)), closed=True,
                     facecolor='#B8D9A8', edgecolor='#6B9B58',
                     lw=1, alpha=0.5, zorder=1))
        label = geom.get('cerros_label', 'CERROS')
        ax.text(max(xlim[1]-dxv*0.04, cerros[0][1]+0.01),
                (ylim[0]+ylim[1])/2, label, fontsize=9, color='#3D6C2D',
                ha='right', va='center', style='italic', alpha=0.55,
                rotation=-90, fontweight='bold', zorder=2)

    # Sabana / llanura occidental
    sabana = geom.get('sabana')
    if sabana and xlim[0] < sabana['min_lon']:
        ax.axvspan(xlim[0], sabana['min_lon'], alpha=0.18,
                   color=sabana.get('color', '#F2D88D'), zorder=1)
        if sabana.get('label'):
            ax.text(xlim[0]+dxv*0.05, (ylim[0]+ylim[1])/2,
                    sabana['label'], fontsize=9, color='#8E6E2A',
                    ha='center', va='center', style='italic', alpha=0.55,
                    rotation=90, fontweight='bold', zorder=2)

    # Ejes viales
    for nombre, info in geom.get('ejes', {}).items():
        x, y, orient = info['x'], info['y'], info.get('orient', 'v')
        if (max(x) >= xlim[0]-0.005 and min(x) <= xlim[1]+0.005 and
            max(y) >= ylim[0]-0.005 and min(y) <= ylim[1]+0.005):
            ax.plot(x, y, color='#9A9A9A', lw=0.9, alpha=0.55, zorder=2)
            xm, ym = sum(x)/2, sum(y)/2
            xm = max(min(xm, xlim[1]-dxv*0.06), xlim[0]+dxv*0.06)
            ym = max(min(ym, ylim[1]-dyv*0.06), ylim[0]+dyv*0.06)
            rot = 90 if orient == 'v' else (0 if orient == 'h' else 55)
            ax.text(xm, ym, nombre, fontsize=6.5, color='#777',
                    alpha=0.8, rotation=rot, ha='center', va='center', zorder=2,
                    path_effects=[pe.withStroke(linewidth=2.2, foreground=geom.get('fondo', '#FBF7EE'))])

    # Barrios de referencia
    for b in geom.get('barrios', []):
        lat, lon = b['lat'], b['lon']
        if xlim[0] <= lon <= xlim[1] and ylim[0] <= lat <= ylim[1]:
            ax.scatter([lon], [lat], s=10, color='#999', alpha=0.5,
                       marker='s', zorder=2)
            ax.text(lon, lat-dyv*0.012, b['name'], fontsize=6.5,
                    color='#888', alpha=0.75, ha='center', va='top',
                    style='italic', zorder=2,
                    path_effects=[pe.withStroke(linewidth=2, foreground=geom.get('fondo', '#FBF7EE'))])

    ax.grid(True, alpha=0.12, color='gray', linestyle=':', zorder=0)


def heat_map(places: List[Dict], out_path: str, geom: Dict,
             value_key: str = 'idx_desencanto',
             size_key: str = 'total_menciones',
             title: str = 'Mapa de calor afectivo',
             xlim: Optional[tuple] = None, ylim: Optional[tuple] = None):
    """Mapa de calor: cada lugar coloreado según un valor escalar.

    places: lista de dicts con al menos 'lat', 'lon', value_key, size_key.
    """
    fig, ax = plt.subplots(figsize=(12, 13), dpi=115)

    # Calcular bounds si no se pasan
    if xlim is None or ylim is None:
        lats = [p['lat'] for p in places if p.get('lat')]
        lons = [p['lon'] for p in places if p.get('lon')]
        if xlim is None:
            xlim = (min(lons) - 0.02, max(lons) + 0.02)
        if ylim is None:
            ylim = (min(lats) - 0.02, max(lats) + 0.02)

    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.set_aspect('equal')
    draw_base(ax, geom, xlim, ylim)

    cmap = LinearSegmentedColormap.from_list('desencanto',
                                              ['#2E7D32', '#FFFFFF', '#C62828'])
    norm = Normalize(vmin=-1, vmax=1)

    for p in places:
        if p.get('lat') is None or p.get('lon') is None:
            continue
        val = p.get(value_key)
        size_val = p.get(size_key, 1) or 1
        color = cmap(norm(val)) if val is not None else '#9E9E9E'
        size = 80 + 70 * np.log1p(size_val)
        ax.scatter([p['lon']], [p['lat']], s=size, color=color,
                   edgecolor='white', lw=1.8, zorder=5, alpha=0.9)

    # Etiquetas para los más significativos
    sorted_p = sorted([p for p in places if p.get(size_key, 0) >= 4],
                      key=lambda x: -x.get(size_key, 0))
    for p in sorted_p[:20]:
        if p.get('lat') is None: continue
        ax.text(p['lon']+0.005, p['lat']+0.002, p.get('name', '?'),
                fontsize=7.5, color='#1a1a1a', ha='left', va='center',
                fontweight='bold', zorder=8,
                path_effects=[pe.withStroke(linewidth=3, foreground='white')])

    # Colorbar
    sm = ScalarMappable(cmap=cmap, norm=norm); sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.4, pad=0.02, aspect=22)
    cbar.set_label('Índice (-1 alegría · +1 desencanto)', fontsize=9, color='#333')

    ax.set_title(title, fontsize=13, fontweight='bold', color='#1F4E78', pad=14)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_edgecolor('#999'); s.set_linewidth(0.7)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=115, bbox_inches='tight', facecolor='white')
    plt.close()
    return out_path


def route_map(paradas: List[Dict], out_path: str, geom: Dict,
              title: str = 'Recorrido',
              subtitle: str = '',
              emo_color: Optional[Dict[str, str]] = None):
    """Mapa de una ruta narrativa con paradas numeradas y coloreadas por emoción.

    paradas: lista de dicts con 'nombre', 'lat', 'lon', 'emocion' (opcional).
    emo_color: dict {emocion: color_hex}. Si no, paradas en gris.
    """
    lons = [p['lon'] for p in paradas]
    lats = [p['lat'] for p in paradas]
    minx, maxx = min(lons), max(lons)
    miny, maxy = min(lats), max(lats)
    dx_ = max(maxx-minx, 0.018); dy_ = max(maxy-miny, 0.018)
    cx_, cy_ = (minx+maxx)/2, (miny+maxy)/2
    half = max(dx_, dy_)/2 + max(dx_, dy_)*0.55
    xlim = (cx_-half*1.15, cx_+half*1.15)
    ylim = (cy_-half, cy_+half)

    fig, ax = plt.subplots(figsize=(10, 10), dpi=110)
    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.set_aspect('equal')
    draw_base(ax, geom, xlim, ylim)

    # Línea de recorrido
    from matplotlib.patches import FancyArrowPatch
    for i in range(len(lons)-1):
        arrow = FancyArrowPatch((lons[i], lats[i]), (lons[i+1], lats[i+1]),
                                arrowstyle='-|>', mutation_scale=18, lw=2.2,
                                color='#555', alpha=0.7, zorder=4,
                                shrinkA=14, shrinkB=14,
                                connectionstyle='arc3,rad=0.05')
        ax.add_patch(arrow)

    dxv = xlim[1]-xlim[0]; dyv = ylim[1]-ylim[0]
    for i, p in enumerate(paradas, 1):
        emo = p.get('emocion')
        color = (emo_color or {}).get(emo, '#9E9E9E')
        ax.scatter([p['lon']], [p['lat']], s=620, color=color,
                   edgecolor='white', lw=2.5, zorder=6, alpha=0.95)
        ax.text(p['lon'], p['lat'], str(i), color='white', fontsize=13,
                fontweight='bold', ha='center', va='center', zorder=7)
        ang = np.arctan2(p['lat']-cy_, p['lon']-cx_)
        ox = np.cos(ang)*dxv*0.04; oy = np.sin(ang)*dyv*0.04
        ha = 'left' if ox >= 0 else 'right'
        emo_txt = f' · {emo}' if emo else ''
        ax.annotate(f'{i}. {p["nombre"]}{emo_txt}',
                    xy=(p['lon'], p['lat']), xytext=(p['lon']+ox, p['lat']+oy),
                    fontsize=8.5, color='#1a1a1a', ha=ha, va='center',
                    fontweight='bold', zorder=8,
                    path_effects=[pe.withStroke(linewidth=3.5, foreground='white')])

    fig.suptitle(title, fontsize=14, fontweight='bold', y=0.975, color='#1F4E78')
    if subtitle:
        ax.set_title(subtitle, fontsize=10, color='#444', pad=8)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_edgecolor('#999'); s.set_linewidth(0.7)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(out_path, dpi=110, bbox_inches='tight', facecolor='white')
    plt.close()
    return out_path
