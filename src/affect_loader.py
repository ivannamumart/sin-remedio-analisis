"""
affect_loader.py
----------------
Carga la extracción afectiva externa (Excel producido por LLM o anotación humana).

Formato esperado: hoja con columnas 'Párrafo' y al menos una de:
- 'Categorías emocionales'
- 'Categorías sociales'
- 'Otras categorías'
- 'Todas las categorías'

Cada celda contiene categorías separadas por comas.
"""

import pandas as pd
from typing import Optional, Dict, Any


def parse_categories(s: Any) -> list:
    """Parsea una celda con categorías separadas por comas."""
    if pd.isna(s):
        return []
    return [c.strip() for c in str(s).split(',') if c.strip()]


def load(
    path: str,
    sheet_name: str = 'Extracción emocional',
    column_map: Optional[Dict[str, str]] = None,
) -> pd.DataFrame:
    """Carga el Excel de extracción emocional.

    Args:
        path: ruta al archivo Excel.
        sheet_name: nombre o índice de la hoja a cargar.
        column_map: dict para renombrar columnas. Por defecto usa los nombres
            estándar del proyecto Sin remedio.

    Returns:
        DataFrame con columnas:
        - Párrafo
        - cats_emocionales_list (list)
        - cats_sociales_list (list)
        - cats_otras_list (list)
        - cats_todas_list (list)
        - cats_string (str original, para referencia)
    """
    df = pd.read_excel(path, sheet_name=sheet_name)

    if column_map:
        df = df.rename(columns=column_map)

    # Detectar columnas existentes flexiblemente
    col_map_estandar = {
        'Categorías emocionales': 'cats_emocionales_list',
        'Categorías sociales': 'cats_sociales_list',
        'Otras categorías': 'cats_otras_list',
        'Todas las categorías': 'cats_todas_list',
    }

    for src, dst in col_map_estandar.items():
        if src in df.columns:
            df[dst] = df[src].apply(parse_categories)
        else:
            df[dst] = [[] for _ in range(len(df))]

    # String original consolidado
    if 'Todas las categorías' in df.columns:
        df['cats_string'] = df['Todas las categorías']
    else:
        df['cats_string'] = df['cats_todas_list'].apply(lambda x: ', '.join(x))

    return df


def get_unique_categories(df: pd.DataFrame) -> Dict[str, set]:
    """Devuelve sets de categorías únicas por tipo."""
    out = {'emocionales': set(), 'sociales': set(), 'otras': set(), 'todas': set()}
    for col, key in [
        ('cats_emocionales_list', 'emocionales'),
        ('cats_sociales_list', 'sociales'),
        ('cats_otras_list', 'otras'),
        ('cats_todas_list', 'todas'),
    ]:
        if col in df.columns:
            for lst in df[col]:
                if isinstance(lst, list):
                    out[key].update(lst)
    return out
