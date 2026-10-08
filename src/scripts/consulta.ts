// Consulta por punto: mapa, búsqueda, tablero y pase.
import { Map as Mapa, Marker, LngLatBounds, setWorkerUrl, type GeoJSONSource } from "maplibre-gl";
import urlWorker from "maplibre-gl/dist/maplibre-gl-worker.mjs?url";
import "maplibre-gl/dist/maplibre-gl.css";

// El worker de MapLibre 6 es un módulo aparte; se sirve como archivo del propio sitio
setWorkerUrl(urlWorker);
import qrcode from "qrcode-generator";
import { htmlError, htmlPase, htmlPaseCargando, POLITICA, type Politica, type Resumen } from "../lib/pase";
import { geoAUtm, utmAGeo } from "../lib/utm";
import { BOLETIN_COMPLETO } from "../lib/sitio";
import { cargarFicha, cargarPresets, conectarPase } from "./pase-interactivo";

const BASE = import.meta.env.BASE_URL;
const SITIO = new URL(BASE, "https://bajaloreto.github.io").toString();

type Pos = [number, number];
type Anillo = Pos[];
type Geo = { type: "Polygon"; coordinates: Anillo[] } | { type: "MultiPolygon"; coordinates: Anillo[][] };

const COLOR: Record<Politica, string> = {
  "aprovechamiento-sustentable": "#d08a2e", "conservacion": "#2f7d4a", "preservacion": "#8cc06d", "restauracion": "#c0533a",
};

const $ = <T extends HTMLElement>(s: string) => document.querySelector<T>(s)!;
const lado = $("#lado"), filas = $("#filas"), aviso = $("#aviso"), coord = $("#coord");

// ---------- geometría ----------
function dentroAnillo([x, y]: Pos, anillo: Anillo) {
  let dentro = false;
  for (let i = 0, j = anillo.length - 1; i < anillo.length; j = i++) {
    const [xi, yi] = anillo[i], [xj, yj] = anillo[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) dentro = !dentro;
  }
  return dentro;
}
function dentro(p: Pos, g: Geo) {
  const polis = g.type === "Polygon" ? [g.coordinates] : g.coordinates;
  return polis.some(([ext, ...huecos]) => dentroAnillo(p, ext) && !huecos.some((h) => dentroAnillo(p, h)));
}
const distanciaKm = (a: Pos, b: Pos) => {
  const r = Math.PI / 180, dLat = (b[1] - a[1]) * r, dLon = (b[0] - a[0]) * r;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(a[1] * r) * Math.cos(b[1] * r) * Math.sin(dLon / 2) ** 2;
  return 12742 * Math.asin(Math.sqrt(h));
};
const sinAcentos = (s: string) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim();

// ---------- carga ----------
const json = (url: string) => fetch(url).then((r) => { if (!r.ok) throw new Error(String(r.status)); return r.json(); });
lado.addEventListener("click", (e) => {
  if ((e.target as HTMLElement).closest('[data-accion="reintentar"]') && !seleccion) location.reload();
});
let datos: [Resumen[], any, any, Awaited<ReturnType<typeof cargarPresets>>];
try {
  datos = await Promise.all([json(`${BASE}datos/indice.json`), json(`${BASE}datos/ugas.geojson`), json(`${BASE}datos/contexto.geojson`), cargarPresets()]);
} catch {
  lado.innerHTML = htmlError("Revisa tu conexión a internet: el mapa y las fichas no terminaron de descargarse.");
  throw new Error("No se pudieron cargar los datos de ePOEL");
}
const [indice, ugasGeo, contexto, presets] = datos;
const porId = new Map(indice.map((u) => [u.id, u]));
const geoPorId = new Map<string, Geo>(ugasGeo.features.map((f: any) => [f.properties.id, f.geometry]));
const tierra: Geo = contexto.features.find((f: any) => f.properties.capa === "tierra").geometry;
const localidades = contexto.features.filter((f: any) => f.properties.capa === "localidad")
  .map((f: any) => ({ nombre: f.properties.nombre as string, pos: f.geometry.coordinates as Pos, poblacion: f.properties.poblacion as number }));

