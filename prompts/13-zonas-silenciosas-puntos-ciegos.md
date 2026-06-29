# 13 · Integración — Zonas Silenciosas y Puntos Ciegos (cruce intensidad MMI × reportes)

> **Prompt de integración.** Asume que los prompts 01–12 ya están ejecutados y el sistema funciona
> (módulos `app/data`, `app/knowledge`, `app/tools`, `app/agents`, `app/reporting`, `app/api`, `frontend`).
> Este prompt **añade y modifica** código existente; NO recrees el proyecto.

---

## Por qué (contexto de negocio)

El cliente quiere una **nueva sección/análisis** que mitigue el **sesgo de no-reporte**:

> Los reportes ciudadanos provienen de donde hay señal eléctrica, conectividad y población que reporta.
> **Las zonas más golpeadas suelen ser, precisamente, las que NO reportan.** Si la IA prioriza solo sobre
> los reportes recibidos, desviará la ayuda lejos de las zonas más críticas.

La idea operativa (instrucción directa del responsable): **cruzar** la **intensidad sísmica por
localidad (MMI)** —con su población— contra los **reportes efectivamente recibidos** en VenApp. Donde
hubo **alta intensidad + población importante** pero **pocos o cero reportes**, es muy probable que **no
haya internet/agua/servicios, esté cerca del epicentro y haya personas que necesitan ayuda y no pueden
comunicarse** → esa zona debe **tratarse como "zona de atención" (no "zona sin problema") y priorizarse**,
apoyándose en protocolos y en lo ocurrido en eventos similares.

## Qué vamos a construir

1. Un **dataset de referencia de intensidad MMI por localidad** (fuente: tabla de El País / ShakeMap del
   24J), ya provisto como CSV.
2. Un **motor de cruce** intensidad×población×reportes que produce el **ranking de zonas silenciosas /
   puntos ciegos** con un índice de prioridad.
3. Una **nueva tool** del agente, campos nuevos en el **dossier**, una **sección nueva en el Word** (con
   tabla + "mapa de puntos ciegos") y un **nuevo tipo de informe**, más la actualización de la **base de
   conocimiento** con la metodología y la regla de mitigación.

---

## Paso 0 · Colocar el dataset

Coloca el archivo **`data_seed/intensidad_mmi_24j.csv`** (te lo entrego junto a este prompt) en el repo.
Columnas: `localidad, mmi, habitantes, pais, fuente`. Son ~140 localidades (127 en Venezuela), con la
intensidad de sacudida (Modified Mercalli Intensity) y población por localidad. Crea la carpeta
`data_seed/` si no existe. **Versiona este CSV** (no contiene PII ni secretos).

> Si por algún motivo no tienes el CSV, recréalo con estos valores de intensidad MMI ≥ 6,0 (los más
> críticos) y completa el resto con la tabla de El País: Puerto Cabello 8,0 (209.080) · Catia La Mar 7,9
> (661.897) · Ocumare de la Costa 7,6 (7.000) · Maiquetía 7,1 (87.909) · San Felipe 6,8 (220.786) ·
> Caracas 6,8 (2.245.744) · La Guaira 6,6 (203.520) · Tucacas 6,6 (13.901) · Los Guayos 6,5 (130.345) ·
> Caraballeda 6,4 (48.622) · Guacara 6,4 (200.212) · La Colonia Tovar 6,4 (21.000) · Los Teques 6,3 ·
> Petare 6,3 · San Diego 6,3 · Chichiriviche 6,3 · Valencia 6,2 · Cagua 6,2 · Tocuyito 6,2 · Palo Negro
> 6,2 · Santa Cruz 6,2 · Baruta 6,1 · Santa Rita 6,1 · Maracay 6,0 · El Limón 6,0.

---

## Paso 1 · Cargar y normalizar el dataset MMI — `app/data/intensidad_mmi.py`

- Modelo `LocalidadMMI(BaseModel)`: `localidad, mmi: float, habitantes: int, pais: str, fuente: str`,
  más campos derivados `localidad_norm: str` (minúsculas, sin acentos, sin sufijos `(1)/(2)`),
  `peso_mmi: float`, `indice_exposicion: float`.
- `cargar_mmi() -> list[LocalidadMMI]`: lee el CSV, filtra `pais == "VE"` por defecto (parámetro
  `solo_venezuela=True`), normaliza nombres y calcula derivados. Cachéalo en memoria.
