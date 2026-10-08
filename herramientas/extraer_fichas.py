"""Extrae las fichas de UGA del Apéndice 10 del Boletín como datos estructurados.

Genera datos/poel/ugas/<id>.json. Requiere haber corrido antes extraer_tablas_maestras.py
(usa lineamientos.json para identificar los lineamientos de cada ficha).

Uso: .venv/bin/python herramientas/extraer_fichas.py
"""
import difflib
import json
import re

from boletin import BOLETIN_URL, DATOS, GRUPOS, abrir, limpiar, lineas

PRIMERA_PAGINA = 136
ULTIMA_PAGINA = 495

ETIQUETAS = [
    ("superficie", r"Superficie total:?"),
    ("localidad", r"Localidad de referencia:?"),
    ("poblacion", r"Poblaci[oó]n:?"),
    ("actividad", r"(Clasificaci[oó]n|Actividad):?"),
    ("vegetacion", r"Superficie de Vegetaci[oó]n \(Ha\)"),
    ("politica", r"Pol[ií]tica Ambiental:?"),
    ("conflictos", r"Conflictos potenciales:?"),
    ("areas", r"[ÁA]reas de atenci[oó]n especial"),
    ("fragilidad", r"Fragilidad:?"),
    ("vulnerabilidad", r"Vulnerabilidad:?"),
    ("presion", r"Presi[oó]n:?"),
    ("lineamientos", r"Lineamientos Ecol[oó]gicos:?"),
    ("estrategias", r"Estrategias ecol[oó]gicas generales:?"),
    ("estrategias_particulares", r"Estrategias? ecol[oó]gicas?( particular(es)?)?:?"),
    ("criterios", r"Criterios de regulaci[oó]n ecol[oó]gica:?"),
]

POLITICAS = [  # prefijo (sin acentos) -> clave; tolera variantes como "Aprovechamientos sustentable"
    ("aprovechamiento", "aprovechamiento-sustentable"),
    ("conservacion", "conservacion"),
    ("preservacion", "preservacion"),
    ("restauracion", "restauracion"),
]
NIVELES = ("baja", "media", "alta")

# Etiqueta de fila en la matriz de criterios -> clave de grupo (mismo orden que GRUPOS)
FILAS_MATRIZ = [
    (r"Agua", "agua"),
    (r"Flora", "flora-fauna"),
    (r"Manejo", "manejo-ecosistemas"),
    (r"Residuos", "residuos"),
    (r"Asent\.?\s*Hum\.?\s*I$", "asentamientos-humanos-1"),
    (r"Asent\.?\s*Hum\.?\s*II$", "asentamientos-humanos-2"),
    (r"Infraest", "infraestructura"),
    (r"Acuacultura", "acuacultura"),
    (r"Agricultura", "agricultura"),
    (r"Construcci", "construccion"),
    (r"Extracci", "mineria"),
    (r"Pecuario", "pecuario"),
    (r"Pesca", "pesca"),
    (r"Turismo\s*I$", "turismo-1"),
    (r"Turismo\s*II$", "turismo-2"),
    (r"Turismo\s*III$", "turismo-3"),
]


def sin_acentos(s):
    return s.lower().translate(str.maketrans("áéíóú", "aeiou")).strip()


def normalizar_id(texto):
    t = re.sub(r"[\s‐\-–]", "", texto).replace("UGA", "")
    m = re.fullmatch(r"(\d+)([a-zA-Z]?)", t)
    return f"{int(m.group(1))}{m.group(2).lower()}"


def encabezados(doc):
    """Páginas donde empieza cada ficha: [(pagina, id)]."""
    out = []
    for n in range(PRIMERA_PAGINA, ULTIMA_PAGINA + 1):
        for l in lineas(doc[n - 1]):
            if l[5] > 18 and "UGA" in l[6]:
                out.append((n, normalizar_id(l[6])))
    return out


def reglas_horizontales(pagina):
    ys = []
    for dib in pagina.get_drawings():
        for item in dib["items"]:
            if item[0] == "l" and abs(item[1].y - item[2].y) < 1 and abs(item[1].x - item[2].x) > 150:
                ys.append(item[1].y)
            elif item[0] == "re" and item[1].width > 150:
                ys.extend([item[1].y0, item[1].y1])
    return sorted(ys)