// ---------- mapa ----------
const mapa = new Mapa({
  container: "mapa",
  bounds: [[-111.86, 25.33], [-110.94, 26.6]],
  fitBoundsOptions: { padding: 20 },
  attributionControl: { compact: true, customAttribution: "Datos: POEL Loreto (Boletín Oficial de B.C.S. No. 12, 2014) · Contexto: INEGI vía ePOEL 2019" },
  style: {
    version: 8,
    sources: {
      contexto: { type: "geojson", data: contexto },
      ugas: { type: "geojson", data: ugasGeo, promoteId: "id" },
      seleccion: { type: "geojson", data: { type: "FeatureCollection", features: [] } },
      satelite: {
        type: "raster", tileSize: 256, maxzoom: 15,
        tiles: ["https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2024_3857/default/g/{z}/{y}/{x}.jpg"],
        attribution: 'Sentinel-2 cloudless — <a href="https://s2maps.eu" target="_blank" rel="noopener">s2maps.eu</a> by EOX IT Services GmbH (Contains modified Copernicus Sentinel data 2024), CC BY-NC-SA 4.0',
      },
    },
    layers: [
      { id: "mar", type: "background", paint: { "background-color": "#d7e2ea" } },
      { id: "tierra", type: "fill", source: "contexto", filter: ["==", ["get", "capa"], "tierra"], paint: { "fill-color": "#f7f8f9" } },
      { id: "satelite", type: "raster", source: "satelite", layout: { visibility: "none" } },
      { id: "ugas-relleno", type: "fill", source: "ugas", paint: {
        "fill-color": ["match", ["get", "politica"], "aprovechamiento-sustentable", COLOR["aprovechamiento-sustentable"], "conservacion", COLOR.conservacion, "preservacion", COLOR.preservacion, "restauracion", COLOR.restauracion, "#9aa1a8"],
        "fill-opacity": ["case", ["==", ["get", "procedencia"], "epoel-2019"], 0.28, 0.42],
      } },
      { id: "ugas-borde", type: "line", source: "ugas", paint: {
        "line-color": ["match", ["get", "politica"], "aprovechamiento-sustentable", COLOR["aprovechamiento-sustentable"], "conservacion", COLOR.conservacion, "preservacion", COLOR.preservacion, "restauracion", COLOR.restauracion, "#9aa1a8"],
        "line-width": 1.2,
      } },
      { id: "ugas-borde-prov", type: "line", source: "ugas", filter: ["==", ["get", "procedencia"], "epoel-2019"], paint: { "line-color": "#646a71", "line-width": 1, "line-dasharray": [2, 2] } },
      { id: "caminos", type: "line", source: "contexto", filter: ["==", ["get", "capa"], "camino"], paint: { "line-color": "#6b737c", "line-width": ["interpolate", ["linear"], ["zoom"], 8, 0.8, 13, 2.4] } },
      { id: "sel-halo", type: "line", source: "seleccion", paint: { "line-color": "#ffffff", "line-width": 7 } },
      { id: "sel-borde", type: "line", source: "seleccion", paint: { "line-color": "#0b0d10", "line-width": 3.2 } },
    ],
  },
});

// Rótulos como HTML (sin servidor de tipografías externo)
const rotulosUga: Marker[] = [];
for (const u of indice) if (u.centro) {
  const el = document.createElement("div");
  el.className = "etq-uga";
  el.dataset.uga = u.id;
  el.textContent = u.id;
  rotulosUga.push(new Marker({ element: el }).setLngLat(u.centro).addTo(mapa));
}
const rotulosLoc = localidades.filter((l: { poblacion: number }) => (l.poblacion ?? 0) >= 20).map((l: { nombre: string; pos: Pos; poblacion: number }) => {
  const el = document.createElement("div");
  el.className = "etq-loc";
  el.textContent = l.nombre;
  return { m: new Marker({ element: el, anchor: "left", offset: [-3, 0] }).setLngLat(l.pos).addTo(mapa), pob: l.poblacion };
});
{
  const el = document.createElement("div");
  el.className = "etq-mar";
  el.textContent = "GOLFO DE CALIFORNIA";
  new Marker({ element: el }).setLngLat([-111.08, 25.98]).addTo(mapa);
}
function ajustarRotulos() {
  const z = mapa.getZoom();
  rotulosUga.forEach((m) => (m.getElement().style.display = z >= 10.2 ? "" : "none"));
  rotulosLoc.forEach(({ m, pob }) => (m.getElement().style.display = z >= 11 || (z >= 9 && pob >= 300) || pob >= 5000 ? "" : "none"));
}

