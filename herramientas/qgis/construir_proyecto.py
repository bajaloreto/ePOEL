"""Arma qgis/revision/proyecto.qgz con PyQGIS. Lo llama herramientas/proyecto_qgis.py con el Python de QGIS:

    QT_QPA_PLATFORM=offscreen /Applications/QGIS.app/Contents/MacOS/python herramientas/qgis/construir_proyecto.py qgis/revision
"""
import json
import sys
from pathlib import Path
from urllib.parse import quote

from qgis.core import (QgsApplication, QgsBookmark, QgsCategorizedSymbolRenderer, QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform, QgsEditorWidgetSetup, QgsFillSymbol, QgsPalLayerSettings, QgsProject,
                       QgsRasterLayer, QgsReferencedRectangle, QgsRendererCategory, QgsTextBufferSettings,
                       QgsTextFormat, QgsVectorLayer, QgsVectorLayerSimpleLabeling)
from qgis.PyQt.QtGui import QColor, QFont

DESTINO = Path(sys.argv[1]).resolve()
UTM = QgsCoordinateReferenceSystem("EPSG:32612")
WGS84 = QgsCoordinateReferenceSystem("EPSG:4326")

ESTADOS = [  # valor, etiqueta, color de relleno y borde
    ("pendiente", "Pendiente", "255,212,0"),
    ("correcta", "Correcta tal cual", "47,125,74"),
    ("corregida", "Corregida a mano", "64,140,255"),
    ("descartar", "Descartar (volver a 2019 o sin polígono)", "160,160,160"),
]


def xyz(nombre, url, zmax):
    return QgsRasterLayer(f"type=xyz&url={quote(url, safe=':/')}&zmin=0&zmax={zmax}", nombre, "wms")


def contorno(color, ancho, punteado=False):
    return QgsFillSymbol.createSimple({"color": "0,0,0,0", "outline_color": color, "outline_width": str(ancho),
                                       "outline_style": "dash" if punteado else "solid"})


def etiquetas(capa, campo, tamano=10, color="#0b0d10", halo="#ffffff"):
    formato = QgsTextFormat()
    formato.setFont(QFont("Arial", tamano, QFont.Bold))
    formato.setSize(tamano)
    formato.setColor(QColor(color))
    halo_cfg = QgsTextBufferSettings()
    halo_cfg.setEnabled(True)
    halo_cfg.setSize(1.2)
    halo_cfg.setColor(QColor(halo))
    formato.setBuffer(halo_cfg)
    ajustes = QgsPalLayerSettings()
    ajustes.fieldName = campo
    ajustes.setFormat(formato)
    capa.setLabeling(QgsVectorLayerSimpleLabeling(ajustes))
    capa.setLabelsEnabled(True)