- **`peso_mmi(mmi)`** (proxy heurístico de fracción de daño potencial — **NO** es estimación de víctimas;
  documenta esto):
  ```
  mmi < 4.5      -> 0.05
  4.5 <= mmi <5.5-> 0.15
  5.5 <= mmi <6.0-> 0.35
  6.0 <= mmi <6.5-> 0.60
  6.5 <= mmi <7.0-> 0.80
  7.0 <= mmi <8.0-> 1.00
  mmi >= 8.0     -> 1.20
  ```
- `indice_exposicion = habitantes * peso_mmi(mmi)` (≈ personas potencialmente expuestas a daño relevante).
- Constantes de epicentros (Yaracuy) para un realce opcional por cercanía:
  `EPICENTROS = [("San Felipe", 10.34, -68.74), ("Yumare", 10.61, -68.70)]` (coords aproximadas).

## Paso 2 · Emparejar localidades MMI ↔ geografía VenApp — `app/data/match_geo.py`

El reto: la `localidad` de El País debe casar con `province.name` / `municipality.name` /
`parroquia.name` de VenApp. Resuélvelo así (de mayor a menor confianza):

1. **Mapa manual curado** `MAPA_LOCALIDAD_VENAPP` para las localidades de **alta intensidad** (las que más
   importan), p. ej.:
   - "Maiquetía", "Catia La Mar", "Caraballeda", "La Guaira", "Ocumare de la Costa" → estado **La Guaira**
     (Vargas) con su parroquia/municipio correspondiente.
   - "Caracas" → Distrito Capital (+ parroquias de Libertador); "Petare" → Miranda/Sucre; "Baruta" →
     Miranda/Baruta; "Los Teques" → Miranda/Guaicaipuro.
   - "Puerto Cabello", "Tucacas", "Chichiriviche" → **Carabobo/Falcón** según corresponda; "Valencia",
     "Guacara", "Los Guayos", "San Diego", "Tocuyito" → **Carabobo**.
   - "Maracay", "Cagua", "Palo Negro", "Turmero", "El Limón", "La Victoria" → **Aragua**;
     "San Felipe", "Yaritagua" → **Yaracuy**.
   Completa el mapa al menos para todas las MMI ≥ 6,0.
2. **Match difuso** con `rapidfuzz` contra los valores reales de `parroquia.name`, luego
   `municipality.name`, luego `province.name` (usa `consultar_db(agrupar_por=...)` para obtener los
   catálogos reales de VenApp). Umbral configurable (p. ej. score ≥ 88).
3. Cada match guarda `granularidad` (`parroquia`/`municipio`/`estado`) y `confianza_match`
   (`alta`/`media`/`baja`). Si no hay match, `granularidad="sin_match"` y se reporta aparte.

> Diseña el matcher para que sea **auditable**: que el informe pueda decir con qué confianza casó cada zona.

## Paso 3 · Motor de cruce (puntos ciegos) — `app/data/zonas_silenciosas.py`

`analizar_puntos_ciegos(umbral_mmi=6.0, umbral_habitantes=20000, umbral_cobertura=0.25) -> AnalisisPuntosCiegos`:

1. Carga `cargar_mmi()` (solo VE) y empareja con geografía (paso 2).
2. Para cada localidad emparejada, obtén **reportes observados** de VenApp en su zona, usando
   `consultar_db` a la granularidad del match (parroquia → municipio → estado). Suma los conteos.
3. Calcula la **tasa global** entre localidades **con** reportes:
   `tasa_global = sum(reportes_obs) / sum(indice_exposicion de las que reportan)`.
4. Por localidad:
   - `reportes_esperados = indice_exposicion * tasa_global`
   - `deficit = max(0, reportes_esperados - reportes_obs)`
   - `cobertura = reportes_obs / max(reportes_esperados, 1)`   # 0 = silenciosa, ≥1 = como se espera
   - `indice_punto_ciego = deficit_normalizado(0-100) * peso_mmi`  # alto = grave y muy expuesta
   - (Opcional) realce por **cercanía a epicentro** si hay coords del match.
5. **Bandera `CRÍTICA`** cuando `mmi >= umbral_mmi` **y** `habitantes >= umbral_habitantes` **y**
   `cobertura < umbral_cobertura`. (Caso del ejemplo del cliente: Caraballeda 6,4 / 48.622 hab con ~0
   reportes → CRÍTICA.)
