# Sitio estático sin servicios de terceros que requieran token o cuenta

ePOEL 2019 dependía del token, el estilo y los tilesets de la cuenta personal de Mapbox de un exdesarrollador. Si esa cuenta se cerraba, el mapa entero desaparecía, y los datos solo pudieron rescatarse descargando sus tiles.

Para no repetirlo, la plataforma se construye con Astro, genera un sitio 100% estático publicable en GitHub Pages y sirve sus propios datos y mapa base desde el repositorio. El mapa usa MapLibre GL (libre) y un extracto PMTiles de Protomaps de la región de Loreto. Ningún componente indispensable requiere token, cuenta ni servicio de pago.

Los servicios externos opcionales se aceptan solo si la plataforma sigue funcionando cuando fallan. Hoy son la capa satelital EOX Sentinel‑2 (CC BY‑NC‑SA, aceptable porque el proyecto es gratuito y no comercial) y la analítica GoatCounter.

## Considered Options

- Mapbox o MapTiler con token propio: rechazado por el costo, el bloqueo y el mismo riesgo de cuenta.
- OpenFreeMap como mapa base: es una buena opción gratuita, pero sigue siendo un servicio externo; queda como alternativa si el PMTiles crece demasiado para el repo.
- SPA con Vite: rechazada porque Astro genera una página estática por UGA, citable, indexable e imprimible.
