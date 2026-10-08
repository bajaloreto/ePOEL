"""Valida las UGAs digitalizadas y decide cuáles usa el sitio.

Controles por UGA:
  - Área: diferencia con la superficie de la ficha (independiente cuando la escala sale de los rótulos UTM); salvo
    en las fichas de INC-013, cuya superficie no corresponde a su mapa.
  - Ubicación: el polígono debe caer en el Municipio de Loreto (a ≤30 km de la tierra de contexto, por las islas).
  - Escala por superficie: como el área no es un control independiente, la ubicación se corrobora con el
    polígono de 2019 (centroides a ≤500 m o IoU ≥ 0.3); si no hay de 2019, queda para revisión.
  - Duplicado: no debe ser casi el mismo polígono que otra UGA (IoU > 0.6), señal de un mapa equivocado.

Estados: «aceptada» (se usa), «revisar» (se usa con aviso de revisión pendiente) y «rechazada» (no se usa).
Resultado: datos/poel/digitalizacion/validacion.json.

Uso: .venv/bin/python herramientas/validar_digitalizacion.py
"""
import json

import numpy as np
from pyproj import Transformer
from shapely import transform
from shapely.geometry import shape
from shapely.ops import unary_union

from boletin import DATOS, RAIZ
from construir_geodatos import geometrias_2019
from digitalizar_fichas import AREA_DUDOSA

DIGITALIZACION = DATOS / "digitalizacion"
A_UTM = Transformer.from_crs("EPSG:4326", "EPSG:32612", always_xy=True)


def utm(g):
    return transform(g, lambda c: np.column_stack(A_UTM.transform(c[:, 0], c[:, 1])))


def main():
    ctx = json.loads((RAIZ / "public" / "datos" / "contexto.geojson").read_text())
    tierra = unary_union([utm(shape(f["geometry"])) for f in ctx["features"] if f["properties"].get("capa") == "tierra"])
    v2019 = {k: utm(g).buffer(0) for k, g in geometrias_2019().items()}
    lote = {r["id"]: r for r in map(json.loads, (DIGITALIZACION / "lote.jsonl").read_text().splitlines())}
    geoms, ctrl = {}, {}
    for p in sorted(DIGITALIZACION.glob("*.geojson")):
        feat = json.loads(p.read_text())["features"][0]
        geoms[p.stem] = utm(shape(feat["geometry"])).buffer(0)
        ctrl[p.stem] = feat["properties"]["control"]

    salida = {}
    for uga, r in sorted(lote.items()):
        if uga not in geoms:
            salida[uga] = {"estado": "sin-digitalizar", "motivos": [r.get("detalle") or r["estado"]]}
            continue
        g, c, motivos = geoms[uga], ctrl[uga], []
        estado = "aceptada"
        d = abs(c["diferencia_area_pct"])
        previa = v2019.get(uga)
        if uga in AREA_DUDOSA:
            motivos.append("superficie de la ficha incompatible con su mapa (INC-013); no se usa como control")
            if previa is None or g.intersection(previa).area / g.union(previa).area < 0.5:
                estado = "revisar"
        elif d > 5:
            estado = "revisar"; motivos.append(f"área {c['diferencia_area_pct']:+.1f} % respecto a la ficha")
        if g.distance(tierra) > 30_000:
            estado = "rechazada"; motivos.append("fuera del Municipio de Loreto: rótulos UTM mal leídos")
        if previa is not None:
            iou = g.intersection(previa).area / g.union(previa).area
            dist = g.centroid.distance(previa.centroid)
        else:
            iou = dist = None
        if c.get("escala_por_superficie"):
            if previa is not None and (dist <= 500 or iou >= 0.3):
                motivos.append("escala por superficie; ubicación corroborada con 2019")
            elif estado != "rechazada":
                estado = "revisar"; motivos.append("escala por superficie sin corroborar la ubicación")
        # Los traslapes parciales se resuelven al construir el mapa (cede el polígono menos preciso); aquí solo se
        # marcan los que parecen el mismo polígono dos veces, señal de un mapa equivocado (como en INC-012)
        for otra, h in geoms.items():
            if otra != uga and g.intersects(h):
                iou_otra = g.intersection(h).area / g.union(h).area
                if iou_otra > 0.6 and estado != "rechazada":
                    estado = "revisar"; motivos.append(f"casi el mismo polígono que la UGA {otra} (IoU {iou_otra:.2f})")
        salida[uga] = {"estado": estado, "motivos": motivos,
                       "iou_2019": None if iou is None else round(iou, 2),
                       "distancia_centroide_2019_m": None if dist is None else round(dist)}
    (DIGITALIZACION / "validacion.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1) + "\n")
    cuenta = {}
    for v in salida.values():
        cuenta[v["estado"]] = cuenta.get(v["estado"], 0) + 1
    print(cuenta)
    for uga, v in salida.items():
        if v["estado"] in ("revisar", "rechazada"):
            print(uga, v["estado"], "; ".join(v["motivos"]))


if __name__ == "__main__":
    main()
