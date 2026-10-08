# Plan de acción — modernización de ePOEL

Acordado con Hugo Quintero el 2026‑10‑07. Sin fecha externa; ritmo de medio tiempo. Glosario en [CONTEXT.md](../CONTEXT.md); decisiones en [docs/adr](adr/).

## Fase 0 — Rescate y bases (1–2 semanas)

- [x] Congelar la versión 2019: tag `v1-2019` (publicado en GitHub)
- [x] Rescatar las capas de la cuenta de Mapbox de Helden → `rescate/mapbox-2019/` (18 capas)
- [x] Extraer del Boletín las tablas maestras: 19 lineamientos, 18 estrategias y 192 criterios en 16 grupos
- [x] Extraer las 122 fichas de UGA como datos estructurados, validadas contra las imágenes del Boletín
- [x] Abrir el registro de incidencias (`datos/poel/incidencias.json`)
- [x] Piloto de digitalización semiautomática (UGAs 12, 1a y 45)
- [x] Corregir créditos y licencias: LICENSE, LICENSE-DATOS.md, CREDITOS.md
- [x] Borrador del descargo (`docs/descargo.md`)
- [ ] **Hugo**: visto bueno por escrito para usar el escudo del Municipio de Loreto y el logo de Eco‑Alianza
- [ ] **Hugo**: título, fecha y vigencia del convenio de colaboración Eco‑Alianza – H. Ayuntamiento
- [ ] **Hugo**: avisar a Helden Velis y a Brenda E. García
- [ ] **Hugo**: decidir el tratamiento de las localidades de 2019 que no vienen del Boletín (INC‑010)

## Fase 1 — POEL bien hecho (6–8 semanas)

- Digitalizar en lote las 122 UGAs; Hugo revisa y corrige en QGIS; validación topológica (sin huecos ni traslapes); procedencia por polígono.
- Base técnica: Astro + MapLibre GL, PMTiles de Protomaps alojado en el repo, satélite EOX 2024 opcional, despliegue con GitHub Actions (ADR 0003).
- Consulta por clic, coordenadas geográficas o UTM 12N, localidad, ID de UGA y GPS; aviso claro para puntos fuera del POEL, con enlace al instrumento que probablemente aplique (POEM del Golfo de California, Programa de Manejo del PNBL).
- Ficha web por UGA (`/poel/uga/5a/`): política, actividad, lineamientos, estrategias y criterios con texto completo; cita del Boletín; procedencia e incidencias; impresión limpia; enlace compartible.
- Capas de soporte rescatadas con su procedencia visible (minería fuera hasta actualizarla); descargas GeoJSON; créditos y descargo; botón "Reportar incidencia" (correo y GitHub Issues); GoatCounter; diseño mobile‑first.
- Administración local: importadores (CSV UTM, SHP, KML/KMZ, GeoJSON), validación, edición de metadatos y textos, vista previa y diff antes del commit.

## Fase 2 — Expansión

PSDUL 2024 (cuando lleguen los shapefiles; marcado "en proceso" mientras no se publique), inglés, PWA sin conexión, actualización de las capas de soporte desde fuentes vigentes (incluida minería), nombre nuevo y dominio propio.

## Fase 3 — Plataforma territorial

Otros instrumentos (Programa de Manejo del PNBL, POEM del Golfo de California) y consulta cruzada: "qué dice cada instrumento en este punto".

## Diseño de la interfaz (en curso)

- [x] Skill Impeccable instalada para el proyecto (`.claude/settings.json`) y `PRODUCT.md` escrito.
- [x] Tirada de dirección visual (seed `c3ec5e0f`): Hugo se inclina por una mezcla de "Carta topográfica INEGI" y "Manual con pestañas", conservando "¿Qué quieres hacer?".
- [ ] Elegir dirección con las maquetas A (carta + manual), B (pase y tablero) y C (señalética) en `.impeccable/mocks/comparar.html`.
- [ ] Pendiente del extractor: las "áreas de atención especial" a veces parten la justificación entre renglones (p. ej. UGA 45).
