"""Digitaliza (borrador) el polígono de una UGA a partir del mapa de ubicación de su ficha en el Boletín.

Método (ADR 0002):
  1. Extrae el mapa de la ficha (imagen del PDF).
  2. Lee con OCR (Vision de macOS, herramientas/ocr) los rótulos UTM del marco y ajusta una
     transformación píxel -> UTM 12N por mínimos cuadrados.
  3. Separa el relleno rojo de la UGA (descarta líneas finas del mismo color, como carreteras)
     y lo vectoriza.
  4. Reproyecta a WGS84 y compara el área con la superficie declarada en la ficha.

Resultado: datos/poel/digitalizacion/<id>.geojson + <id>.png (diagnóstico). Es un BORRADOR
que debe revisarse en QGIS antes de considerarse válido.

Uso: .venv/bin/python herramientas/digitalizar_fichas.py 12 1a 45
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
import pymupdf
from pyproj import Transformer
from shapely.geometry import Polygon, MultiPolygon, mapping, shape
from shapely import transform as transformar
from shapely.ops import unary_union

from boletin import DATOS, RAIZ, abrir

OCR = RAIZ / "herramientas" / "ocr" / "ocr"
SALIDA = DATOS / "digitalizacion"
# Datum del POEL: UTM zona 12N (ITRF92 ≈ WGS84 a nivel submétrico para esta escala)
A_WGS84 = Transformer.from_crs("EPSG:32612", "EPSG:4326", always_xy=True)
ESCALA_RENDER = 3  # para mapas vectoriales: píxeles por punto PDF
# El trazo de contorno de la UGA y el seguimiento por centros de píxel dejan fuera ~1.1–1.7 px de borde
# (medido en el piloto: UGAs 12, 1a y 45). Se compensa con un margen fijo igual para todas las fichas;
# la comparación con la superficie de la ficha sigue siendo un control independiente.
CORRECCION_BORDE_PX = 1.4


def ocr(png):
    if not OCR.exists():
        raise SystemExit("Compila el OCR: swiftc -O herramientas/ocr/ocr.swift -o herramientas/ocr/ocr")
    return json.loads(subprocess.run([str(OCR), str(png)], capture_output=True, text=True, check=True).stdout)


def rotulos_utm(textos):
    """Rótulos del marco: 6 dígitos = Este (x), 7 dígitos que empiezan con 2 = Norte (y)."""
    este, norte = [], []
    for t in textos:
        s = re.sub(r"\D", "", t["texto"])
        cx, cy = t["x"] + t["w"] / 2, t["y"] + t["h"] / 2
        if len(s) == 6 and t["h"] < t["w"] and t.get("conf", 1) > 0.5:
            este.append((cx, int(s), cy))
        elif len(s) == 7 and s.startswith("2") and t.get("conf", 1) > 0.5:
            norte.append((cy, int(s), cx))
    return este, norte


def ajuste(pares):
    """Ajuste lineal píxel -> metros. Devuelve (pendiente, ordenada, residuo máximo en m)."""
    px = np.array([p[0] for p in pares]); m = np.array([p[1] for p in pares], dtype=float)
    if len(set(m)) < 2:
        raise ValueError("se necesitan al menos dos rótulos distintos por eje")
    a, b = np.polyfit(px, m, 1)
    return a, b, float(np.max(np.abs(a * px + b - m)))


def mascara_uga(rgb, marco):
    """Relleno rojo oscuro de la UGA dentro del marco del mapa principal."""
    # El relleno de las UGAs en las fichas es RGB (168, 0, 0); las carreteras usan un rojo más oscuro.
    r, g, b = [rgb[:, :, i].astype(int) for i in range(3)]
    rojo = ((r >= 150) & (r <= 190) & (g < 25) & (b < 25)).astype(np.uint8) * 255
    x0, y0, x1, y1 = marco
    recorte = np.zeros_like(rojo)
    recorte[y0:y1, x0:x1] = rojo[y0:y1, x0:x1]
    # Cerrar los huecos que dejan rótulos, puntos y líneas dibujados encima de la UGA
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    return cv2.morphologyEx(recorte, cv2.MORPH_CLOSE, k, iterations=2)


def vectorizar(mascara, min_px=60):
    contornos, jerarquia = cv2.findContours(mascara, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if jerarquia is None:
        return None
    poligonos = []
    for i, c in enumerate(contornos):
        if jerarquia[0][i][3] != -1 or cv2.contourArea(c) < min_px or len(c) < 3:
            continue
        huecos = [contornos[j][:, 0, :] for j in range(len(contornos))
                  if jerarquia[0][j][3] == i and cv2.contourArea(contornos[j]) > min_px and len(contornos[j]) >= 3]
        poligonos.append(Polygon(c[:, 0, :], [h for h in huecos]).buffer(0))
    return unary_union(poligonos) if poligonos else None


def imagen_del_mapa(doc, mapa, tmp):
    if mapa["tipo"] == "imagen":
        pix = pymupdf.Pixmap(doc, mapa["xref"])
        if pix.n - pix.alpha != 3:
            pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
    else:  # vectorial: se rasteriza la región del mapa a alta resolución
        x0, y0, x1, y1 = mapa["bbox"]
        clip = pymupdf.Rect(x0 - 15, y0 - 15, x1 + 15, y1 + 15)
        pix = doc[mapa["pagina_boletin"] - 1].get_pixmap(matrix=pymupdf.Matrix(ESCALA_RENDER, ESCALA_RENDER), clip=clip)
    pix.save(tmp)
    rgb = cv2.cvtColor(cv2.imread(str(tmp)), cv2.COLOR_BGR2RGB)
    return rgb


def digitalizar(doc, uga):
    ficha = json.loads((DATOS / "ugas" / f"{uga}.json").read_text())
    mapa = ficha["mapa_ubicacion"]
    SALIDA.mkdir(parents=True, exist_ok=True)
    png = SALIDA / f"{uga}.mapa.png"
    rgb = imagen_del_mapa(doc, mapa, png)
    este, norte = rotulos_utm(ocr(png))
    # Si un eje tiene un solo valor rotulado, se usa la escala del otro (los mapas tienen píxeles cuadrados)
    if len({v for _, v, _ in este}) >= 2:
        ax, bx, res_x = ajuste(este)
    else:
        ay, _, _ = ajuste(norte)
        ax = -ay
        bx = float(np.mean([v - ax * px for px, v, _ in este])); res_x = 0.0
    if len({v for _, v, _ in norte}) >= 2:
        ay, by, res_y = ajuste(norte)
    else:
        ay = -ax
        by = float(np.mean([v - ay * px for px, v, _ in norte])); res_y = 0.0
    # Marco del mapa principal: entre los rótulos Norte izquierdos y derechos, y los Este de arriba y abajo
    xs_norte = sorted(p[2] for p in norte)
    x0 = int(min(xs_norte)) + 8
    x1 = int(max(x for x in xs_norte if x < rgb.shape[1] * 0.85)) - 8
    ys_este = sorted(p[2] for p in este)
    y0, y1 = int(min(ys_este)) + 8, int(max(ys_este)) - 8
    geom_px = vectorizar(mascara_uga(rgb, (x0, y0, x1, y1)))
    if geom_px is None:
        return {"id": uga, "estado": "sin-relleno-rojo"}
    utm = transformar(geom_px, lambda c: np.column_stack([ax * c[:, 0] + bx, ay * c[:, 1] + by]))
    utm = utm.buffer(abs(ax) * CORRECCION_BORDE_PX, join_style="mitre", mitre_limit=3)
    utm = utm.simplify(abs(ax) * 0.75)  # tolerancia ~ 3/4 de píxel
    area_ha = utm.area / 10_000
    wgs = transformar(utm, lambda c: np.column_stack(A_WGS84.transform(c[:, 0], c[:, 1])))
    m_por_px = (abs(ax) + abs(ay)) / 2
    resultado = {
        "id": uga,
        "estado": "borrador",
        "metros_por_pixel": round(m_por_px, 1),
        "precision_estimada_m": round(m_por_px * 2, 0),
        "residuo_georreferencia_m": round(max(res_x, res_y), 1),
        "rotulos_utm": {"este": len(este), "norte": len(norte)},
        "area_digitalizada_ha": round(area_ha, 2),
        "superficie_ficha_ha": ficha["superficie_ha"],
        "diferencia_area_pct": round(100 * (area_ha - ficha["superficie_ha"]) / ficha["superficie_ha"], 1),
        "poligonos": len(getattr(wgs, "geoms", [wgs])),
    }
    feature = {
        "type": "Feature",
        "properties": {
            "uga": uga,
            "politica": ficha["politica"],
            "procedencia": {
                "metodo": "digitalizacion-semiautomatica",
                "fuente": f"Mapa de ubicación de la ficha UGA {uga}, Boletín Oficial No. 12 (12-mar-2014), p. {mapa['pagina_boletin']} del PDF",
                "datum_supuesto": "UTM 12N (ITRF92 ≈ WGS84)",
                "correccion_borde_px": CORRECCION_BORDE_PX,
                "precision_aprox_m": resultado["precision_estimada_m"],
                "revisada_en_qgis": False,
            },
            "control": {k: resultado[k] for k in ("residuo_georreferencia_m", "area_digitalizada_ha",
                                                    "superficie_ficha_ha", "diferencia_area_pct")},
        },
        "geometry": mapping(wgs),
    }
    (SALIDA / f"{uga}.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": [feature]},
                                                      ensure_ascii=False) + "\n")
    # Imagen de diagnóstico: contorno digitalizado sobre el mapa original
    diag = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    for g in getattr(geom_px, "geoms", [geom_px]):
        cv2.polylines(diag, [np.array(g.exterior.coords, dtype=np.int32)], True, (255, 160, 0), 2)
    cv2.rectangle(diag, (x0, y0), (x1, y1), (0, 200, 0), 1)
    cv2.imwrite(str(SALIDA / f"{uga}.png"), diag)
    png.unlink()
    return resultado


def main():
    doc = abrir()
    ugas = sys.argv[1:]
    if not ugas:
        raise SystemExit(__doc__)
    for uga in ugas:
        try:
            print(json.dumps(digitalizar(doc, uga), ensure_ascii=False))
        except Exception as e:  # se reporta y se sigue con la siguiente
            print(json.dumps({"id": uga, "estado": "error", "detalle": str(e)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
