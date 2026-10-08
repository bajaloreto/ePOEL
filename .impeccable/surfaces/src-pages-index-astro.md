---
version: 1
slug: "src-pages-index-astro"
primary_target: "src/pages/index.astro"
related_targets: []
---

# Consulta por punto (pantalla principal)

Alcance: la pantalla principal de ePOEL, que incluye buscador, mapa, tablero de UGAs y ficha de la UGA consultada. Modo: Operate. Audiencia: ciudadano o inversionista (principal) y funcionario municipal (secundario). Tarea: saber qué aplica en un punto y obtener una ficha citable e imprimible.

## Direction contract

THESIS: Consultar un punto produce un pase: un documento segmentado, citable e imprimible que dice qué UGA aplica y qué criterios rigen la actividad elegida, mientras un tablero ordena las UGAs vecinas. Se rechazan el visor SIG de tarjetas flotantes sobre un mapa a sangre y el portal burocrático de tablas grises.

OWN-WORLD: Tinta #0B0D10 en la barra y el tablero, pizarra #1C2127, panel #E6E8EB y la superficie blanca del pase. El amarillo #FFD400 se reserva para lo que cambia o exige atención: selección, presión alta e incidencias. Las políticas en el mapa son ocre, verde oscuro, verde claro y terracota. Barlow Condensed se usa en cabeceras, códigos y tablero, Barlow en la lectura, y JetBrains Mono con cifras tabulares solo en códigos, coordenadas y medidas. El pase lleva segmentos rotulados, perforación, talón y un código QR real hacia la ficha.

STORY: El visitante busca o hace clic y su pase aparece: UGA, política, superficie, presión. Elige "¿Qué quieres hacer?" y ve solo los criterios que aplican, cada uno con su página del Boletín. Imprime el pase (blanco y negro puro) o copia el enlace. El funcionario usa el tablero para revisar las UGAs vecinas y sus incidencias.

FIRST VIEWPORT: Escritorio 1440: barra de tinta de 60 px con ePOEL y buscador. Tablero de 380 px a la izquierda (UGA | Política | Dist. | Incid.), mapa flexible al centro y pase de 440 px a la derecha: UGA a 64 px, cuatro segmentos, perforación, destinos, criterios y talón con QR y la donación de HuQuMa Studio. La acción primaria son los destinos de "¿Qué quieres hacer?"; la secundaria, "Imprimir pase". En celular: barra, mapa de 34 vh, el pase como hoja que sube (la ficha completa a un deslizamiento) y el tablero debajo. Movimiento distintivo: al consultar otra UGA, el tablero reordena sus filas en su lugar (cada fila conserva su identidad y se desplaza), la nueva selección queda iluminada en amarillo hasta que se ve, y el pase se reimprime segmento por segmento.

FORM: Retador "Pase de abordar y tablero" (vernacular-ephemera-boarding-pass-and-gate-board), elegido por Hugo con maquetas a la vista frente a la dirección asignada (tercera de la lista propia: señalética SCT). Seed c3ec5e0f.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Decisiones abiertas

- Ubicación final de los logos institucionales (Municipio y Eco‑Alianza), pendiente del visto bueno por escrito.
- Afinar los presets de "¿Qué quieres hacer?" criterio por criterio, no solo por grupo.