const pin = (() => {
  const el = document.createElement("div");
  el.innerHTML = `<svg width="26" height="34" viewBox="0 0 26 34" aria-hidden="true"><path d="M13 33s11-11.6 11-20A11 11 0 0 0 2 13c0 8.4 11 20 11 20z" fill="#ffd400" stroke="#0b0d10" stroke-width="2"/><circle cx="13" cy="13" r="4" fill="#0b0d10"/></svg>`;
  return new Marker({ element: el, anchor: "bottom" });
})();

// ---------- estado ----------
let seleccion: string | null = null;
let referencia: Pos | null = null;
let presetActual = "casa";

function urlEstado() {
  const p = new URLSearchParams();
  if (seleccion) p.set("uga", seleccion);
  if (referencia) p.set("punto", referencia.map((v) => v.toFixed(5)).join(","));
  if (presetActual !== "casa") p.set("hacer", presetActual);
  history.replaceState(null, "", `${location.pathname}${p.size ? `?${p}` : ""}`);
}

function mostrarCoord(p: Pos) {
  const [e, n] = geoAUtm(p[0], p[1]);
  coord.textContent = `${p[1].toFixed(4)} N  ${Math.abs(p[0]).toFixed(4)} O  ·  UTM 12N ${Math.round(e)} E  ${Math.round(n)} N`;
}

// ---------- tablero ----------
let filaNueva: string | null = null;
const observador = new IntersectionObserver((entradas) => {
  for (const e of entradas) if (e.isIntersecting && (e.target as HTMLElement).dataset.uga === filaNueva) {
    setTimeout(() => { filaNueva = null; e.target.classList.remove("nueva"); }, 1600);
    observador.unobserve(e.target);
  }
}, { threshold: 0.9 });

