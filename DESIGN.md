---
name: ePOEL
description: Consulta del Programa de Ordenamiento Ecológico Local de Loreto, B.C.S., como un pase citable e imprimible.
colors:
  tinta: "#0b0d10"
  pizarra: "#1c2127"
  linea-oscura: "#23292f"
  acero: "#646a71"
  acero-claro: "#9aa1a8"
  panel: "#e6e8eb"
  superficie: "#ffffff"
  papel: "#f4f5f7"
  linea: "#e1e4e7"
  amarillo-senal: "#ffd400"
  politica-aprovechamiento: "#d08a2e"
  politica-conservacion: "#2f7d4a"
  politica-preservacion: "#8cc06d"
  politica-restauracion: "#c0533a"
  mar: "#d7e2ea"
  tierra: "#f7f8f9"
typography:
  display:
    fontFamily: "Barlow Condensed, Arial Narrow, sans-serif"
    fontSize: "56px"
    fontWeight: 700
    lineHeight: 0.9
    letterSpacing: "0.01em"
  headline:
    fontFamily: "Barlow Condensed, Arial Narrow, sans-serif"
    fontSize: "27px"
    fontWeight: 700
    lineHeight: 1.05
  title:
    fontFamily: "Barlow Condensed, Arial Narrow, sans-serif"
    fontSize: "19px"
    fontWeight: 700
    lineHeight: 1.2
  body:
    fontFamily: "Barlow, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.45
  label:
    fontFamily: "Barlow Condensed, Arial Narrow, sans-serif"
    fontSize: "12.5px"
    fontWeight: 600
    letterSpacing: "0.08em"
  cifra:
    fontFamily: "JetBrains Mono, ui-monospace, monospace"
    fontSize: "15px"
    fontWeight: 600
    letterSpacing: "-0.01em"
    fontFeature: "tnum"
rounded:
  fino: "3px"
  control: "4px"
  tarjeta: "6px"
  pase: "12px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "20px"
components:
  boton-primario:
    backgroundColor: "{colors.tinta}"
    textColor: "{colors.superficie}"
    rounded: "{rounded.control}"
    padding: "5px 9px"
  boton-primario-hover:
    backgroundColor: "{colors.pizarra}"
    textColor: "{colors.superficie}"
  boton-secundario:
    backgroundColor: "{colors.superficie}"
    textColor: "{colors.tinta}"
    rounded: "{rounded.control}"
    padding: "5px 9px"
  boton-secundario-hover:
    backgroundColor: "{colors.panel}"
  destino:
    backgroundColor: "{colors.superficie}"
    textColor: "{colors.tinta}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "7px 0"
  destino-activo:
    backgroundColor: "{colors.tinta}"
    textColor: "{colors.amarillo-senal}"
  buscador:
    backgroundColor: "{colors.papel}"
    textColor: "{colors.tinta}"
    rounded: "{rounded.control}"
    height: "40px"
    padding: "0 44px 0 40px"
  pase:
    backgroundColor: "{colors.superficie}"
    textColor: "{colors.tinta}"
    rounded: "{rounded.pase}"
  tablero:
    backgroundColor: "{colors.tinta}"
    textColor: "{colors.panel}"
  tablero-fila-seleccionada:
    backgroundColor: "{colors.amarillo-senal}"
    textColor: "{colors.tinta}"
  marca-alerta:
    backgroundColor: "{colors.amarillo-senal}"
    textColor: "{colors.tinta}"
    rounded: "{rounded.fino}"
    padding: "0 5px"
---

# Design System: ePOEL

## Overview

**Creative North Star: "El Pase del Territorio"**

Cada consulta emite un pase: un documento segmentado, perforado y con talón que dice qué Unidad de Gestión Ambiental (UGA) aplica en un punto, qué política rige y qué criterios valen para la actividad elegida, cada uno con su página del Boletín Oficial. El tablero oscuro funciona como la sala de espera: ordena las UGAs vecinas por distancia, como un tablero de salidas que reacomoda sus filas sin perderlas de vista. El mapa queda en medio, como el territorio que ambos describen.

