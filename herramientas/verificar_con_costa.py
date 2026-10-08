"""Verifica la georreferencia de cada UGA digitalizada contra la costa real.

Los mapas de las fichas pintan el mar en azul claro. Con la misma transformación (y desplazamiento de datum) que
produjo el polígono, la orilla de ese mar debe caer sobre la costa real (tierra de contexto.geojson). Es un control
independiente de los rótulos UTM y de la superficie de la ficha: confirma la escala y la posición del mapa completo.

Por cada UGA cuyo mapa muestra costa mide:
  - distancia mediana de la orilla del mapa a la costa real, sin mover nada;
  - el desplazamiento y el factor de escala que mejor la ajustan (si la mejora es grande, la georreferencia está mal).

Resultado: datos/poel/digitalizacion/costa.json, que usa validar_digitalizacion.py.

Uso: .venv/bin/python herramientas/verificar_con_costa.py [ids...]
"""
import json
import sys

import cv2
import numpy as np
from pyproj import Transformer
from shapely import transform
from shapely.geometry import shape
from shapely.ops import unary_union

import digitalizar_fichas as d
from boletin import DATOS, RAIZ

DIG = DATOS / "digitalizacion"
A_UTM = Transformer.from_crs("EPSG:4326", "EPSG:32612", always_xy=True)
MIN_PUNTOS = 60


def costa_real():
    ctx = json.loads((RAIZ / "public" / "datos" / "contexto.geojson").read_text())
    tierra = unary_union([shape(f["geometry"]) for f in ctx["features"] if f["properties"].get("capa") == "tierra"])
    return transform(tierra, lambda c: np.column_stack(A_UTM.transform(c[:, 0], c[:, 1]))).buffer(0).boundary


def orilla_del_mapa(rgb, marco, paso):
    """Píxeles de la orilla del mar (azul claro) dentro del marco del mapa principal, uno cada `paso` píxeles."""
    r, g, b = [rgb[:, :, i].astype(int) for i in range(3)]
    mar = ((b > 225) & (r > 160) & (r < 215) & (g > 190) & (g < 230)).astype(np.uint8)
    x0, y0, x1, y1 = marco
    m = np.zeros_like(mar)
    m[y0 + 6:y1 - 6, x0 + 6:x1 - 6] = mar[y0 + 6:y1 - 6, x0 + 6:x1 - 6]
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    borde = cv2.morphologyEx(m, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))
    borde[:y0 + 8, :] = 0; borde[y1 - 8:, :] = 0; borde[:, :x0 + 8] = 0; borde[:, x1 - 8:] = 0
    ys, xs = np.nonzero(borde)
    sel = (xs % paso == 0) | (ys % paso == 0)
    return np.column_stack([xs[sel], ys[sel]]).astype(float)


