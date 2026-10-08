// Configuración del sitio.
const BASE = import.meta.env.BASE_URL;
export const REPO = "https://github.com/bajaloreto/ePOEL";

// Contacto público. El formulario envía por Web3Forms (https://web3forms.com): su clave de acceso es pública por
// diseño y se obtiene escribiendo el correo de destino en esa página. Mientras CLAVE_WEB3FORMS sea null, el
// formulario abre el programa de correo del visitante con el mensaje ya redactado.
export const CONTACTO = {
  usuario: "info",
  dominio: "loreto.com",
  CLAVE_WEB3FORMS: null as string | null,
  // hCaptcha gratuito de Web3Forms: solo se carga en la página de contacto y solo si hay clave
  captcha: true,
};

export function enlaceReporte(titulo: string, uga?: string): string {
  const q = new URLSearchParams({ asunto: titulo, ...(uga ? { uga } : {}) });
  return `${BASE}contacto/?${q}`;
}

// Boletín Oficial No. 12 alojado en el sitio (herramientas/extractos_boletin.py): el original completo pesa ~40 MB y
// no está linealizado, así que las citas apuntan a extractos ligeros con las mismas páginas.
export const BOLETIN_OFICIAL = "https://finanzas.bcs.gob.mx/wp-content/themes/voice/assets/images/boletines/2014/12.pdf";
export const BOLETIN_COMPLETO = `${BASE}fuentes/boletin-oficial-bcs-12-2014.pdf`;
const CRITERIOS = { desde: 78, hasta: 118 };

export function enlaceBoletin(pagina: number): string {
  return pagina >= CRITERIOS.desde && pagina <= CRITERIOS.hasta
    ? `${BASE}fuentes/criterios.pdf#page=${pagina - CRITERIOS.desde + 1}`
    : `${BOLETIN_COMPLETO}#page=${pagina}`;
}

export const enlaceFicha = (id: string) => `${BASE}fuentes/fichas/${encodeURIComponent(id)}.pdf`;