def secciones(doc, paginas):
    """Agrupa las líneas de la ficha por sección según las etiquetas en negritas."""
    out, actual = {}, "encabezado"
    for n in paginas:
        pagina = doc[n - 1]
        reglas = reglas_horizontales(pagina)
        for linea in lineas(pagina):
            x0, y0, x1, y1, negrita, tam, texto = linea
            if y0 > pagina.rect.height - 70 and re.fullmatch(r"\d{1,3}", texto):
                continue  # número de página de la ficha
            if texto.startswith("APENDICE 10") or tam > 18 or tam < 6:
                continue  # encabezado, título de la ficha o rótulos del mapa de ubicación
            clave = next((k for k, rx in ETIQUETAS if re.fullmatch(rx, texto, re.I)), None)
            if clave:
                actual = clave
                out.setdefault(actual, [])
                continue
            out.setdefault(actual, []).append({"pagina": n, "x": x0, "y": y0, "y1": y1, "negrita": negrita,
                                               "texto": texto, "reglas": reglas})
    return out


def texto_de(sec):
    return limpiar("\n".join(l["texto"] for l in sec)) if sec else None


def numero(texto):
    m = re.search(r"[\d,]+(\.\d+)?", texto or "")
    return float(m.group().replace(",", "")) if m else None


def tabla_vegetacion(sec):
    """Filas: [vegetación, ha] a la izquierda y [sector, nivel, valor] a la derecha."""
    vegetacion, aptitud = [], []
    for l in sec or []:
        if l["texto"] in ("Sector", "Aptitud"):
            continue
        es_numero = re.fullmatch(r"[\d,]+(\.\d+)?", l["texto"]) is not None
        if l["x"] < 250 and not es_numero:
            vegetacion.append([l["texto"], None, l["y"]])
        elif l["x"] < 310:
            if es_numero and vegetacion:
                fila = min(vegetacion, key=lambda v: abs(v[2] - l["y"]))
                fila[1] = numero(l["texto"])
        elif l["x"] < 400:
            aptitud.append({"sector": l["texto"], "nivel": None, "valor": None, "y": l["y"]})
        elif aptitud and abs(aptitud[-1]["y"] - l["y"]) < 4:
            if l["x"] < 480:
                aptitud[-1]["nivel"] = l["texto"].lower()
            else:
                aptitud[-1]["valor"] = numero(l["texto"])
    # "Turismo" / "alternativo": el nombre del sector puede ocupar dos renglones
    for i in range(len(aptitud) - 1, 0, -1):
        if aptitud[i]["sector"][:1].islower() and aptitud[i - 1]["nivel"] is None:
            aptitud[i - 1].update(sector=f'{aptitud[i - 1]["sector"]} {aptitud[i]["sector"]}',
                                  nivel=aptitud[i]["nivel"], valor=aptitud[i]["valor"])
            del aptitud[i]
    for a in aptitud:
        a.pop("y")
    return ([{"tipo": v[0], "hectareas": v[1]} for v in vegetacion], aptitud)


def areas_atencion(sec):
    """Dos columnas (área | justificación); las filas se separan por reglas horizontales."""
    filas = []
    for l in sec or []:
        if l["texto"] == "Justificación":
            continue
        nueva_fila = not filas or any(filas[-1]["y_ultima"] < r < l["y"] + 2 for r in l["reglas"]) \
            or l["pagina"] != filas[-1]["pagina"]
        if nueva_fila:
            filas.append({"area": [], "justificacion": [], "y_ultima": l["y"], "pagina": l["pagina"]})
        (filas[-1]["area"] if l["x"] < 300 else filas[-1]["justificacion"]).append(l["texto"])
        filas[-1]["y_ultima"] = max(filas[-1]["y_ultima"], l["y"])
    return [{"area": limpiar(" ".join(f["area"])), "justificacion": limpiar(" ".join(f["justificacion"]))}
            for f in filas if f["area"] or f["justificacion"]]


def parrafos_por_reglas(sec):
    parrafos, previa = [], None
    for l in sec or []:
        corte = previa is None or l["pagina"] != previa["pagina"] \
            or any(previa["y1"] - 2 < r < l["y"] + 2 for r in l["reglas"])
        if corte:
            parrafos.append([])
        parrafos[-1].append(l["texto"])
        previa = l
    return [limpiar(" ".join(p)) for p in parrafos]


