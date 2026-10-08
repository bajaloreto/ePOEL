# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Astro (sitio 100% estático) + MapLibre GL + mapa base PMTiles de Protomaps alojado en el repositorio; despliegue en GitHub Pages (ADR 0003). Ningún componente indispensable puede depender de un servicio con token o cuenta. El sitio jQuery/Bootstrap/Mapbox de 2019 es legado (tag `v1-2019`) y se trata solo como evidencia, no como sistema visual a conservar.

## Users

- **Principal — ciudadanos e inversionistas** (incluidos residentes y compradores extranjeros) que tienen un terreno o un proyecto en el Municipio de Loreto y necesitan saber qué permite el ordenamiento ecológico en ese punto antes de comprar, construir o invertir.
- **Secundario — funcionarios municipales** (Ecología, Desarrollo Urbano) que dictaminan factibilidades y necesitan precisión, búsqueda por coordenadas y fichas que se puedan imprimir o anexar a expedientes.
- Organizaciones, investigadores y docentes se atienden con datos descargables, no con herramientas de análisis dedicadas.

## Product Purpose

Responder "¿qué aplica en este punto?": a partir de un clic, unas coordenadas (geográficas o UTM 12N), una localidad o un ID de UGA, mostrar la Unidad de Gestión Ambiental (UGA), su política ambiental, actividad, lineamientos, estrategias y criterios de regulación ecológica con su texto completo, cada dato citado contra la Versión publicada. El éxito es que una persona no especialista entienda qué puede y qué no puede hacer en su terreno, y que un funcionario pueda verificar cada dato en el Boletín.

## Positioning

Es la única versión digital pública y consultable del POEL de Loreto: los archivos digitales originales se perdieron, y esta plataforma reconstruye fichas y polígonos directamente del Boletín Oficial No. 12 (12‑mar‑2014), con procedencia, precisión e incidencias declaradas por cada dato. Está concebida como plataforma territorial que irá sumando instrumentos (PSDUL 2024, Programa de Manejo del PNBL, POEM del Golfo de California) para responder qué dice cada uno en el mismo punto.

## Operating Context

- Se consulta mucho desde el celular, a veces en el terreno o en comunidades rurales con señal débil.
- En oficina, las fichas se imprimen o anexan a expedientes y dictámenes; la impresión debe ser limpia y citable.
- La autoridad jurídica es siempre el Boletín Oficial; la plataforma enlaza a él como única referencia en PDF.
- Mantenimiento por una sola persona técnica (Hugo Quintero) con una herramienta local de administración y QGIS.

## Capabilities and Constraints

- Fase 1: POEL completo (122 UGAs), consulta por punto, fichas web por UGA (`/poel/uga/<id>/`), capas de soporte con procedencia, descargas GeoJSON, reporte de incidencias (correo y GitHub Issues), analítica sin cookies (GoatCounter).
- Español es la fuente de verdad; inglés como traducción en fase 2. PWA sin conexión en fase 2.
- Herramienta informativa, no oficial: descargo visible conforme a Libre Uso MX (no sugerir aval oficial).
- Terminología canónica en `CONTEXT.md` (UGA, Polígono, Política ambiental, Actividad, Criterio de regulación ecológica, Procedencia, Incidencia).
- Abierto: nombre nuevo de la plataforma y dominio propio (fase 2); visto bueno escrito para usar el escudo del Municipio y el logo de Eco‑Alianza.

## Brand Commitments

- Nombre actual: **ePOEL**.
- Voz: **cercana y precisa** — explica en lenguaje llano para el ciudadano, pero cita la norma con exactitud jurídica; nunca simplifica a costa de cambiar el sentido normativo.
- Créditos obligatorios: Hugo Quintero, Helden Velis, Brenda E. García; Eco‑Alianza de Loreto; Resources Legacy Fund (2018); HuQuMa Studio como donador; CIBNOR como autor del POEL.
- Logos del Municipio de Loreto y de Eco‑Alianza solo con visto bueno escrito (pendiente); logo de HuQuMa Studio como donador.

## Evidence on Hand

- `datos/poel/ugas/*.json`: 122 fichas estructuradas del Apéndice 10.
- `datos/poel/lineamientos.json` (19), `estrategias.json` (18), `criterios.json` (192 en 16 grupos).
- `datos/poel/incidencias.json`: discrepancias registradas.
- `datos/poel/digitalizacion/`: polígonos piloto (UGAs 12, 1a, 45); el resto pendiente.
- `rescate/mapbox-2019/`: capas de soporte de 2019.
- No hay testimonios, métricas de uso ni avales institucionales: no inventarlos.

## Product Principles

1. El Boletín manda: todo dato normativo se cita y se puede verificar; las discrepancias se muestran, no se esconden.
2. Primero la respuesta: lo que aplica en el punto consultado va antes que cualquier exploración o capa.
3. Honestidad sobre la precisión: cada polígono declara cómo se obtuvo y cuánto puede desviarse.
4. Funciona en el terreno: rápido en celular con mala señal, sin depender de servicios de terceros.
5. Sirve igual en papel: una ficha impresa debe ser completa y citable.

## Accessibility & Inclusion

- Rendimiento y peso mínimos para celulares con conexión débil.
- Impresión limpia de fichas para expedientes.
- Lenguaje llano en la interfaz; terminología técnica siempre explicada en contexto.
