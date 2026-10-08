"""Aplica la revisión hecha en QGIS (qgis/revision/revisar.geojson) a los datos del POEL.

Por cada UGA según su campo `revision`:
  - correcta / corregida: guarda su polígono (tal como quedó en QGIS) en datos/poel/digitalizacion/revisadas/<id>.geojson,
    marcado como revisado; la validación lo acepta y el sitio lo usa en lugar del digitalizado automático.
  - descartar: guarda un registro sin geometría; el sitio vuelve al polígono de 2019 o a ninguno.
  - pendiente: no hace nada.

Las revisiones viven aparte de la digitalización automática, así que volver a correr digitalizar_fichas.py no las pisa.

Uso: .venv/bin/python herramientas/aplicar_revision_qgis.py
     .venv/bin/python herramientas/validar_digitalizacion.py && npm run datos
"""
import json
from datetime import date

from shapely.geometry import mapping, shape

from boletin import DATOS, RAIZ

ORIGEN = RAIZ / "qgis" / "revision" / "revisar.geojson"
REVISADAS = DATOS / "digitalizacion" / "revisadas"


def redondear(coords):
    if isinstance(coords[0], (int, float)):
        return [round(coords[0], 6), round(coords[1], 6)]
    return [redondear(c) for c in coords]


def main():
    REVISADAS.mkdir(parents=True, exist_ok=True)
    cuenta = {}
    for f in json.loads(ORIGEN.read_text())["features"]:
        p = f["properties"]
        revision = p.get("revision") or "pendiente"
        cuenta[revision] = cuenta.get(revision, 0) + 1
        if revision == "pendiente":
            continue
        if revision not in ("correcta", "corregida", "descartar"):
            raise SystemExit(f"UGA {p['uga']}: valor de revisión desconocido «{revision}»")
        geometria = None
        if revision != "descartar":
            g = shape(f["geometry"]).buffer(0)
            if g.is_empty:
                raise SystemExit(f"UGA {p['uga']}: geometría vacía tras la edición")
            geometria = mapping(g)
            geometria = {"type": geometria["type"], "coordinates": redondear(json.loads(json.dumps(geometria["coordinates"])))}
        original = json.loads((DATOS / "digitalizacion" / f"{p['uga']}.geojson").read_text())["features"][0]["properties"]
        registro = {"type": "Feature", "properties": {
            "uga": p["uga"], "revision": revision, "notas": p.get("notas") or "", "fecha": date.today().isoformat(),
            "procedencia": {**original["procedencia"], "revisada_en_qgis": revision != "descartar"},
        }, "geometry": geometria}
        (REVISADAS / f"{p['uga']}.geojson").write_text(
            json.dumps({"type": "FeatureCollection", "features": [registro]}, ensure_ascii=False) + "\n")
    print(cuenta)


if __name__ == "__main__":
    main()
