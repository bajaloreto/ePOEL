"""Genera los datos que publica el sitio (public/datos/) a partir de datos/poel y rescate/.

- ugas.geojson: una feature por UGA con geometría. Prioridad de procedencia:
  1) datos/poel/digitalizacion/<id>.geojson (re-digitalizada desde el Boletín, ADR 0002)
  2) ePOEL 2019 (public/legacy/js/variablesgeojsons.js), marcada como provisional
- fichas/<id>.json: ficha completa con los textos de lineamientos, estrategias y criterios.
- indice.json: catálogo ligero de las 122 UGAs (para el tablero y el buscador).
- contexto.geojson: tierra, localidades y caminos (rescate de 2019) para el mapa base propio.

Uso: .venv/bin/python herramientas/construir_geodatos.py
"""
import json
import re
from pathlib import Path

from shapely.geometry import MultiPolygon, mapping, shape
from shapely.ops import unary_union

from boletin import BOLETIN_URL, DATOS, GRUPOS, RAIZ

SALIDA = RAIZ / "public" / "datos"
LEGADO = RAIZ / "public" / "legacy" / "js" / "variablesgeojsons.js"
RESCATE = RAIZ / "rescate" / "mapbox-2019"
NOMBRE_GRUPO = dict(GRUPOS)


def redondear(geom, decimales=6):
    def r(c):
        return [round(c[0], decimales), round(c[1], decimales)] if isinstance(c[0], (int, float)) else [r(x) for x in c]
    g = mapping(geom)
    return {"type": g["type"], "coordinates": r(json.loads(json.dumps(g["coordinates"])))}


def geometrias_2019():
    texto = LEGADO.read_text()
    out = {}
    for m in re.finditer(r"var\s+(\w+)\s*=\s*(\{.*?\n\})\s*;?", texto, re.S):
        for f in json.loads(m.group(2))["features"]:
            uid = f["properties"]["nombre"].replace("UGA-", "").strip().lower()
            # «UGA-7» lleva la clave y la superficie de la 7a, pero su forma es la de la 7b: se digitalizó de la
            # ficha 7a, que en el Boletín trae el mapa de la 7b (INC-008, INC-012)
            uid = "7b" if uid == "7" else uid
            out.setdefault(uid, []).append(shape(f["geometry"]).buffer(0))
    return {k: unary_union(v) for k, v in out.items()}


def incidencia_para_ficha(inc, procedencia):
    """Texto en lenguaje llano para la ficha. "aviso" se resalta; "nota" informa sin alarmar."""
    if inc["id"] == "INC-007":  # sin polígono en 2019: depende de si ya se re-digitalizó
        if procedencia["metodo"] == "digitalizada":
            return {"id": inc["id"], "nivel": "nota",
                    "texto": "ePOEL 2019 no tenía polígono para esta UGA; este se digitalizó del mapa de su ficha en el Boletín."}
        return {"id": inc["id"], "nivel": "aviso", "texto": "Esta UGA todavía no tiene polígono digitalizado; aún no puede ubicarse en el mapa."}
    return {"id": inc["id"], "nivel": "nota" if inc["estado"] == "resuelta" else "aviso",
            "texto": inc.get("texto_ficha") or inc["titulo"]}


