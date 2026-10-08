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

Las UGAs sin digitalizar (rótulos UTM ilegibles, relleno no detectado o área incompatible con la ficha) usan el
polígono provisional de 2019 si existe; quedan para digitalizar a mano en QGIS. Ninguna está revisada en QGIS todavía.
