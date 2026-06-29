# Vulnerabilidad per cápita — Terremoto 24J

> Corte de datos: **26/06/2026 15:43** (hora Venezuela) · Generado: 26/06/2026 15:43.
> Universo: reportes de categoría **Terremoto 24J** (datos de campo, autodeclarados).

## Metodología

Para cada entidad (estado / municipio / parroquia) se calcula un **índice de afectación
per cápita** y se normaliza a **0–100 %**, donde 100 % = la entidad más afectada de ese nivel.

```
ponderado = reportes + 2·colapsadas + 4·desaparecidos + 1·críticos
índice    = ponderado / (población + 20,000) × 10.000
vulnerabilidad % = 100 × índice / índice_máximo_del_nivel
```

- **Ponderación por gravedad**: un desaparecido pesa 4×, una vivienda colapsada 2× y un
  caso crítico (vidas) suma además; así el índice mezcla **volumen** y **severidad**.
- **Suavizado del denominador** (+20,000 hab): evita que una parroquia
  diminuta (p. ej. Catedral, ~4.500 hab, casco institucional) distorsione el ranking con
  un denominador minúsculo. Es negligible para entidades grandes.
- **Rep/10k hab** = reportes por cada 10.000 habitantes (densidad bruta, sin suavizado),
  como referencia intuitiva.
- **MMI** = intensidad Mercalli del sismo en la zona (investigada/estimada).

## 1) Estados (24)

| # | Estado | Población | MMI | Reportes | Desap. | Colaps. | Críticos | Rep/10k | **Vulnerab.** |
| --: | --- | --: | :--: | --: | --: | --: | --: | --: | --: |
| 1 | La Guaira | 380,000 | VI | 771 | 456 | 248 | 514 | 20.3 | **100.0%** |
| 2 | Caracas | 2,080,000 | VI | 4,164 | 45 | 1758 | 69 | 20.0 | **41.9%** |
| 3 | Miranda | 3,200,000 | VI | 1,546 | 38 | 552 | 46 | 4.8 | **9.8%** |
| 4 | Yaracuy | 690,000 | VIII | 313 | 4 | 75 | 7 | 4.5 | **7.6%** |
| 5 | Aragua | 1,850,000 | VII | 709 | 11 | 189 | 14 | 3.8 | **6.8%** |
| 6 | Carabobo | 2,480,000 | VII | 703 | 10 | 186 | 16 | 2.8 | **5.0%** |
| 7 | Guárico | 900,000 | V | 121 | 3 | 49 | 3 | 1.3 | **2.8%** |
| 8 | Lara | 2,050,000 | VII | 261 | 6 | 65 | 7 | 1.3 | **2.3%** |
| 9 | Cojedes | 380,000 | VII | 48 | 2 | 9 | 2 | 1.3 | **2.1%** |
| 10 | Falcón | 1,080,000 | VI | 76 | 5 | 23 | 5 | 0.7 | **1.5%** |
| 11 | Sucre | 1,050,000 | IV | 76 | 3 | 14 | 3 | 0.7 | **1.2%** |
| 12 | Anzoátegui | 1,850,000 | IV | 116 | 1 | 34 | 1 | 0.6 | **1.1%** |
| 13 | Delta Amacuro | 200,000 | II | 11 | 0 | 4 | 0 | 0.6 | **1.0%** |
| 14 | Apure | 560,000 | IV | 30 | 2 | 6 | 2 | 0.5 | **1.0%** |
| 15 | Mérida | 1,010,000 | IV | 20 | 11 | 4 | 11 | 0.2 | **0.9%** |
| 16 | Amazonas | 200,000 | II | 11 | 0 | 3 | 0 | 0.6 | **0.9%** |
| 17 | Nueva Esparta | 600,000 | III | 13 | 4 | 4 | 5 | 0.2 | **0.8%** |
| 18 | Bolívar | 1,850,000 | III | 52 | 8 | 12 | 9 | 0.3 | **0.7%** |
| 19 | Trujillo | 820,000 | V | 31 | 0 | 12 | 0 | 0.4 | **0.7%** |
| 20 | Barinas | 950,000 | V | 28 | 2 | 6 | 2 | 0.3 | **0.6%** |
| 21 | Portuguesa | 1,080,000 | VI | 29 | 0 | 10 | 0 | 0.3 | **0.5%** |
| 22 | Monagas | 1,050,000 | III | 27 | 2 | 8 | 2 | 0.3 | **0.5%** |
| 23 | Táchira | 1,320,000 | IV | 10 | 4 | 3 | 4 | 0.1 | **0.3%** |
| 24 | Zulia | 4,200,000 | V | 38 | 5 | 12 | 5 | 0.1 | **0.2%** |

