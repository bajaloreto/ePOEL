// Comportamiento del pase, compartido por la consulta y las páginas estáticas de cada UGA.
import { htmlCriterios, type Ficha, type Preset } from "../lib/pase";

const BASE = import.meta.env.BASE_URL;
let presetsCache: Preset[] | null = null;
const fichasCache = new Map<string, Promise<Ficha>>();

export async function cargarPresets(): Promise<Preset[]> {
  presetsCache ??= await fetch(`${BASE}datos/presets.json`).then((r) => r.json());
  return presetsCache!;
}

export function cargarFicha(id: string): Promise<Ficha> {
  if (!fichasCache.has(id)) fichasCache.set(id, fetch(`${BASE}datos/fichas/${id}.json`).then((r) => r.json()));
  return fichasCache.get(id)!;
}

export function conectarPase(pase: HTMLElement, alCambiarPreset?: (id: string) => void) {
  const id = pase.dataset.uga!;
  const lista = pase.querySelector<HTMLElement>(".criterios")!;
  const porActividad = pase.querySelector<HTMLElement>(".por-actividad")!;

  pase.querySelectorAll<HTMLButtonElement>("[data-preset]").forEach((b) =>
    b.addEventListener("click", async () => {
      const [ficha, presets] = await Promise.all([cargarFicha(id), cargarPresets()]);
      const preset = presets.find((p) => p.id === b.dataset.preset)!;
      pase.querySelectorAll("[data-preset]").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
      porActividad.innerHTML = htmlCriterios(ficha, preset);
      lista.scrollTop = 0;
      alCambiarPreset?.(preset.id);
    }),
  );

  // La cabecera se compacta mientras se recorren los criterios (solo cuando el pase tiene su propio desplazamiento)
  lista.addEventListener("scroll", () => pase.classList.toggle("compacto", lista.scrollTop > 24), { passive: true });

  pase.querySelector('[data-accion="imprimir"]')?.addEventListener("click", () => window.print());
  pase.querySelector<HTMLButtonElement>('[data-accion="copiar"]')?.addEventListener("click", async (e) => {
    const b = e.currentTarget as HTMLButtonElement;
    const enlace = b.dataset.enlace ?? location.href;
    try {
      await navigator.clipboard.writeText(enlace);
      b.textContent = "Enlace copiado";
    } catch {
      b.textContent = "Copia la dirección del navegador";
    }
    setTimeout(() => (b.textContent = "Copiar enlace"), 2200);
  });
}

// Al imprimir se abren todos los grupos para que la ficha impresa quede completa
let abiertos: HTMLDetailsElement[] = [];
addEventListener("beforeprint", () => {
  document.querySelectorAll(".pase.compacto").forEach((p) => p.classList.remove("compacto"));
  abiertos = [...document.querySelectorAll<HTMLDetailsElement>("details.grupo")].filter((d) => d.open);
  document.querySelectorAll<HTMLDetailsElement>("details.grupo").forEach((d) => { d.removeAttribute("name"); d.open = true; });
});
addEventListener("afterprint", () => {
  document.querySelectorAll<HTMLDetailsElement>("details.grupo").forEach((d) => { d.open = abiertos.includes(d); d.setAttribute("name", "grupos"); });
});