6. Devuelve un modelo pydantic `AnalisisPuntosCiegos`:
   ```python
   class ZonaCiega(BaseModel):
       localidad: str; estado: str|None; municipio: str|None; parroquia: str|None
       mmi: float; habitantes: int; indice_exposicion: float
       reportes_observados: int; reportes_esperados: float
       cobertura: float; indice_punto_ciego: float
       critica: bool; confianza_match: str; granularidad: str
       interpretacion: str   # frase lista para el informe
   class AnalisisPuntosCiegos(BaseModel):
       generado_en: datetime; parametros: dict
       zonas_criticas: list[ZonaCiega]      # ordenadas por indice_punto_ciego desc
       zonas_silenciosas: list[ZonaCiega]   # cobertura baja pero no crítica
       zonas_visibles: list[ZonaCiega]      # buena cobertura (control)
       sin_match: list[str]                 # localidades MMI sin geografía resuelta
       resumen: str
   ```
7. **Reglas de interpretación (obligatorias en cada `interpretacion`/resumen):** baja/nula recepción de
   reportes **NO** significa ausencia de daño; se trata como **zona de atención**, no "zona sin problema".
   Causas probables: caída de conectividad/energía, daño a infraestructura, cercanía al epicentro. Por eso
   estas zonas se **priorizan** para verificación en terreno.

> **Solo lectura** sobre VenApp, siempre vía `safe_match`/`consultar_db` con el filtro de evento+fecha.
> El cruce no escribe nada en producción.

## Paso 4 · Nueva tool del agente — modificar `app/tools/registry.py`

Añade `consultar_zonas_silenciosas`:
- Descripción: "Cruza la intensidad sísmica MMI por localidad (con población) contra los reportes
  recibidos para detectar **puntos ciegos**: zonas de alta intensidad y mucha población con pocos o cero
  reportes, que probablemente tienen comunicaciones caídas y necesitan ayuda urgente. Devuelve un ranking
  priorizado. Recordar: poca señal = zona de atención, NO zona sin problema."
- `input_schema`: `{ "umbral_mmi": {type:number, default:6.0}, "umbral_habitantes": {type:integer, default:20000}, "umbral_cobertura": {type:number, default:0.25}, "top": {type:integer, default:20} }`
- Ejecutor: llama `analizar_puntos_ciegos(...)`, serializa (sin PII; es agregado por localidad).
- Asigna esta tool al **Analista de datos** y al **Estratega** (prompt 07).

## Paso 5 · Base de conocimiento — modificar `app/knowledge/`

Añade entradas (`EntradaConocimiento`):
- **Metodología del sesgo de no-reporte** (categoría `protocolo`, confianza alta): qué es, por qué los
  datos ciudadanos subrepresentan a las zonas más golpeadas, y la **mitigación obligatoria**: publicar
  junto a cada análisis el **mapa de puntos ciegos**, tratado como *zona de atención*. Cita el principio
  de la Imagen/sección "El riesgo que obliga al ajuste: el sesgo de no-reporte".
- **Fuente de intensidad MMI 24J** (categoría `contexto_evento`): tabla de intensidad por localidad
  (El País / ShakeMap-USGS), con las localidades de mayor MMI; marca como referencia externa citable.
  Localidades de mayor sacudida: Puerto Cabello 8,0; Catia La Mar 7,9; Ocumare de la Costa 7,6;
  Maiquetía 7,1; San Felipe/Caracas 6,8; La Guaira/Tucacas 6,6 — todas próximas al eje epicentral
  Yaracuy–costa central.
- **Indicador "índice de punto ciego"** (categoría `indicador`): definición, cómo se calcula (paso 3),
  por qué importa, umbral de alerta.
- Vincula con casos históricos ya existentes (México 2017 / Turquía 2023): zonas sin reportes por
  colapso de comunicaciones resultaron ser de las más afectadas (lección accionable).

## Paso 6 · Dossier y agentes — modificar `app/agents/`

- En `app/agents/dossier.py`, añade al modelo `Dossier`:
  ```python
  puntos_ciegos: list[dict] = []        # zonas críticas/silenciosas serializadas
  resumen_puntos_ciegos: str = ""
  ```
- En `app/agents/prompts.py`:
  - **Analista:** que SIEMPRE invoque `consultar_zonas_silenciosas` y reporte el ranking con cifras
    exactas (intensidad, población, reportes observados vs esperados, cobertura).
  - **Estratega:** que convierta el ranking en **acciones priorizadas** (verificación en terreno de las
    zonas CRÍTICAS primero), justificando con protocolos (ventana 72 h, verificación cívico-militar) y
    casos similares; y que redacte el mensaje rector del cliente: *"de acuerdo al cruce de información,
    en tal lugar la intensidad fue de X, hasta ahora no se han recibido reportes; según los protocolos y
    casos comparables, es muy probable una tragedia mayor: priorizar."* Debe separar hecho/inferencia y
    no afirmar daño como certeza, pero **sí** elevar la prioridad.
  - **Redactor:** que incluya la sección de puntos ciegos en el contenido estructurado.

