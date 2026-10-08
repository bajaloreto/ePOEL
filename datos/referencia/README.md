# Datos de referencia

## `inegi-localidades-loreto.csv`

Catálogo Único de Claves de Áreas Geoestadísticas Estatales, Municipales y Localidades (AGEEML) de INEGI, municipio
de Loreto (clave 03009): 209 localidades con coordenadas. Descargado por Hugo Quintero el 2026-10-08 de
https://www.inegi.org.mx/app/ageeml/ — información pública de INEGI, se cita como fuente.

Uso en ePOEL: `herramientas/verificar_con_localidades.py` compara los puntos de localidad que dibujan los mapas del
Boletín con estas coordenadas para verificar la escala y la lectura de los rótulos UTM. Ojo (INC-014): estas
coordenadas coinciden con los mapas del Boletín *sin* la corrección de datum, y la imagen satelital confirma que la
corrección es necesaria; por eso no se usan para verificar el datum.
