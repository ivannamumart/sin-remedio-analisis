"""
spatial_extraction.py
---------------------
Extracción de referencias espaciales del corpus.

Cada lugar del catálogo se define con su patrón regex, supuesto histórico,
zona, coordenadas aproximadas y etiquetas para análisis estadístico.
"""

import re
import pandas as pd
from typing import List, Dict, Any


def extract(
    parrafos: List[Dict[str, Any]],
    catalogo: List[Dict[str, Any]],
    contexto_chars: int = 120,
) -> pd.DataFrame:
    """Extrae referencias espaciales del corpus.

    Args:
        parrafos: lista producida por corpus.parse_paragraphs().
        catalogo: lista de dicts con las claves:
            - patron: str con regex
            - nombre_canonico: str
            - tipo_lugar: str
            - supuesto_real: str
            - justificacion: str
            - zona: str
            - lat, lon: float (pueden ser None)
            - funcion_narrativa: str
            - etiquetas: str
        contexto_chars: caracteres a izquierda/derecha del match para el fragmento.

    Returns:
        DataFrame con una fila por (párrafo × lugar detectado).
    """
    # Compilar patrones una sola vez
    compiled = []
    for entry in catalogo:
        try:
            compiled.append((re.compile(entry['patron']), entry))
        except re.error as e:
            print(f"Patrón inválido para '{entry.get('nombre_canonico','?')}': {e}")

    filas = []
    for p in parrafos:
        texto = p['texto']
        for rx, entry in compiled:
            matches = list(rx.finditer(texto))
            if not matches:
                continue
            m = matches[0]  # primer match para el fragmento
            ini = max(0, m.start() - contexto_chars)
            fin = min(len(texto), m.end() + contexto_chars)
            fragmento = texto[ini:fin].strip()
            if len(fragmento) > 300:
                fragmento = fragmento[:297] + '…'
            cita_ini = max(0, m.start() - 30)
            cita_fin = min(len(texto), m.end() + 30)
            cita = texto[cita_ini:cita_fin].strip()

            filas.append({
                'Párrafo': p['parrafo_id'],
                'Capítulo': p['capitulo'],
                'Fragmento (300 car.)': fragmento,
                'Referencia textual (cita)': cita,
                'Lugar nombrado (canónico)': entry['nombre_canonico'],
                'Tipo de lugar': entry.get('tipo_lugar', ''),
                'Supuesto histórico': entry.get('supuesto_real', ''),
                'Justificación del supuesto': entry.get('justificacion', ''),
                'Zona': entry.get('zona', ''),
                'Latitud (aprox.)': entry.get('lat'),
                'Longitud (aprox.)': entry.get('lon'),
                'Función narrativa': entry.get('funcion_narrativa', ''),
                'Etiquetas': entry.get('etiquetas', ''),
                'Frecuencia en el párrafo': len(matches),
            })

    df = pd.DataFrame(filas)
    if not df.empty:
        df['__num'] = df['Párrafo'].str.extract(r'P-(\d+)').astype(int)
        df = df.sort_values('__num').drop(columns=['__num']).reset_index(drop=True)
    return df


def summary_by_place(df: pd.DataFrame) -> pd.DataFrame:
    """Resumen de frecuencias por lugar canónico."""
    if df.empty:
        return pd.DataFrame()
    return df.groupby(
        ['Lugar nombrado (canónico)', 'Tipo de lugar', 'Zona', 'Supuesto histórico'],
        as_index=False
    ).agg(
        Frecuencia_total=('Frecuencia en el párrafo', 'sum'),
        Apariciones_en_parrafos=('Párrafo', 'nunique'),
    ).sort_values('Frecuencia_total', ascending=False)


def summary_by_chapter(df: pd.DataFrame) -> pd.DataFrame:
    """Conteo de referencias por capítulo."""
    if df.empty:
        return pd.DataFrame()
    return df.groupby('Capítulo', as_index=False).agg(
        Total_referencias=('Frecuencia en el párrafo', 'sum'),
        Lugares_distintos=('Lugar nombrado (canónico)', 'nunique'),
        Parrafos_con_referencia=('Párrafo', 'nunique'),
    )
