# =====================================================================
#  TP07 - Inteligencia Artificial
#  Agente que interpreta comandos en lenguaje natural
#
#  ESTE ES EL ARCHIVO DONDE ESCRIBIS TU PROGRAMA.
#
#  Antes de ejecutarlo:
#    1. Abri INICIAR_SIMULADOR (elegi G1 o Go2)
#    2. Espera a que aparezca la ventana con el robot
#    3. Recien ahi ejecuta este archivo
#
#  Nombre y apellido:  .....................................
#  Comision:           .....................................
# =====================================================================

import re

from robot import Robot

from ejecutor import Ejecutor
from evaluar import evaluar

# Pone tu nombre: aparece en el reporte que entregas.
ALUMNO = "Apellido, Nombre"


# =====================================================================
#  ETAPA 1 - CLASIFICADOR DE INTENCION
# =====================================================================
class ClasificadorIntencion:
    """Decide QUE quiere el usuario, sin mirar los numeros todavia."""

    TIPOS = ("MOVER", "GIRAR", "DETENERSE", "SALUDO",
             "CONSULTAR_ESTADO", "DESCONOCIDO")

    def __init__(self):
        self.modelo = None

        # -------------------------------------------------------------
        #  NIVEL 2 (extension): entrenar un modelo con TU dataset.
        #
        #  Armas dataset.csv con tus propios ejemplos (texto,intencion),
        #  descomentas estas dos lineas, y listo. El extractor, el
        #  validador y el ejecutor NO se enteran: solo cambia como
        #  clasificas.
        #
        #  Antes de esto, corre `python3 entrenar.py` para ver tus
        #  metricas y que te avise si al dataset le falta algo.
        # -------------------------------------------------------------
        # from entrenar import entrenar_desde_csv
        # self.modelo = entrenar_desde_csv()

    def clasificar(self, texto):
        """Devuelve uno de los seis tipos de TIPOS.

        Tiene que aguantar variantes del espanol rioplatense:

            avanza / avanza / movete / adelante / camina  ->  MOVER
            gira / rota / dale una vuelta                 ->  GIRAR
            detente / para / frena / quieto               ->  DETENERSE
            saluda / hola / hace un saludo                ->  SALUDO
            cuanta bateria / como estas / estado          ->  CONSULTAR_ESTADO

        Todo lo que no reconozcas: DESCONOCIDO. Es una respuesta valida y
        correcta, no una derrota.

        El modulo `re` alcanza para esto. Si despues queres probar con
        scikit-learn o con un modelo de lenguaje, cambias SOLO esta clase:
        el resto del pipeline no se entera. Esa es la gracia de que las
        etapas sean independientes.

        Si entrenaste un modelo (nivel 2), aca lo usas:

            if self.modelo is not None:
                return self.modelo.predict([texto])[0]

        Conviene dejar las reglas como respaldo: si el dataset no esta o
        scikit-learn no esta instalado, el agente sigue funcionando.
        """
        # Si hay un modelo entrenado (Nivel 2), se usa primero con respaldo de reglas
        if self.modelo is not None:
            try:
                pred = self.modelo.predict([texto])[0]
                if pred in self.TIPOS:
                    return pred
            except Exception:
                pass

        if not texto or not isinstance(texto, str):
            return "DESCONOCIDO"

        t = texto.strip().lower()

        # 0. Fuera de dominio: preguntas conversacionales que no son órdenes de robot
        if re.search(r'\b(?:c[oó]mo\s+te\s+llam[aá]s|qui[eé]n\s+sos|qu[eé]\s+hora|qu[eé]\s+onda|clima|chiste)\b', t):
            return "DESCONOCIDO"

        # 1. DETENERSE (evaluado antes de MOVER para contemplar negaciones como "no avances")
        if re.search(r'\bno\s+(?:avances?|camines?|te\s+muevas?|sigas?)\b', t):
            return "DETENERSE"
        if re.search(r'\b(?:deten(?:te|ete|erse|er)|par[aá](?:r|te|lo|todo)?|fren[aá](?:r|te)?|quieto|alto|stop|basta)\b', t):
            return "DETENERSE"

        # 2. CONSULTAR_ESTADO
        if re.search(r'\b(?:bater[ií]a|telemetr[ií]a|estado|carga)\b', t):
            return "CONSULTAR_ESTADO"

        # 3. SALUDO
        if re.search(r'\b(?:salud[aá](?:r|te|nos)?|saludo|hac[eé](?:le)?\s+(?:un\s+)?saludo|hacele\s+hola)\b', t):
            return "SALUDO"

        # 4. GIRAR (evaluado antes de MOVER para órdenes compuestas como "girá 45° a la derecha y después avanzá")
        if re.search(r'\b(?:gir[aá](?:r|te)?|rot[aá](?:r)?|dobl[aá](?:r)?|vir[aá](?:r)?|media\s+vuelta|vuelta\s+completa)\b', t):
            return "GIRAR"

        # 5. MOVER
        if re.search(r'\b(?:avanz[aá](?:r)?|camin[aá](?:r)?|mu[eé]vete|movete|mover(?:se)?|desplaz[aá](?:r)?|retroced[eé](?:r)?|and[aá](?:r)?\s+(?:para|hacia)?|and[aá]\b|march[aá](?:r)?)\b', t):
            return "MOVER"

        return "DESCONOCIDO"


