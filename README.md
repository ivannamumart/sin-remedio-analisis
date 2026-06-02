# Geoaffect Toolkit · Cartografía geocrítica asistida

Herramientas reproducibles para el análisis espacial y afectivo de corpus literarios,
con visualizaciones interactivas y reportes en Excel y mapas.

Diseñado originalmente para *Sin remedio* de Antonio Caballero (Bogotá, 1972), pero
configurable para cualquier corpus narrativo con marcas de párrafo o capítulo.
[English version below]
---
## Transparencia Metodológica e Integración de IA
Este proyecto se desarrolló mediante un flujo de trabajo *human-in-the-loop*, utilizando a Claude como colaborador asistido por IA.
- **Rol de la IA**: Generación de código, extracción de patrones y análisis estadístico.
- **Rol de la investigadora**: Preparación del corpus, ingeniería de prompts, validación crítica y análisis interpretativo.
- **Compromiso**: Priorizamos la transparencia para garantizar la replicabilidad y auditoría científica.

## Uso
La estructura es modular y permite correr los análisis en Google Colab:
- `/src`: Módulos de código (corpus, extracción, análisis, visualización).
- `/notebooks`: Cuadernos de Jupyter autocontenidos.
- `/configs`: Archivos YAML para adaptar el toolkit a otros corpus.

## Estructura

```
sin_remedio_toolkit/
├── src/                          Módulos reusables
│   ├── corpus.py                 Carga y parseo de corpus
│   ├── spatial_extraction.py     Extracción de referencias espaciales (regex + catálogo)
│   ├── affect_loader.py          Carga de la extracción afectiva (Excel)
│   ├── character_extraction.py   Detección de personajes en párrafos
│   ├── cross_analysis.py         Cruces emocional × espacial y triple cruce
│   ├── viz_maps.py               Mapas estilizados con base de Bogotá
│   ├── viz_network.py            Grafos bipartitos personaje × lugar
│   ├── viz_heatmap.py            Heatmap personaje × categoría espacial
│   ├── exporters.py              Exportadores a Excel, CSV, JSON, GeoJSON
│   └── interactive.py            Generación de HTML interactivos (Leaflet)
│
├── configs/                      Configuración por proyecto (YAML)
│   ├── sin_remedio.yaml          Catálogos de lugares, personajes, polaridad, geometría
│   └── plantilla_proyecto.yaml   Plantilla en blanco para nuevos proyectos
│
├── notebooks/                    Notebooks de ejecución (uno por análisis)
│   ├── 01_extraccion_espacial.ipynb
│   ├── 02_cruce_emocional.ipynb
│   ├── 03_red_personajes.ipynb
│   ├── 04_triple_cruce.ipynb
│   ├── 05_recorridos_y_mapas.ipynb
│   └── 06_dashboards_interactivos.ipynb
│
├── data/                         Inputs del usuario
│   ├── corpus.txt                Texto del corpus (formato esperado en docs/)
│   └── extraccion_emocional.xlsx Clasificación afectiva externa (opcional)
│
├── outputs/                      Archivos generados
│
├── docs/
│   └── formato_corpus.md         Especificación del formato de corpus
│
└── requirements.txt              Dependencias mínimas
```

---

## Instalación rápida

```bash
git clone <repo-url> geoaffect-toolkit
cd geoaffect-toolkit
pip install -r requirements.txt
```

En Colab:

```python
!pip install -q -r requirements.txt
```

---

## Uso mínimo (Sin remedio)

```python
from src import corpus, spatial_extraction, affect_loader, cross_analysis
from src import exporters, viz_maps

# 1. Cargar el corpus
texto = corpus.load('data/corpus.txt')
parrafos = corpus.parse_paragraphs(texto)

# 2. Extraer referencias espaciales con el catálogo
config = corpus.load_config('configs/sin_remedio.yaml')
df_esp = spatial_extraction.extract(parrafos, config['lugares'])

# 3. Cargar la extracción emocional externa
df_emo = affect_loader.load('data/extraccion_emocional.xlsx')

# 4. Cruzar
cruce = cross_analysis.cross(df_esp, df_emo)
piv = cross_analysis.pivot_lugar_categoria(cruce, config['polaridad'])

# 5. Exportar
exporters.to_excel(piv, 'outputs/cruce_espacial_emocional.xlsx')
viz_maps.heat_map(piv, 'outputs/mapa_calor.png', geom=config['geometria_base'])
```

---

## Reutilizar con otro corpus

Para analizar otra novela urbana, basta con:

1. Colocar el texto en `data/corpus.txt` (ver `docs/formato_corpus.md`).
2. Copiar `configs/plantilla_proyecto.yaml`, renombrarlo y llenar con los lugares,
   personajes y polaridades de la nueva obra.
3. Ejecutar los notebooks `01_…` a `06_…` apuntando al nuevo YAML.

No hace falta tocar el código de `src/`.

---

## Notebooks

Cada notebook es autocontenido: importa los módulos, carga la configuración y
produce los outputs correspondientes. Pueden correrse en orden o por separado.

| Notebook | Produce |
|----------|---------|
| `01_extraccion_espacial` | `extraccion_espacial.xlsx` |
| `02_cruce_emocional` | `cruce_espacial_emocional.xlsx`, `mapa_calor_afectivo.png`, GeoJSON |
| `03_red_personajes` | `red_personajes_lugares.xlsx`, `red_bipartita.png` |
| `04_triple_cruce` | `triple_cruce.xlsx`, `heatmap_personaje_cat_espacial.png` |
| `05_recorridos_y_mapas` | Mapas individuales de cada recorrido + mapa maestro |
| `06_dashboards_interactivos` | HTMLs con Leaflet (mapa afectivo, red, dashboard triple) |

---

## Notas metodológicas

- Las **extracciones espaciales** se basan en regex y catálogo manual de lugares.
  Privilegian precisión sobre exhaustividad. Revisión humana recomendada antes
  de publicar resultados.
- La **extracción afectiva** se asume producida externamente (por ejemplo, con
  un LLM con esquema *human-in-the-loop*). El toolkit recibe el resultado y lo
  cruza con la geografía.
- La **detección de personajes** usa el catálogo del YAML. Para nombres muy
  comunes (María, Juan), revisar muestras de coocurrencias para descartar
  homonimias.

---

## Licencia y citación

Código bajo licencia MIT. Si usas el toolkit para tu investigación, cita el
trabajo original sobre el que se desarrolló:

> Muñoz, I. (2026). *Bogotá, ciudad del Sin remedio: cartografía geocrítica y
> oráculo espacial de la narrativa de Antonio Caballero asistido por
> inteligencia artificial.* Maestría en Humanidades Digitales, Universidad de
> los Andes.
