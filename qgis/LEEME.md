# Revisión de UGAs en QGIS

Proyecto para revisar a mano, sobre imagen satelital, las UGAs que la digitalización automática dejó «por revisar»
(10 al 2026-10-08: las que no pudieron verificarse contra la costa ni contra localidades, o que esos controles ponen en duda).
El motivo de cada una está en su marcador y en el campo `motivo`.
Requiere QGIS 3.44 o posterior.

## Preparar

```
.venv/bin/python herramientas/proyecto_qgis.py
```

Genera `qgis/revision/` (no se versiona; se puede regenerar en cualquier momento):

| Capa | Para qué |
|---|---|
| UGAs por revisar (editar) | Los polígonos a revisar. Amarillo = pendiente, verde = correcta, azul = corregida, gris = descartar. |
| Referencia › UGAs aceptadas | Las vecinas ya aceptadas, en contorno blanco: los bordes compartidos deben coincidir. |
| Referencia › Polígonos de ePOEL 2019 | Apagada; contorno magenta punteado para comparar. |
| Referencia › Costa (contexto 2019) | Línea de costa usada para el ajuste de datum. |
| Mapas de las fichas | El mapa de cada ficha del Boletín, georreferenciado igual que su polígono. Enciende el de la UGA que revisas. |
| Imagen satelital | Esri World Imagery (solo como referencia visual) y Sentinel‑2 2024 de EOX. |

## Revisar

1. Abre `qgis/revision/proyecto.qgz`.
2. Ver › Administrador de marcadores espaciales: cada UGA tiene un marcador con el motivo de la revisión.
3. Enciende el mapa de su ficha y compáralo con el polígono y con el satélite: costa, arroyos, caminos y localidades.
4. Si hace falta, activa la edición de «UGAs por revisar» y ajusta los vértices (herramienta de vértices; usa el
   autoensamblado con «UGAs aceptadas» para no dejar huecos ni traslapes).
5. En el formulario de la UGA (clic con la herramienta de identificar) pon `revision`:
   - **Correcta tal cual**: el polígono automático está bien.
   - **Corregida a mano**: lo ajustaste.
   - **Descartar**: no sirve; el sitio vuelve al polígono de 2019 o a ninguno.
   Anota en `notas` lo que encontraste (por ejemplo, «borde norte siguiendo el arroyo»).
6. Guarda la edición. Puedes revisar por partes: las pendientes se quedan como están.

## Aplicar

```
.venv/bin/python herramientas/aplicar_revision_qgis.py
.venv/bin/python herramientas/validar_digitalizacion.py
npm run datos
```

Las revisiones quedan en `datos/poel/digitalizacion/revisadas/` (eso sí se versiona) y prevalecen sobre la
digitalización automática, aunque esta se vuelva a correr. En la ficha web, el polígono aparece como «revisado sobre
imagen satelital».