## 2) Municipios (30)

| # | Estado | Municipio | Población | MMI | Reportes | Desap. | Colaps. | Críticos | Rep/10k | **Vulnerab.** |
| --: | --- | --- | --: | :--: | --: | --: | --: | --: | --: | --: |
| 1 | La Guaira | Vargas | 360,000 | VI | 771 | 456 | 248 | 514 | 21.4 | **100.0%** |
| 2 | Caracas | Libertador | 2,246,000 | VI | 4,149 | 31 | 1753 | 54 | 18.5 | **36.4%** |
| 3 | Miranda | Independencia | 40,000 | — | 72 | 3 | 29 | 3 | 18.0 | **25.5%** |
| 4 | Miranda | Plaza | 270,000 | — | 264 | 4 | 124 | 6 | 9.8 | **19.4%** |
| 5 | Miranda | Brion | 50,000 | — | 64 | 4 | 21 | 5 | 12.8 | **19.1%** |
| 6 | Miranda | Simon Bolivar | 40,000 | — | 72 | 1 | 14 | 1 | 18.0 | **18.4%** |
| 7 | Miranda | Cristobal Rojas | 110,000 | — | 87 | 3 | 29 | 4 | 7.9 | **13.1%** |
| 8 | Miranda | Tomas Lander | 70,000 | — | 74 | 0 | 16 | 0 | 10.6 | **12.4%** |
| 9 | Miranda | Paz Castillo | 110,000 | — | 78 | 2 | 29 | 2 | 7.1 | **11.8%** |
| 10 | Miranda | Chacao | 70,000 | VI | 44 | 1 | 24 | 2 | 6.3 | **11.5%** |
| 11 | Carabobo | Naguanagua | 160,000 | — | 116 | 0 | 31 | 0 | 7.2 | **10.4%** |
| 12 | Aragua | Girardot | 460,000 | VI | 308 | 2 | 72 | 3 | 6.7 | **10.2%** |
| 13 | Miranda | Guaicaipuro | 230,000 | V | 138 | 4 | 41 | 4 | 6.0 | **10.1%** |
| 14 | Miranda | Zamora | 250,000 | — | 145 | 2 | 50 | 4 | 5.8 | **10.0%** |
| 15 | Yaracuy | Independencia | 80,000 | VII | 58 | 0 | 18 | 0 | 7.2 | **9.9%** |
| 16 | Aragua | Francisco Linares Alcantara | 120,000 | VI | 70 | 2 | 22 | 3 | 5.8 | **9.4%** |
| 17 | Miranda | Urdaneta | 90,000 | — | 54 | 1 | 14 | 1 | 6.0 | **8.3%** |
| 18 | Aragua | Mario Briceno Iragorry | 110,000 | VI | 61 | 1 | 17 | 1 | 5.5 | **8.1%** |
| 19 | Miranda | Sucre | 600,000 | VI | 254 | 4 | 90 | 5 | 4.2 | **7.7%** |
| 20 | Carabobo | Diego Ibarra | 110,000 | — | 62 | 0 | 16 | 0 | 5.6 | **7.6%** |
| 21 | Carabobo | Guacara | 160,000 | — | 77 | 1 | 16 | 3 | 4.8 | **6.8%** |
| 22 | Yaracuy | San Felipe | 221,000 | VIII | 88 | 1 | 24 | 1 | 4.0 | **6.2%** |
| 23 | Yaracuy | Bruzual | 120,000 | VII | 57 | 0 | 6 | 1 | 4.8 | **5.3%** |
| 24 | Aragua | Jose Felix Ribas | 150,000 | VI | 51 | 0 | 15 | 0 | 3.4 | **5.0%** |
| 25 | Miranda | Baruta | 250,000 | V | 65 | 2 | 21 | 2 | 2.6 | **4.6%** |
| 26 | Carabobo | Puerto Cabello | 200,000 | VII | 51 | 0 | 16 | 0 | 2.6 | **4.0%** |
| 27 | Lara | Iribarren | 1,059,000 | VII | 204 | 3 | 52 | 4 | 1.9 | **3.2%** |
| 28 | Carabobo | Valencia | 1,484,000 | VI | 244 | 6 | 56 | 7 | 1.6 | **2.7%** |
| 29 | Sucre | Sucre | 420,000 | — | 69 | 2 | 13 | 2 | 1.6 | **2.5%** |
| 30 | Anzoátegui | Simon Bolivar | 350,000 | — | 50 | 0 | 14 | 0 | 1.4 | **2.2%** |

## 3) Parroquias (52)

