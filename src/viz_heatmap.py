"""
viz_heatmap.py
--------------
Heatmap personaje × categoría espacial, coloreado por índice de desencanto.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable
from pathlib import Path
from typing import Dict, List


def color_idx(idx, cmap, norm):
    if idx is None:
        return '#F5F5F5'
    return cmap(norm(idx))


def heatmap_personaje_categoria(
    df_triple,
    personajes_info: Dict[str, Dict],
    out_path: str,
    cats_order: List[str] = None,
    min_apariciones: int = 4,
    circulo_colors: Dict[str, str] = None,
):
    """Heatmap con personajes (filas) × categoría espacial (columnas).

    df_triple: DataFrame del triple cruce (cross_analysis.triple_cross()).
    personajes_info: {nombre: {'circulo': str, ...}}
    """
    if cats_order is None:
        cats_order = ['Élite', 'Popular', 'Tránsito urbano',
                      'Institucional/represivo', 'Otro']
    if circulo_colors is None:
        circulo_colors = {
            'Núcleo': '#C62828', 'Familia oligarca': '#7B1FA2',
            'Bohemia/izquierda': '#F57C00', 'Maoístas': '#D32F2F',
            'Amantes': '#C2185B', 'Militar': '#455A64',
            'Servicio': '#5D4037', 'Cosmopolita': '#1976D2',
            'Otro': '#616161',
        }

    # Filtrar a personajes y categorías reales
    df = df_triple[(df_triple['Personaje'] != '(sin personaje)') &
                   (df_triple['Categoría'] != '(sin clasificación)')].copy()

    # Calcular índice por celda
    data_idx, data_n = {}, {}
    for pers in df['Personaje'].unique():
        for cat in cats_order:
            sub = df[(df['Personaje'] == pers) & (df['Cat_social_lugar'] == cat)]
            n_neg = sub[sub['Polaridad'] == 'Negativa']['Párrafo'].nunique()
            n_pos = sub[sub['Polaridad'] == 'Positiva']['Párrafo'].nunique()
            n_tot = sub['Párrafo'].nunique()
            idx = ((n_neg - n_pos) / (n_neg + n_pos)) if (n_pos+n_neg) > 0 else None
            data_idx[(pers, cat)] = idx
            data_n[(pers, cat)] = n_tot

    # Filtrar personajes significativos
    pers_total = df.groupby('Personaje')['Párrafo'].nunique()
    significativos = pers_total[pers_total >= min_apariciones].sort_values(
        ascending=False).index.tolist()

    # Ordenar por círculo
    pers_orden = []
    circulos_vistos = []
    for circ in circulo_colors:
        grupo = [p for p in significativos
                 if personajes_info.get(p, {}).get('circulo') == circ]
        grupo.sort(key=lambda x: -pers_total[x])
        if grupo:
            circulos_vistos.append(circ)
            pers_orden.extend(grupo)

    n_pers = len(pers_orden)
    n_cats = len(cats_order)
    cell_w, cell_h = 1.0, 0.65

    fig, ax = plt.subplots(figsize=(13, max(8, n_pers*0.55)), dpi=115)
    cmap = LinearSegmentedColormap.from_list('desencanto',
                                              ['#2E7D32', '#FFFFFF', '#C62828'])
    norm = Normalize(vmin=-1, vmax=1)

    for i, pers in enumerate(pers_orden):
        for j, cat in enumerate(cats_order):
            x = j*cell_w; y = (n_pers-1-i)*cell_h
            idx = data_idx[(pers, cat)]
            n = data_n[(pers, cat)]
            color = color_idx(idx, cmap, norm) if n > 0 else '#F5F5F5'
            ax.add_patch(mpatches.Rectangle(
                (x, y), cell_w*0.95, cell_h*0.92,
                facecolor=color, edgecolor='white', lw=1.5))
            if n > 0:
                tc = '#000' if (idx is None or abs(idx) < 0.5) else 'white'
                ax.text(x+cell_w*0.475, y+cell_h*0.62, f'n={n}',
                        ha='center', va='center', fontsize=9,
                        fontweight='bold', color=tc)
                if idx is not None:
                    ax.text(x+cell_w*0.475, y+cell_h*0.28, f'{idx:+.2f}',
                            ha='center', va='center', fontsize=8.5,
                            color=tc, style='italic')

    # Columnas
    for j, cat in enumerate(cats_order):
        ax.text(j*cell_w+cell_w*0.475, n_pers*cell_h+0.08, cat,
                ha='center', va='bottom', fontsize=10.5,
                fontweight='bold', color='#1F4E78')

    # Filas
    for i, pers in enumerate(pers_orden):
        y = (n_pers-1-i)*cell_h + cell_h*0.46
        circ = personajes_info.get(pers, {}).get('circulo', 'Otro')
        color = circulo_colors.get(circ, '#666')
        ax.text(-0.10, y, pers, ha='right', va='center',
                fontsize=10, fontweight='bold', color=color)
        ax.scatter([-0.04], [y], s=70, color=color,
                   edgecolor='white', lw=1.2, zorder=10)

    ax.text(n_cats*cell_w/2, n_pers*cell_h+0.55,
            'Personaje × Categoría espacial · color = índice de desencanto',
            ha='center', fontsize=13, fontweight='bold', color='#1F4E78')

    sm = ScalarMappable(cmap=cmap, norm=norm); sm.set_array([])
    cbar_ax = fig.add_axes([0.92, 0.30, 0.018, 0.4])
    cbar = plt.colorbar(sm, cax=cbar_ax)
    cbar.set_label('Índice de desencanto', fontsize=9)

    ax.set_xlim(-1.7, n_cats*cell_w+0.1)
    ax.set_ylim(-0.5, n_pers*cell_h+0.85)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_visible(False)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=115, bbox_inches='tight', facecolor='white')
    plt.close()
    return out_path
