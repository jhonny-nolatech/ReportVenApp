# Prompt — Plan de Albergues y Atención a Desplazados (Terremoto 24J)

Genera un documento técnico-operativo PUNTUAL que responda: **"¿qué viene para la
gente que se quedó sin casa?"** — el dimensionamiento y la logística de albergues y
campamentos para la población desplazada por el Terremoto 24J.

Audiencia: comité de crisis y dirección estratégica. El documento debe permitir
**tomar decisiones de aprovisionamiento** (cuánto de cada cosa, dónde y para
cuántas personas), pensando "desde cero" (enfoque de campamento de emergencia).

## Reglas
- Usa EXCLUSIVAMENTE la data del bloque CONTEXTO. No inventes cifras.
- Las cantidades de suministros y la estimación de desplazados son DETERMINISTAS:
  toma los valores EXACTOS del bloque "Logística de albergues — proyecciones
  DETERMINISTAS" del CONTEXTO. No los recalcules ni los redondees a tu criterio.
- Cita el estándar y la fuente (Esfera, ACNUR, PMA/OMS) tal como vienen en las
  tablas. Marca explícitamente lo que sea estimación de planificación (energía).
- Español, formato markdown (encabezados ##/###, tablas |...|, listas, **negrita**).
- Todas las fechas/horas en hora de Venezuela (Caracas, UTC-4), según el bloque
  "Corte temporal" del CONTEXTO.
- Cuando un dato no esté en el contexto, escribe "[a completar con inventario /
  instancia responsable]". No rellenes con supuestos.

## Estructura obligatoria

### 1. Resumen ejecutivo
3–5 frases: magnitud del desplazamiento estimado (cota media y cota alta), la
urgencia (réplicas activas, gente a la intemperie) y qué decide este documento.

### 2. Población a reubicar (con intervalo de confianza)
Presenta la población a reubicar como un **INTERVALO** (de cuánto a cuánto), no como
un número único, para que el comité pueda **estar preparado** para la cota alta. Usa
EXACTAMENTE las cifras del contexto:
- **Personas a reubicar ahora** (edificaciones derrumbadas): el rango bajo–alto, con
  la estimación central. Indica que para planificar se dimensiona con la **cota alta**.
- **Próximas a reubicar** (edificaciones en riesgo de colapso): el rango bajo–alto.
- Incluye la **"Comparación con el cálculo anterior"** del contexto, EN FORMA DE
  CÁLCULO: de cuánto tenía el cálculo anterior a cuánto da el intervalo actual, y por
  qué (apartamentos por edificio realistas + edificaciones deduplicadas).
- Incluye la tabla **"Personas a reubicar por estado"** y la lectura operativa:
  **La Guaira = reubicación inmediata** (más derrumbes); **Caracas = evacuación
  preventiva** (concentra las edificaciones en riesgo).
NO incluyas discusión de "sesgo" ni de método por reportes: presenta directamente las
cifras de edificaciones afectadas como la base del cálculo.

### 3. Tipología de campamentos
Propón 3–4 tipos de campamento según tamaño/contexto (p. ej. micro-albergue urbano
~100 pers., albergue medio ~250–500 pers., macro-campamento ~1.000 pers., y
acogida en familias/edificaciones seguras). Para cada uno indica cuándo conviene,
ventajas y requisitos mínimos. Prioriza **abrigar a la gente** cuanto antes.

### 4. Proyección de suministros por tamaño de campamento
Reproduce, como tablas, las proyecciones del contexto para 100 / 250 / 500 / 1.000
personas, agrupadas por categoría: **Agua y saneamiento, Albergue, Alimentación,
Energía, Salud e higiene**. Mantén las columnas Cantidad/Unidad/Estándar/Fuente.

### 5. Necesidades agregadas para la población desplazada
Usa la tabla agregada del contexto (cota media de planificación) para mostrar el
total a aprovisionar: agua (y nº de cisternas), baños químicos, camas/camillas,
tiendas, raciones por el horizonte, plantas eléctricas (kVA), puestos de salud,
kits de higiene, etc. Añade una fila con la cota alta como escenario de máxima
demanda donde aplique.

### 6. Priorización territorial y despliegue
Con los desplazados por estado y la tabla "Zonas prioritarias para instalar
albergues (ranking IPCT)" del contexto, recomienda DÓNDE instalar primero
(estados/parroquias con mayor concentración y mayor IPCT), considerando superficie
del sitio (45 m²/persona) y acceso para cisternas/logística. Incluye la tabla de
zonas prioritarias IPCT y cruza con los desplazados estimados por estado.

### 7. Suministros disponibles y brechas
Tabla de "qué se necesita vs. qué hay disponible vs. brecha". Donde no haya
inventario en el contexto, marca "[a completar con inventario]". Indica qué pedir y
a quién (proveedores/instancias), sin inventar disponibilidades.

### 8. Mensajes preventivos de salud y seguridad (para difundir)
Lista accionable y breve de mensajes a la población desplazada y a quien sigue en
viviendas dañadas. Cubre OBLIGATORIAMENTE:
- **Réplicas**: salir de estructuras dañadas/agrietadas y buscar refugio seguro; no
  reingresar a edificaciones con daño.
- **Agua y vectores**: evitar charcos/aguas estancadas (dengue/zancudos); consumir
  solo agua segura/tratada.
- **Heridas e infecciones**: lavar incluso cortes mínimos; no exponer heridas a agua
  contaminada o barro; buscar atención si hay signos de infección.
- **Higiene en albergues**: lavado de manos, manejo de residuos, prevención de
  enfermedades respiratorias y diarreicas por hacinamiento.
Marca cuáles son preventivos generales y cuáles son de competencia de otras
instancias (salud pública), como apoyo de VenApp.

### 9. Próximos pasos y responsables
3–6 acciones concretas con responsable sugerido y plazo, para pasar de la
estimación al aprovisionamiento real.

No incluyas una sección final de conclusiones que repita el resumen ejecutivo.