| # | Estado | Municipio | Parroquia | Población | MMI | Reportes | Desap. | Colaps. | Críticos | Rep/10k | **Vulnerab.** |
| --: | --- | --- | --- | --: | :--: | --: | --: | --: | --: | --: | --: |
| 1 | La Guaira | Vargas | Caraballeda | 40,000 | VI | 200 | 91 | 93 | 115 | 50.0 | **100.0%** |
| 2 | Caracas | Libertador | Altagracia | 45,000 | VI | 253 | 3 | 125 | 6 | 56.2 | **55.6%** |
| 3 | Caracas | Libertador | Santa Teresa | 18,000 | VI | 126 | 0 | 50 | 0 | 70.0 | **41.3%** |
| 4 | Caracas | Libertador | La Pastora | 75,000 | VI | 282 | 0 | 130 | 3 | 37.6 | **39.8%** |
| 5 | La Guaira | Vargas | La Guaira | 22,000 | VI | 47 | 33 | 13 | 33 | 21.4 | **39.3%** |
| 6 | Caracas | Libertador | San Juan | 105,000 | VI | 344 | 1 | 171 | 4 | 32.8 | **38.5%** |
| 7 | Caracas | Libertador | La Candelaria | 55,000 | VI | 218 | 0 | 91 | 0 | 39.6 | **37.0%** |
| 8 | Caracas | Libertador | Catedral | 4,500 | VI | 64 | 1 | 25 | 1 | 142.2 | **33.7%** |
| 9 | Caracas | Libertador | San Jose | 40,000 | VI | 146 | 2 | 62 | 2 | 36.5 | **32.4%** |
| 10 | Caracas | Libertador | San Bernardino | 28,000 | VI | 102 | 0 | 58 | 0 | 36.4 | **31.5%** |
| 11 | La Guaira | Vargas | Macuto | 17,000 | VI | 41 | 15 | 23 | 17 | 24.1 | **30.7%** |
| 12 | La Guaira | Vargas | Naiguata | 18,000 | VI | 31 | 25 | 4 | 25 | 17.2 | **29.9%** |
| 13 | La Guaira | Vargas | Catia La Mar | 125,000 | VI | 138 | 69 | 54 | 84 | 11.0 | **29.0%** |
| 14 | Caracas | Libertador | El Junquito | 45,000 | VI | 119 | 4 | 54 | 7 | 26.4 | **26.7%** |
| 15 | Caracas | Libertador | El Recreo | 110,000 | VI | 282 | 3 | 96 | 7 | 25.6 | **26.3%** |
| 16 | Caracas | Libertador | Sucre | 396,000 | VI | 743 | 2 | 320 | 3 | 18.8 | **23.2%** |
| 17 | Caracas | Libertador | San Agustin | 40,000 | VI | 96 | 0 | 52 | 1 | 24.0 | **23.2%** |
| 18 | Caracas | Libertador | Santa Rosalia | 110,000 | VI | 198 | 5 | 86 | 5 | 18.0 | **21.1%** |
| 19 | Caracas | Libertador | Coche | 55,000 | VI | 127 | 0 | 45 | 2 | 23.1 | **20.3%** |
| 20 | Caracas | Libertador | San Pedro | 50,000 | VI | 108 | 0 | 47 | 0 | 21.6 | **20.0%** |
| 21 | Caracas | Libertador | Antimano | 145,000 | VI | 223 | 1 | 96 | 3 | 15.4 | **17.7%** |
| 22 | La Guaira | Vargas | Urimare | 45,000 | VI | 50 | 9 | 32 | 13 | 11.1 | **17.4%** |
| 23 | Caracas | Libertador | El Paraiso | 95,000 | VI | 159 | 2 | 56 | 2 | 16.7 | **16.9%** |
| 24 | Caracas | Libertador | Macarao | 48,000 | VI | 90 | 0 | 35 | 0 | 18.8 | **16.3%** |
| 25 | Miranda | Plaza | Guarenas | 250,000 | V | 264 | 4 | 124 | 6 | 10.6 | **13.7%** |
| 26 | Caracas | Libertador | 23 De Enero | 80,000 | VI | 107 | 1 | 38 | 1 | 13.4 | **13.0%** |
| 27 | Yaracuy | Independencia | Independencia | 35,000 | VIII | 58 | 0 | 18 | 0 | 16.6 | **11.9%** |
| 28 | Miranda | Brion | Higuerote | 40,000 | IV | 53 | 3 | 16 | 4 | 13.2 | **11.7%** |
| 29 | Caracas | Libertador | Caricuao | 138,000 | VI | 119 | 2 | 42 | 2 | 8.6 | **9.4%** |
| 30 | Miranda | Simon Bolivar | San Francisco De Yare | 28,000 | V | 47 | 0 | 9 | 0 | 16.8 | **9.4%** |
| 31 | Caracas | Libertador | El Valle | 140,000 | VI | 119 | 3 | 39 | 4 | 8.5 | **9.2%** |
| 32 | Caracas | Libertador | La Vega | 140,000 | VI | 124 | 1 | 35 | 1 | 8.9 | **8.6%** |
| 33 | Miranda | Zamora | Guatire | 190,000 | V | 143 | 2 | 49 | 4 | 7.5 | **8.4%** |
| 34 | La Guaira | Vargas | Maiquetia | 38,000 | VI | 21 | 7 | 5 | 8 | 5.5 | **8.0%** |
| 35 | Miranda | Paz Castillo | Santa Lucia | 115,000 | V | 78 | 2 | 29 | 2 | 6.8 | **7.5%** |
| 36 | Miranda | Guaicaipuro | Los Teques | 170,000 | V | 109 | 1 | 35 | 1 | 6.4 | **6.7%** |
| 37 | Carabobo | Naguanagua | Urbana Naguanagua | 165,000 | VII | 116 | 0 | 31 | 0 | 7.0 | **6.7%** |
| 38 | Miranda | Tomas Lander | Ocumare Del Tuy | 80,000 | V | 67 | 0 | 13 | 0 | 8.4 | **6.5%** |
| 39 | Aragua | Girardot | Urbana Madre Maria De San Jose | 85,000 | VII | 62 | 1 | 11 | 1 | 7.3 | **5.9%** |
| 40 | La Guaira | Vargas | El Junko | 4,000 | VI | 6 | 1 | 4 | 2 | 15.0 | **5.8%** |
| 41 | Miranda | Cristobal Rojas | Charallave | 135,000 | V | 71 | 2 | 21 | 3 | 5.3 | **5.5%** |
| 42 | La Guaira | Vargas | Carlos Soublette | 44,000 | VI | 17 | 4 | 7 | 4 | 3.9 | **5.5%** |
| 43 | Yaracuy | San Felipe | Capital San Felipe | 115,000 | VIII | 59 | 1 | 19 | 1 | 5.1 | **5.2%** |
| 44 | Miranda | Sucre | Leoncio Martinez | 105,000 | VI | 48 | 0 | 22 | 0 | 4.6 | **5.1%** |
| 45 | Carabobo | Valencia | Urbana Rafael Urdaneta | 115,000 | VII | 54 | 3 | 13 | 4 | 4.7 | **4.9%** |
| 46 | Aragua | Girardot | Urbana Andres Eloy Blanco | 95,000 | VII | 45 | 1 | 12 | 1 | 4.7 | **4.5%** |
| 47 | Carabobo | Valencia | Urbana San Jose | 130,000 | VII | 58 | 2 | 11 | 2 | 4.5 | **4.2%** |
| 48 | Miranda | Sucre | Petare | 440,000 | VI | 148 | 2 | 46 | 3 | 3.4 | **3.8%** |
| 49 | Aragua | Girardot | Urbana Las Delicias | 140,000 | VII | 49 | 0 | 10 | 0 | 3.5 | **3.0%** |
| 50 | La Guaira | Vargas | Carayaca | 42,000 | VI | 7 | 1 | 5 | 1 | 1.7 | **2.5%** |
| 51 | Carabobo | Valencia | Urbana Miguel Pena | 430,000 | VII | 74 | 0 | 17 | 0 | 1.7 | **1.7%** |
| 52 | Lara | Iribarren | Juan De Villegas | 330,000 | VII | 48 | 1 | 11 | 1 | 1.5 | **1.5%** |

## Lecturas clave

- **Estado más afectado per cápita**: La Guaira (100 %).
- **Municipio más afectado per cápita**: Vargas · La Guaira (100 %).
- **Parroquia más afectada per cápita**: Caraballeda · Vargas · La Guaira (100 %; 91 desaparecidos y 93 colapsos sobre ~40,000 hab).
- En **números absolutos** mandan Caracas/Libertador por su población; **normalizado por
  habitantes**, La Guaira (Vargas/Caraballeda) domina la afectación.

## Advertencias de datos

- La **población es estimada** (censo INE 2011 + proyección, investigada y verificada con IA);
  úsala como orden de magnitud, no como cifra oficial exacta.
- Los reportes son **autodeclarados** (verdad de campo parcial), no un censo de daños.
- Algunos reportes están **mal geolocalizados**; se aplica una **lista blanca** de entidades para
  filtrar etiquetas erróneas, por lo que entidades con muy pocos casos pueden no aparecer.

*Generado por `tools/gen_md_vulnerabilidad.py` · Sala Situacional VenApp.*
