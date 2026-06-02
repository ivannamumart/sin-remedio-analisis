"""
corpus.py
---------
Carga y parseo del corpus literario.

Funciones principales:
- load(path):                 lee el archivo de texto.
- parse_paragraphs(texto):    devuelve lista de dicts {capitulo, parrafo_id, texto}.
- load_config(path):          carga el YAML de configuración del proyecto.
"""

import re
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional


def load(path: str) -> str:
    """Lee el archivo de corpus como string UTF-8."""
    return Path(path).read_text(encoding='utf-8')


def load_config(path: str) -> Dict[str, Any]:
    """Carga el YAML de configuración del proyecto."""
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def parse_paragraphs(
    texto: str,
    chapter_regex: str = r'={20,}\s*\n(CAPÍTULO\s+[IVXLC]+)\s*\n={20,}',
    paragraph_marker: str = r'\[P-(\d+)\]',
    auto_split: bool = False,
) -> List[Dict[str, Any]]:
    """Parsea el corpus en párrafos con metadatos.

    Args:
        texto: string del corpus completo.
        chapter_regex: patrón regex que detecta encabezados de capítulo.
            Por defecto, espera bloques de '=' que envuelven 'CAPÍTULO X'.
        paragraph_marker: patrón regex con un grupo capturador para el ID del párrafo.
            Por defecto, '[P-123]'. Pasar None para usar auto_split.
        auto_split: si es True, los párrafos se determinan por separación de
            líneas en blanco. Útil para corpus sin marcas explícitas.

    Returns:
        Lista de dicts: [{'capitulo': str, 'parrafo_id': str,
                          'parrafo_num': int, 'texto': str}, ...]
    """
    chapters = re.split(chapter_regex, texto)
    # split deja: [pre_text, capítulo_1_título, capítulo_1_cuerpo,
    #              capítulo_2_título, capítulo_2_cuerpo, ...]

    parrafos = []
    counter_global = 0

    # Si no hay capítulos detectados, tratar todo el texto como un solo bloque
    if len(chapters) == 1:
        chapters = ['', 'TEXTO COMPLETO', chapters[0]]

    for i in range(1, len(chapters), 2):
        chap_name = chapters[i].strip()
        chap_text = chapters[i+1] if i+1 < len(chapters) else ""

        if paragraph_marker and not auto_split:
            # Buscar marcadores [P-N] y extraer el contenido entre ellos
            pattern = paragraph_marker + r'\s*(.+?)(?=' + paragraph_marker + r'|\n={20,}|\Z)'
            for match in re.finditer(pattern, chap_text, re.DOTALL):
                num = int(match.group(1))
                content = match.group(2).strip()
                parrafos.append({
                    'capitulo': chap_name,
                    'parrafo_num': num,
                    'parrafo_id': f'P-{num}',
                    'texto': content,
                })
        else:
            # Auto-split por dobles saltos de línea
            for block in re.split(r'\n\s*\n', chap_text):
                block = block.strip()
                if block:
                    counter_global += 1
                    parrafos.append({
                        'capitulo': chap_name,
                        'parrafo_num': counter_global,
                        'parrafo_id': f'P-{counter_global}',
                        'texto': block,
                    })
    return parrafos


def parse_from_config(corpus_path: str, config: Dict[str, Any]) -> List[Dict]:
    """Atajo: carga el corpus y aplica los parámetros del YAML."""
    texto = load(corpus_path)
    corp_cfg = config.get('corpus', {})
    return parse_paragraphs(
        texto,
        chapter_regex=corp_cfg.get('chapter_regex',
            r'={20,}\s*\n(CAPÍTULO\s+[IVXLC]+)\s*\n={20,}'),
        paragraph_marker=corp_cfg.get('paragraph_marker', r'\[P-(\d+)\]'),
        auto_split=corp_cfg.get('auto_split_paragraphs', False),
    )


# Smoke test
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        texto = load(sys.argv[1])
        parags = parse_paragraphs(texto)
        print(f'Párrafos parseados: {len(parags)}')
        if parags:
            print(f'Primero: {parags[0]["parrafo_id"]} ({parags[0]["capitulo"]})')
            print(f'Texto:   {parags[0]["texto"][:100]}…')