def main():
    app = QgsApplication([], False)
    app.initQgis()
    proyecto = QgsProject.instance()
    proyecto.setCrs(UTM)
    proyecto.setTitle("ePOEL — revisión de UGAs digitalizadas")
    raiz = proyecto.layerTreeRoot()

    # Polígonos por revisar (editables), coloreados según el avance de la revisión
    revisar = QgsVectorLayer(str(DESTINO / "revisar.geojson"), "UGAs por revisar (editar)", "ogr")
    categorias = []
    for valor, etiqueta, rgb in ESTADOS:
        simbolo = QgsFillSymbol.createSimple({"color": f"{rgb},45", "outline_color": f"{rgb},255", "outline_width": "0.8"})
        categorias.append(QgsRendererCategory(valor, simbolo, etiqueta))
    revisar.setRenderer(QgsCategorizedSymbolRenderer("revision", categorias))
    etiquetas(revisar, "uga", 11)
    campos = revisar.fields()
    revisar.setEditorWidgetSetup(campos.indexOf("revision"), QgsEditorWidgetSetup(
        "ValueMap", {"map": [{etiqueta: valor} for valor, etiqueta, _ in ESTADOS]}))
    revisar.setEditorWidgetSetup(campos.indexOf("notas"), QgsEditorWidgetSetup("TextEdit", {"IsMultiline": True}))
    formulario = revisar.editFormConfig()
    for i, campo in enumerate(campos):
        if campo.name() not in ("revision", "notas"):
            formulario.setReadOnly(i, True)
    revisar.setEditFormConfig(formulario)
    proyecto.addMapLayer(revisar, False)

    # Referencias de solo lectura
    aceptadas = QgsVectorLayer(str(DESTINO / "referencia" / "aceptadas.geojson"), "UGAs aceptadas", "ogr")
    aceptadas.renderer().setSymbol(contorno("255,255,255,200", 0.4))
    etiquetas(aceptadas, "uga", 8, "#ffffff", "#0b0d10")
    v2019 = QgsVectorLayer(str(DESTINO / "referencia" / "epoel-2019.geojson"), "Polígonos de ePOEL 2019", "ogr")
    v2019.renderer().setSymbol(contorno("230,60,200,230", 0.5, punteado=True))
    tierra = QgsVectorLayer(str(DESTINO / "referencia" / "tierra.geojson"), "Costa (contexto 2019)", "ogr")
    tierra.renderer().setSymbol(contorno("0,200,255,200", 0.3))
    for capa in (aceptadas, v2019, tierra):
        capa.setReadOnly(True)
        proyecto.addMapLayer(capa, False)

    # Mapas de las fichas georreferenciados, semitransparentes
    mapas = []
    for uga in json.loads((DESTINO / "ugas-por-revisar.json").read_text()):
        capa = QgsRasterLayer(str(DESTINO / "mapas" / f"{uga}.png"), f"Mapa de la ficha {uga}")
        capa.setCrs(UTM)
        capa.renderer().setOpacity(0.65)
        proyecto.addMapLayer(capa, False)
        mapas.append(capa)

    # Imagen satelital
    esri = xyz("Esri World Imagery (solo referencia)",
               "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", 19)
    eox = xyz("Sentinel-2 cloudless 2024 (EOX, CC BY-NC-SA)",
              "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2024_3857/default/g/{z}/{y}/{x}.jpg", 15)
    for capa in (esri, eox):
        proyecto.addMapLayer(capa, False)

    # Árbol de capas: lo editable arriba, el satélite abajo
    raiz.addLayer(revisar)
    ref = raiz.addGroup("Referencia")
    for capa in (aceptadas, v2019, tierra):
        ref.addLayer(capa)
    ref.findLayer(v2019.id()).setItemVisibilityChecked(False)
    grupo_mapas = raiz.addGroup("Mapas de las fichas (Boletín, georreferenciados)")
    for capa in mapas:
        grupo_mapas.addLayer(capa).setItemVisibilityChecked(False)
    sat = raiz.addGroup("Imagen satelital")
    sat.addLayer(esri)
    sat.addLayer(eox).setItemVisibilityChecked(False)

    # Un marcador por UGA para saltar de una a otra (Ver > Marcadores espaciales)
    a_utm = QgsCoordinateTransform(WGS84, UTM, proyecto)
    extension_total = None
    for f in revisar.getFeatures():
        caja = a_utm.transformBoundingBox(f.geometry().boundingBox())
        caja.scale(1.3)
        marcador = QgsBookmark()
        marcador.setName(f"UGA {f['uga']} — {f['motivo']}")
        marcador.setGroup("Por revisar")
        marcador.setExtent(QgsReferencedRectangle(caja, UTM))
        proyecto.bookmarkManager().addBookmark(marcador)
        if extension_total is None:
            extension_total = caja
        else:
            extension_total.combineExtentWith(caja)
    if extension_total is not None:
        proyecto.viewSettings().setDefaultViewExtent(QgsReferencedRectangle(extension_total, UTM))

    if not proyecto.write(str(DESTINO / "proyecto.qgz")):
        raise SystemExit("No se pudo escribir el proyecto")
    app.exitQgis()


if __name__ == "__main__":
    main()
