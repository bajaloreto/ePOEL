// Formulario de contacto con defensas contra spam, sin servidor propio:
//  - campos trampa (un robot los llena; una persona no los ve),
//  - tiempo mínimo de llenado,
//  - un envío por minuto desde el mismo navegador,
//  - límite de enlaces en el mensaje,
//  - hCaptcha y filtro de spam de Web3Forms cuando hay clave.
// Sin clave de Web3Forms, abre el programa de correo con el mensaje ya redactado.
import { CONTACTO } from "../lib/sitio";

const correo = `${CONTACTO.usuario}@${CONTACTO.dominio}`;
const forma = document.querySelector<HTMLFormElement>("#contacto")!;
const estado = document.querySelector<HTMLElement>("#estado")!;
const enviar = document.querySelector<HTMLButtonElement>("#enviar")!;
const abierto = Date.now();
const TIEMPO_MINIMO_MS = 5000;
const ESPERA_ENTRE_ENVIOS_MS = 60_000;
const MAX_ENLACES = 3;

document.querySelector("#correo-publico")!.textContent = correo;

// Asunto y UGA llegan desde el botón «Reportar» del pase
const q = new URLSearchParams(location.search);
const asunto = q.get("asunto")?.slice(0, 120);
const uga = q.get("uga")?.slice(0, 8);
if (asunto) (document.querySelector("#asunto") as HTMLInputElement).value = asunto;
if (uga) {
  (document.querySelector("#uga") as HTMLInputElement).value = uga;
  const m = document.querySelector<HTMLTextAreaElement>("#mensaje")!;
  m.placeholder = `Sobre la UGA ${uga}: …`;
}

const conCaptcha = Boolean(CONTACTO.CLAVE_WEB3FORMS && CONTACTO.captcha);
if (conCaptcha) {
  document.querySelector("#captcha")!.removeAttribute("hidden");
  const s = document.createElement("script");
  s.src = "https://web3forms.com/client/script.js";
  s.async = true;
  s.defer = true;
  document.head.append(s);
}

function avisar(texto: string, tipo: "error" | "ok" | "info" = "info") {
  estado.textContent = texto;
  estado.dataset.tipo = tipo;
}

function leer(clave: string): number {
  try { return Number(localStorage.getItem(clave) ?? 0); } catch { return 0; }
}
function guardar(clave: string, valor: number) {
  try { localStorage.setItem(clave, String(valor)); } catch { /* sin almacenamiento: no se limita */ }
}

forma.addEventListener("input", (e) => (e.target as HTMLElement).removeAttribute("aria-invalid"));

forma.addEventListener("submit", async (e) => {
  e.preventDefault();
  const datos = new FormData(forma);
  // Robots: campos trampa llenos o envío instantáneo. Se responde como si todo saliera bien.
  if (datos.get("sitio_web") || datos.get("botcheck") || Date.now() - abierto < TIEMPO_MINIMO_MS) {
    forma.reset();
    avisar("Gracias, recibimos tu mensaje.", "ok");
    return;
  }
  // minlength solo se comprueba cuando la persona escribe; se valida también aquí
  const campos = forma.elements as unknown as Record<string, HTMLInputElement>;
  const largo = (c: string) => String(datos.get(c) ?? "").trim().length;
  campos.nombre.setCustomValidity(largo("name") >= 2 ? "" : "corto");
  campos.mensaje.setCustomValidity(largo("message") >= 20 ? "" : "corto");
  campos.correo.setCustomValidity(/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(String(datos.get("email")).trim()) ? "" : "formato");
  if (!forma.checkValidity()) {
    const invalido = forma.querySelector<HTMLInputElement>(":invalid");
    invalido?.setAttribute("aria-invalid", "true");
    invalido?.focus();
    avisar(invalido?.id === "correo" ? "Revisa tu correo electrónico." : invalido?.id === "mensaje"
      ? "El mensaje debe tener al menos 20 caracteres." : "Completa tu nombre.", "error");
    return;
  }
  const mensaje = String(datos.get("message"));
  if ((mensaje.match(/https?:\/\//gi) ?? []).length > MAX_ENLACES) {
    avisar(`Incluye como máximo ${MAX_ENLACES} enlaces en el mensaje.`, "error");
    return;
  }
  const ultimo = leer("epoel-contacto");
  if (Date.now() - ultimo < ESPERA_ENTRE_ENVIOS_MS) {
    avisar("Ya enviaste un mensaje hace un momento. Espera un minuto para enviar otro.", "error");
    return;
  }

  const asuntoFinal = `${datos.get("subject")}${datos.get("uga") ? ` [UGA ${datos.get("uga")}]` : ""}`;
  if (!CONTACTO.CLAVE_WEB3FORMS) {
    const cuerpo = `${mensaje}\n\n— ${datos.get("name")} <${datos.get("email")}>`;
    location.href = `mailto:${correo}?subject=${encodeURIComponent(asuntoFinal)}&body=${encodeURIComponent(cuerpo)}`;
    avisar("Se abrió tu programa de correo con el mensaje listo para enviar.", "ok");
    return;
  }

  if (conCaptcha && !datos.get("h-captcha-response")) {
    avisar("Marca la casilla de verificación antes de enviar.", "error");
    return;
  }
  enviar.disabled = true;
  avisar("Enviando…");
  try {
    const cuerpo = Object.fromEntries(datos);
    delete cuerpo.sitio_web;
    const r = await fetch("https://api.web3forms.com/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ ...cuerpo, access_key: CONTACTO.CLAVE_WEB3FORMS, subject: asuntoFinal, from_name: "ePOEL Loreto" }),
    });
    const res = await r.json().catch(() => ({}));
    if (!r.ok || !res.success) throw new Error(res.message || `HTTP ${r.status}`);
    guardar("epoel-contacto", Date.now());
    forma.reset();
    avisar("Gracias, recibimos tu mensaje. Te responderemos a tu correo.", "ok");
  } catch {
    avisar(`No se pudo enviar. Inténtalo de nuevo o escríbenos directamente a ${correo}.`, "error");
  } finally {
    enviar.disabled = false;
  }
});