function pintarTablero() {
  const b = mapa.getBounds();
  const ref = referencia ?? (seleccion && porId.get(seleccion)?.centro) ?? ([mapa.getCenter().lng, mapa.getCenter().lat] as Pos);
  // Con una UGA consultada se listan sus vecinas más cercanas; sin consulta, las que están a la vista
  const candidatas = indice.filter((u) => u.centro && (seleccion || b.contains(u.centro)));
  const visibles = candidatas.map((u) => ({ u, d: distanciaKm(ref, u.centro!) }))
    .sort((a, b) => (a.u.id === seleccion ? -1 : b.u.id === seleccion ? 1 : a.d - b.d))
    .slice(0, seleccion ? 12 : 60);
  $("#titulo-tablero").textContent = seleccion ? "UGAs cercanas" : "UGAs en esta vista";
  // Reordenamiento en su lugar: cada fila conserva su identidad y se desplaza (FLIP)
  const antes = new Map([...filas.children].map((tr) => [(tr as HTMLElement).dataset.uga!, tr.getBoundingClientRect().top]));
  const existentes = new Map([...filas.children].map((tr) => [(tr as HTMLElement).dataset.uga!, tr as HTMLTableRowElement]));
  const nuevas: HTMLTableRowElement[] = visibles.map(({ u, d }) => {
    const tr = existentes.get(u.id) ?? document.createElement("tr");
    tr.dataset.uga = u.id;
    tr.className = [u.id === seleccion ? "sel" : "", u.id === filaNueva ? "nueva" : ""].join(" ").trim();
    tr.tabIndex = 0;
    tr.setAttribute("aria-label", `${u.nombre}, ${u.politica ? POLITICA[u.politica] : ""}`);
    tr.innerHTML = `<td class="cifra">${u.id.toUpperCase()}</td>
      <td><span class="pol"><i style="background:${u.politica ? COLOR[u.politica] : "#9aa1a8"}"></i>${u.politica ? POLITICA[u.politica] : "—"}</span></td>
      <td class="cifra">${u.id === seleccion ? "AQUÍ" : `${d.toFixed(1)} km`}</td>
      <td>${u.incidencia ? `<span class="inc cifra" title="Aviso ${u.incidencia}">${u.incidencia.replace("INC-", "")}</span>`
        : u.nota ? `<span class="inc-nota cifra" title="Nota ${u.nota}">${u.nota.replace("INC-", "")}</span>` : `<span class="nada">—</span>`}</td>`;
    return tr;
  });
  filas.replaceChildren(...nuevas);
  const fn = filaNueva && nuevas.find((tr) => tr.dataset.uga === filaNueva);
  if (fn) observador.observe(fn);
  if (!nuevas.length) filas.innerHTML = `<tr class="sin-ugas"><td colspan="4">No hay UGAs en esta vista. Aleja el mapa o busca un lugar.</td></tr>`;
  $("#cuenta").textContent = String(visibles.length);
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  for (const tr of nuevas) {
    const t0 = antes.get(tr.dataset.uga!);
    if (t0 === undefined) continue;
    const dy = t0 - tr.getBoundingClientRect().top;
    if (Math.abs(dy) > 1) tr.animate([{ transform: `translateY(${dy}px)` }, { transform: "translateY(0)" }], { duration: 420, easing: "cubic-bezier(.2,.8,.2,1)" });
  }
}
filas.addEventListener("click", (e) => {
  const tr = (e.target as HTMLElement).closest("tr");
  if (tr) seleccionar(tr.dataset.uga!, { encuadrar: true });
});
filas.addEventListener("keydown", (e) => {
  const tr = (e.target as HTMLElement).closest("tr");
  if (tr && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); seleccionar(tr.dataset.uga!, { encuadrar: true }); }
});

// ---------- selección ----------
function encuadrar(id: string) {
  const g = geoPorId.get(id);
  if (!g) return;
  const caja = new LngLatBounds();
  (g.type === "Polygon" ? [g.coordinates] : g.coordinates).forEach((p) => p[0].forEach((c) => caja.extend(c)));
  mapa.fitBounds(caja, { padding: 60, maxZoom: 14, duration: 700 });
}

async function seleccionar(id: string, opciones: { punto?: Pos; encuadrar?: boolean } = {}) {
  const resumen = porId.get(id);
  if (!resumen) return;
  const nueva = seleccion !== id;
  seleccion = id;
  referencia = opciones.punto ?? null;
  const g = geoPorId.get(id);
  (mapa.getSource("seleccion") as GeoJSONSource).setData(g ? { type: "Feature", properties: {}, geometry: g } : { type: "FeatureCollection", features: [] });
  document.querySelectorAll(".etq-uga.sel").forEach((e) => e.classList.remove("sel"));
  document.querySelector(`.etq-uga[data-uga="${id}"]`)?.classList.add("sel");
  if (opciones.punto) { pin.setLngLat(opciones.punto).addTo(mapa); mostrarCoord(opciones.punto); } else pin.remove();
  if (opciones.encuadrar) encuadrar(id);

  if (nueva) filaNueva = id;
  pintarTablero();
  lado.innerHTML = htmlPaseCargando(resumen);
  let ficha;
  try {
    ficha = await cargarFicha(id);
  } catch {
    lado.innerHTML = htmlError("La ficha no terminó de descargarse. Revisa tu conexión e inténtalo de nuevo.");
    lado.querySelector('[data-accion="reintentar"]')?.addEventListener("click", () => seleccionar(id, opciones));
    return;
  }
  if (seleccion !== id) return; // el usuario ya consultó otra UGA mientras cargaba
  const enlace = `${SITIO}poel/uga/${id}/`;
  const qr = qrcode(0, "M");
  qr.addData(enlace);
  qr.make();
  lado.innerHTML = htmlPase(ficha, presets, presetActual, { qr: qr.createSvgTag({ cellSize: 2, margin: 0, scalable: true }), enlace });
  const pase = lado.querySelector<HTMLElement>(".pase")!;
  // El pase se "reimprime" segmento por segmento, de arriba abajo, como sale de la impresora
  if (nueva && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
    [...pase.children].forEach((el, i) => (el as HTMLElement).animate(
      [{ clipPath: "inset(0 0 100% 0)" }, { clipPath: "inset(0 0 0 0)" }],
      { duration: 340, delay: i * 55, easing: "cubic-bezier(.16,1,.3,1)", fill: "backwards" }));
  }
  conectarPase(pase, (p) => { presetActual = p; urlEstado(); });
  urlEstado();
}