def verificar(doc, uga, costa, dx, dy):
    feat = json.loads((DIG / f"{uga}.geojson").read_text())["features"][0]
    geo = feat["properties"]["georreferencia"]
    mapa = json.loads((DATOS / "ugas" / f"{geo['ficha_mapa']}.json").read_text())["mapa_ubicacion"]
    tmp = DIG / f"{uga}.costa.png"
    rgb = d.imagen_del_mapa(doc, mapa, tmp, geo["factor_render"])
    tmp.unlink()
    marco = d.marco_del_mapa(rgb)
    if marco is None:
        return {"estado": "sin-marco"}
    px = orilla_del_mapa(rgb, marco, paso=3 * geo["factor_render"])
    if len(px) < MIN_PUNTOS:
        return {"estado": "sin-costa", "puntos": len(px)}
    utm = np.column_stack([geo["a_x"] * px[:, 0] + geo["b_x"] + dx, geo["a_y"] * px[:, 1] + geo["b_y"] + dy])
    if len(utm) > 1500:
        utm = utm[np.random.default_rng(0).choice(len(utm), 1500, replace=False)]
    dist = Distancias(costa, utm, margen=4000, resolucion=max(4.0, abs(geo["a_x"]) / 2))
    base = dist(utm)
    mediana = float(np.median(base))
    precision = feat["properties"]["procedencia"]["precision_aprox_m"]
    if mediana > 1500:
        # La orilla del mapa no tiene costa real cerca: la capa de costa no cubre esa zona (p. ej. la bahía junto a la 1a)
        return {"estado": "sin-costa-de-referencia", "puntos": int(len(utm)), "mediana_m": round(mediana)}
    trunc = 3000.0
    costo = lambda p: float(np.mean(np.minimum(dist(p), trunc)))
    # Mejor ajuste por desplazamiento y escala alrededor del centro de la orilla
    c = utm.mean(axis=0)
    paso = max(abs(geo["a_x"]) * 2, 10)
    mejor = (costo(utm), 0.0, 0.0, 1.0)
    for s in np.round(np.arange(0.5, 1.5001, 0.025), 3):
        esc = c + (utm - c) * s
        for ex in np.arange(-12, 13) * paso:
            for ey in np.arange(-12, 13) * paso:
                k = costo(esc + [ex, ey])
                if k < mejor[0] - 1e-9:
                    mejor = (k, float(ex), float(ey), float(s))
    return {"estado": "medida", "puntos": int(len(utm)), "precision_m": precision,
            "mediana_m": round(mediana, 1), "costo_m": round(costo(utm), 1),
            "mejor_ajuste": {"costo_m": round(mejor[0], 1), "desplazamiento_m": [round(mejor[1]), round(mejor[2])],
                             "escala": mejor[3]}}


class Distancias:
    """Distancia a la costa precalculada en una malla (transformada de distancia de OpenCV) alrededor de los puntos."""

    def __init__(self, costa, puntos, margen, resolucion):
        from shapely.geometry import box
        self.x0, self.y0 = puntos.min(axis=0) - margen
        x1, y1 = puntos.max(axis=0) + margen
        self.r = resolucion
        ancho, alto = int((x1 - self.x0) / self.r) + 1, int((y1 - self.y0) / self.r) + 1
        lienzo = np.full((alto, ancho), 255, np.uint8)
        tramo = costa.intersection(box(self.x0, self.y0, x1, y1))
        for linea in getattr(tramo, "geoms", [tramo]):
            if linea.is_empty or linea.geom_type not in ("LineString", "LinearRing"):
                continue
            c = np.array(linea.coords)
            pix = np.column_stack([(c[:, 0] - self.x0) / self.r, (y1 - c[:, 1]) / self.r]).round().astype(np.int32)
            cv2.polylines(lienzo, [pix], False, 0, 1)
        self.y1 = y1
        self.d = cv2.distanceTransform(lienzo, cv2.DIST_L2, 5) * self.r
        if not (lienzo == 0).any():
            self.d[:] = 1e9

    def __call__(self, p):
        i = np.clip(((self.y1 - p[:, 1]) / self.r).round().astype(int), 0, self.d.shape[0] - 1)
        j = np.clip(((p[:, 0] - self.x0) / self.r).round().astype(int), 0, self.d.shape[1] - 1)
        return self.d[i, j]


def main():
    ids = sys.argv[1:] or sorted(p.stem for p in DIG.glob("*.geojson"))
    costa = costa_real()
    dx, dy = d.desplazamiento_datum()
    doc = d.abrir()
    archivo = DIG / "costa.json"
    salida = json.loads(archivo.read_text()) if archivo.exists() and sys.argv[1:] else {}
    for uga in ids:
        salida[uga] = verificar(doc, uga, costa, dx, dy)
        print(uga, json.dumps(salida[uga], ensure_ascii=False))
    archivo.write_text(json.dumps(dict(sorted(salida.items())), ensure_ascii=False, indent=1) + "\n")


if __name__ == "__main__":
    main()
