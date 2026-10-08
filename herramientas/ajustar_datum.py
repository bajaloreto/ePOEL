"""Ajusta el desplazamiento de datum de las UGAs digitalizadas contra la línea de costa (INC-011).

La leyenda de los mapas del Boletín declara «Datum WGS84, elipsoide Clarke 1866», que es contradictoria: Clarke
1866 es el elipsoide de NAD27. Si las coordenadas de los rótulos están en NAD27, los polígonos quedan corridos
~100–200 m respecto a WGS84. Esta herramienta mide ese corrimiento sin suponer el datum:

  1. Toma los bordes de las UGAs costeras digitalizadas con escala propia (no por superficie).
  2. Busca el desplazamiento (Este, Norte) que acerca más esos bordes a la costa (tierra de contexto.geojson,
     derivada de las cuencas rescatadas de 2019), con una distancia truncada a 150 m para que los tramos
     interiores no pesen.
  3. Suma el resultado al desplazamiento vigente en datos/poel/digitalizacion/datum.json, si pasa de 10 m.

Después hay que volver a correr digitalizar_fichas.py para que el desplazamiento se aplique; una segunda corrida
de esta herramienta debe dar un residuo cercano a cero.

Uso: .venv/bin/python herramientas/ajustar_datum.py
"""
import json
from datetime import date

import numpy as np
from pyproj import Transformer
from shapely import distance, points, transform
from shapely.geometry import shape
from shapely.ops import unary_union

from boletin import DATOS, RAIZ

DIGITALIZACION = DATOS / "digitalizacion"
DATUM = DIGITALIZACION / "datum.json"
CONTEXTO = RAIZ / "public" / "datos" / "contexto.geojson"
A_UTM = Transformer.from_crs("EPSG:4326", "EPSG:32612", always_xy=True)


def utm(g):
    return transform(g, lambda c: np.column_stack(A_UTM.transform(c[:, 0], c[:, 1])))


def main():
    ctx = json.loads(CONTEXTO.read_text())
    costa = unary_union([utm(shape(f["geometry"])) for f in ctx["features"]
                         if f["properties"].get("capa") == "tierra"]).buffer(0).boundary
    zona = costa.buffer(400)
    puntos, usadas = [], []
    for p in sorted(DIGITALIZACION.glob("*.geojson")):
        feat = json.loads(p.read_text())["features"][0]
        if feat["properties"]["control"].get("escala_por_superficie"):
            continue
        g = utm(shape(feat["geometry"])).buffer(0)
        if g.distance(costa) > 200:
            continue
        borde = g.boundary.intersection(zona)
        n0 = len(puntos)
        for tramo in getattr(borde, "geoms", [borde]):
            if not tramo.is_empty:
                puntos += [tramo.interpolate(d).coords[0] for d in np.arange(0, tramo.length, 20)]
        if len(puntos) > n0:
            usadas.append(p.stem)
    pts = np.array(puntos)

    def costo(dx, dy):
        return float(np.mean(np.minimum(distance(points(pts + [dx, dy]), costa), 150)))

    grueso = min((costo(dx, dy), dx, dy) for dx in range(-300, 301, 20) for dy in range(-300, 301, 20))
    fino = min((costo(dx, dy), dx, dy) for dx in range(grueso[1] - 20, grueso[1] + 21, 5)
               for dy in range(grueso[2] - 20, grueso[2] + 21, 5))
    previo = json.loads(DATUM.read_text()) if DATUM.exists() else {"desplazamiento_m": {"este": 0, "norte": 0}}
    # Un residuo de hasta 10 m es el paso de la búsqueda (5 m) más el ruido de la costa: no se aplica, para que
    # el desplazamiento no oscile entre corridas
    aplicar = (fino[1] ** 2 + fino[2] ** 2) ** 0.5 > 10
    este = previo["desplazamiento_m"]["este"] + (fino[1] if aplicar else 0)
    norte = previo["desplazamiento_m"]["norte"] + (fino[2] if aplicar else 0)
    nad27 = Transformer.from_crs("EPSG:26712", "EPSG:32612", always_xy=True).transform(465000, 2875000)
    DATUM.write_text(json.dumps({
        "desplazamiento_m": {"este": este, "norte": norte},
        "residuo_de_esta_corrida_m": {"este": fino[1], "norte": fino[2]},
        "costo_m": {"sin_residuo": round(costo(0, 0), 1), "con_residuo": round(fino[0], 1)},
        "referencia_nad27_a_wgs84_m": {"este": round(nad27[0] - 465000, 1), "norte": round(nad27[1] - 2875000, 1)},
        "ugas_costeras": usadas,
        "puntos": len(pts),
        "costa": "tierra de public/datos/contexto.geojson (cuencas hidrológicas rescatadas de ePOEL 2019)",
        "fecha": date.today().isoformat(),
    }, ensure_ascii=False, indent=2) + "\n")
    print(f"residuo {fino[1]:+} m E, {fino[2]:+} m N (costo {costo(0, 0):.1f} -> {fino[0]:.1f} m); "
          f"desplazamiento total {este:+} m E, {norte:+} m N con {len(usadas)} UGAs")


if __name__ == "__main__":
    main()