function fueraDeCobertura(p: Pos, enTierra: boolean) {
  seleccion = null;
  referencia = p;
  (mapa.getSource("seleccion") as GeoJSONSource).setData({ type: "FeatureCollection", features: [] });
  pin.setLngLat(p).addTo(mapa);
  mostrarCoord(p);
  lado.innerHTML = enTierra
    ? `<div class="vacio"><h1>Zona aún sin polígono</h1><p>Este punto está en tierra dentro del municipio, pero todavía no tenemos digitalizado el polígono de la UGA que le corresponde. Estamos re-digitalizando las UGAs desde los mapas del Boletín Oficial.</p>
       <p>Mientras tanto, consulta el <a href="${BOLETIN_COMPLETO}#page=136" target="_blank" rel="noopener">Apéndice 10 del Boletín</a> (PDF completo, 40 MB) o elige una UGA cercana en el tablero.</p></div>`
    : `<div class="vacio externo"><h1>Este punto no está cubierto por el POEL de Loreto</h1><p>El POEL regula la parte terrestre del municipio. En el mar o fuera del municipio probablemente aplica otro instrumento:</p>
       <ul><li><a href="https://www.gob.mx/semarnat/acciones-y-programas/bitacora-ambiental-golfo-de-california" target="_blank" rel="noopener">Programa de Ordenamiento Ecológico Marino del Golfo de California</a> (bitácora ambiental, SEMARNAT) </li>
       <li><a href="https://simec.conanp.gob.mx/ficha.php?anp=31&reg=3" target="_blank" rel="noopener">Parque Nacional Bahía de Loreto</a> (ficha CONANP)</li></ul></div>`;
  pintarTablero();
  urlEstado();
}

function consultarPunto(p: Pos, opciones: { volar?: boolean } = {}) {
  if (opciones.volar) mapa.flyTo({ center: p, zoom: Math.max(mapa.getZoom(), 12.5), duration: 800 });
  for (const [id, g] of geoPorId) if (dentro(p, g)) return seleccionar(id, { punto: p });
  fueraDeCobertura(p, dentro(p, tierra));
}

mapa.on("click", (e) => consultarPunto([e.lngLat.lng, e.lngLat.lat]));
mapa.on("mousemove", "ugas-relleno", () => (mapa.getCanvas().style.cursor = "pointer"));
mapa.on("mouseleave", "ugas-relleno", () => (mapa.getCanvas().style.cursor = ""));
mapa.on("zoom", ajustarRotulos);
mapa.on("moveend", () => pintarTablero());

