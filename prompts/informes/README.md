# Prompts de generación de informes — Terremoto 24J

Prompts maestros para generar los tres informes ejecutivos a partir de la data
consolidada del evento (panorama VenApp + inventario de infraestructura/hospitales/
servicios + verificación de edificios). Cada uno define audiencia, estructura
obligatoria, reglas editoriales y formato de entrega.

| Archivo | Informe | Audiencia |
|---|---|---|
| [informe_tecnico_operativo.md](informe_tecnico_operativo.md) | Informe Técnico-Operativo de Situación | Comité operativo, Protección Civil, Bomberos, FANB, salud, GIS, logística |
| [brief_presidencial.md](brief_presidencial.md) | Brief Presidencial de Emergencia | Presidencia / decisión de alto nivel |
| [plan_comunicacion_emergencia.md](plan_comunicacion_emergencia.md) | Plan de Comunicación de Emergencia | Vocerías y equipos de comunicación |

## Uso

Se pasan como instrucción a un agente junto con la data consolidada del corte
vigente; el agente devuelve el informe siguiendo la estructura del prompt. Mantener
siempre fecha y hora de corte, y separar hechos confirmados de estimaciones.
