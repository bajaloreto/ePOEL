"""Valida las UGAs digitalizadas y decide cuáles usa el sitio.

Controles por UGA:
  - Área: diferencia con la superficie de la ficha (independiente cuando la escala sale de los rótulos UTM); salvo
    en las fichas de INC-013, cuya superficie no corresponde a su mapa.
  - Ubicación: el polígono debe caer en el Municipio de Loreto (a ≤30 km de la tierra de contexto, por las islas).
  - Escala por superficie: como el área no es un control independiente, la ubicación se corrobora con el
    polígono de 2019 (centroides a ≤500 m o IoU ≥ 0.3); si no hay de 2019, queda para revisión.
  - Posición (costa.json y localidades.json): la orilla del mapa frente a la costa real y las localidades rotuladas
    frente a sus coordenadas. Dentro de 2 × la precisión confirma (y acepta una UGA por revisar); más allá de 3 ×
    la pone en duda. Una localidad a más de 1 km delata un rótulo mal leído. La costa y 3 o más localidades pesan
    igual; si discrepan, la UGA conserva su estado y queda la nota.
  - Duplicado: no debe ser casi el mismo polígono que otra UGA (IoU > 0.6), señal de un mapa equivocado.

Estados: «aceptada» (se usa), «revisar» (se usa con aviso de revisión pendiente) y «rechazada» (no se usa).
Una revisión manual en QGIS (datos/poel/digitalizacion/revisadas/) prevalece sobre estos controles.
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

    archivo_costa = DIGITALIZACION / "costa.json"
    costa = json.loads(archivo_costa.read_text()) if archivo_costa.exists() else {}
    archivo_loc = DIGITALIZACION / "localidades.json"
    locs = json.loads(archivo_loc.read_text()) if archivo_loc.exists() else {}
    salida = {}
    for uga, r in sorted(lote.items()):
        revisada = DIGITALIZACION / "revisadas" / f"{uga}.geojson"
        if revisada.exists():  # la revisión manual en QGIS manda (aplicar_revision_qgis.py)
            p = json.loads(revisada.read_text())["features"][0]["properties"]
            salida[uga] = {"estado": "rechazada" if p["revision"] == "descartar" else "aceptada",
                           "motivos": [f"revisión en QGIS ({p['fecha']}): {p['revision']}" + (f". {p['notas']}" if p["notas"] else "")],
                           "revision_qgis": p["revision"]}
            continue
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
        # Posición del mapa completo, con controles independientes de rótulos y superficie (el área no detecta un mapa
        # trasladado): la costa real (verificar_con_costa.py) y las localidades rotuladas (verificar_con_localidades.py).
        if estado != "rechazada":
            veredictos = []  # (fuerza, ok, texto)
            cc = costa.get(uga, {})
            if cc.get("estado") == "medida":
                prec = cc["precision_m"]
                ok = cc["mediana_m"] <= max(2 * prec, 40)
                mal = cc["mediana_m"] > max(3 * prec, 100)
                if ok or mal:
                    aj = cc["mejor_ajuste"]
                    veredictos.append((2, ok, f"costa del mapa a {cc['mediana_m']:.0f} m de la real" + ("" if ok else
                        f" (ajusta mejor con {aj['desplazamiento_m'][0]:+} m E, {aj['desplazamiento_m'][1]:+} m N y escala {aj['escala']})")))
            ll = locs.get(uga, {})
            if ll.get("estado") == "medida":
                prec = ll["precision_m"]
                pares = ll["pares"]
                lejos = [q for q in pares if q["error_m"] > 1000]
                # Dos o más localidades lejos con el mismo corrimiento delatan un rótulo mal leído; una sola lejana suele
                # ser un homónimo (la localidad del mapa no está en la capa de referencia) y se descarta.
                coinciden = [q for q in lejos if sum(1 for r in lejos if abs(r["dx_m"] - q["dx_m"]) < 1000
                                                   and abs(r["dy_m"] - q["dy_m"]) < 1000) >= 2]
                cerca = [q["error_m"] for q in pares if q["error_m"] <= 5000]
                n = len(cerca)
                med = float(np.median(cerca)) if cerca else None
                if coinciden:
                    veredictos.append((3, False, f"{len(coinciden)} localidades corridas ~{coinciden[0]['error_m'] / 1000:.0f} km "
                                                 "en la misma dirección: posible rótulo mal leído"))
                elif n >= 3 and med <= max(2 * prec, 60):
                    veredictos.append((2, True, f"{n} localidades a {med:.0f} m (mediana)"))
                elif n >= 3 and med > max(3 * prec, 150):
                    veredictos.append((2, False, f"{n} localidades a {med:.0f} m (mediana)"))
                elif n == 2 and max(cerca) <= max(2 * prec, 60):  # con dos, ambas deben coincidir
                    veredictos.append((1, True, f"2 localidades a {min(cerca):.0f} y {max(cerca):.0f} m"))
                elif n == 2 and min(cerca) > max(3 * prec, 150):
                    veredictos.append((1, False, f"2 localidades a {min(cerca):.0f} y {max(cerca):.0f} m"))
            if iou is not None and iou >= 0.8:
                veredictos.append((1, True, f"coincide con el polígono de 2019 (IoU {iou:.2f})"))
            if veredictos:
                fuerza = max(v[0] for v in veredictos)
                decisivos = [v for v in veredictos if v[0] == fuerza]
                if all(v[1] for v in decisivos):
                    if estado == "revisar":
                        estado = "aceptada"
                    motivos.append("posición confirmada: " + "; ".join(v[2] for v in veredictos))
                elif not any(v[1] for v in decisivos):
                    estado = "revisar"
                    motivos.append("posición en duda: " + "; ".join(v[2] for v in veredictos))
                else:  # controles igual de fuertes en desacuerdo: no cambia el estado, se deja constancia
                    motivos.append("controles de posición en desacuerdo: " + "; ".join(v[2] for v in veredictos))
            else:
                motivos.append("sin verificación independiente de la posición")
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
