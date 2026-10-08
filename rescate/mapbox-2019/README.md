# Rescate de capas de ePOEL 2019 (Mapbox)

Reconstrucción en GeoJSON (WGS84) de los 18 tilesets vectoriales que usaba ePOEL 2019, alojados en la cuenta de Mapbox `helden9` (Helden Velis). Se rescataron el 2026-10-07 con `herramientas/rescate_mapbox.py`, descargando cada tileset a su zoom máximo y uniendo los fragmentos cortados por los bordes de tile.

- `manifest.json`: tileset de origen, zoom descargado, número de features y fechas de Mapbox de cada capa.
- `estilo-mapbox-helden9.json`: estilo original (colores y simbología de 2019).

**Procedencia y precisión.** Son datos de 2019 derivados de fuentes oficiales de esa época (INEGI, RAN, CONANP, CONAGUA, minería). Las vector tiles simplifican la geometría según su zoom máximo: a z12–z15 la precisión es de unos metros, y a z8–z10 (concesiones mineras y humedales) puede ser de decenas a cientos de metros. Los atributos se conservan tal como estaban en los tiles.

Las capas de UGAs y del PSDU incluidas aquí son solo archivo: las UGAs se re-digitalizan desde el Boletín Oficial (ADR 0002).