El carácter es tangible y oficial. Las piezas se comportan como objetos de papel con bordes firmes de tinta, casi sin sombras, con cifras monoespaciadas para códigos, coordenadas y medidas. Se lee como un documento que podría sellarse, pero habla en lenguaje llano. La densidad es alta y ordenada: en una sola vista caben buscador, tablero, mapa y pase completo, y nada compite con la respuesta.

Se rechazan explícitamente dos mundos: el visor SIG de tarjetas flotantes sobre un mapa a sangre y el portal burocrático de tablas grises.

**Key Characteristics:**
- Tres columnas fijas en escritorio: tablero de tinta, mapa flexible, pase blanco.
- Un solo color de acento, el Amarillo Señal, reservado para lo que cambia o exige atención.
- Barlow Condensed para rotular, Barlow para leer y JetBrains Mono para cifras.
- Perforaciones punteadas, talón con QR real e identificador de la UGA, como un pase de abordar.
- Impresión en blanco y negro puro, completa y citable.

## Colors

Una base neutra casi monocroma de tinta, acero y papel, con un único acento amarillo y cuatro colores de política que solo viven en el mapa y en las claves de política.

### Primary
- **Tinta** (`tinta`): barra superior, tablero, texto principal, bordes de botones y el botón primario. Es la voz del sistema; casi todo lo que no es papel es tinta.
- **Amarillo Señal** (`amarillo-senal`): selección (fila activa del tablero, marcador del mapa, destino elegido), presión alta, incidencias de nivel aviso, anillo de foco y selección de texto. Nunca decora.

### Secondary
- **Pizarra** (`pizarra`): estado hover del botón primario y superficies oscuras secundarias.
- **Línea oscura** (`linea-oscura`): divisiones dentro del tablero y sus cabeceras.

### Tertiary
Colores de política ambiental, con significado normativo fijo; se usan en el relleno del mapa (42 % de opacidad, 28 % si el polígono es provisional), en sus bordes y en la clave cuadrada junto al nombre de la política:
- **Ocre Aprovechamiento** (`politica-aprovechamiento`): Aprovechamiento sustentable.
- **Verde Conservación** (`politica-conservacion`): Conservación.
- **Verde Preservación** (`politica-preservacion`): Preservación.
- **Terracota Restauración** (`politica-restauracion`): Restauración.

### Neutral
- **Panel** (`panel`): fondo de la aplicación detrás del pase y color de los recortes de la perforación.
- **Superficie** (`superficie`): el papel del pase, tarjetas y páginas de texto.
- **Papel** (`papel`): fondo del talón y del buscador; un blanco apenas más frío que la superficie.
- **Línea** (`linea`): divisiones internas del pase (segmentos, grupos, avisos).
- **Acero** (`acero`): etiquetas, metadatos y citas («Boletín, p. 103»).
- **Acero claro** (`acero-claro`): etiquetas y cifras secundarias sobre fondo de tinta.
- **Mar** (`mar`) y **Tierra** (`tierra`): mapa base propio, sin servicios externos.

### Named Rules
**The Una Señal Rule.** El Amarillo Señal solo marca selección, alerta o foco. Si un elemento amarillo no cambia ni exige atención, es un error.

**The Política Sagrada Rule.** Los cuatro colores de política significan una política ambiental y nada más. No se reutilizan para estados, categorías ni decoración.

## Typography

**Display Font:** Barlow Condensed (con Arial Narrow)
**Body Font:** Barlow (con system-ui)
**Label/Mono Font:** JetBrains Mono, con cifras tabulares

**Character:** Una condensada de señalética para rotular, que cabe en columnas estrechas y se lee de lejos, con una humanista de la misma familia para el texto normativo largo. La monoespaciada aparece solo donde la exactitud se cuenta carácter por carácter.

### Hierarchy
- **Display** (700, 56 px, 0.9): el identificador de la UGA en la cabecera del pase. En celular baja a 40 px y en el pase compacto a 30 px.
- **Headline** (700, 27 px, 1.05): el nombre de la política ambiental, precedido por su clave de color.
- **Title** (700, 19–21 px): grupos de criterios, «¿Qué quieres hacer aquí?» y cabeceras del tablero.
- **Body** (400, 15 px, 1.45; criterios a 14.5 px y 1.5): texto de criterios y lineamientos, citado completo. Páginas de texto a 16 px con un máximo de 68 caracteres por línea.
- **Label** (600, 12.5 px, 0.08 em, mayúsculas): rótulos de segmentos, columnas del tablero y leyendas institucionales.
- **Cifra** (JetBrains Mono, tabular): códigos (C1, L12, EG3), superficies, distancias, coordenadas y número de páginas.