def mejor_lineamiento(texto, catalogo):
    mejor = max(catalogo, key=lambda c: difflib.SequenceMatcher(None, texto, c["texto"]).ratio())
    return mejor, difflib.SequenceMatcher(None, texto, mejor["texto"]).ratio()


def identificar_lineamientos(parrafos, catalogo):
    # Une fragmentos que el salto de página separó cuando la unión se parece más a un lineamiento.
    unidos = []
    for p in parrafos:
        if unidos:
            _, sim_prev = mejor_lineamiento(unidos[-1], catalogo)
            _, sim_union = mejor_lineamiento(unidos[-1] + " " + p, catalogo)
            fragmento = p[:1].islower() or len(p) < 40
            if fragmento or (sim_prev < 0.85 and sim_union > sim_prev):
                unidos[-1] = unidos[-1] + " " + p
                continue
        unidos.append(p)
    out = []
    for p in unidos:
        mejor, similitud = mejor_lineamiento(p, catalogo)
        lid = mejor["id"] if similitud >= 0.85 else None
        previo = next((x for x in out if lid and x["id"] == lid), None)
        if previo:  # el Boletín repite el renglón (p. ej. UGA 3a); se conserva una vez
            previo["repeticiones_en_boletin"] = previo.get("repeticiones_en_boletin", 1) + 1
            continue
        out.append({"id": lid, "similitud": round(similitud, 3), "texto_en_ficha": p})
    return out


def estrategias_y_criterios(doc, paginas):
    """Lee la fila EG y la matriz de criterios por posición de palabras."""
    eg, matriz, columnas_previas = [], {}, None
    for n in paginas:
        palabras = doc[n - 1].get_text("words")
        # Fila de estrategias: pares "EG" / número en la misma columna
        egs = [w for w in palabras if w[4] == "EG"]
        for w in egs:
            num = next((p[4] for p in palabras if abs(p[0] - w[0]) < 3 and 4 < p[1] - w[1] < 16
                        and p[4].isdigit()), None)
            if num:
                eg.append(f"EG{int(num)}")
        # Matriz de criterios
        titulo = next((w for w in palabras if w[4] == "Criterios"
                       and any(p[4] == "regulación" and abs(p[1] - w[1]) < 3 for p in palabras)), None)
        if titulo:
            cab_y = min((p[1] for p in palabras if p[4] == "1" and p[1] > titulo[1] + 5), default=None)
            if cab_y is None:
                continue
            columnas = {int(p[4]): (p[0] + p[2]) / 2 for p in palabras
                        if abs(p[1] - cab_y) < 3 and p[4].isdigit() and p[0] > 150}
            columnas_previas = columnas
        elif columnas_previas:
            # la matriz continúa en esta página sin repetir el encabezado de columnas
            columnas, cab_y = columnas_previas, -10
        else:
            continue
        limite_etiquetas = columnas.get(1, 180) - 12  # la tabla no siempre está en la misma posición
        etiquetas = [p for p in palabras if p[1] > cab_y + 5 and p[0] < limite_etiquetas and not p[4] == "X"]
        lineas_etq = {}
        for p in etiquetas:
            lineas_etq.setdefault(round(p[1]), []).append(p[4])
        filas = []  # (y_inicio, grupo)
        for y, ws in sorted(lineas_etq.items()):
            texto = " ".join(ws)
            g = next((g for rx, g in FILAS_MATRIZ if re.match(rx, texto)), None)
            if g:
                filas.append((y, g))
        for p in palabras:
            if p[4] != "X" or p[1] <= cab_y + 5:
                continue
            fila = max((f for f in filas if f[0] <= p[1] + 3), default=None, key=lambda f: f[0])
            col = min(columnas, key=lambda c: abs(columnas[c] - (p[0] + p[2]) / 2))
            if fila:
                matriz.setdefault(fila[1], set()).add(col)
    orden = [g for g, _ in GRUPOS]
    return (sorted(set(eg), key=lambda e: int(e[2:])),
            {g: sorted(matriz[g]) for g in orden if g in matriz})