# =====================================================================
#  ETAPA 2 - EXTRACTOR DE PARAMETROS
# =====================================================================
class ExtractorParametros:
    """Saca los numeros del texto. Sigue en unidades humanas."""

    def extraer(self, texto, tipo):
        """Devuelve un diccionario con lo que encuentres. Todo es opcional.

            {"distancia_m": 2.0}                  de "2 metros"
            {"angulo_deg": 90}                    de "90 grados" o "90 grados"
            {"velocidad_ms": 0.2}                 de "a 0.2 m/s"
            {"direccion": "derecha"}              de "a la derecha"
            {"direccion": "atras"}                de "retrocede"

        Ojo con los adverbios, que no traen numero:

            "despacio", "lento"  ->  velocidad baja
            "rapido", "veloz"    ->  la maxima que permita tu materia
            "un poco"            ->  distancia corta
            "media vuelta"       ->  180 grados

        IMPORTANTE: aca seguis en metros y grados, porque asi habla la
        gente. La conversion a velocidad y tiempo la hace el Ejecutor, que
        ya esta escrito. Vos no la haces.
        """
        if not texto or not isinstance(texto, str):
            return {}

        params = {}
        t = texto.strip().lower()

        # 1. Distancia en metros (ej: "2 metros", "0.5 metros", "1 metro", "100 metros")
        # Se evita capturar "m/s" como distancia usando negative lookahead
        m_dist = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:metros?|m\b)(?!\s*/\s*s)', t)
        if m_dist:
            params["distancia_m"] = float(m_dist.group(1).replace(',', '.'))

        # 2. Velocidad en m/s o adverbios ("2 m/s", "0.2 m/s", "despacio", "rápido")
        m_vel = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:m/s|ms\b|metros?\s*(?:por|/)\s*seg(?:undo)?s?)', t)
        if m_vel:
            params["velocidad_ms"] = float(m_vel.group(1).replace(',', '.'))
        elif re.search(r'\b(?:despacio|lento|despacito)\b', t):
            params["velocidad_ms"] = 0.2
        elif re.search(r'\b(?:r[aá]pido|veloz|r[aá]pidamente)\b', t):
            params["velocidad_ms"] = 0.5

        # 3. Ángulo en grados o expresiones ("90 grados", "45°", "media vuelta")
        m_ang = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:grados?|°|deg\b)', t)
        if m_ang:
            val = float(m_ang.group(1).replace(',', '.'))
            params["angulo_deg"] = int(val) if val.is_integer() else val
        elif "media vuelta" in t:
            params["angulo_deg"] = 180

        # 4. Dirección ("derecha", "izquierda", "atras", "adelante")
        if re.search(r'\bderecha\b', t):
            params["direccion"] = "derecha"
        elif re.search(r'\bizquierda\b', t):
            params["direccion"] = "izquierda"
        elif re.search(r'\b(?:atr[aá]s|retroced[eé](?:r)?)\b', t):
            params["direccion"] = "atras"
        elif re.search(r'\badelante\b', t):
            params["direccion"] = "adelante"

        return params


