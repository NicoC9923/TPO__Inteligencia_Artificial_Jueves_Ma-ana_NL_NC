"""Tests rapidos para el soporte bilingue (ES+EN) agregado sobre mi_tp07.py.

No es parte de la entrega del TP (evaluar.py / casos_prueba.json siguen
intactos y en 25/25). Esto cubre solo la logica pura agregada para el
control por voz: clasificador, extractor y el validador de seguridad.

Correr con:  py -3 test_voz_bilingue.py
"""

from mi_tp07 import ClasificadorIntencion, ExtractorParametros, ValidadorSeguridad, _perfil_por_defecto

fallos = []


def check(desc, condicion):
    estado = "ok " if condicion else "FALLO"
    print(f"  [{estado}] {desc}")
    if not condicion:
        fallos.append(desc)


# ---------------------------------------------------------------------
# Slice 1 (rojo->verde): palabras peligrosas en ingles deben bloquear
# ---------------------------------------------------------------------
validador = ValidadorSeguridad(_perfil_por_defecto())

print("Validador de seguridad - palabras peligrosas en ingles")
for texto in ["jump off the table", "push the box", "run as fast as you can", "break the door"]:
    es_seguro, motivo = validador.validar(texto, "DESCONOCIDO", {})
    check(f'"{texto}" -> bloqueado', es_seguro is False and motivo == "palabra peligrosa")

# ---------------------------------------------------------------------
# Slice 2: clasificador en ingles
# ---------------------------------------------------------------------
clasificador = ClasificadorIntencion()

print("\nClasificador - ingles")
casos_clasificador = [
    ("move forward 2 meters", "MOVER"),
    ("walk slowly", "MOVER"),
    ("turn right 90 degrees", "GIRAR"),
    ("stop", "DETENERSE"),
    ("don't move", "DETENERSE"),
    ("say hello", "SALUDO"),
    ("what's your battery status", "CONSULTAR_ESTADO"),
    ("what's your name", "DESCONOCIDO"),
]
for texto, esperado in casos_clasificador:
    obtenido = clasificador.clasificar(texto)
    check(f'"{texto}" -> {esperado} (dio {obtenido})', obtenido == esperado)

# ---------------------------------------------------------------------
# Slice 3: extractor en ingles
# ---------------------------------------------------------------------
extractor = ExtractorParametros()

print("\nExtractor - ingles")
casos_extractor = [
    ("move forward 2 meters", "MOVER", {"distancia_m": 2.0, "direccion": "adelante"}),
    ("turn right 90 degrees", "GIRAR", {"angulo_deg": 90, "direccion": "derecha"}),
    ("walk slowly", "MOVER", {"velocidad_ms": 0.2}),
    ("half turn", "GIRAR", {"angulo_deg": 180}),
]
for texto, tipo, esperado_parcial in casos_extractor:
    obtenido = extractor.extraer(texto, tipo)
    ok = all(obtenido.get(k) == v for k, v in esperado_parcial.items())
    check(f'"{texto}" -> {esperado_parcial} (dio {obtenido})', ok)

print()
if fallos:
    print(f"{len(fallos)} FALLO(S)")
    raise SystemExit(1)
print("Todo OK")
