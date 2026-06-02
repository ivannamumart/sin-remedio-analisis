# Formato esperado de corpus

El parser de `corpus.py` reconoce capítulos y párrafos por marcas.

## Formato canónico (corpus de Sin remedio)

```
============================
CAPÍTULO I
============================

[P-1] Texto del primer párrafo de toda la novela...

[P-2] Texto del segundo párrafo...

============================
CAPÍTULO II
============================

[P-225] Texto del párrafo 225...
```

Reglas:

1. Cada capítulo viene precedido por una línea de signos `=` (≥20), su título y
   otra línea de `=`. El título puede ser `CAPÍTULO I`, `CAPÍTULO 1`,
   `Capítulo Uno`, etc. — el regex por defecto admite romanos en mayúsculas.
2. Cada párrafo arranca con el marcador `[P-N]` donde `N` es un entero único
   en todo el corpus.
3. El contenido del párrafo va hasta el siguiente marcador `[P-` o el siguiente
   bloque de `=`.

## Cómo generar el corpus desde un texto plano

Si tienes una novela como texto continuo (sin marcas), puedes generar el
formato con un pequeño script:

```python
import re

with open('novela_cruda.txt') as f:
    texto = f.read()

# Detectar capítulos por encabezado "Capítulo X"
chapters = re.split(r'\n\s*(Cap[íi]tulo\s+[\w]+)\s*\n', texto)

out = []
counter = 1
for i in range(1, len(chapters), 2):
    title = chapters[i].strip().upper()
    body = chapters[i+1]
    out.append(f'\n{"="*30}\n{title}\n{"="*30}\n')
    # Cada párrafo = bloque separado por línea en blanco
    for parag in re.split(r'\n\s*\n', body):
        if parag.strip():
            out.append(f'[P-{counter}] {parag.strip()}\n')
            counter += 1

with open('corpus.txt', 'w') as f:
    f.write('\n'.join(out))
```

## Formatos alternativos soportados

El parser también acepta variantes si se indican en el YAML:

```yaml
corpus:
  chapter_regex: 'CAP[ÍI]TULO\s+([IVXLC]+)'
  paragraph_marker: '\[P-(\d+)\]'
```

Para corpus sin marca de párrafo explícita, usar la opción de auto-splitting:

```yaml
corpus:
  paragraph_marker: null
  auto_split_paragraphs: true     # cada bloque separado por \n\n se cuenta como párrafo
```