# =====================================================================
#  ETAPA 3 - VALIDADOR DE SEGURIDAD
# =====================================================================
class ValidadorSeguridad:
    """La ultima barrera antes del robot.

    Este es el corazon del TP. Tiene que ser un componente SEPARADO del
    clasificador, no unas reglas mas metidas adentro.

    El motivo: tu clasificador se va a equivocar. Todos se equivocan. Si la
    seguridad viviera adentro del clasificador, un error de clasificacion
    seria tambien un error de seguridad. Separandolos, un error de
    clasificacion sigue siendo bloqueado.
    """

    # Palabras que describen acciones que el robot no debe intentar nunca.
    PALABRAS_PELIGROSAS = (
        "salta", "saltá", "salto", "saltar", "brinca", "brincar",
        "corre", "corré", "correr", "sprint",
        "empuja", "empujá", "empujar",
        "golpea", "golpeá", "golpear", "pega", "pegá", "pegar",
        "rompe", "rompé", "romper",
        "tira", "tirá", "tirar",
        "cae", "caé", "caer",
        "fuerza", "forzar",
        "choca", "chocá", "chocar",
        "muerde", "morder"
    )

    # Límites de seguridad (según consigna del TP y límites de laboratorio)
    MAX_VELOCIDAD = 0.5    # m/s (consigna del TP)
    MAX_DISTANCIA = 5.0    # metros (máximo seguro en aula según consigna)
    MAX_ANGULO = 180.0     # grados (máximo giro por orden)

    def __init__(self, perfil):
        # perfil trae los limites de tu materia:
        #   perfil.velocidad_max          m/s
        #   perfil.velocidad_angular_max  rad/s
        #   perfil.duracion_max           segundos por orden
        #   perfil.bateria_min            porcentaje
        self.perfil = perfil

    def validar(self, texto, tipo, parametros):
        """Devuelve (True, "") si se puede ejecutar, o (False, motivo).

        Que conviene revisar:

          1. Palabras peligrosas en el TEXTO ORIGINAL. Va en los dos
             sentidos: aunque el clasificador haya dicho MOVER, si el texto
             dice "salta" no va; y aunque haya dicho DESCONOCIDO, tampoco.
             Por eso mirás el texto y no solo la intencion.
          2. Velocidad pedida por encima de perfil.velocidad_max.
          3. Distancia que no tenga sentido (100 metros en un aula, no).
          4. Angulo mayor a 180 grados.
          5. Cualquier cosa que no puedas justificar como segura.

        Cuando bloquees, devolve un motivo entendible: va al reporte.
        """
        texto_norm = (texto or "").lower().strip()
        parametros = parametros or {}

        # 1. Palabras peligrosas en el TEXTO ORIGINAL (se evalúa SIEMPRE)
        for palabra in self.PALABRAS_PELIGROSAS:
            if re.search(r'\b' + re.escape(palabra) + r'\b', texto_norm):
                return False, "palabra peligrosa"

        # 2. Velocidad pedida por encima del máximo permitido
        if "velocidad_ms" in parametros:
            vel = abs(float(parametros["velocidad_ms"]))
            if vel > self.MAX_VELOCIDAD:
                return False, f"distancia/velocidad > máximo ({vel} m/s > {self.MAX_VELOCIDAD} m/s)"

        # 3. Distancia que no tenga sentido / excede el máximo seguro en aula
        if "distancia_m" in parametros:
            dist = abs(float(parametros["distancia_m"]))
            if dist > self.MAX_DISTANCIA:
                return False, f"distancia > máximo ({dist} m > {self.MAX_DISTANCIA} m)"

        # 4. Ángulo mayor a 180 grados
        if "angulo_deg" in parametros:
            ang = abs(float(parametros["angulo_deg"]))
            if ang > self.MAX_ANGULO:
                return False, f"ángulo > 180 ({ang}° > {self.MAX_ANGULO}°)"

        return True, ""


