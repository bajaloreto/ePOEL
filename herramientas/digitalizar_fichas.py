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
# Rótulos UTM que el OCR lee mal de forma consistente y que el ajuste conjunto no puede resolver solo (dos lecturas
# igual de coherentes). Cada corrección se apoya en una verificación independiente.
#   73a y 73b: «460000» se lee «450000» arriba y abajo; las localidades del mapa quedan a +9.8–10.1 km al Este de sus
#   coordenadas reales con 450000 y a ~100 m con 460000 (verificar_con_localidades.py).
ROTULOS_CORREGIDOS = {"73a": {450000: 460000}, "73b": {450000: 460000}}

# INC-013: fichas cuya superficie declarada no corresponde a su mapa; el área no sirve de control
AREA_DUDOSA = set(next((i["ugas"] for i in json.loads((DATOS / "incidencias.json").read_text())
                        if i["id"] == "INC-013"), []))
ESCALA_RENDER = 3  # para mapas vectoriales: píxeles por punto PDF
# El trazo de contorno de la UGA y el seguimiento por centros de píxel dejan fuera ~1.1–1.7 px de borde
# (medido en el piloto: UGAs 12, 1a y 45). Se compensa con un margen fijo igual para todas las fichas;
# la comparación con la superficie de la ficha sigue siendo un control independiente.
CORRECCION_BORDE_PX = 1.4
ESCALA_MAX_M_PX = 200


def ocr(png):
    if not OCR.exists():
        raise SystemExit("Compila el OCR: swiftc -O herramientas/ocr/ocr.swift -o herramientas/ocr/ocr")
    return json.loads(subprocess.run([str(OCR), str(png)], capture_output=True, text=True, check=True).stdout)


# Intervalo plausible de coordenadas UTM 12N para el Municipio de Loreto (con margen): descarta lecturas como
# «143500» en lugar de «443500», que desplazarían la UGA cientos de kilómetros.
# Extensión de las UGAs aceptadas en la primera corrida (E 422–507 km, N 2,788–2,939 km) más ~15 km de marco.
ESTE_LORETO = (400_000, 530_000)
NORTE_LORETO = (2_770_000, 2_955_000)


def ocr_con_giros(png):
    """OCR de la imagen tal cual y girada 90° en ambos sentidos: los rótulos Norte van en vertical y a veces solo
    se leen bien con la imagen girada. Las cajas de las versiones giradas se devuelven a coordenadas originales y
    solo se conservan sus lecturas de 7 dígitos (Norte)."""
    textos = ocr(png)
    img = cv2.imread(str(png))
    alto, ancho = img.shape[:2]
    for giro, a_original in ((cv2.ROTATE_90_CLOCKWISE, lambda cx, cy: (cy, alto - 1 - cx)),
                             (cv2.ROTATE_90_COUNTERCLOCKWISE, lambda cx, cy: (ancho - 1 - cy, cx))):
        girada = png.with_suffix(".giro.png")
        cv2.imwrite(str(girada), cv2.rotate(img, giro))
        for t in ocr(girada):
            if len(re.sub(r"\D", "", t["texto"])) != 7:
                continue
            cx, cy = a_original(t["x"] + t["w"] / 2, t["y"] + t["h"] / 2)
            textos.append({**t, "x": cx - t["h"] / 2, "y": cy - t["w"] / 2, "w": t["h"], "h": t["w"]})
        girada.unlink()
    return textos


