"""Publica el Boletín Oficial No. 12 en el sitio, completo y en extractos ligeros.

El servidor del Gobierno del Estado (finanzas.bcs.gob.mx) no siempre responde, y el PDF completo pesa ~40 MB y no
está linealizado: el navegador lo descarga entero antes de mostrar una página, lo que en un celular con mala señal
equivale a no poder consultarlo. Por eso se publican:

  - public/fuentes/boletin-oficial-bcs-12-2014.pdf: copia íntegra, sin modificar (se verifica su SHA-256).
  - public/fuentes/criterios.pdf: pp. 78–118, donde están los criterios de regulación ecológica que citan los pases.
  - public/fuentes/fichas/<id>.pdf: las páginas de la ficha de cada UGA (Apéndice 10).
  - public/fuentes/manifiesto.json: huella del original y rangos de páginas de cada extracto.

Los extractos solo copian páginas: no alteran su contenido.

Uso: .venv/bin/python herramientas/extractos_boletin.py
"""
import hashlib
import json
import shutil

import pymupdf

from boletin import BOLETIN_PDF, BOLETIN_URL, DATOS, RAIZ

SALIDA = RAIZ / "public" / "fuentes"
COMPLETO = SALIDA / "boletin-oficial-bcs-12-2014.pdf"
PAGINAS_CRITERIOS = (78, 118)
TITULO = "Boletín Oficial del Gobierno del Estado de Baja California Sur No. 12 (12-mar-2014)"


def sha256(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def extracto(doc, desde, hasta, destino):
    nuevo = pymupdf.open()
    nuevo.insert_pdf(doc, from_page=desde - 1, to_page=hasta - 1)
    nuevo.set_metadata({"title": f"Extracto del {TITULO}, pp. {desde}–{hasta}",
                        "subject": f"Copia de las páginas {desde} a {hasta} del original: {BOLETIN_URL}",
                        "producer": "ePOEL (herramientas/extractos_boletin.py)"})
    nuevo.save(destino, garbage=4, deflate=True)
    return destino.stat().st_size


def main():
    (SALIDA / "fichas").mkdir(parents=True, exist_ok=True)
    huella = sha256(BOLETIN_PDF)
    if not COMPLETO.exists() or sha256(COMPLETO) != huella:
        shutil.copyfile(BOLETIN_PDF, COMPLETO)
    doc = pymupdf.open(BOLETIN_PDF)
    manifiesto = {"original": {"url": BOLETIN_URL, "archivo": COMPLETO.name, "sha256": huella,
                               "paginas": doc.page_count, "bytes": COMPLETO.stat().st_size},
                  "criterios": {"archivo": "criterios.pdf", "paginas": list(PAGINAS_CRITERIOS)},
                  "fichas": {}}
    peso = extracto(doc, *PAGINAS_CRITERIOS, SALIDA / "criterios.pdf")
    for ruta in sorted((DATOS / "ugas").glob("*.json")):
        ficha = json.loads(ruta.read_text())
        desde, hasta = ficha["fuente"]["paginas_pdf"]
        peso += extracto(doc, desde, hasta, SALIDA / "fichas" / f"{ficha['id']}.pdf")
        manifiesto["fichas"][ficha["id"]] = [desde, hasta]
    (SALIDA / "manifiesto.json").write_text(json.dumps(manifiesto, ensure_ascii=False, indent=1) + "\n")
    print(f"original {COMPLETO.stat().st_size / 1e6:.1f} MB; extractos {peso / 1e6:.1f} MB "
          f"({len(manifiesto['fichas'])} fichas + criterios)")


if __name__ == "__main__":
    main()