### Named Rules
**The Cifra Exacta Rule.** Todo número que alguien podría copiar a un expediente (coordenada, superficie, página, código) va en JetBrains Mono tabular. El texto corrido nunca.

## Layout

En escritorio hay una barra de 60 px y debajo tres columnas que llenan la ventana: tablero de 400 px, mapa flexible y pase de 432 px. Cada columna desplaza su contenido por separado; la página no tiene desplazamiento propio. Dentro del pase solo se desplaza la zona de criterios. Al recorrerla, la cabecera se compacta en una línea (política, superficie y presión), siempre que quede contenido por recorrer.

En celular (≤860 px) el orden es barra, mapa de 30 vh, el pase como hoja que se monta 22 px sobre el mapa y el tablero debajo. La primera fila de destinos debe verse dentro de los 812 px de un teléfono común. Los segmentos se mantienen en una fila de cuatro.

El ritmo de espaciado es corto y repetido: 4, 8, 12 y 20 px. El margen interior del pase es de 20 px a los lados.

## Elevation & Depth

El sistema es plano por capas tonales: tinta, panel y papel separan planos sin sombras. Solo dos objetos se levantan: el pase (y la tarjeta de estado vacío) sobre el panel, y el aviso flotante del buscador. La profundidad del pase viene sobre todo de su forma de documento (perforaciones, talón), no de la sombra.

### Shadow Vocabulary
- **Pase** (`box-shadow: 0 6px 22px rgba(11, 13, 16, .12)`): el pase y la tarjeta de estado vacío sobre el panel.
- **Aviso flotante** (`box-shadow: 0 8px 24px rgba(11, 13, 16, .25)`): el mensaje de búsqueda que aparece bajo el buscador.
- **Leyenda del mapa** (`box-shadow: 0 2px 10px rgba(11, 13, 16, .12)`): controles flotantes del mapa.

### Named Rules
**The Papel Sobre Mesa Rule.** Solo el pase se eleva sobre el panel. Botones, filas, segmentos y grupos son planos; un botón con sombra está fuera del sistema.

## Shapes

Esquinas firmes y pequeñas: 3 px en marcas, códigos y clave de política; 4 px en botones, destinos y buscador; 6 px en tarjetas de ejemplo; 12 px solo en el pase y la tarjeta de estado vacío. Los botones llevan borde de tinta de 1.5 px, como un sello. La perforación es una línea punteada de 2 px con dos recortes semicirculares de 22 px del color del panel en los bordes, y el talón separa el identificador de la UGA con otra línea punteada vertical. Los triángulos de los acordeones se dibujan con bordes CSS, no con caracteres ni iconos externos.

## Components

### Buttons
Tangibles y oficiales: rectángulos de 4 px con borde de tinta de 1.5 px y texto en Barlow Condensed seminegra.
- **Shape:** esquinas de 4 px (`rounded.control`).
- **Primary:** fondo de tinta con texto blanco; solo para «Imprimir pase» y «Reintentar».
- **Hover / Focus:** el primario pasa a pizarra; el secundario, a panel. El foco es un contorno de tinta de 2 px con anillo Amarillo Señal de 5 px, y dentro de la barra y el tablero, un contorno amarillo.
- **Secondary:** fondo blanco con borde de tinta («Copiar enlace», «Reportar»).

### Chips
- **Destinos («¿Qué quieres hacer aquí?»):** seis botones iguales en una fila (tres por fila en celular), en mayúsculas de Barlow Condensed a 15 px. El activo se invierte: fondo de tinta y texto Amarillo Señal.
- **Marca de alerta:** Amarillo Señal con texto de tinta y esquinas de 3 px, para presión alta e incidencias de nivel aviso («INC 07»).
- **Marca de nota:** contorno gris sin relleno, para incidencias informativas.