def ocr_de_franjas(rgb, marco, tmp):
    """OCR de las franjas de rótulos que rodean el marco, ampliadas al triple: los rótulos de letra pequeña que el
    OCR de la imagen completa no ve. Las franjas laterales (Norte, en vertical) se giran antes de leerlas."""
    alto, ancho = rgb.shape[:2]
    x0, y0, x1, y1 = marco
    franjas = [  # (recorte, giro, función que devuelve un punto de la franja a la imagen original)
        ((0, 0, ancho, y0), None), ((0, y1, ancho, alto), None),
        ((0, 0, x0, alto), cv2.ROTATE_90_CLOCKWISE), ((x1, 0, min(x1 + (x1 - x0) // 4, ancho), alto), cv2.ROTATE_90_CLOCKWISE),
    ]
    textos, z = [], 3
    for (a, b, c, d), giro in franjas:
        if c - a < 8 or d - b < 8:
            continue
        img = cv2.resize(cv2.cvtColor(rgb[b:d, a:c], cv2.COLOR_RGB2BGR), None, fx=z, fy=z, interpolation=cv2.INTER_CUBIC)
        h_rec = img.shape[0]
        if giro is not None:
            img = cv2.rotate(img, giro)
        cv2.imwrite(str(tmp), img)
        for t in ocr(tmp):
            cx, cy = t["x"] + t["w"] / 2, t["y"] + t["h"] / 2
            w, h = t["w"] / z, t["h"] / z
            if giro is not None:  # deshace el giro horario: (x', y') = (h-1-y, x)
                cx, cy = cy, h_rec - 1 - cx
                w, h = h, w
            cx, cy = a + cx / z, b + cy / z
            textos.append({**t, "x": cx - w / 2, "y": cy - h / 2, "w": w, "h": h})
    tmp.unlink(missing_ok=True)
    return textos


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


def normalizar(candidatos):
    """Los rótulos del marco son múltiplos de 500 m: una lectura a ≤300 m de uno se redondea (el OCR confunde 5 y 3)."""
    limpios = []
    for px, v, otro in candidatos:
        r = round(v / 500) * 500
        if abs(r - v) <= 300:
            limpios.append((px, r, otro))
    return limpios


def mejor_grupo(rotulos, pendiente, tolerancia):
    """Rótulos coherentes con una pendiente dada: los que comparten la misma ordenada (valor − pendiente·píxel).
    Una lectura con un dígito equivocado («2914000» por «2814000») queda fuera del grupo."""
    ordenadas = [v - pendiente * px for px, v, _ in rotulos]
    mejor = []
    for b in ordenadas:
        grupo = [r for r, o in zip(rotulos, ordenadas) if abs(o - b) <= tolerancia]
        clave = (len({v for _, v, _ in grupo}), len(grupo))
        if clave > (len({v for _, v, _ in mejor}), len(mejor)):
            mejor = grupo
    return mejor


def georreferenciar(este, norte, escala_fija=None, escala_max=None):
    """Ajuste conjunto píxel -> UTM de los dos ejes.

    Los mapas tienen píxeles cuadrados: el Este crece con x (pendiente +s) y el Norte decrece con y (−s). Se prueba
    cada escala s que sugiere un par de rótulos de cualquier eje y se queda la que hace coherentes más rótulos en
    ambos ejes a la vez; así un rótulo mal leído en un eje no puede imponer una escala absurda. Después, cada eje
    con al menos dos valores coherentes se ajusta por mínimos cuadrados.
    Devuelve (ax, bx, ay, by, residuo_m, ejes_con_escala_propia) o None.
    """
    este, norte = normalizar(este), normalizar(norte)
    if not este or not norte:
        return None
    if escala_fija:
        escalas = [escala_fija]
    else:
        escalas = []
        for rot in (este, norte):
            for (p1, v1, _), (p2, v2, _) in combinations(rot, 2):
                if v1 != v2 and abs(p1 - p2) >= 20:
                    e = abs((v2 - v1) / (p2 - p1))
                    if escala_max is None or e <= escala_max:
                        escalas.append(e)
        if not escalas:
            return None
    mejor = None
    for e in escalas:
        tol = max(5 * e, 25)
        ge, gn = mejor_grupo(este, e, tol), mejor_grupo(norte, -e, tol)
        clave = (len({v for _, v, _ in ge}) + len({v for _, v, _ in gn}), len(ge) + len(gn))
        if mejor is None or clave > mejor[0]:
            mejor = (clave, e, ge, gn)
    _, e, ge, gn = mejor
    if not escala_fija and mejor[0][0] < 3:
        return None  # sin al menos tres valores coherentes no hay escala confiable
    propios = 0
    if len({v for _, v, _ in ge}) >= 2 and not escala_fija:
        ax, bx, res_x = ajuste(ge); propios += 1
    else:
        ax, bx, res_x = e, float(np.mean([v - e * px for px, v, _ in ge])), 0.0
    if len({v for _, v, _ in gn}) >= 2 and not escala_fija:
        ay, by, res_y = ajuste(gn); propios += 1
    else:
        ay, by, res_y = -e, float(np.mean([v + e * px for px, v, _ in gn])), 0.0
    return ax, bx, ay, by, max(res_x, res_y), propios


def ajuste(pares):
    """Ajuste lineal píxel -> metros. Devuelve (pendiente, ordenada, residuo máximo en m)."""
    px = np.array([p[0] for p in pares]); m = np.array([p[1] for p in pares], dtype=float)
    if len(set(m)) < 2:
        raise ValueError("se necesitan al menos dos rótulos distintos por eje")
    a, b = np.polyfit(px, m, 1)
    return a, b, float(np.max(np.abs(a * px + b - m)))


def mascara_uga(rgb, marco, f=1):
    """Relleno rojo oscuro de la UGA dentro del marco del mapa principal."""
    # El relleno de las UGAs en las fichas es RGB (168, 0, 0) (en alguna, como la 46, (217, 0, 17)); las carreteras usan un rojo más oscuro.
    r, g, b = [rgb[:, :, i].astype(int) for i in range(3)]
    rojo = ((r >= 140) & (r <= 235) & (g < 45) & (b < 45) & (r - g > 110)).astype(np.uint8) * 255
    x0, y0, x1, y1 = marco
    recorte = np.zeros_like(rojo)
    recorte[y0:y1, x0:x1] = rojo[y0:y1, x0:x1]
    # Cerrar los huecos que dejan rótulos, puntos y líneas dibujados encima de la UGA
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    return cv2.morphologyEx(recorte, cv2.MORPH_CLOSE, k, iterations=2 * f)


def marco_del_mapa(rgb):
    """Rectángulo del mapa principal: el marco más grande formado por líneas oscuras largas, a la izquierda.
    En los mapas ampliados el trazo del marco se aclara, por eso se prueba también un umbral más claro."""
    for umbral in (110, 170):
        marco = _marco(rgb, umbral)
        if marco:
            return marco
    return None


def _marco(rgb, umbral):
    alto, ancho = rgb.shape[:2]
    oscuro = (cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY) < umbral).astype(np.uint8) * 255
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
    if uga not in AREA_DUDOSA and all(abs(i[0]["diferencia_area_pct"]) > 25 for i in validos):
        # Área incompatible con la ficha: georreferencia o relleno equivocados; no se guarda
        mejor = min(validos, key=lambda i: abs(i[0]["diferencia_area_pct"]))[0]
        return {**mejor, "estado": "rechazada-area"}
    resultado, feature, diag = min(validos, key=lambda i: (uga not in AREA_DUDOSA and abs(i[0]["diferencia_area_pct"]) > 25,
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
    textos = ocr_con_giros(png)
    png.unlink()
    este, norte = rotulos_utm(textos)
    corregir = ROTULOS_CORREGIDOS.get(uga, {})
    este = [(p, corregir.get(v, v), o) for p, v, o in este]
    marco = marco_del_mapa(rgb)
    if marco and (len({v for _, v, _ in normalizar(este)}) < 2 or len({v for _, v, _ in normalizar(norte)}) < 2):
        mas_este, mas_norte = rotulos_utm(ocr_de_franjas(rgb, marco, SALIDA / f"{uga}.franja.png"))
        este, norte = este + [(p, corregir.get(v, v), o) for p, v, o in mas_este], norte + mas_norte
    if not normalizar(este) or not normalizar(norte):
        return {"id": uga, "estado": "sin-rotulos", "rotulos_utm": {"este": len(este), "norte": len(norte)}}, None, None
    escala_por_superficie = False
    # Marco del mapa principal; si no se detecta, se deduce de los rótulos
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
    # Los mapas de menor detalle del Boletín (UGAs 73a y 73b) rondan 150 m por píxel nativo: una escala mayor sale de
    # rótulos mal leídos
    geo = georreferenciar(este, norte, escala_max=ESCALA_MAX_M_PX / f)
    if geo is None:
        # Sin escala confiable en los rótulos: sale de la superficie declarada en la ficha (el control de área
        # deja de ser independiente y se marca así en la procedencia); los rótulos solo dan la posición
        area_px = geom_px.buffer(borde_px, join_style="mitre", mitre_limit=3).area
        geo = georreferenciar(este, norte, escala_fija=(ficha["superficie_ha"] * 10_000 / area_px) ** 0.5)
        escala_por_superficie = True
    ax, bx, ay, by, residuo, propios = geo
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
        "residuo_georreferencia_m": round(residuo, 1),
        "rotulos_utm": {"este": len(este), "norte": len(norte)},
        "escala_por_superficie": escala_por_superficie,
        "ejes_con_escala_propia": propios,
        "pixeles_no_cuadrados_pct": round(100 * abs(abs(ax) - abs(ay)) / abs(ay), 1) if propios == 2 else None,
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
            # Transformación píxel -> UTM 12N (antes del desplazamiento de datum) del mapa renderizado al factor
            # indicado: permite montar el mapa de la ficha georreferenciado (herramientas/proyecto_qgis.py)
            "georreferencia": {"a_x": ax, "b_x": bx, "a_y": ay, "b_y": by, "factor_render": f,
                               "pagina_mapa": mapa["pagina_boletin"], "ficha_mapa": origen},
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