def politica(texto):
    t = sin_acentos(texto or "")
    claves = {clave for prefijo, clave in POLITICAS if t.startswith(prefijo)}
    return claves.pop() if len(claves) == 1 else None


def nivel(texto):
    """'Alta (dentro del área del PSRDU)' -> {'nivel': 'alta', 'nota': 'dentro del área del PSRDU'}."""
    if not texto:
        return None
    m = re.match(r"(baja|media|alta)\b[\s:(]*(.*?)\)?$", texto, re.I)
    if not m:
        return {"nivel": None, "nota": texto}
    return {"nivel": m.group(1).lower(), "nota": m.group(2).strip() or None}


def mapa_de_ubicacion(doc, n):
    pagina = doc[n - 1]
    imagenes = pagina.get_image_info(xrefs=True)
    if not imagenes:
        # Algunas fichas traen el mapa como dibujo vectorial con rótulos UTM como texto
        rotulos = [l for l in lineas(pagina) if l[5] < 6]
        if not rotulos:
            return None
        return {"pagina_boletin": n, "tipo": "vectorial",
                "bbox": [round(min(l[0] for l in rotulos), 1), round(min(l[1] for l in rotulos), 1),
                         round(max(l[2] for l in rotulos), 1), round(max(l[3] for l in rotulos), 1)]}
    img = max(imagenes, key=lambda i: (i["bbox"][2] - i["bbox"][0]) * (i["bbox"][3] - i["bbox"][1]))
    return {"pagina_boletin": n, "tipo": "imagen", "xref": img["xref"], "bbox": [round(v, 1) for v in img["bbox"]],
            "pixeles": [img["width"], img["height"]]}


def main():
    doc = abrir()
    catalogo = json.loads((DATOS / "lineamientos.json").read_text())
    heads = encabezados(doc)
    destino = DATOS / "ugas"
    destino.mkdir(parents=True, exist_ok=True)
    for k, (inicio, uga) in enumerate(heads):
        fin = heads[k + 1][0] - 1 if k + 1 < len(heads) else ULTIMA_PAGINA
        paginas = range(inicio, fin + 1)
        sec = secciones(doc, paginas)
        vegetacion, aptitud = tabla_vegetacion(sec.get("vegetacion"))
        eg, matriz = estrategias_y_criterios(doc, paginas)
        lineamientos = identificar_lineamientos(parrafos_por_reglas(sec.get("lineamientos")), catalogo)
        ficha = {
            "id": uga,
            "numero": int(re.match(r"\d+", uga).group()),
            "nombre": f"UGA {uga}",
            "superficie_ha": numero(texto_de(sec.get("superficie"))),
            "localidad_referencia": texto_de(sec.get("localidad")),
            "poblacion": texto_de(sec.get("poblacion")),
            "actividad": texto_de(sec.get("actividad")),
            "politica": politica(texto_de(sec.get("politica"))),
            "politica_texto": texto_de(sec.get("politica")),
            "conflictos_potenciales": texto_de(sec.get("conflictos")),
            "vegetacion_ha": vegetacion,
            "aptitud": aptitud,
            "areas_atencion_especial": areas_atencion(sec.get("areas")),
            "fragilidad": nivel(texto_de(sec.get("fragilidad"))),
            "vulnerabilidad": nivel(texto_de(sec.get("vulnerabilidad"))),
            "presion": nivel(texto_de(sec.get("presion"))),
            "lineamientos": lineamientos,
            "estrategias": eg,
            "estrategias_particulares": texto_de([l for l in sec.get("estrategias_particulares", [])
                                                  if not re.fullmatch(r"(EG|\d{1,2})", l["texto"])]),
            "criterios": matriz,
            "mapa_ubicacion": mapa_de_ubicacion(doc, inicio),
            "fuente": {
                "documento": "Boletín Oficial del Gobierno del Estado de B.C.S. No. 12 Extraordinario, 12-mar-2014, Apéndice 10",
                "url": BOLETIN_URL,
                "paginas_pdf": [inicio, fin],
            },
            "extraccion": {"metodo": "automatica (herramientas/extraer_fichas.py)", "verificada": False},
        }
        (destino / f"{uga}.json").write_text(json.dumps(ficha, ensure_ascii=False, indent=2) + "\n")
    print(f"fichas: {len(heads)}")


if __name__ == "__main__":
    main()