### Cards / Containers
- **Corner Style:** 12 px en el pase; 6 px en las tarjetas de ejemplo del estado vacío.
- **Background:** superficie blanca; talón en papel.
- **Shadow Strategy:** solo la sombra del pase (ver Elevation & Depth).
- **Border:** ninguno exterior; divisiones internas de 1 px en línea.
- **Internal Padding:** 20 px a los lados; cabecera de 14 px arriba.

### Inputs / Fields
- **Style:** buscador de 40 px de alto sobre papel, con borde interior de 1 px gris (#c9ced4), lupa a la izquierda y botón de ubicación a la derecha.
- **Focus:** pasa a blanco con borde interior de tinta de 2 px y anillo Amarillo Señal de 3 px.
- **Error:** un aviso flotante debajo explica el formato esperado con ejemplos en monoespaciada.
- **Formularios (Contacto):** mismos campos sobre papel con borde interior gris y foco de tinta con anillo Amarillo Señal; rótulos en mayúsculas espaciadas de Barlow Condensed; un campo inválido toma borde terracota y el mensaje de estado aparece debajo, sobre el botón primario.

### Navigation
Barra de tinta de 60 px: «ePOEL» en Barlow Condensed negra a 28 px con «Loreto» en acero claro, buscador al centro y enlaces de texto («Acerca de», «Datos abiertos») a 17 px que pasan de gris claro a blanco al pasar el cursor. En celular la barra se apila y los enlaces se ocultan.

### El pase
Componente insignia. De arriba abajo:
1. Cabecera: identificador de la UGA en display, localidad y actividad, y a la derecha el sello del Boletín Oficial (número, página y fecha) que enlaza al PDF.
2. Política con su clave de color.
3. Cuatro segmentos rotulados: superficie, población, fragilidad y presión.
4. Avisos: presión, incidencias y procedencia del polígono.
5. Perforación.
6. Destinos.
7. Criterios agrupados en acordeones, plegados al abrir la UGA, con triángulo ▶/▼ y conteo a la derecha.
8. Perforación.
9. Talón de 110 px o menos: descargo en un renglón, acciones, QR real hacia la ficha, identificador de la UGA y créditos de desarrollo y alojamiento.

Al consultar otra UGA, el pase se reimprime segmento por segmento.

### Tablero
Tabla en Barlow Condensed sobre tinta: UGA, política con clave de color, distancia en monoespaciada y la columna de incidencias. La fila seleccionada pinta su celda de UGA en Amarillo Señal y su distancia dice «AQUÍ». Al cambiar de consulta, las filas se reacomodan en su lugar (cada una conserva su identidad y se desplaza) y la recién llegada queda teñida de amarillo hasta que se ve. En el pie, logos institucionales en blanco o gris, nunca a color.

## Do's and Don'ts

### Do:
- **Do** citar la página del Boletín junto a cada criterio («Boletín, p. 103») en acero de 12 px.
- **Do** reservar el Amarillo Señal para selección, presión alta, incidencias de nivel aviso y foco (The Una Señal Rule).
- **Do** declarar la procedencia de cada polígono en el pase y distinguir los provisionales en el mapa con borde punteado y menor opacidad.
- **Do** imprimir en blanco y negro puro: sin barra, tablero, mapa ni destinos; todos los grupos abiertos; marcas con contorno negro.
- **Do** mostrar los logos institucionales y de donación en monocromo (blanco sobre tinta, gris oscuro sobre papel), enlazados a sus sitios.

### Don't:
- **Don't** construir un visor SIG de tarjetas flotantes sobre un mapa a sangre.
- **Don't** caer en el portal burocrático de tablas grises.
- **Don't** usar los colores de política para otra cosa que no sea una política ambiental (The Política Sagrada Rule).
- **Don't** abrir un grupo de criterios por defecto: el usuario debe ver primero cuántos grupos hay.
- **Don't** cargar fuentes, glifos, mosaicos o iconos de servicios con token o cuenta; las fuentes van empaquetadas y los rótulos del mapa son HTML.
- **Don't** sugerir aval oficial: el escudo del Municipio y el logo de Eco‑Alianza nunca encabezan el pase ni se usan como sello.
