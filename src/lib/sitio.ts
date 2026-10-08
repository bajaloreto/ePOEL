// Configuración del sitio. CONTACTO: pendiente de que Hugo defina el correo público de reportes.
export const REPO = "https://github.com/bajaloreto/ePOEL";
export const CONTACTO: string | null = null;

export function enlaceReporte(titulo: string): string {
  if (CONTACTO) return `mailto:${CONTACTO}?subject=${encodeURIComponent(titulo)}`;
  return `${REPO}/issues/new?title=${encodeURIComponent(titulo)}&labels=incidencia`;
}
