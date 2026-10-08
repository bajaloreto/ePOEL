# Las geometrías de las UGAs se re‑digitalizan desde los mapas de las fichas

Los shapefiles originales del POEL (elaborado por el CIBNOR, coordinado por el Dr. Ricardo Rodríguez‑Estrella) se perdieron. Entre 2018 y 2020 y de nuevo en 2026 se buscaron en el CIBNOR, el Ayuntamiento y otras dependencias, sin éxito. Los polígonos de ePOEL 2019 también se digitalizaron a partir de los mapas en PDF (Hugo Quintero y Brenda E. García, app Mapeo); están incompletos (160 de 184 polígonos) y su método no quedó documentado.

Decidimos re‑digitalizar todas las UGAs a partir de los mapas que acompañan cada ficha en el Apéndice 10 del Boletín. Esos mapas muestran la UGA en rojo sólido y la retícula UTM rotulada en el marco. El método es semiautomático: georreferenciar con las marcas UTM, vectorizar por color, ajustar bordes entre UGAs vecinas y validar a mano en QGIS.

Cada polígono declara su procedencia y su precisión aproximada. Los datos de 2019 sirven solo como comparación; nunca son autoridad.

## Consequences

- Las geometrías son una aproximación cartográfica de la Versión publicada, no linderos legales. El descargo de la plataforma debe decirlo.
- Si algún día aparecen los shapefiles originales, sustituyen a estas geometrías y este ADR queda superado.
