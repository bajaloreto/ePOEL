// Renderizador único del "pase" de una UGA: lo usan las páginas estáticas (/poel/uga/<id>/)
// y la consulta interactiva, para que ambas muestren exactamente lo mismo.
import { enlaceBoletin, enlaceFicha, enlaceReporte } from "./sitio";

export type Politica = "aprovechamiento-sustentable" | "conservacion" | "preservacion" | "restauracion";

export interface Nivel { nivel: "baja" | "media" | "alta" | null; nota: string | null }
export interface Criterio { id: string; texto: string; pagina: number }
export interface GrupoCriterios { grupo: string; nombre: string; items: Criterio[] }

export interface Ficha {
  id: string;
  numero: number;
  nombre: string;
  superficie_ha: number;
  localidad_referencia: string | null;
  poblacion: string | null;
  actividad: string;
  politica: Politica | null;
  politica_texto: string;
  conflictos_potenciales: string | null;
  areas_atencion_especial: { area: string; justificacion: string }[];
  fragilidad: Nivel | null;
  vulnerabilidad: Nivel | null;
  presion: Nivel | null;
  lineamientos: { id: string | null; texto: string }[];
  estrategias: { id: string; titulo: string }[];
  estrategias_particulares: string | null;
  criterios: GrupoCriterios[];
  fuente: { documento: string; url: string; paginas_pdf: [number, number] };
  procedencia_geometria: { metodo: string; texto: string; precision_m: number | null; revisada: boolean; validacion?: string };
  incidencias: { id: string; nivel: "aviso" | "nota"; texto: string }[];
}

export interface Resumen {
  id: string; nombre: string; politica: Politica | null; actividad: string; superficie_ha: number;
  localidad: string | null; presion: string | null; procedencia: string; incidencias: number;
  incidencia: string | null; nota: string | null; centro?: [number, number];
}

export interface Preset { id: string; nombre: string; corto: string; grupos: string[] | null }

export const POLITICA: Record<Politica, string> = {
  "aprovechamiento-sustentable": "Aprovechamiento sustentable",
  "conservacion": "Conservación",
  "preservacion": "Preservación",
  "restauracion": "Restauración",
};

const esc = (s: unknown) =>
  String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]!);

