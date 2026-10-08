"""Utilidades comunes para leer el Boletín Oficial de B.C.S. No. 12 (12-mar-2014), que publica el POEL."""
import re
from pathlib import Path

import pymupdf

RAIZ = Path(__file__).resolve().parent.parent
BOLETIN_PDF = RAIZ / "fuentes" / "boletin-oficial-bcs-2014-12.pdf"
BOLETIN_URL = "https://finanzas.bcs.gob.mx/wp-content/themes/voice/assets/images/boletines/2014/12.pdf"
DATOS = RAIZ / "datos" / "poel"

# Orden de las filas en la matriz de criterios de cada ficha y en la Tabla 18.
GRUPOS = [
    ("agua", "Agua"),
    ("flora-fauna", "Flora y fauna"),
    ("manejo-ecosistemas", "Manejo de ecosistemas"),
    ("residuos", "Residuos"),
    ("asentamientos-humanos-1", "Asentamientos humanos I"),
    ("asentamientos-humanos-2", "Asentamientos humanos II"),
    ("infraestructura", "Infraestructura y equipamiento"),
    ("acuacultura", "Acuacultura"),
    ("agricultura", "Agricultura"),
    ("construccion", "Construcción"),
    ("mineria", "Minería (extracción)"),
    ("pecuario", "Pecuario"),
    ("pesca", "Pesca"),
    ("turismo-1", "Turismo I"),
    ("turismo-2", "Turismo II"),
    ("turismo-3", "Turismo III"),
]

# Encabezado de la Tabla 18 -> clave de grupo
ENCABEZADOS_TABLA_18 = {
    "AGUA": "agua",
    "FLORA Y FAUNA": "flora-fauna",
    "MANEJO DE ECOSISTEMAS": "manejo-ecosistemas",
    "RESIDUOS": "residuos",
    "ASENTAMIENTOS HUMANOS I": "asentamientos-humanos-1",
    "ASENTAMIENTOS HUMANOS II": "asentamientos-humanos-2",
    "INFRAESTRUCTURA Y EQUIPAMIENTO": "infraestructura",
    "ACUACULTURA": "acuacultura",
    "AGRÍCOLA": "agricultura",
    "CONSTRUCCIÓN": "construccion",
    "MINERIA": "mineria",
    "PECUARIO": "pecuario",
    "PESCA": "pesca",
    "TURISMO I": "turismo-1",
    "TURISMO II": "turismo-2",
    "TURISMO III": "turismo-3",
}


def abrir():
    if not BOLETIN_PDF.exists():
        raise SystemExit(f"Falta {BOLETIN_PDF}. Descárgalo de {BOLETIN_URL}")
    return pymupdf.open(BOLETIN_PDF)


def limpiar(texto):
    """Normaliza espacios y guiones de corte de línea del texto extraído."""
    texto = texto.replace("‐", "-").replace("­", "")
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\s*\n\s*", " ", texto)
    return texto.strip()


def lineas(pagina):
    """Líneas de texto de una página como (x0, y0, x1, y1, negrita, tamaño, texto)."""
    out = []
    for bloque in pagina.get_text("dict")["blocks"]:
        for linea in bloque.get("lines", []):
            spans = [s for s in linea["spans"] if s["text"].strip()]
            if not spans:
                continue
            texto = re.sub(r"\s+", " ", "".join(s["text"] for s in linea["spans"]).replace("\xa0", " ")).strip()
            negrita = "Bold" in spans[0]["font"] or bool(spans[0]["flags"] & 16)
            out.append((*linea["bbox"], negrita, spans[0]["size"], texto))
    return sorted(out, key=lambda l: (round(l[1]), l[0]))
