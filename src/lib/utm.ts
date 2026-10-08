// Conversión UTM ⇄ geográficas (WGS84). Loreto está en la zona 12 norte.
const A = 6378137;
const F = 1 / 298.257223563;
const K0 = 0.9996;
const E2 = F * (2 - F);
const EP2 = E2 / (1 - E2);
const rad = (g: number) => (g * Math.PI) / 180;
const meridiano = (zona: number) => rad((zona - 1) * 6 - 180 + 3);

export function utmAGeo(este: number, norte: number, zona = 12): [number, number] {
  const x = este - 500000;
  const mu = norte / K0 / (A * (1 - E2 / 4 - (3 * E2 ** 2) / 64 - (5 * E2 ** 3) / 256));
  const e1 = (1 - Math.sqrt(1 - E2)) / (1 + Math.sqrt(1 - E2));
  const phi1 = mu
    + ((3 * e1) / 2 - (27 * e1 ** 3) / 32) * Math.sin(2 * mu)
    + ((21 * e1 ** 2) / 16 - (55 * e1 ** 4) / 32) * Math.sin(4 * mu)
    + ((151 * e1 ** 3) / 96) * Math.sin(6 * mu)
    + ((1097 * e1 ** 4) / 512) * Math.sin(8 * mu);
  const s = Math.sin(phi1), c = Math.cos(phi1), t = Math.tan(phi1);
  const n1 = A / Math.sqrt(1 - E2 * s * s);
  const t1 = t * t, c1 = EP2 * c * c;
  const r1 = (A * (1 - E2)) / Math.pow(1 - E2 * s * s, 1.5);
  const d = x / (n1 * K0);
  const lat = phi1 - ((n1 * t) / r1) * (d ** 2 / 2
    - ((5 + 3 * t1 + 10 * c1 - 4 * c1 ** 2 - 9 * EP2) * d ** 4) / 24
    + ((61 + 90 * t1 + 298 * c1 + 45 * t1 ** 2 - 252 * EP2 - 3 * c1 ** 2) * d ** 6) / 720);
  const lon = meridiano(zona) + (d - ((1 + 2 * t1 + c1) * d ** 3) / 6
    + ((5 - 2 * c1 + 28 * t1 - 3 * c1 ** 2 + 8 * EP2 + 24 * t1 ** 2) * d ** 5) / 120) / c;
  return [(lon * 180) / Math.PI, (lat * 180) / Math.PI];
}

export function geoAUtm(lon: number, lat: number, zona = 12): [number, number] {
  const phi = rad(lat), s = Math.sin(phi), c = Math.cos(phi), t = Math.tan(phi);
  const n = A / Math.sqrt(1 - E2 * s * s);
  const tt = t * t, cc = EP2 * c * c, aa = c * (rad(lon) - meridiano(zona));
  const m = A * ((1 - E2 / 4 - (3 * E2 ** 2) / 64 - (5 * E2 ** 3) / 256) * phi
    - ((3 * E2) / 8 + (3 * E2 ** 2) / 32 + (45 * E2 ** 3) / 1024) * Math.sin(2 * phi)
    + ((15 * E2 ** 2) / 256 + (45 * E2 ** 3) / 1024) * Math.sin(4 * phi)
    - ((35 * E2 ** 3) / 3072) * Math.sin(6 * phi));
  const este = K0 * n * (aa + ((1 - tt + cc) * aa ** 3) / 6 + ((5 - 18 * tt + tt ** 2 + 72 * cc - 58 * EP2) * aa ** 5) / 120) + 500000;
  const norte = K0 * (m + n * t * (aa ** 2 / 2 + ((5 - tt + 9 * cc + 4 * cc ** 2) * aa ** 4) / 24
    + ((61 - 58 * tt + tt ** 2 + 600 * cc - 330 * EP2) * aa ** 6) / 720));
  return [este, norte];
}