const cap = (s: string | null | undefined) => (s ? s.charAt(0).toUpperCase() + s.slice(1) : "—");
const ha = (n: number) => n.toLocaleString("es-MX", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const poblacion = (p: string | null) => {
  if (!p) return "—";
  if (/cero|despoblad/i.test(p)) return "0";
  const m = p.match(/[\d,]+/);
  return m ? m[0] : p;
};

export function gruposDe(ficha: Ficha, preset: Preset): GrupoCriterios[] {
  if (!preset.grupos) return ficha.criterios;
  return preset.grupos.map((g) => ficha.criterios.find((c) => c.grupo === g)).filter(Boolean) as GrupoCriterios[];
}

export function htmlCriterios(ficha: Ficha, preset: Preset): string {
  const grupos = gruposDe(ficha, preset);
  const total = grupos.reduce((n, g) => n + g.items.length, 0);
  const resumen = grupos.length
    ? `${esc(preset.nombre)}: aplican <b>${total} criterios</b> en ${grupos.length} ${grupos.length === 1 ? "grupo" : "grupos"}.`
    : `${esc(preset.nombre)}: esta UGA no tiene criterios de esos grupos.`;
  return `<p class="resumen">${resumen}</p>` + grupos.map((g) => `
    <details class="grupo" name="grupos">
      <summary><span>${esc(g.nombre)}</span><span class="cifra">${String(g.items.length).padStart(2, "0")}</span></summary>
      <ol>${g.items.map((c) => `
        <li><span class="cifra codigo">${esc(c.id)}</span><div>${esc(c.texto)}<a class="cita" href="${esc(enlaceBoletin(c.pagina))}" target="_blank" rel="noopener">Boletín, p. ${c.pagina}</a></div></li>`).join("")}
      </ol>
    </details>`).join("");
}

export function htmlPase(ficha: Ficha, presets: Preset[], presetId: string, opciones: { qr?: string; enlace?: string } = {}): string {
  const preset = presets.find((p) => p.id === presetId) ?? presets[0];
  const pres = ficha.presion?.nivel;
  const politica = ficha.politica ? POLITICA[ficha.politica] : ficha.politica_texto;
  const [p0] = ficha.fuente.paginas_pdf;
  const proc = ficha.procedencia_geometria;
  const precision = proc.precision_m ? ` (±${proc.precision_m} m)` : "";
  const poligono = `Polígono ${({ "digitalizada": "digitalizado del mapa de la ficha", "epoel-2019": "provisional de ePOEL 2019, pendiente de re-digitalizar", "sin-geometria": "pendiente de digitalizar" } as Record<string, string>)[proc.metodo] ?? proc.metodo}${precision}${proc.validacion === "revisar" ? ", con revisión pendiente" : ""}.`;
  return `
  <article class="pase" data-uga="${esc(ficha.id)}" aria-label="Ficha de la ${esc(ficha.nombre)}">
    <header class="pase-cab">
      <div>
        <h1>${esc(ficha.nombre)}</h1>
        <p class="pase-lugar">${esc(ficha.localidad_referencia ?? "Sin localidad de referencia")} · ${esc(ficha.actividad)}</p>
      </div>
      <a class="emisor" href="${esc(enlaceFicha(ficha.id))}" target="_blank" rel="noopener" title="Páginas de esta ficha en el Boletín Oficial (PDF)">Boletín Oficial<b class="cifra">No. 12 · p. ${p0}</b>12‑mar‑2014</a>
    </header>
    <p class="linea-compacta">${esc(politica)} · <span class="cifra">${ha(ficha.superficie_ha)} ha</span>${pres ? ` · Presión <b class="${pres === "alta" ? "alerta" : ""}">${cap(pres)}</b>` : ""}</p>
    <div class="compactable"><div>
      <div class="politica" data-politica="${esc(ficha.politica ?? "")}"><span class="etq">Política</span><span class="val">${esc(politica)}</span></div>
      <dl class="segmentos">
        <div><dt>Superficie</dt><dd class="cifra">${ha(ficha.superficie_ha)} ha</dd></div>
        <div><dt>Población</dt><dd class="cifra">${esc(poblacion(ficha.poblacion))}</dd></div>
        <div><dt>Fragilidad</dt><dd>${cap(ficha.fragilidad?.nivel)}</dd></div>
        <div><dt>Presión</dt><dd>${pres === "alta" ? `<mark>${cap(pres)}</mark>` : cap(pres)}</dd></div>
      </dl>
      <ul class="avisos">
        ${ficha.presion?.nota ? `<li>Presión ${esc(ficha.presion.nivel)}: ${esc(ficha.presion.nota)}.</li>` : ""}
        ${ficha.incidencias.map((i) => i.nivel === "aviso"
          ? `<li><mark class="cifra">${esc(i.id)}</mark> ${esc(i.texto)}</li>`
          : `<li class="nota"><span class="cifra">${esc(i.id)}</span> ${esc(i.texto)}</li>`).join("")}
        ${proc.metodo !== "digitalizada" && ficha.incidencias.some((i) => i.id === "INC-007") ? "" : `<li class="nota">${esc(poligono)}</li>`}
      </ul>
    </div></div>
    <div class="perforado" aria-hidden="true"></div>
    <section class="destinos" aria-labelledby="dest-${esc(ficha.id)}">
      <h2 id="dest-${esc(ficha.id)}">¿Qué quieres hacer aquí?</h2>
      <div class="fila" role="group" aria-label="Actividad">${presets.map((p) => `
        <button type="button" data-preset="${esc(p.id)}" aria-pressed="${p.id === preset.id}" title="${esc(p.nombre)}">${esc(p.corto)}</button>`).join("")}
      </div>
    </section>
    <div class="criterios" tabindex="0" aria-label="Criterios que aplican"><div class="por-actividad" aria-live="polite">${htmlCriterios(ficha, preset)}</div>
      <details class="grupo extra" name="grupos"><summary><span>Lineamientos ecológicos</span><span class="cifra">${String(ficha.lineamientos.length).padStart(2, "0")}</span></summary>
        <ol>${ficha.lineamientos.map((l) => `<li><span class="cifra codigo">${esc(l.id ?? "—")}</span><div>${esc(l.texto)}</div></li>`).join("")}</ol></details>
      <details class="grupo extra" name="grupos"><summary><span>Estrategias ecológicas</span><span class="cifra">${String(ficha.estrategias.length).padStart(2, "0")}</span></summary>
        <ol>${ficha.estrategias.map((e) => `<li><span class="cifra codigo">${esc(e.id)}</span><div>${esc(e.titulo)}</div></li>`).join("")}</ol>
        ${ficha.estrategias_particulares ? `<p class="particular">${esc(ficha.estrategias_particulares)}</p>` : ""}</details>
      ${ficha.areas_atencion_especial.length ? `<details class="grupo extra" name="grupos"><summary><span>Áreas de atención especial</span><span class="cifra">${String(ficha.areas_atencion_especial.length).padStart(2, "0")}</span></summary>
        <ol>${ficha.areas_atencion_especial.map((a) => `<li><span class="cifra codigo">·</span><div><b>${esc(a.area)}</b>${a.justificacion ? `. ${esc(a.justificacion)}` : ""}</div></li>`).join("")}</ol></details>` : ""}
    </div>
    <div class="perforado" aria-hidden="true"></div>
    <footer class="talon">
      <div class="talon-txt">
        <p>Informativa: solo el Boletín tiene validez jurídica.</p>
        <div class="acciones">
          <button type="button" class="prim" data-accion="imprimir">Imprimir pase</button>
          <button type="button" data-accion="copiar"${opciones.enlace ? ` data-enlace="${esc(opciones.enlace)}"` : ""}>Copiar enlace</button>
          <a class="boton" data-accion="reportar" href="${esc(enlaceReporte(`Incidencia en la ${ficha.nombre}`, ficha.id))}">Reportar</a>
        </div>
      </div>
      <div class="qr" aria-label="Código QR hacia esta ficha">${opciones.qr ?? ""}</div>
      <div class="talon-id" aria-hidden="true"><span>UGA</span><b>${esc(ficha.id)}</b></div>
      <p class="donado"><span>Desarrollada y donada por</span> <a href="https://huquma.studio/" target="_blank" rel="noopener"><img src="${import.meta.env.BASE_URL}marca/huquma-horizontal.png" alt="HuQuMa Studio" width="75" height="18"></a>
        <span class="alojada">Alojada en</span> <a href="https://loreto.com/" target="_blank" rel="noopener"><img src="${import.meta.env.BASE_URL}marca/loreto-com-oscuro.png" alt="Loreto.com" width="51" height="18"></a></p>
    </footer>
  </article>`;
}

// Mientras llega la ficha, el pase muestra de inmediato lo que ya se sabe de la UGA
export function htmlPaseCargando(r: Resumen): string {
  const politica = r.politica ? POLITICA[r.politica] : "—";
  return `
  <article class="pase cargando" data-uga="${esc(r.id)}" aria-busy="true" aria-label="Cargando la ficha de la ${esc(r.nombre)}">
    <header class="pase-cab"><div><h1>${esc(r.nombre)}</h1><p class="pase-lugar">${esc(r.localidad ?? "Sin localidad de referencia")} · ${esc(r.actividad)}</p></div></header>
    <div class="politica" data-politica="${esc(r.politica ?? "")}"><span class="etq">Política</span><span class="val">${esc(politica)}</span></div>
    <dl class="segmentos">
      <div><dt>Superficie</dt><dd class="cifra">${ha(r.superficie_ha)} ha</dd></div>
      <div><dt>Presión</dt><dd>${r.presion === "alta" ? "<mark>Alta</mark>" : cap(r.presion)}</dd></div>
    </dl>
    <p class="estado-carga">Cargando criterios…</p>
  </article>`;
}

export function htmlError(mensaje: string): string {
  return `<div class="vacio error" role="alert"><h1>No pudimos cargar la información</h1><p>${esc(mensaje)}</p>
    <button type="button" class="reintentar" data-accion="reintentar">Reintentar</button></div>`;
}
