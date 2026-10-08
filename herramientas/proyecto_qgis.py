"""Prepara un proyecto de QGIS para revisar a mano las UGAs digitalizadas que quedaron «por revisar».

Escribe en qgis/revision/:
  - revisar.geojson: los polígonos por revisar, editables, con los campos `revision` (pendiente, correcta,
    corregida, descartar) y `notas` para llenar en QGIS.
  - referencia/: UGAs aceptadas, polígonos de ePOEL 2019 y costa (solo lectura).
  - mapas/<id>.png + .pgw + .png.aux.xml: el mapa de la ficha en el Boletín, georreferenciado con la misma
    transformación (y desplazamiento de datum) que produjo el polígono, para compararlos encima del satélite.
  - proyecto.qgz: lo arma herramientas/qgis/construir_proyecto.py con el Python de QGIS.

Después de revisar en QGIS: .venv/bin/python herramientas/aplicar_revision_qgis.py

Uso: .venv/bin/python herramientas/proyecto_qgis.py [--qgis /Applications/QGIS.app]
"""
import json
import os
import subprocess
import sys
from pathlib import Path

from pyproj import CRS

import digitalizar_fichas as d
from boletin import DATOS, RAIZ
from construir_geodatos import geometrias_2019
from shapely.geometry import mapping

DIG = DATOS / "digitalizacion"
DESTINO = RAIZ / "qgis" / "revision"
WKT_UTM12N = CRS.from_epsg(32612).to_wkt()


def coleccion(features):
    return {"type": "FeatureCollection", "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
            "features": features}


def mapa_georreferenciado(doc, uga, geo, dx, dy):
    """Guarda el mapa de la ficha como PNG con archivo de mundo (centro del píxel superior izquierdo) en UTM 12N."""
    ficha_mapa = json.loads((DATOS / "ugas" / f"{geo['ficha_mapa']}.json").read_text())["mapa_ubicacion"]
    png = DESTINO / "mapas" / f"{uga}.png"
    d.imagen_del_mapa(doc, ficha_mapa, png, geo["factor_render"])
    png.with_suffix(".pgw").write_text("\n".join(str(v) for v in (
        geo["a_x"], 0.0, 0.0, geo["a_y"], geo["b_x"] + dx, geo["b_y"] + dy)) + "\n")
    (DESTINO / "mapas" / f"{uga}.png.aux.xml").write_text(f"<PAMDataset><SRS>{WKT_UTM12N}</SRS></PAMDataset>\n")


def main():
    qgis = Path(sys.argv[sys.argv.index("--qgis") + 1]) if "--qgis" in sys.argv else Path("/Applications/QGIS.app")
    validacion = json.loads((DIG / "validacion.json").read_text())
    archivo_pistas = DIG / "pistas_revision.json"  # hallazgos de las verificaciones automáticas, para orientar la revisión
    pistas = json.loads(archivo_pistas.read_text()) if archivo_pistas.exists() else {}
    por_revisar = [u for u, v in validacion.items() if v["estado"] == "revisar"]
    (DESTINO / "mapas").mkdir(parents=True, exist_ok=True)
    (DESTINO / "referencia").mkdir(parents=True, exist_ok=True)
    dx, dy = d.desplazamiento_datum()
    doc = d.abrir()

    revisar, aceptadas = [], []
    for p in sorted(DIG.glob("*.geojson")):
        uga = p.stem
        feat = json.loads(p.read_text())["features"][0]
        ficha = json.loads((DATOS / "ugas" / f"{uga}.json").read_text())
        ctrl, proc = feat["properties"]["control"], feat["properties"]["procedencia"]
        props = {"uga": uga, "politica": ficha["politica"], "superficie_ficha_ha": ficha["superficie_ha"],
                 "area_digitalizada_ha": ctrl["area_digitalizada_ha"], "diferencia_pct": ctrl["diferencia_area_pct"],
                 "precision_m": proc["precision_aprox_m"], "escala_por_superficie": ctrl.get("escala_por_superficie", False),
                 "fuente": proc["fuente"]}
        if uga in por_revisar:
            props |= {"motivo": "; ".join(validacion[uga]["motivos"]), "pista": pistas.get(uga, ""),
                      "revision": "pendiente", "notas": ""}
            revisar.append({"type": "Feature", "properties": props, "geometry": feat["geometry"]})
            mapa_georreferenciado(doc, uga, feat["properties"]["georreferencia"], dx, dy)
        elif validacion.get(uga, {}).get("estado") == "aceptada":
            aceptadas.append({"type": "Feature", "properties": props, "geometry": feat["geometry"]})

    archivo = DESTINO / "revisar.geojson"
    sin_aplicar = [f["properties"]["uga"] for f in (json.loads(archivo.read_text())["features"] if archivo.exists() else [])
                   if f["properties"].get("revision") != "pendiente" and not (DIG / "revisadas" / f"{f['properties']['uga']}.geojson").exists()]
    if sin_aplicar:
        raise SystemExit(f"{archivo} tiene revisiones sin aplicar ({', '.join(sin_aplicar)}): corre aplicar_revision_qgis.py antes de regenerar.")
    archivo.write_text(json.dumps(coleccion(revisar), ensure_ascii=False, indent=1) + "\n")
    (DESTINO / "referencia" / "aceptadas.geojson").write_text(json.dumps(coleccion(aceptadas), ensure_ascii=False) + "\n")
    v2019 = [{"type": "Feature", "properties": {"uga": k}, "geometry": mapping(g)} for k, g in sorted(geometrias_2019().items())]
    (DESTINO / "referencia" / "epoel-2019.geojson").write_text(json.dumps(coleccion(v2019), ensure_ascii=False) + "\n")
    ctx = json.loads((RAIZ / "public" / "datos" / "contexto.geojson").read_text())
    tierra = [f for f in ctx["features"] if f["properties"].get("capa") == "tierra"]
    (DESTINO / "referencia" / "tierra.geojson").write_text(json.dumps(coleccion(tierra)) + "\n")
    (DESTINO / "ugas-por-revisar.json").write_text(json.dumps(por_revisar) + "\n")

    # El proyecto se arma con el Python de QGIS (PyQGIS)
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen",
           "PROJ_DATA": str(qgis / "Contents" / "Resources" / "qgis" / "proj"),
           "GDAL_DATA": str(qgis / "Contents" / "Resources" / "qgis" / "gdal")}
    subprocess.run([str(qgis / "Contents" / "MacOS" / "python"), str(RAIZ / "herramientas" / "qgis" / "construir_proyecto.py"),
                    str(DESTINO)], check=True, env=env)
    print(f"{len(revisar)} UGAs por revisar; proyecto en {DESTINO / 'proyecto.qgz'}")


if __name__ == "__main__":
    main()
