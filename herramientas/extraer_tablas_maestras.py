"""Extrae del Boletín las tablas maestras del POEL: lineamientos (T16), estrategias (T17) y criterios (T18).

Uso: .venv/bin/python herramientas/extraer_tablas_maestras.py
"""
import json
import re

from boletin import DATOS, ENCABEZADOS_TABLA_18, abrir, limpiar, lineas

PAG_T16 = range(58, 61)
PAG_T17 = range(61, 78)
PAG_T18 = range(78, 119)


def es_pie_de_pagina(linea, alto):
    return linea[1] > alto - 80 and re.fullmatch(r"\d{1,3}", linea[6])


def lineamientos(doc):
    out = []
    for n in PAG_T16:
        for tabla in doc[n - 1].find_tables().tables:
            for fila in tabla.extract():
                codigo = (fila[0] or "").strip().replace(" ", "")
                texto = limpiar(fila[1] or "")
                if re.fullmatch(r"L\d+", codigo):
                    item = {"id": codigo, "texto": texto, "pagina_boletin": n}
                    if any(x["id"] == codigo for x in out):
                        # El Boletín repite "L18"; se numera en secuencia y se registra como incidencia.
                        item["id"] = f"L{len(out) + 1}"
                        item["id_en_boletin"] = codigo
                    out.append(item)
                elif texto and out and not codigo and "Lineamientos ecológicos" not in texto:
                    out[-1]["texto"] += " " + texto  # fila partida entre páginas
    return out


def estrategias(doc):
    # Cada estrategia: código en negritas a la izquierda ("E 1", "EG 2"…), título en
    # negritas a la derecha (puede empezar un renglón arriba del código) y texto normal.
    todas, iniciado = [], False
    for n in PAG_T17:
        pagina = doc[n - 1]
        for linea in lineas(pagina):
            texto = linea[6]
            if not iniciado:
                iniciado = texto.startswith("Tabla 17")
                continue
            if texto.startswith("CRITERIOS DE REGULACI"):
                iniciado = False
                break
            if not es_pie_de_pagina(linea, pagina.rect.height):
                todas.append((n, *linea))
        if n > PAG_T17[0] and not iniciado:
            break
    codigos = [i for i, l in enumerate(todas) if l[5] and l[1] < 80 and re.fullmatch(r"EG?\s?\d{1,2}", l[7])]
    out = []
    for k, i in enumerate(codigos):
        n, y = todas[i][0], todas[i][2]
        fin = codigos[k + 1] if k + 1 < len(codigos) else len(todas)
        inicio = i
        # el título puede empezar un renglón antes que el código
        while inicio > 0 and todas[inicio - 1][0] == n and todas[inicio - 1][5] and todas[inicio - 1][1] >= 90 and y - todas[inicio - 1][2] < 15:
            inicio -= 1
        titulo, texto = [], []
        for l in todas[inicio:fin]:
            if l is todas[i]:
                continue
            if l[5] and l[1] >= 90 and not texto:
                titulo.append(l[7])
            elif not (k + 1 < len(codigos) and l[5] and l[1] >= 90 and l[0] == todas[fin][0] and todas[fin][2] - l[2] < 15 and l[2] < todas[fin][2] + 1):
                texto.append(l[7])
        numero = re.search(r"\d+", todas[i][7]).group()
        out.append({"id": f"EG{numero}", "titulo": limpiar(" ".join(titulo)).capitalize(),
                    "texto": limpiar("\n".join(texto)), "pagina_boletin": n})
    return out


def criterios(doc):
    out, grupo = [], None
    for n in PAG_T18:
        for tabla in doc[n - 1].find_tables().tables:
            for fila in tabla.extract():
                celdas = [(c or "").strip() for c in fila] + ["", "", ""]
                encabezado = " ".join(c for c in celdas if c)
                m = re.search(r"CRITERIOS DE REGULACI.N ECOL.GICA\s+(.+)", encabezado)
                if m:
                    nombre = re.sub(r"\s+", " ", m.group(1)).strip().upper()
                    grupo = ENCABEZADOS_TABLA_18.get(nombre)
                    if grupo is None:
                        raise ValueError(f"Encabezado de grupo desconocido en p{n}: {nombre!r}")
                    continue
                # Columna de código: la primera celda que parece un código (A 5, FF 3, T III 7…)
                celdas = [c.replace("\u2010", "-") for c in celdas]
                codigo_idx = next((i for i, c in enumerate(celdas[:4])
                                   if re.fullmatch(r"[A-ZÁÉÍÓÚ][A-Za-zÁÉÍÓÚ]{0,3}([\s-]?[IV]{1,3})?\s?\d{1,2}", c)), None)
                if codigo_idx is not None:
                    codigo = celdas[codigo_idx]
                    texto = limpiar(" ".join(c for c in celdas[codigo_idx + 1:] if c))
                    out.append({
                        "id": re.sub(r"[\s-]+", "", codigo),
                        "grupo": grupo,
                        "numero": int(re.search(r"(\d+)$", codigo).group(1)),
                        "texto": texto,
                        "pagina_boletin": n,
                    })
                elif out and grupo == out[-1]["grupo"]:
                    # continuación de la celda de texto (viñetas o salto de página)
                    resto = limpiar(" ".join(c for c in celdas[1:] if c))
                    if resto:
                        out[-1]["texto"] += " " + resto
    return out


def main():
    doc = abrir()
    DATOS.mkdir(parents=True, exist_ok=True)
    for nombre, datos in [("lineamientos", lineamientos(doc)),
                          ("estrategias", estrategias(doc)),
                          ("criterios", criterios(doc))]:
        (DATOS / f"{nombre}.json").write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n")
        print(f"{nombre}: {len(datos)}")


if __name__ == "__main__":
    main()