def main():
    fichas = {p.stem: json.loads(p.read_text()) for p in (DATOS / "ugas").glob("*.json")}
    lin = {l["id"]: l for l in json.loads((DATOS / "lineamientos.json").read_text())}
    est = {e["id"]: e for e in json.loads((DATOS / "estrategias.json").read_text())}
    crit = {(c["grupo"], c["numero"]): c for c in json.loads((DATOS / "criterios.json").read_text())}
    incidencias = json.loads((DATOS / "incidencias.json").read_text())
    v2019 = geometrias_2019()
    archivo_validacion = DATOS / "digitalizacion" / "validacion.json"
    validacion = json.loads(archivo_validacion.read_text()) if archivo_validacion.exists() else {}

    (SALIDA / "fichas").mkdir(parents=True, exist_ok=True)
    features, indice = [], []
    orden = lambda u: (int(re.match(r"\d+", u).group()), u)
    for uid in sorted(fichas, key=orden):
        f = fichas[uid]
        dig = DATOS / "digitalizacion" / f"{uid}.geojson"
        estado_dig = validacion.get(uid, {}).get("estado", "aceptada")
        if dig.exists() and estado_dig in ("aceptada", "revisar"):
            feat = json.loads(dig.read_text())["features"][0]
            geom = shape(feat["geometry"])
            proc = feat["properties"]["procedencia"]
            procedencia = {"metodo": "digitalizada", "texto": "Digitalizada del mapa de la ficha del Boletín",
                           "precision_m": proc["precision_aprox_m"], "revisada": proc["revisada_en_qgis"],
                           "validacion": estado_dig}
        elif uid in v2019:
            geom = v2019[uid]
            procedencia = {"metodo": "epoel-2019", "texto": "Provisional: geometría de ePOEL 2019, pendiente de re-digitalizar",
                           "precision_m": None, "revisada": False}
        else:
            geom, procedencia = None, {"metodo": "sin-geometria", "texto": "Sin geometría todavía", "precision_m": None, "revisada": False}

        incs = [incidencia_para_ficha(i, procedencia) for i in incidencias if uid in i["ugas"]]
        resumen = {
            "id": uid, "nombre": f"UGA {uid}", "politica": f["politica"], "actividad": f["actividad"],
            "superficie_ha": f["superficie_ha"], "localidad": f["localidad_referencia"],
            "presion": (f["presion"] or {}).get("nivel"), "procedencia": procedencia["metodo"],
            "incidencias": sum(1 for i in incs if i["nivel"] == "aviso"),
            "incidencia": next((i["id"] for i in incs if i["nivel"] == "aviso"), None),
            "nota": next((i["id"] for i in incs if i["nivel"] == "nota"), None),
        }
        if geom is not None and not geom.is_empty:
            c = geom.representative_point()
            resumen["centro"] = [round(c.x, 5), round(c.y, 5)]
            if isinstance(geom, MultiPolygon) or geom.geom_type == "Polygon":
                features.append({"type": "Feature", "id": len(features),
                                 "properties": {k: resumen[k] for k in ("id", "politica", "procedencia")},
                                 "geometry": redondear(geom)})
        indice.append(resumen)

        detalle = dict(f)
        detalle.pop("extraccion", None)
        detalle["procedencia_geometria"] = procedencia
        detalle["incidencias"] = incs
        detalle["lineamientos"] = [{"id": l["id"], "texto": lin[l["id"]]["texto"] if l["id"] else l["texto_en_ficha"]}
                                   for l in f["lineamientos"]]
        detalle["estrategias"] = [{"id": e, "titulo": est[e]["titulo"]} for e in f["estrategias"]]
        detalle["criterios"] = [{"grupo": g, "nombre": NOMBRE_GRUPO[g],
                                 "items": [{"id": crit[(g, n)]["id"], "texto": crit[(g, n)]["texto"],
                                            "pagina": crit[(g, n)]["pagina_boletin"]} for n in ns]}
                                for g, ns in f["criterios"].items()]
        detalle["fuente"]["url"] = BOLETIN_URL
        (SALIDA / "fichas" / f"{uid}.json").write_text(json.dumps(detalle, ensure_ascii=False))

    (SALIDA / "ugas.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False))
    (SALIDA / "indice.json").write_text(json.dumps(indice, ensure_ascii=False))
    (SALIDA / "presets.json").write_text((DATOS / "presets.json").read_text())

    # Contexto: tierra (unión de cuencas), localidades y caminos rescatados de 2019
    cuencas = [shape(f["geometry"]).buffer(0) for f in json.loads((RESCATE / "cuencas_hidrologicas.geojson").read_text())["features"]]
    tierra = unary_union(cuencas).buffer(0.0003).buffer(-0.0003).simplify(0.0002)
    ctx = [{"type": "Feature", "properties": {"capa": "tierra"}, "geometry": redondear(tierra, 5)}]
    for f in json.loads((RESCATE / "localidades.geojson").read_text())["features"]:
        p = f["properties"]
        ctx.append({"type": "Feature", "properties": {"capa": "localidad", "nombre": (p.get("NOM_LOC") or "").title(),
                                                       "poblacion": p.get("POBTOT")},
                    "geometry": redondear(shape(f["geometry"]), 5)})
    for f in json.loads((RESCATE / "vialidades.geojson").read_text())["features"]:
        ctx.append({"type": "Feature", "properties": {"capa": "camino"}, "geometry": redondear(shape(f["geometry"]).simplify(0.0001), 5)})
    (SALIDA / "contexto.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": ctx}, ensure_ascii=False))

    con = sum(1 for i in indice if i["procedencia"] != "sin-geometria")
    print(f"UGAs: {len(indice)} · con geometría: {con} · features: {len(features)}")
    for p in sorted(SALIDA.glob("*")):
        if p.is_file():
            print(f"  {p.name}: {p.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
