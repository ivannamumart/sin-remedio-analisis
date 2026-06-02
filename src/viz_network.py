"""
viz_network.py
--------------
Grafo bipartito personajes ↔ lugares.
Personajes a la izquierda agrupados por círculo, lugares a la derecha agrupados
por categoría socio-espacial.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from pathlib import Path
from typing import Dict, List


def bipartite_network(
    df_coocurrencias,
    personajes_info: Dict[str, Dict],
    categorias_sociales: Dict[str, List[str]],
    out_path: str,
    min_personaje_weight: int = 3,
    circulo_colors: Dict[str, str] = None,
    cat_colors: Dict[str, str] = None,
):
    """Crea un grafo bipartito personajes ↔ lugares.

    df_coocurrencias: DataFrame con columnas ['Personaje', 'Lugar', 'Coocurrencias'].
    personajes_info: {nombre: {'circulo': str}}.
    categorias_sociales: {cat: [lugares]}.
    """
    if circulo_colors is None:
        circulo_colors = {
            'Núcleo': '#C62828', 'Familia oligarca': '#7B1FA2',
            'Familia/amistades': '#7B1FA2', 'Familia': '#9C27B0',
            'Bohemia/izquierda': '#F57C00', 'Maoístas': '#D32F2F',
            'Bohemia': '#FB8C00', 'Amantes': '#C2185B',
            'Cosmopolita': '#1976D2', 'Militar': '#455A64',
            'Servicio': '#5D4037', 'Otro': '#616161',
        }
    if cat_colors is None:
        cat_colors = {'Élite': '#7B1FA2', 'Popular': '#F57C00',
                      'Tránsito urbano': '#1976D2',
                      'Institucional/represivo': '#455A64', 'Otro': '#666'}

    filt = df_coocurrencias.copy()
    pers_total = filt.groupby('Personaje')['Coocurrencias'].sum()
    significativos = pers_total[pers_total >= min_personaje_weight].index.tolist()
    filt = filt[filt['Personaje'].isin(significativos)]

    # Lugar → categoría social
    lugar_to_cat = {}
    for cat, lista in categorias_sociales.items():
        for l in lista:
            lugar_to_cat[l] = cat

    def cat_de(lugar): return lugar_to_cat.get(lugar, 'Otro')

    # Orden de personajes por círculo
    pers_lista = []
    orden_circulos = list(circulo_colors.keys())
    for circ in orden_circulos:
        grupo = [p for p in significativos
                 if personajes_info.get(p, {}).get('circulo') == circ]
        grupo.sort(key=lambda x: -pers_total.get(x, 0))
        pers_lista.extend(grupo)

    # Orden de lugares por categoría
    lugares_en_grafo = filt['Lugar'].unique().tolist()
    lugar_total = filt.groupby('Lugar')['Coocurrencias'].sum().to_dict()
    lugares_por_cat = {c: [] for c in cat_colors}
    for l in lugares_en_grafo:
        cat = cat_de(l)
        lugares_por_cat.setdefault(cat, []).append(l)
    for cat in lugares_por_cat:
        lugares_por_cat[cat].sort(key=lambda x: -lugar_total.get(x, 0))

    orden_cats = ['Élite', 'Popular', 'Tránsito urbano',
                  'Institucional/represivo', 'Otro']
    lugares_lista = []
    for cat in orden_cats:
        lugares_lista.extend(lugares_por_cat.get(cat, []))

    n_pers = len(pers_lista)
    n_lug = len(lugares_lista)
    y_pers = np.linspace(0.95, 0.05, n_pers)
    y_lug = np.linspace(0.95, 0.05, n_lug)
    pos_pers = {p: (0.05, y_pers[i]) for i, p in enumerate(pers_lista)}
    pos_lug = {l: (0.95, y_lug[i]) for i, l in enumerate(lugares_lista)}

    fig, ax = plt.subplots(figsize=(16, 12), dpi=120)
    ax.set_xlim(-0.10, 1.10); ax.set_ylim(-0.02, 1.05)
    ax.set_facecolor('#FBF6E9')

    # Marcos de grupo (personajes)
    for circ in orden_circulos:
        grupo = [p for p in pers_lista
                 if personajes_info.get(p, {}).get('circulo') == circ]
        if not grupo: continue
        indices = [pers_lista.index(p) for p in grupo]
        y_top = y_pers[indices[0]] + 0.025
        y_bot = y_pers[indices[-1]] - 0.025
        ax.add_patch(mpatches.Rectangle(
            (0.0, y_bot), 0.13, y_top-y_bot,
            facecolor=circulo_colors[circ], alpha=0.10, zorder=1,
            edgecolor='none'))
        y_mid = (y_top + y_bot) / 2
        ax.text(-0.005, y_mid, circ.upper(), fontsize=8,
                fontweight='bold', color=circulo_colors[circ],
                va='center', ha='right', alpha=0.85, rotation=90)

    # Marcos de grupo (lugares)
    for cat in orden_cats:
        grupo = lugares_por_cat.get(cat, [])
        if not grupo: continue
        indices = [lugares_lista.index(l) for l in grupo]
        y_top = y_lug[indices[0]] + 0.025
        y_bot = y_lug[indices[-1]] - 0.025
        color = cat_colors.get(cat, '#999')
        ax.add_patch(mpatches.Rectangle(
            (0.87, y_bot), 0.13, y_top-y_bot,
            facecolor=color, alpha=0.10, zorder=1, edgecolor='none'))
        y_mid = (y_top + y_bot) / 2
        ax.text(1.005, y_mid, cat.upper(), fontsize=8,
                fontweight='bold', color=color, va='center', ha='left',
                alpha=0.85, rotation=-90)

    # Aristas
    max_w = filt['Coocurrencias'].max()
    for _, e in filt.iterrows():
        if e['Personaje'] not in pos_pers or e['Lugar'] not in pos_lug:
            continue
        x1, y1 = pos_pers[e['Personaje']]
        x2, y2 = pos_lug[e['Lugar']]
        w = e['Coocurrencias']
        circ = personajes_info.get(e['Personaje'], {}).get('circulo', 'Otro')
        color = circulo_colors.get(circ, '#666')
        alpha = 0.20 + 0.55 * (w/max_w)
        lw = 0.5 + 2.0 * (w/max_w)
        mid_x = 0.50
        ctrl_y = (y1 + y2)/2
        t = np.linspace(0, 1, 50)
        bx = (1-t)**2*x1 + 2*(1-t)*t*mid_x + t**2*x2
        by = (1-t)**2*y1 + 2*(1-t)*t*ctrl_y + t**2*y2
        ax.plot(bx, by, color=color, lw=lw, alpha=alpha, zorder=3,
                solid_capstyle='round')

    # Nodos
    for p, (x, y) in pos_pers.items():
        circ = personajes_info.get(p, {}).get('circulo', 'Otro')
        color = circulo_colors.get(circ, '#666')
        w = pers_total.get(p, 1)
        size = 200 + 70 * np.log1p(w)
        ax.scatter([x], [y], s=size, color=color, edgecolor='white',
                   lw=1.8, zorder=5, alpha=0.95)
        ax.text(x-0.018, y, p[:16]+('…' if len(p)>16 else ''),
                fontsize=8.5, color='#222', ha='right', va='center',
                fontweight='bold', zorder=6,
                path_effects=[pe.withStroke(linewidth=2, foreground='#FBF6E9')])

    for l, (x, y) in pos_lug.items():
        cat = cat_de(l)
        color = cat_colors.get(cat, '#666')
        w = lugar_total.get(l, 1)
        size = 100 + 50 * np.log1p(w)
        ax.scatter([x], [y], s=size, color=color, edgecolor='white',
                   lw=1.8, zorder=5, marker='s', alpha=0.95)
        label = l[:24]+('…' if len(l)>24 else '')
        ax.text(x+0.018, y, label, fontsize=8.2, color='#1F4E78',
                ha='left', va='center', fontweight='bold', zorder=6,
                path_effects=[pe.withStroke(linewidth=2, foreground='#FBF6E9')])

    ax.set_title('Red bipartita: personajes ↔ lugares',
                 fontsize=11.5, fontweight='bold', color='#1F4E78',
                 pad=12, loc='left')
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_visible(False)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=120, bbox_inches='tight', facecolor='white')
    plt.close()
    return out_path
