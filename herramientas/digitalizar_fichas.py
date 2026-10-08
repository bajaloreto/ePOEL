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

Uso: .venv/bin/python herramientas/digitalizar_fichas.py 12 1a 45   (lote completo: ver datos/poel/digitalizacion/README.md)
"""
import json
import re
from itertools import combinations
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
A_WGS84 = Transformer.from_crs("EPSG:32612", "EPSG:4326", always_xy=True)
# Datum (INC-011): la leyenda de los mapas dice «WGS84, elipsoide Clarke 1866». Las coordenadas de los rótulos
# se tratan como UTM 12N y se les suma el desplazamiento que ajusta herramientas/ajustar_datum.py contra la costa.
DATUM = SALIDA / "datum.json"


def desplazamiento_datum():
    if DATUM.exists():
        d = json.loads(DATUM.read_text())
        return d["desplazamiento_m"]["este"], d["desplazamiento_m"]["norte"]
    return 0.0, 0.0


# INC-012: el Boletín imprime en algunas fichas el mapa de otra UGA. MAPA_EN_FICHA dice en qué ficha está el mapa
# verdadero de una UGA; SIN_MAPA_PROPIO son las fichas cuyo mapa es de otra UGA y no tienen el propio.
MAPA_EN_FICHA = {"7a": "6"}
SIN_MAPA_PROPIO = {"6"}
ESCALA_RENDER = 3  # para mapas vectoriales: píxeles por punto PDF
# El trazo de contorno de la UGA y el seguimiento por centros de píxel dejan fuera ~1.1–1.7 px de borde
# (medido en el piloto: UGAs 12, 1a y 45). Se compensa con un margen fijo igual para todas las fichas;
# la comparación con la superficie de la ficha sigue siendo un control independiente.
CORRECCION_BORDE_PX = 1.4


def ocr(png):
    if not OCR.exists():
        raise SystemExit("Compila el OCR: swiftc -O herramientas/ocr/ocr.swift -o herramientas/ocr/ocr")
    return json.loads(subprocess.run([str(OCR), str(png)], capture_output=True, text=True, check=True).stdout)


# Intervalo plausible de coordenadas UTM 12N para el Municipio de Loreto (con margen): descarta lecturas como
# «143500» en lugar de «443500», que desplazarían la UGA cientos de kilómetros.
ESTE_LORETO = (380_000, 560_000)
NORTE_LORETO = (2_740_000, 2_990_000)


def rotulos_utm(textos):
    """Rótulos del marco: 6 dígitos = Este (x), 7 dígitos que empiezan con 2 = Norte (y)."""
    este, norte = [], []
    for t in textos:
        s = re.sub(r"\D", "", t["texto"])
        cx, cy = t["x"] + t["w"] / 2, t["y"] + t["h"] / 2
        if len(s) == 6 and t["h"] < t["w"] and t.get("conf", 1) > 0.5 and ESTE_LORETO[0] <= int(s) <= ESTE_LORETO[1]:
            este.append((cx, int(s), cy))
        elif len(s) == 7 and t.get("conf", 1) > 0.5 and NORTE_LORETO[0] <= int(s) <= NORTE_LORETO[1]:
            norte.append((cy, int(s), cx))
    return este, norte


def limpiar_eje(candidatos, signo):
    """Corrige y filtra los rótulos de un eje.

    Los rótulos del marco son múltiplos de 500 m: una lectura a ≤300 m de uno se redondea (el OCR confunde 5 y 3).
    Luego se busca la recta píxel -> metros con más rótulos coherentes (signo +1 para el Este, que crece a la
    derecha; −1 para el Norte, que decrece hacia abajo) y se descartan las lecturas que no caen en ella
    (p. ej. «2245000» en lugar de «2845000»).
    """
    limpios = []
    for px, v, otro in candidatos:
        r = round(v / 500) * 500
        if abs(r - v) <= 300:
            limpios.append((px, r, otro))
    mejor = None
    for (p1, v1, _), (p2, v2, _) in combinations(limpios, 2):
        if v1 == v2 or abs(p1 - p2) < 5:
            continue
        a = (v2 - v1) / (p2 - p1)
        if a * signo <= 0:
            continue
        b = v1 - a * p1
        dentro = [c for c in limpios if abs(a * c[0] + b - c[1]) < abs(a) * 6]
        clave = (len({c[1] for c in dentro}), len(dentro))
        if mejor is None or clave > mejor[0]:
            mejor = (clave, dentro)
    if mejor:
        return mejor[1]
    if not limpios:
        return []
    # Un solo valor: se conserva el más repetido
    moda = max({v for _, v, _ in limpios}, key=lambda v: sum(1 for c in limpios if c[1] == v))
    return [c for c in limpios if c[1] == moda]


def ajuste(pares):
    """Ajuste lineal píxel -> metros. Devuelve (pendiente, ordenada, residuo máximo en m)."""
    px = np.array([p[0] for p in pares]); m = np.array([p[1] for p in pares], dtype=float)
    if len(set(m)) < 2:
        raise ValueError("se necesitan al menos dos rótulos distintos por eje")
    a, b = np.polyfit(px, m, 1)
    return a, b, float(np.max(np.abs(a * px + b - m)))


def mascara_uga(rgb, marco, f=1):
    """Relleno rojo oscuro de la UGA dentro del marco del mapa principal."""
    # El relleno de las UGAs en las fichas es RGB (168, 0, 0); las carreteras usan un rojo más oscuro.
    r, g, b = [rgb[:, :, i].astype(int) for i in range(3)]
    rojo = ((r >= 140) & (r <= 200) & (g < 45) & (b < 45) & (r - g > 110)).astype(np.uint8) * 255
    x0, y0, x1, y1 = marco
    recorte = np.zeros_like(rojo)
    recorte[y0:y1, x0:x1] = rojo[y0:y1, x0:x1]
    # Cerrar los huecos que dejan rótulos, puntos y líneas dibujados encima de la UGA
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    return cv2.morphologyEx(recorte, cv2.MORPH_CLOSE, k, iterations=2 * f)


def marco_del_mapa(rgb):
    """Rectángulo del mapa principal: el marco más grande formado por líneas oscuras largas, a la izquierda."""
    alto, ancho = rgb.shape[:2]
    oscuro = (cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY) < 110).astype(np.uint8) * 255
    h = cv2.morphologyEx(oscuro, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (int(ancho * 0.25), 1)))
    v = cv2.morphologyEx(oscuro, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, int(alto * 0.25))))
    lineas = cv2.dilate(h | v, np.ones((3, 3), np.uint8))
    contornos, _ = cv2.findContours(lineas, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cajas = [cv2.boundingRect(c) for c in contornos]
    cajas = [(x, y, w, h) for x, y, w, h in cajas if w > ancho * 0.3 and h > alto * 0.4 and x < ancho * 0.3]
    if not cajas:
        return None
    x, y, w, h = max(cajas, key=lambda c: c[2] * c[3])
    return x + 4, y + 4, x + w - 4, y + h - 4


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


def factores_render(mapa):
    """Los mapas de baja resolución (~500 px) se prueban también al doble: el OCR a veces lee mejor los rótulos así."""
    return (1, 2) if mapa["tipo"] == "imagen" and mapa["pixeles"][0] < 600 else (1,)


def imagen_del_mapa(doc, mapa, tmp, f=1):
    if mapa["tipo"] == "imagen":
        # Algunos mapas vienen partidos en varias imágenes contiguas: se renderiza la región que forman juntas,
        # a la resolución nativa de la imagen para que los píxeles conserven su tamaño original.
        pagina = doc[mapa["pagina_boletin"] - 1]
        region = pymupdf.Rect(mapa["bbox"])
        piezas = [pymupdf.Rect(i["bbox"]) for i in pagina.get_image_info()]
        crecio = True
        while crecio:
            crecio = False
            for r in piezas:
                if not region.contains(r) and (r + (-3, -3, 3, 3)).intersects(region):
                    region |= r; crecio = True
        escala = mapa["pixeles"][0] / (mapa["bbox"][2] - mapa["bbox"][0]) * f
        pix = pagina.get_pixmap(matrix=pymupdf.Matrix(escala, escala), clip=region)
    else:  # vectorial: se rasteriza la región del mapa a alta resolución
        x0, y0, x1, y1 = mapa["bbox"]
        clip = pymupdf.Rect(x0 - 15, y0 - 15, x1 + 15, y1 + 15)
        pix = doc[mapa["pagina_boletin"] - 1].get_pixmap(matrix=pymupdf.Matrix(ESCALA_RENDER, ESCALA_RENDER), clip=clip)
    pix.save(tmp)
    rgb = cv2.cvtColor(cv2.imread(str(tmp)), cv2.COLOR_BGR2RGB)
    return rgb


def digitalizar(doc, uga):
    """Prueba cada resolución y escribe el mejor resultado: escala por rótulos antes que por superficie y,
    entre esos, el área más cercana a la de la ficha."""
    ficha = json.loads((DATOS / "ugas" / f"{uga}.json").read_text())
    SALIDA.mkdir(parents=True, exist_ok=True)
    for viejo in (SALIDA / f"{uga}.geojson", SALIDA / f"{uga}.png"):
        viejo.unlink(missing_ok=True)
    if uga in SIN_MAPA_PROPIO:
        return {"id": uga, "estado": "sin-mapa-propio", "detalle": "la ficha trae el mapa de otra UGA (INC-012)"}
    origen = MAPA_EN_FICHA.get(uga, uga)
    mapa = json.loads((DATOS / "ugas" / f"{origen}.json").read_text())["mapa_ubicacion"]
    intentos = [intento(doc, uga, ficha, mapa, f) for f in factores_render(mapa)]
    validos = [i for i in intentos if i[0]["estado"] == "borrador"]
    if not validos:
        return intentos[0][0]
    if all(abs(i[0]["diferencia_area_pct"]) > 15 for i in validos):
        # Área incompatible con la ficha: georreferencia o relleno equivocados; no se guarda
        mejor = min(validos, key=lambda i: abs(i[0]["diferencia_area_pct"]))[0]
        return {**mejor, "estado": "rechazada-area"}
    resultado, feature, diag = min(validos, key=lambda i: (abs(i[0]["diferencia_area_pct"]) > 15,
                                                          i[0]["escala_por_superficie"],
                                                          -i[0]["ejes_con_escala_propia"],
                                                          abs(i[0]["diferencia_area_pct"])))
    (SALIDA / f"{uga}.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": [feature]},
                                                      ensure_ascii=False) + "\n")
    cv2.imwrite(str(SALIDA / f"{uga}.png"), diag)
    return resultado


def intento(doc, uga, ficha, mapa, f):
    origen = MAPA_EN_FICHA.get(uga, uga)
    png = SALIDA / f"{uga}.mapa.png"
    rgb = imagen_del_mapa(doc, mapa, png, f)
    textos = ocr(png)
    png.unlink()
    este, norte = rotulos_utm(textos)
    este, norte = limpiar_eje(este, +1), limpiar_eje(norte, -1)
    if not este or not norte:
        return {"id": uga, "estado": "sin-rotulos", "rotulos_utm": {"este": len(este), "norte": len(norte)}}, None, None
    escala_por_superficie = False
    # Marco del mapa principal; si no se detecta, se deduce de los rótulos
    marco = marco_del_mapa(rgb)
    if marco is None:
        xs_norte = sorted(p[2] for p in norte)
        ys_este = sorted(p[2] for p in este)
        marco = (int(min(xs_norte)) + 8, int(min(ys_este)) + 8,
                 int(max(x for x in xs_norte if x < rgb.shape[1] * 0.85)) - 8, int(max(ys_este)) - 8)
    x0, y0, x1, y1 = marco
    borde_px = CORRECCION_BORDE_PX * f  # la corrección está calibrada en píxeles nativos
    mascara = mascara_uga(rgb, marco, f)
    geom_px = vectorizar(mascara, min_px=60 * f * f)
    if geom_px is None:
        return {"id": uga, "estado": "sin-relleno-rojo"}, None, None
    # Si un eje tiene un solo valor rotulado, se usa la escala del otro (los mapas tienen píxeles cuadrados)
    dos_x, dos_y = len({v for _, v, _ in este}) >= 2, len({v for _, v, _ in norte}) >= 2
    if dos_x:
        ax, bx, res_x = ajuste(este)
    if dos_y:
        ay, by, res_y = ajuste(norte)
    if not dos_x and not dos_y:
        # Un solo rótulo por eje: la escala sale de la superficie declarada en la ficha (el control de área
        # deja de ser independiente y se marca así en la procedencia)
        area_px = geom_px.buffer(borde_px, join_style="mitre", mitre_limit=3).area
        ax = (ficha["superficie_ha"] * 10_000 / area_px) ** 0.5
        ay = -ax
        escala_por_superficie = True
    if not dos_x:
        ax = -ay if dos_y else ax
        bx = float(np.mean([v - ax * px for px, v, _ in este])); res_x = 0.0
    if not dos_y:
        ay = -ax
        by = float(np.mean([v - ay * px for px, v, _ in norte])); res_y = 0.0
    utm = transformar(geom_px, lambda c: np.column_stack([ax * c[:, 0] + bx, ay * c[:, 1] + by]))
    utm = utm.buffer(abs(ax) * borde_px, join_style="mitre", mitre_limit=3)
    utm = utm.simplify(abs(ax) * f * 0.75)  # tolerancia ~ 3/4 de píxel nativo
    area_ha = utm.area / 10_000
    dx, dy = desplazamiento_datum()
    utm = transformar(utm, lambda c: c + [dx, dy])
    wgs = transformar(utm, lambda c: np.column_stack(A_WGS84.transform(c[:, 0], c[:, 1])))
    m_por_px = (abs(ax) + abs(ay)) / 2 * f  # por píxel nativo
    resultado = {
        "id": uga,
        "estado": "borrador",
        "metros_por_pixel": round(m_por_px, 1),
        "precision_estimada_m": round(m_por_px * 2, 0),
        "residuo_georreferencia_m": round(max(res_x, res_y), 1),
        "rotulos_utm": {"este": len(este), "norte": len(norte)},
        "escala_por_superficie": escala_por_superficie,
        "ejes_con_escala_propia": int(dos_x) + int(dos_y),
        "pixeles_no_cuadrados_pct": round(100 * abs(abs(ax) - abs(ay)) / abs(ay), 1) if dos_x and dos_y else None,
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
                "fuente": f"Mapa de ubicación de la ficha UGA {origen}, Boletín Oficial No. 12 (12-mar-2014), p. {mapa['pagina_boletin']} del PDF"
                          + (f" (el Boletín imprime ahí el mapa de la UGA {uga}; INC-012)" if origen != uga else ""),
                "datum": f"UTM 12N con desplazamiento de {dx:+.0f} m E y {dy:+.0f} m N ajustado contra la costa (INC-011)",
                "correccion_borde_px": CORRECCION_BORDE_PX,
                "precision_aprox_m": resultado["precision_estimada_m"],
                "escala_por_superficie": escala_por_superficie,
                "revisada_en_qgis": False,
            },
            "control": {k: resultado[k] for k in ("residuo_georreferencia_m", "area_digitalizada_ha", "escala_por_superficie",
                                                    "superficie_ficha_ha", "diferencia_area_pct")},
        },
        "geometry": mapping(wgs),
    }
    # Imagen de diagnóstico: contorno digitalizado sobre el mapa original
    diag = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    for g in getattr(geom_px, "geoms", [geom_px]):
        cv2.polylines(diag, [np.array(g.exterior.coords, dtype=np.int32)], True, (255, 160, 0), 2)
    cv2.rectangle(diag, (x0, y0), (x1, y1), (0, 200, 0), 1)
    return resultado, feature, diag


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
