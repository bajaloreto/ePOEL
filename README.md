# ePOEL — Loreto

**Plataforma pública e informativa para consultar los instrumentos de ordenamiento territorial y ambiental del Municipio de Loreto, Baja California Sur.** Empieza por el Programa de Ordenamiento Ecológico Local (POEL) y crecerá hacia otros instrumentos.

> 🚧 **En modernización (2026).** El sitio publicado en https://bajaloreto.github.io/ePOEL sigue siendo la versión 2019 (tag `v1-2019`). La nueva versión se construye por fases; ver [docs/plan-de-accion.md](docs/plan-de-accion.md).

## Qué responde

"¿Qué dice el POEL en este punto?": la Unidad de Gestión Ambiental (UGA), su política ambiental, actividades, lineamientos, estrategias y los criterios de regulación ecológica que aplican, cada dato citado contra el **Boletín Oficial de B.C.S. No. 12 (12‑mar‑2014)**, la única versión con validez jurídica.

## Estructura

```
datos/poel/          Datos estructurados extraídos del Boletín (fuente de verdad: ADR 0001)
  ugas/<id>.json     122 fichas de UGA (Apéndice 10)
  lineamientos.json  Tabla 16 · estrategias.json  Tabla 17 · criterios.json  Tabla 18
  incidencias.json   Discrepancias registradas entre fuentes y su resolución
  digitalizacion/    Borradores de polígonos digitalizados desde los mapas de las fichas (ADR 0002)
herramientas/        Scripts de extracción, digitalización y rescate (Python)
rescate/mapbox-2019/ Capas de soporte rescatadas de los tilesets de ePOEL 2019
docs/adr/            Decisiones de arquitectura
CONTEXT.md           Glosario del dominio (UGA, política ambiental, criterio…)
```

La versión 2019 (`index.html`, `js/`, `css/`, `assets/`, `capas/`) permanece en la raíz hasta que la nueva plataforma la reemplace; después se conservará en `/legacy`.

## Herramientas

Requieren Python 3.11+ y el Boletín en `fuentes/boletin-oficial-bcs-2014-12.pdf` (no se versiona; descárgalo de la [URL oficial](https://finanzas.bcs.gob.mx/wp-content/themes/voice/assets/images/boletines/2014/12.pdf)).

```bash
python3 -m venv .venv && .venv/bin/pip install -r herramientas/requirements.txt
.venv/bin/python herramientas/extraer_tablas_maestras.py   # lineamientos, estrategias, criterios
.venv/bin/python herramientas/extraer_fichas.py            # 122 fichas de UGA
swiftc -O herramientas/ocr/ocr.swift -o herramientas/ocr/ocr   # OCR (macOS) para digitalizar
.venv/bin/python herramientas/digitalizar_fichas.py 12 1a 45   # borradores de polígonos
```

## Créditos y licencias

- Créditos: [CREDITOS.md](CREDITOS.md). Proyecto de Hugo Quintero, Helden Velis y Brenda E. García, impulsado por Eco‑Alianza de Loreto, con financiamiento inicial de Resources Legacy Fund y mantenimiento donado por HuQuMa Studio.
- Código: [MIT](LICENSE). Datos y textos: [LICENSE-DATOS.md](LICENSE-DATOS.md) (datos derivados bajo CC BY 4.0; textos del POEL como información pública del Municipio).
- **Herramienta informativa, no oficial**: ver [docs/descargo.md](docs/descargo.md).

Reporta errores o discrepancias en [Issues](https://github.com/bajaloreto/ePOEL/issues).