// ---------- búsqueda ----------
function interpretar(q: string): { tipo: "uga"; id: string } | { tipo: "punto"; p: Pos } | null {
  const t = q.trim();
  const uga = t.match(/^(?:uga\s*[-–]?\s*)?(\d{1,2}\s*[a-f]?)$/i);
  if (uga) {
    const id = uga[1].replace(/\s/g, "").toLowerCase();
    if (porId.has(id)) return { tipo: "uga", id };
  }
  const nums = t.replace(/[°ºNnOoWw]/g, " ").match(/-?\d+(?:\.\d+)?/g)?.map(Number) ?? [];
  if (nums.length === 2) {
    const [a, b] = nums;
    const e = [a, b].find((v) => v >= 100000 && v < 1000000), n = [a, b].find((v) => v >= 1000000 && v < 10000000);
    if (e && n) return { tipo: "punto", p: utmAGeo(e, n) };
    const lat = [a, b].find((v) => Math.abs(v) >= 20 && Math.abs(v) <= 32);
    const lon = [a, b].find((v) => Math.abs(v) >= 105 && Math.abs(v) <= 118);
    if (lat && lon) return { tipo: "punto", p: [-Math.abs(lon), Math.abs(lat)] };
  }
  const nombre = sinAcentos(t);
  if (nombre.length >= 3) {
    const loc = localidades.filter((l: { nombre: string }) => sinAcentos(l.nombre).includes(nombre))
      .sort((x: { poblacion: number }, y: { poblacion: number }) => (y.poblacion ?? 0) - (x.poblacion ?? 0))[0];
    if (loc) return { tipo: "punto", p: loc.pos };
    const porLocalidad = indice.find((u) => u.localidad && sinAcentos(u.localidad).includes(nombre));
    if (porLocalidad) return { tipo: "uga", id: porLocalidad.id };
  }
  return null;
}

function ejecutar(q: string) {
  aviso.hidden = true;
  const r = interpretar(q);
  if (!r) {
    aviso.innerHTML = `No encontramos <b>${q.replace(/</g, "&lt;")}</b>. Prueba con una localidad (<code>Nopoló</code>), coordenadas (<code>25.93, -111.36</code>), UTM (<code>463701 2868159</code>) o una UGA (<code>UGA 45</code>).`;
    aviso.hidden = false;
    return;
  }
  if (r.tipo === "uga") seleccionar(r.id, { encuadrar: true });
  else consultarPunto(r.p, { volar: true });
}
$("#buscar").addEventListener("submit", (e) => { e.preventDefault(); ejecutar($<HTMLInputElement>("#q").value); });
$<HTMLInputElement>("#q").addEventListener("input", () => (aviso.hidden = true));
lado.addEventListener("click", (e) => {
  const b = (e.target as HTMLElement).closest<HTMLButtonElement>("[data-ejemplo]");
  if (b) { $<HTMLInputElement>("#q").value = b.dataset.ejemplo!; ejecutar(b.dataset.ejemplo!); }
});
$("#gps").addEventListener("click", () => {
  if (!navigator.geolocation) return;
  navigator.geolocation.getCurrentPosition(
    (pos) => consultarPunto([pos.coords.longitude, pos.coords.latitude], { volar: true }),
    () => { aviso.textContent = "No pudimos obtener tu ubicación. Revisa el permiso de ubicación del navegador."; aviso.hidden = false; },
    { enableHighAccuracy: true, timeout: 10000 },
  );
});

// ---------- capas ----------
$("#b-satelite").addEventListener("click", (e) => {
  const b = e.currentTarget as HTMLButtonElement;
  const on = b.getAttribute("aria-pressed") !== "true";
  b.setAttribute("aria-pressed", String(on));
  mapa.setLayoutProperty("satelite", "visibility", on ? "visible" : "none");
  mapa.setPaintProperty("tierra", "fill-opacity", on ? 0 : 1);
});

// ---------- inicio desde la URL ----------
mapa.on("load", () => {
  ajustarRotulos();
  // El crédito del mapa empieza plegado para no tapar el mapa en pantallas chicas
  const plegar = () => document.querySelector(".maplibregl-ctrl-attrib")?.classList.remove("maplibregl-compact-show");
  plegar();
  mapa.once("idle", plegar);
  mapa.on("resize", plegar);
  const p = new URLSearchParams(location.search);
  presetActual = presets.some((x) => x.id === p.get("hacer")) ? p.get("hacer")! : "casa";
  const punto = p.get("punto")?.split(",").map(Number) as Pos | undefined;
  if (punto?.length === 2 && punto.every(Number.isFinite)) consultarPunto(punto, { volar: true });
  else if (p.get("uga") && porId.has(p.get("uga")!)) seleccionar(p.get("uga")!, { encuadrar: true });
  else pintarTablero();
});
