# Digitalización de las UGAs (ADR 0002)

Polígonos re-digitalizados de los mapas de ubicación de las fichas del Boletín Oficial No. 12 (Apéndice 10).

Flujo, desde la raíz del repositorio:

```
ls datos/poel/ugas | sed 's/.json//' | sort -V | xargs .venv/bin/python herramientas/digitalizar_fichas.py > datos/poel/digitalizacion/lote.jsonl
.venv/bin/python herramientas/ajustar_datum.py          # solo si cambia el método; debe dar residuo ≈ 0
.venv/bin/python herramientas/validar_digitalizacion.py
npm run datos
```

| Archivo | Contenido |
|---|---|
| `<id>.geojson` | Polígono en WGS84 con su procedencia (página, datum, precisión) y el control de área. |
| `<id>.png` | Diagnóstico (no se versiona): contorno detectado sobre el mapa original. |
| `lote.jsonl` | Resultado de la última corrida para las 122 UGAs, incluidas las que fallaron y por qué. |
| `datum.json` | Desplazamiento de datum ajustado contra la costa (INC-011). |
| `validacion.json` | Estado de cada UGA: `aceptada`, `revisar`, `rechazada` o `sin-digitalizar`. El sitio usa las dos primeras. |

Estado al 2026-10-08: 97 aceptadas, 22 por revisar y 3 sin digitalizar.

- Sin digitalizar: 6 (el Boletín no trae su mapa, INC-012), 35 y 54 (sus mapas no tienen rótulos del Este). La 35 y
  la 54 usan el polígono provisional de 2019; la 6 no tiene polígono.
- Por revisar: área entre 5 y 25 % distinta de la ficha (franjas delgadas o mapas de baja resolución), escala tomada
  de la superficie sin poder corroborar la ubicación, o fichas de INC-013.
- Al construir el mapa (`construir_geodatos.py`), donde dos polígonos se enciman cede el menos preciso ante uno
  aceptado; los «revisar» y los de 2019 no recortan a nadie.

Ninguna está revisada en QGIS todavía.
