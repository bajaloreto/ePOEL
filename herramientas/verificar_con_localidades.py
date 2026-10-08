"""Verifica la georreferencia de cada UGA digitalizada contra las localidades que rotula su mapa.

Los mapas de las fichas marcan localidades con un punto negro y su nombre. Se leen los nombres con OCR, se ubica el
punto junto a cada nombre y, con la transformación de los rótulos que produjo el polígono, se compara con la
coordenada de esa localidad en los datos rescatados de 2019 (contexto.geojson). Es un control independiente de la
escala y de la lectura de rótulos para los mapas del interior, que no muestran costa.

La comparación se hace SIN el desplazamiento de datum: esas localidades están en el mismo datum que los mapas del
Boletín (quedan ~200 m al sur de los polígonos corregidos; INC-014), así que no sirven para verificar el datum.

Resultado: datos/poel/digitalizacion/localidades.json, que usa validar_digitalizacion.py.

Uso: .venv/bin/python herramientas/verificar_con_localidades.py [ids...]
"""
import json
import re
import sys
import unicodedata

import cv2
import numpy as np
from pyproj import Transformer

import digitalizar_fichas as d
from boletin import DATOS, RAIZ

DIG = DATOS / "digitalizacion"
A_UTM = Transformer.from_crs("EPSG:4326", "EPSG:32612", always_xy=True)


def normalizar(nombre):
    n = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode().lower().strip()
    m = re.fullmatch(r"(.+),\s*(el|la|los|las)", n)  # «PICACHO, EL» -> «el picacho»
    if m:
        n = f"{m.group(2)} {m.group(1)}"
    return re.sub(r"[^a-z0-9 ]", "", re.sub(r"\s+", " ", n)).strip()


def localidades():
    ctx = json.loads((RAIZ / "public" / "datos" / "contexto.geojson").read_text())
    out = {}
    for f in ctx["features"]:
        if f["properties"].get("capa") == "localidad" and f["geometry"]["type"] == "Point":
            x, y = A_UTM.transform(*f["geometry"]["coordinates"][:2])
            out.setdefault(normalizar(f["properties"]["nombre"]), []).append((x, y))
    return out


def puntos_negros(rgb, f):
    """Centros de los puntos negros (símbolo de localidad): manchas oscuras, pequeñas y casi redondas."""
    gris = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    sat = rgb.max(axis=2).astype(int) - rgb.min(axis=2)
    oscuro = ((gris < 90) & (sat < 60)).astype(np.uint8)
    n, _, stats, centros = cv2.connectedComponentsWithStats(oscuro, connectivity=8)
    out = []
    for i in range(1, n):
        x, y, w, h, a = stats[i]
        if 6 * f * f <= a <= 90 * f * f and 0.6 <= w / h <= 1.6 and max(w, h) <= 12 * f and a >= 0.5 * w * h:
            out.append(centros[i])
    return np.array(out)


def verificar(doc, uga, locs, dx, dy):
    feat = json.loads((DIG / f"{uga}.geojson").read_text())["features"][0]
    geo = feat["properties"]["georreferencia"]
    f = geo["factor_render"]
    mapa = json.loads((DATOS / "ugas" / f"{geo['ficha_mapa']}.json").read_text())["mapa_ubicacion"]
    tmp = DIG / f"{uga}.loc.png"
    rgb = d.imagen_del_mapa(doc, mapa, tmp, f)
    textos = d.ocr(tmp)
    tmp.unlink()
    marco = d.marco_del_mapa(rgb)
    puntos = puntos_negros(rgb, f)
    if marco is None or not len(puntos):
        return {"estado": "sin-localidades"}
    x0, y0, x1, y1 = marco
    pares = []
    for t in textos:
        nombre = normalizar(t["texto"])
        if len(nombre) < 4 or nombre not in locs:
            continue
        cx, cy = t["x"], t["y"] + t["h"] / 2  # el punto va a la izquierda del nombre
        if not (x0 < t["x"] < x1 and y0 < t["y"] < y1):
            continue
        dist_px = np.hypot(puntos[:, 0] - cx, puntos[:, 1] - cy)
        k = int(np.argmin(dist_px))
        if dist_px[k] > 3 * t["h"] + 6 * f:
            continue
        px, py = puntos[k]
        x = geo["a_x"] * px + geo["b_x"] + dx
        y = geo["a_y"] * py + geo["b_y"] + dy
        real = min(locs[nombre], key=lambda p: (p[0] - x) ** 2 + (p[1] - y) ** 2)
        pares.append({"localidad": t["texto"], "error_m": round(float(np.hypot(real[0] - x, real[1] - y)), 1),
                      "dx_m": round(real[0] - x), "dy_m": round(real[1] - y)})
    if not pares:
        return {"estado": "sin-localidades"}
    errores = [p["error_m"] for p in pares]
    return {"estado": "medida", "precision_m": feat["properties"]["procedencia"]["precision_aprox_m"],
            "localidades": len(pares), "mediana_m": round(float(np.median(errores)), 1),
            "desplazamiento_mediano_m": [int(np.median([p["dx_m"] for p in pares])), int(np.median([p["dy_m"] for p in pares]))],
            "pares": pares}


def main():
    ids = sys.argv[1:] or sorted(p.stem for p in DIG.glob("*.geojson"))
    locs = localidades()
    dx = dy = 0.0  # ver la nota del encabezado (INC-014)
    doc = d.abrir()
    archivo = DIG / "localidades.json"
    salida = json.loads(archivo.read_text()) if archivo.exists() and sys.argv[1:] else {}
    for uga in ids:
        salida[uga] = verificar(doc, uga, locs, dx, dy)
        r = salida[uga]
        print(uga, r["estado"], r.get("localidades"), r.get("mediana_m"), r.get("desplazamiento_mediano_m"))
    archivo.write_text(json.dumps(dict(sorted(salida.items())), ensure_ascii=False, indent=1) + "\n")


if __name__ == "__main__":
    main()
