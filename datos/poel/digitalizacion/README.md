# Digitalización de las UGAs (ADR 0002)

Polígonos re-digitalizados de los mapas de ubicación de las fichas del Boletín Oficial No. 12 (Apéndice 10).

Flujo, desde la raíz del repositorio:

```
ls datos/poel/ugas | sed 's/.json//' | sort -V | xargs .venv/bin/python herramientas/digitalizar_fichas.py > datos/poel/digitalizacion/lote.jsonl
.venv/bin/python herramientas/ajustar_datum.py              # solo si cambia el método; residuo ≤ 10 m no se aplica
.venv/bin/python herramientas/verificar_con_costa.py        # orilla del mapa frente a la costa real
.venv/bin/python herramientas/verificar_con_localidades.py  # localidades rotuladas frente a sus coordenadas
.venv/bin/python herramientas/validar_digitalizacion.py
npm run datos
```

| Archivo | Contenido |
|---|---|
| `<id>.geojson` | Polígono en WGS84 con su procedencia (página, datum, precisión) y el control de área. |
| `<id>.png` | Diagnóstico (no se versiona): contorno detectado sobre el mapa original. |
| `lote.jsonl` | Resultado de la última corrida para las 122 UGAs, incluidas las que fallaron y por qué. |
| `datum.json` | Desplazamiento de datum ajustado contra la costa (INC-011). |
| `revisadas/<id>.geojson` | Polígono revisado a mano en QGIS (o descartado), con notas y fecha. |
| `pistas_revision.json` | Hallazgos de las verificaciones automáticas para orientar la revisión manual en QGIS. |
| `costa.json`, `localidades.json` | Verificación independiente de la posición de cada mapa (costa real y localidades). |
| `validacion.json` | Estado de cada UGA: `aceptada`, `revisar`, `rechazada` o `sin-digitalizar`. El sitio usa las dos primeras. |

Estado al 2026-10-08: 109 aceptadas, 10 por revisar (18b, 77a, 77b, 78a, 79, 80, 88a, 88b, 88c, 91) y 3 sin digitalizar.
La posición de cada mapa se verifica contra la costa real y las localidades que rotula: así se encontró y corrigió un
rótulo mal leído que desplazaba 10 km las UGAs 73a y 73b (el control de área no detecta traslaciones). Las localidades
vienen del catálogo AGEEML de INEGI (`datos/referencia/`). El datum se confirmó contra Sentinel-2 (INC-014).

- Sin digitalizar: 6 (el Boletín no trae su mapa, INC-012), 35 y 54 (sus mapas no tienen rótulos del Este). La 35 y
  la 54 usan el polígono provisional de 2019; la 6 no tiene polígono.
- Por revisar: área entre 5 y 25 % distinta de la ficha (franjas delgadas o mapas de baja resolución), escala tomada
  de la superficie sin poder corroborar la ubicación, o fichas de INC-013.
- Al construir el mapa (`construir_geodatos.py`), donde dos polígonos se enciman cede el menos preciso ante uno
  aceptado; los «revisar» y los de 2019 no recortan a nadie.

Revisión manual: `qgis/LEEME.md`. Las revisiones se guardan en `revisadas/<id>.geojson` y prevalecen sobre la
digitalización automática. Ninguna está revisada en QGIS todavía.