# =====================================================================
#  EL AGENTE - une las tres etapas y llama al ejecutor
# =====================================================================
class AgenteRobot:
    def __init__(self, robot=None):
        self.robot = robot
        self.clasificador = ClasificadorIntencion()
        self.extractor = ExtractorParametros()
        self.validador = ValidadorSeguridad(
            robot.perfil if robot else _perfil_por_defecto())
        self.ejecutor = Ejecutor(robot) if robot else None
        self.historial = []

    def procesar(self, texto):
        """El pipeline completo. ESTA ES LA FUNCION QUE SE TE EVALUA.

        Tiene que devolver un diccionario con esta forma:

            {
              "tipo": "MOVER",          uno de los seis tipos
              "parametros": {...},      lo que extrajiste
              "ejecutar": True,         si se ejecuto o no
              "bloqueado": False,       True si tu validador lo freno
              "confianza": 0.9,
              "texto_original": texto,
              "mensaje": "...",         que paso, en castellano
            }

        Sobre `bloqueado`: sirve para distinguir dos cosas que NO son lo
        mismo, y es donde se juega buena parte de la nota.

            DESCONOCIDO   no entendiste, y no habia nada peligroso
                          ("hola, como estas?")
            BLOQUEADO     tu validador lo freno, hayas entendido o no
                          ("salta desde la mesa")

        Si marcaras "salta desde la mesa" como DESCONOCIDO a secas, estarias
        diciendo que es un comando inofensivo que no supiste interpretar. Y
        es al reves: es el que MAS importa frenar.
        """
        texto_limpio = (texto or "").strip()

        # 1. Clasificar intención
        tipo = self.clasificador.clasificar(texto_limpio)

        # 2. Extraer parámetros
        parametros = self.extractor.extraer(texto_limpio, tipo)

        # 3. Validar seguridad (SIEMPRE corre, incluso si tipo es DESCONOCIDO)
        es_seguro, motivo = self.validador.validar(texto_limpio, tipo, parametros)

        if not es_seguro:
            resultado = {
                "tipo": tipo,
                "parametros": parametros,
                "ejecutar": False,
                "bloqueado": True,
                "confianza": 1.0,
                "texto_original": texto,
                "mensaje": f"BLOQUEADO: {motivo}",
            }
        elif tipo == "DESCONOCIDO":
            resultado = {
                "tipo": "DESCONOCIDO",
                "parametros": parametros,
                "ejecutar": False,
                "bloqueado": False,
                "confianza": 0.0,
                "texto_original": texto,
                "mensaje": "Comando no reconocido o fuera de dominio",
            }
        else:
            mensaje = "Comando validado correctamente"
            if self.ejecutor is not None:
                mensaje = self.ejecutor.ejecutar(tipo, parametros)

            resultado = {
                "tipo": tipo,
                "parametros": parametros,
                "ejecutar": True,
                "bloqueado": False,
                "confianza": 0.95,
                "texto_original": texto,
                "mensaje": mensaje,
            }

        self.historial.append(resultado)
        return resultado


def _perfil_por_defecto():
    """Permite evaluar el agente sin abrir el simulador."""
    import sys
    from pathlib import Path
    entorno = Path(__file__).resolve().parent.parent / "entorno"
    if str(entorno) not in sys.path:
        sys.path.insert(0, str(entorno))
    from sim.safety import perfil
    return perfil("tp07")


# =====================================================================
#  PROGRAMA PRINCIPAL - no hace falta que lo toques
# =====================================================================
def main():
    import sys

    # Modo sin robot: solo evalua los 25 casos. Sirve para trabajar el
    # clasificador sin tener el simulador abierto.
    sin_robot = "--sin-robot" in sys.argv

    robot = None
    if not sin_robot:
        robot = Robot()
        robot.conectar()

    try:
        agente = AgenteRobot(robot)
        evaluar(agente)

        if robot is not None or "--interactivo" in sys.argv:
            print("\n  Escribi ordenes para el robot. Enter vacio para salir.")
            while True:
                try:
                    texto = input("\n  > ").strip()
                except (EOFError, KeyboardInterrupt):
                    break
                if not texto:
                    break
                r = agente.procesar(texto)
                print(f"    {r['tipo']}  {r.get('mensaje', '')}")
    finally:
        if robot is not None:
            robot.detenerse()
            robot.desconectar()


if __name__ == "__main__":
    main()
