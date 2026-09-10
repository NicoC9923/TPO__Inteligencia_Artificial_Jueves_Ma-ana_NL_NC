"""Servidor local para controlar el robot por voz (ES + EN).

No es parte de la entrega del TP: es un extra personal que reusa el
pipeline de mi_tp07.py (AgenteRobot) tal cual. No modifica entorno/.

Uso:
    1. Abri INICIAR_SIMULADOR (elegi G1 o Go2) y esperá la ventana.
    2. cd mi_desarrollo && py -3 servidor_voz.py
    3. Abrí http://127.0.0.1:8080 en Chrome o Edge (necesita internet
       para el reconocimiento de voz del navegador).
    4. Mantené presionado el botón, hablá, soltá.

Sin simulador abierto podés probar igual con --sin-robot: el pipeline
corre y te dice qué haría, pero el robot no se mueve.
"""

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from mi_tp07 import AgenteRobot
from robot import Robot

PUERTO_DEFAULT = 8080
PAGINA = Path(__file__).resolve().parent / "voz.html"

agente = None  # se arma en main()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, formato, *args):
        pass  # el logging propio alcanza, no hace falta el del server

    def do_GET(self):
        if self.path in ("/", "/voz.html"):
            cuerpo = PAGINA.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path != "/comando":
            self.send_response(404)
            self.end_headers()
            return

        largo = int(self.headers.get("Content-Length", 0))
        crudo = self.rfile.read(largo) if largo else b"{}"
        try:
            datos = json.loads(crudo)
            texto = str(datos.get("texto", "")).strip()
            idioma = str(datos.get("idioma", "es"))
        except (json.JSONDecodeError, TypeError, UnicodeDecodeError):
            self._responder(400, {"error": "JSON invalido"})
            return

        if not texto:
            self._responder(400, {"error": "texto vacio"})
            return

        resultado = agente.procesar(texto)
        resultado["idioma"] = idioma
        print(f"  [{idioma}] \"{texto}\" -> {resultado['tipo']}  {resultado.get('mensaje', '')}")
        self._responder(200, resultado)

    def _responder(self, codigo, data):
        cuerpo = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)


def main():
    global agente

    sin_robot = "--sin-robot" in sys.argv
    puerto = PUERTO_DEFAULT
    for arg in sys.argv:
        if arg.startswith("--puerto="):
            puerto = int(arg.split("=", 1)[1])

    robot = None
    if not sin_robot:
        robot = Robot()
        try:
            robot.conectar()
            print("  Conectado al simulador.")
        except Exception as exc:
            print(f"  No se pudo conectar al simulador ({exc}).")
            print("  Segui en modo --sin-robot: el pipeline corre, el robot no se mueve.")
            robot = None

    agente = AgenteRobot(robot)

    server = ThreadingHTTPServer(("127.0.0.1", puerto), Handler)
    print(f"\n  Abri http://127.0.0.1:{puerto} en Chrome o Edge.")
    print("  Ctrl+C para cerrar.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        if robot is not None:
            robot.detenerse()
            robot.desconectar()


if __name__ == "__main__":
    main()
