// Lectura de los datos generados por herramientas/construir_geodatos.py, en tiempo de construcción.
import type { Ficha, Preset } from "./pase";
import presets from "../../public/datos/presets.json";

const fichas = import.meta.glob<Ficha>("../../public/datos/fichas/*.json", { eager: true, import: "default" });

export const PRESETS = presets as Preset[];

export function todasLasFichas(): Ficha[] {
  const orden = (id: string) => [parseInt(id, 10), id] as const;
  return Object.values(fichas).sort((a, b) => {
    const [na, ia] = orden(a.id), [nb, ib] = orden(b.id);
    return na - nb || ia.localeCompare(ib);
  });
}
