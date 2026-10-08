"""Rescata los tilesets vectoriales de ePOEL v1 (cuenta Mapbox helden9) a GeoJSON.

Descarga cada tile al zoom máximo del tileset dentro de sus bounds, decodifica MVT,
reproyecta a lon/lat y reúne fragmentos cortados por bordes de tile.
"""
import json, os, sys, time, math, urllib.request, urllib.error, gzip
from collections import defaultdict
import mercantile, mapbox_vector_tile
from shapely.geometry import shape, mapping
from shapely.ops import unary_union, linemerge
from shapely import make_valid

TOKEN = "pk.eyJ1IjoiaGVsZGVuOSIsImEiOiJjam54Z2sxankweDEyM3ZuZGd1OGV2b2NsIn0.xuzmd6tEA2f6lgJYLfW_VQ"
OUT = sys.argv[1]  # p. ej. rescate/mapbox-2019
MAX_TILES = 4000

style = json.load(open(os.path.join(OUT, "estilo-mapbox-helden9.json")))
tilesets = style["sources"]["composite"]["url"].replace("mapbox://", "").split(",")
tilesets += [
    "helden9.cjtronjo20l8ae5o4agw8et3k-8trxr",  # aprovechamiento sustentable
    "helden9.cjtropb4h02rh2xmutx2w0rtw-6jw2b",  # preservacion
    "helden9.cjtrooin40lb0efn3kr4ad4o3-064rk",  # conservacion
    "helden9.cjtropxcj0l6k26qq3tsi9k6t-4jyxa",  # restauracion
    "helden9.ck41k95s60f1n2rqdi0hsc92r-4l3hv",  # psdu
]

def get(url, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                data = r.read()
                if data[:2] == b"\x1f\x8b":
                    data = gzip.decompress(data)
                return data
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(2 ** i)
        except Exception:
            time.sleep(2 ** i)
    raise RuntimeError(f"fallo descargando {url}")

def tile_geom_to_lonlat(geom, tile, extent):
    b = mercantile.xy_bounds(tile)
    def tr(c):
        x = b.left + (c[0] / extent) * (b.right - b.left)
        y = b.bottom + (c[1] / extent) * (b.top - b.bottom)
        return list(mercantile.lnglat(x, y))
    def walk(c):
        return tr(c) if isinstance(c[0], (int, float)) else [walk(x) for x in c]
    return {"type": geom["type"], "coordinates": walk(geom["coordinates"])}

os.makedirs(OUT, exist_ok=True)
manifest = []
for tid in tilesets:
    tj = json.loads(get(f"https://api.mapbox.com/v4/{tid}.json?access_token={TOKEN}"))
    z = tj["maxzoom"]
    w, s, e, n = tj["bounds"]
    while len(list(mercantile.tiles(w, s, e, n, z))) > MAX_TILES:
        z -= 1
    tiles = list(mercantile.tiles(w, s, e, n, z))
    layer_name = tj["vector_layers"][0]["id"]
    print(f"{tid} ({layer_name}): z{z} (max {tj['maxzoom']}), {len(tiles)} tiles", flush=True)
    groups = defaultdict(list)
    cache = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fuentes", "tilecache", tid)
    os.makedirs(cache, exist_ok=True)
    for t in tiles:
        cp = os.path.join(cache, f"{t.z}_{t.x}_{t.y}.pbf")
        if os.path.exists(cp):
            data = open(cp, "rb").read() or None
        else:
            data = get(f"https://api.mapbox.com/v4/{tid}/{t.z}/{t.x}/{t.y}.vector.pbf?access_token={TOKEN}")
            open(cp, "wb").write(data or b"")
        if not data:
            continue
        dec = mapbox_vector_tile.decode(data, default_options={"y_coord_down": False})
        for lname, layer in dec.items():
            ext = layer.get("extent", 4096)
            for f in layer["features"]:
                g = shape(tile_geom_to_lonlat(f["geometry"], t, ext))
                key = (lname, f.get("id"), json.dumps(f["properties"], sort_keys=True, ensure_ascii=False))
                groups[key].append(g)
    feats = []
    for (lname, fid, props), geoms in groups.items():
        kind = geoms[0].geom_type
        if "Polygon" in kind:
            g = unary_union([make_valid(x).buffer(1e-9) for x in geoms]).buffer(-1e-9)
        elif "LineString" in kind:
            g = unary_union(geoms)
            if g.geom_type == "MultiLineString":
                g = linemerge(g)
        else:
            # el mismo punto aparece en tiles vecinos (buffer) con mínima diferencia de cuantización
            pts = []
            for x in geoms:
                for pt in getattr(x, "geoms", [x]):
                    if all(pt.distance(q) > 2e-4 for q in pts):
                        pts.append(pt)
            g = pts[0] if len(pts) == 1 else unary_union(pts)
        feats.append({"type": "Feature", "id": fid, "properties": json.loads(props), "geometry": mapping(g)})
    fc = {"type": "FeatureCollection", "name": layer_name, "features": feats}
    path = os.path.join(OUT, f"{layer_name}.geojson")
    json.dump(fc, open(path, "w"), ensure_ascii=False)
    manifest.append({"capa": layer_name, "tileset": tid, "zoom_descargado": z, "zoom_max": tj["maxzoom"],
                     "tiles": len(tiles), "features": len(feats), "bounds": tj["bounds"],
                     "creado_mapbox": tj.get("created"), "modificado_mapbox": tj.get("modified")})
    print(f"  -> {len(feats)} features", flush=True)

json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w"), ensure_ascii=False, indent=2)
print("LISTO")
