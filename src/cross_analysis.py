"""
cross_analysis.py
-----------------
Cruces analíticos: emocional × espacial, triple cruce (con personajes).

Funciones principales:
- cross_spatial_affect():        une referencias espaciales con clasificación afectiva.
- pivot_place_category():        tabla pivote lugar × categoría con índice de desencanto.
- pivot_zone_polarity():         agregación por zona × polaridad.
- pivot_social_category():       agregación por categoría socio-espacial.
- triple_cross():                personaje × lugar × categoría afectiva.
- polarity_of():                 función para clasificar una categoría.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Callable


def make_polarity_fn(polaridad_cfg: Dict[str, List[str]]) -> Callable[[str], str]:
    """Construye una función de polaridad a partir del YAML.

    polaridad_cfg tiene la forma:
    {
        'Negativa': ['Tristeza', 'Ira/Enojo', …],
        'Positiva': ['Alegría', 'Deseo/Erotismo'],
        'Tensión social': ['Clasismo', 'Homofobia', …],
        'Neutra': ['Referencia de lugares', …],
    }
    """
    mapping = {}
    for pol, lista in polaridad_cfg.items():
        for cat in lista:
            mapping[cat] = pol
    def fn(cat):
        return mapping.get(cat, 'Sin clasificación')
    return fn


def cross_spatial_affect(
    df_esp: pd.DataFrame,
    df_emo: pd.DataFrame,
) -> pd.DataFrame:
    """Left join de la extracción espacial con la emocional por Párrafo.

    Cada fila tiene además la lista de categorías del párrafo.
    """
    emo_idx = df_emo.set_index('Párrafo')[
        ['cats_todas_list', 'cats_emocionales_list',
         'cats_sociales_list', 'cats_otras_list', 'cats_string']
    ]
    cruce = df_esp.merge(emo_idx, on='Párrafo', how='left')
    cruce['tiene_clasif_afectiva'] = cruce['cats_todas_list'].apply(
        lambda x: isinstance(x, list) and len(x) > 0
    )
    return cruce


def long_format(cruce: pd.DataFrame, polaridad_fn: Callable) -> pd.DataFrame:
    """Convierte el cruce a formato largo: una fila por (lugar × categoría)."""
    filas = []
    for _, row in cruce.iterrows():
        cats = row['cats_todas_list'] if isinstance(row['cats_todas_list'], list) else []
        if not cats:
            filas.append({
                'Párrafo': row['Párrafo'], 'Capítulo': row['Capítulo'],
                'Lugar': row['Lugar nombrado (canónico)'],
                'Tipo': row['Tipo de lugar'], 'Zona': row['Zona'],
                'Categoría': '(sin clasificación)', 'Polaridad': 'Sin',
            })
        else:
            for c in cats:
                filas.append({
                    'Párrafo': row['Párrafo'], 'Capítulo': row['Capítulo'],
                    'Lugar': row['Lugar nombrado (canónico)'],
                    'Tipo': row['Tipo de lugar'], 'Zona': row['Zona'],
                    'Categoría': c, 'Polaridad': polaridad_fn(c),
                })
    return pd.DataFrame(filas)


def pivot_place_category(
    df_largo: pd.DataFrame,
    negativas: List[str],
    positivas: List[str],
    tension: List[str],
) -> pd.DataFrame:
    """Tabla pivote lugar × categoría con índice de desencanto."""
    df = df_largo[df_largo['Categoría'] != '(sin clasificación)'].copy()
    if df.empty:
        return pd.DataFrame()

    pivot = df.pivot_table(
        index=['Lugar', 'Tipo', 'Zona'],
        columns='Categoría', values='Párrafo',
        aggfunc='count', fill_value=0,
    ).reset_index()

    cat_cols = [c for c in pivot.columns if c not in ('Lugar', 'Tipo', 'Zona')]
    pivot['Total_menciones_cat'] = pivot[cat_cols].sum(axis=1)
    pivot['Negativas'] = pivot[[c for c in cat_cols if c in negativas]].sum(axis=1)
    pivot['Positivas'] = pivot[[c for c in cat_cols if c in positivas]].sum(axis=1)
    pivot['Tension_social'] = pivot[[c for c in cat_cols if c in tension]].sum(axis=1)

    def idx_des(row):
        total_aff = row['Negativas'] + row['Positivas']
        if total_aff == 0:
            return None
        return (row['Negativas'] - row['Positivas']) / total_aff

    pivot['Indice_desencanto'] = pivot.apply(idx_des, axis=1)
    return pivot.sort_values('Total_menciones_cat', ascending=False)


def pivot_zone_polarity(df_largo: pd.DataFrame) -> pd.DataFrame:
    """Distribución de polaridades por zona urbana."""
    df = df_largo[df_largo['Categoría'] != '(sin clasificación)']
    return df.pivot_table(
        index='Zona', columns='Polaridad', values='Párrafo',
        aggfunc='count', fill_value=0
    ).reset_index()


def pivot_social_category(
    df_largo: pd.DataFrame,
    categorias_sociales: Dict[str, List[str]],
) -> pd.DataFrame:
    """Pivote por categoría socio-espacial.

    categorias_sociales: dict {'Élite': [lista lugares], 'Popular': [...], …}
    """
    df = df_largo[df_largo['Categoría'] != '(sin clasificación)'].copy()
    lugar_to_cat = {}
    for cat, lista in categorias_sociales.items():
        for lugar in lista:
            lugar_to_cat[lugar] = cat

    df['Cat_social'] = df['Lugar'].map(lugar_to_cat).fillna('Otro')
    return df.pivot_table(
        index='Cat_social', columns='Polaridad', values='Párrafo',
        aggfunc='count', fill_value=0
    ).reset_index()


def triple_cross(
    cruce: pd.DataFrame,
    parrafos_index_personajes: Dict[str, set],
    polaridad_fn: Callable,
    categorias_sociales: Dict[str, List[str]],
) -> pd.DataFrame:
    """Triple cruce: párrafo × lugar × personaje × categoría.

    Args:
        cruce: producto de cross_spatial_affect().
        parrafos_index_personajes: precómputo de character_extraction.index_paragraphs().
        polaridad_fn: función que toma una categoría y devuelve la polaridad.
        categorias_sociales: mapeo de lugares a categorías sociales.

    Returns:
        DataFrame largo. Una fila por combinación.
    """
    lugar_to_cat = {}
    for cat, lista in categorias_sociales.items():
        for l in lista:
            lugar_to_cat[l] = cat

    filas = []
    for _, row in cruce.iterrows():
        pid = row['Párrafo']
        lugar = row['Lugar nombrado (canónico)']
        pers = parrafos_index_personajes.get(pid, set())
        cats = row['cats_todas_list'] if isinstance(row['cats_todas_list'], list) else []
        if not pers and not cats:
            continue
        pers_list = list(pers) if pers else ['(sin personaje)']
        cats_list = cats if cats else ['(sin clasificación)']
        for p in pers_list:
            for c in cats_list:
                filas.append({
                    'Párrafo': pid, 'Capítulo': row['Capítulo'],
                    'Lugar': lugar, 'Tipo_lugar': row['Tipo de lugar'],
                    'Zona': row['Zona'],
                    'Cat_social_lugar': lugar_to_cat.get(lugar, 'Otro'),
                    'Personaje': p,
                    'Categoría': c, 'Polaridad': polaridad_fn(c) if c != '(sin clasificación)' else 'Sin',
                })
    return pd.DataFrame(filas)


def dominant_emotion_by_place(
    pivot: pd.DataFrame,
    affective_categories: List[str],
) -> Dict[str, Dict]:
    """Para cada lugar, devuelve la categoría afectiva con más menciones.

    Args:
        pivot: producto de pivot_place_category().
        affective_categories: lista de categorías a considerar
            (típicamente: emocionales + tensión social, excluyendo neutras).

    Returns:
        {lugar: {'dominante': str, 'n': int, 'idx_desencanto': float, 'total': int}}
    """
    out = {}
    for _, row in pivot.iterrows():
        lugar = row['Lugar']
        vals = {c: row[c] for c in affective_categories
                if c in pivot.columns and row[c] > 0}
        if vals:
            dom = max(vals, key=vals.get)
            out[lugar] = {
                'dominante': dom, 'n': int(vals[dom]),
                'idx_desencanto': row.get('Indice_desencanto'),
                'total': int(row.get('Total_menciones_cat', 0)),
            }
        else:
            out[lugar] = {
                'dominante': None, 'n': 0,
                'idx_desencanto': row.get('Indice_desencanto'),
                'total': int(row.get('Total_menciones_cat', 0)),
            }
    return out
