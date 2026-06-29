# Paso 09 — Renderer del informe a Word (python-docx)

## Objetivo
Crear `app/report/docx_renderer.py`: convierte un `Informe` (dict validado) en un `.docx`
**profesional, institucional y consistente**. Render determinista (sin IA aquí).

## Diseño visual
- Paleta institucional sobria. Sugerencia: azul/teal profundo `#0B3C5D` (encabezados) + acento
  `#1D6FA3`, gris `#444444` para texto, y para niveles de riesgo: alto `#C0392B`, medio `#E67E22`,
  bajo `#27AE60`.
- Tipografía: Calibri/Helvetica. Tamaños: H1 16pt bold, H2 13pt bold, cuerpo 10.5–11pt.
- Portada con título, clasificación ("CONFIDENCIAL — Uso oficial restringido"), evento, ventana de
  datos, fecha y "Preparado por". Salto de página tras la portada.
- Pie de página con numeración de páginas y nota de confidencialidad.

## Helpers requeridos (python-docx)
Implementa utilidades reutilizables:

```python
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def _set_cell_shading(cell, hex_color: str):
    """Sombrea el fondo de una celda."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)

def _add_page_number_footer(section):
    """Inserta 'Página X de Y' como campos OOXML en el pie."""
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    # ... usar fldSimple/PAGE y NUMPAGES con OxmlElement('w:fldChar') ...

def _heading(doc, text, level=1, color="0B3C5D"):
    h = doc.add_heading(level=level)
    run = h.add_run(text)
    run.font.color.rgb = RGBColor.from_string(color)
    return h

def _kpi_table(doc, kpis): ...
def _data_table(doc, tabla): ...  # con fila de cabecera sombreada
def _risk_block(doc, riesgos): ...  # color por nivel
```

## Función principal
```python
def render_informe(informe: dict, out_path: str) -> str:
    doc = Document()
    # 1) estilos base (fuente por defecto del documento)
    # 2) PORTADA: titulo, clasificacion, evento, ventana_datos, fecha, preparado_por -> page break
    # 3) RESUMEN EJECUTIVO (H1 + párrafo, opcionalmente en recuadro sombreado claro)
    # 4) PANORAMA DE DATOS: narrativa + tabla de KPIs + tablas (cada Tabla -> _data_table)
    # 5) ANÁLISIS DE RIESGOS: _risk_block con color por nivel + evidencia_datos
    # 6) PREDICCIONES: por horizonte
    # 7) CASOS ANÁLOGOS: por país (evento, lección, aplicación a Venezuela, fuente)
    # 8) PROTOCOLOS RECOMENDADOS: por organismo
    # 9) RECOMENDACIONES: tabla priorizada (P1/P2/P3, acción, responsable, plazo)
    # 10) ACCIONES PREVENTIVAS: lista
    # 11) INDICADORES NUEVOS: tabla (indicador, definición, cómo calcularlo)
    # 12) FUENTES: lista numerada con urls como hipervínculos
    # 13) NOTA PII al final, en cursiva y gris
    # pie con numeración en todas las secciones
    doc.save(out_path)
    return out_path
```

Requisitos:
- Si una sección viene vacía en el informe, **omitirla** limpiamente (no dejar títulos huérfanos).
- Tablas con cabecera sombreada (color institucional) y texto de cabecera en blanco/bold.
- Recomendaciones ordenadas por prioridad (P1 → P3) y con celda de prioridad coloreada.
- Riesgos: una pequeña "etiqueta" coloreada según `nivel` (alto/medio/bajo).
- Las urls en `fuentes` deben ser hipervínculos clicables (añadir helper `add_hyperlink`).
- Nombre de archivo: `informe_{tipo}_{YYYYMMDD_HHMM}.docx` dentro de `REPORTS_OUT_DIR`.
- Robusto a campos faltantes (usar `.get` con defaults).

## Criterios de aceptación
- `render_informe(informe_dict, "reports_out/test.docx")` genera un `.docx` que abre sin errores en
  Word/LibreOffice y muestra portada, secciones con datos, tablas con cabecera sombreada,
  numeración de páginas y fuentes como hipervínculos.
- Un informe con secciones vacías no produce títulos sin contenido.