## Paso 7 · Word — nueva sección — modificar `app/reporting/`

En `word_engine.py`, añade la sección **"Zonas Silenciosas y Puntos Ciegos (cruce intensidad × reportes)"**,
ubicada justo después de "Panorama situacional":
- Párrafo introductorio con la **advertencia metodológica** (poca señal = zona de atención).
- **Tabla de zonas críticas** (ordenadas por índice de punto ciego): Localidad · Estado · MMI ·
  Habitantes · Reportes recibidos · Reportes esperados · Cobertura · Prioridad. Resalta en color las filas
  `crítica`.
- **"Mapa de puntos ciegos"**: en `charts.py` añade `mapa_puntos_ciegos(zonas)` → un **gráfico de
  burbujas**: eje X = MMI, eje Y = habitantes (log), tamaño de burbuja = déficit de reportes, color =
  crítica (rojo) / silenciosa (naranja) / visible (verde); etiqueta las críticas. (Si en el futuro hay
  coords, se puede hacer un mapa geográfico real; por ahora este gráfico cumple el rol.)
- Lista de **recomendaciones de verificación** para las zonas críticas y nota de `sin_match` (zonas MMI
  que no se pudieron geolocalizar → revisar manualmente).

## Paso 8 · Catálogo e informes — modificar `app/reporting/catalogo.py` y `app/agents/briefs.py`

- Nuevo tipo de informe `puntos_ciegos` — *"Reporte de Zonas Silenciosas / Puntos Ciegos"*: foco total en
  el cruce intensidad×reportes y la priorización de zonas sin señal. Parámetros: `umbral_mmi`,
  `umbral_habitantes`, `umbral_cobertura`.
- **Inyecta la sección de puntos ciegos** también en `situacional` y `ejecutivo` (el cliente la quiere
  "dentro del documento de hoy"). En `predictivo`, úsala como entrada para predicción de zonas en riesgo.
- Brief de `puntos_ciegos`: prioriza Analista + Estratega; exige tabla, mapa de burbujas y acciones.

## Paso 9 · API y Frontend — verificar/extender

- API: como el catálogo se sirve desde `/catalogo`, el nuevo tipo aparece solo. Verifica que
  `generar_informe("puntos_ciegos", {...})` funcione end-to-end.
- Frontend: el nuevo tipo aparece en el selector automáticamente. Añade los tres deslizadores/umbral
  (`umbral_mmi`, `umbral_habitantes`, `umbral_cobertura`) como parámetros opcionales cuando el tipo sea
  `puntos_ciegos`. (Opcional, si ya hay mapa: pintar las zonas críticas.)

## Paso 10 · Pruebas — extender `tests/`

- `test_match_geo`: las MMI ≥ 6,0 casan con un estado válido y confianza no "baja".
- `test_puntos_ciegos`: `analizar_puntos_ciegos()` corre, devuelve `zonas_criticas` ordenadas por índice
  desc, y toda `cobertura ∈ [0, ∞)` con `cobertura<umbral` en las críticas.
- `test_e2e` (extender): `generar_informe("puntos_ciegos", {})` produce un `.docx` con la tabla y el
  gráfico de burbujas, sin PII.

## Reglas (recordatorio)

- **Solo lectura** sobre VenApp; cruce siempre con filtro evento+fecha; sin PII en el análisis (es
  agregado por localidad).
- **Nunca** interpretar "sin reportes" como "sin problema": es **zona de atención** y se prioriza.
- Cifras de intensidad/población citan a la fuente (El País / ShakeMap); cifras de reportes salen de VenApp.
- El `peso_mmi` y los umbrales son **heurísticas configurables**, no estimaciones de víctimas: decláralo.

## Criterios de aceptación

- [ ] `data_seed/intensidad_mmi_24j.csv` está en el repo y `cargar_mmi()` lo carga (≥120 localidades VE).
- [ ] `ejecutar_tool("consultar_zonas_silenciosas", {})` devuelve un ranking con zonas críticas.
- [ ] Una localidad de MMI alto y muchos habitantes con ~0 reportes aparece como **CRÍTICA** en el top.
- [ ] `generar_informe("puntos_ciegos", {})` y `generar_informe("ejecutivo", {})` incluyen la sección
      "Zonas Silenciosas y Puntos Ciegos" con tabla + mapa de burbujas, y la advertencia metodológica.
- [ ] Los informes nombran explícitamente las zonas a priorizar con su intensidad y déficit de reportes.
