"""
character_extraction.py
-----------------------
Detección de personajes en el corpus a partir de un catálogo manual.

El catálogo es una lista de personajes con sus variantes textuales (nombres
canónicos, diminutivos, apellidos, etc.).
"""

import re
import pandas as pd
from typing import List, Dict, Any
from collections import defaultdict


def detect_in_text(texto: str, catalogo: List[Dict]) -> set:
    """Devuelve el set de personajes canónicos detectados en el texto."""
    detectados = set()
    for personaje in catalogo:
        for variante in personaje.get('variantes', [personaje['canonico']]):
            if re.search(r'\b' + re.escape(variante) + r'\b', texto):
                detectados.add(personaje['canonico'])
                break
    return detectados


def index_paragraphs(parrafos: List[Dict], catalogo: List[Dict]) -> Dict[str, set]:
    """Devuelve dict {parrafo_id: {personaje1, personaje2,…}}.
    Útil como precómputo para cruces masivos."""
    out = {}
    for p in parrafos:
        out[p['parrafo_id']] = detect_in_text(p['texto'], catalogo)
    return out


def cooccurrence_with_spatial(
    df_espacial: pd.DataFrame,
    parrafos_index: Dict[str, set],
    catalogo: List[Dict],
) -> pd.DataFrame:
    """Cruza la extracción espacial con los personajes detectados por párrafo.

    Args:
        df_espacial: DataFrame producido por spatial_extraction.extract().
        parrafos_index: precómputo de index_paragraphs().
        catalogo: lista de personajes para anexar metadatos.

    Returns:
        DataFrame largo: una fila por (párrafo, lugar, personaje).
    """
    info = {p['canonico']: p for p in catalogo}
    filas = []
    for _, row in df_espacial.iterrows():
        pid = row['Párrafo']
        pers = parrafos_index.get(pid, set())
        for per in pers:
            filas.append({
                'Párrafo': pid,
                'Capítulo': row['Capítulo'],
                'Lugar': row['Lugar nombrado (canónico)'],
                'Tipo_lugar': row['Tipo de lugar'],
                'Zona': row['Zona'],
                'Personaje': per,
                'Círculo': info.get(per, {}).get('circulo', ''),
                'Clase': info.get(per, {}).get('clase', ''),
            })
    return pd.DataFrame(filas)


def cooccurrence_counts(df_co: pd.DataFrame) -> pd.DataFrame:
    """Cuenta coocurrencias únicas (un par cuenta una vez por párrafo)."""
    if df_co.empty:
        return pd.DataFrame()
    return df_co.groupby(
        ['Personaje', 'Círculo', 'Lugar', 'Tipo_lugar', 'Zona'],
        as_index=False
    ).agg(
        Coocurrencias=('Párrafo', 'nunique')
    ).sort_values('Coocurrencias', ascending=False)


def character_signature(df_co: pd.DataFrame) -> pd.DataFrame:
    """Resumen por personaje: total de coocurrencias, lugares distintos, capítulos."""
    if df_co.empty:
        return pd.DataFrame()
    return df_co.groupby('Personaje', as_index=False).agg(
        Apariciones=('Párrafo', 'nunique'),
        Lugares_distintos=('Lugar', 'nunique'),
        Capitulos=('Capítulo', 'nunique'),
    ).sort_values('Apariciones', ascending=False)
