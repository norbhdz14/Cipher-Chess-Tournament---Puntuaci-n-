"""
Cipher Chess Tournament - Puntuación, emparejamientos suizos y relojes de ajedrez
Autor: Ing. Norberto Hernández
Cédula profesional: 15061201
Cipher · Sistemas computacionales IoT
Arandas, Jalisco
Licencia: MIT

Arquitectura heredada de "Yu-Gi-Oh! LP Tracker" (Cipher):
  - UI 100 % Kivy en Python (sin .kv), tema oscuro/claro, ES/EN.
  - @blindado: ninguna excepción de UI cierra la app.
  - Todo el estado del torneo vive en clases de lógica pura (Torneo, RelojAjedrez)
    que no dependen de Kivy; la UI solo las pinta.
  - Los relojes usan Clock.schedule_interval + time.monotonic (sin hilos de fondo).
"""
import csv
import io
import json
import math
import os
import time
import traceback
from datetime import datetime
from functools import wraps

from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.graphics.texture import Texture
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scatter import Scatter
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.utils import escape_markup
from kivy.utils import get_color_from_hex as hx

# ---------- Fuente con acentos/símbolos (junto a main.py) ----------
QUIEN = os.path.dirname(os.path.abspath(__file__))


def _buscar_fuente(claves, excluir=()):
    """Busca en la carpeta de la app un .ttf/.otf cuyo nombre contenga todas las claves."""
    try:
        for f in sorted(os.listdir(QUIEN)):
            n = f.lower()
            if (n.endswith((".ttf", ".otf")) and all(c in n for c in claves)
                    and not any(x in n for x in excluir)):
                return os.path.join(QUIEN, f)
    except Exception:
        traceback.print_exc()
    return None


def registrar_fuentes():
    """Sustituye la fuente por defecto ('Roboto') por Noto Sans si el archivo está junto a main.py.
    Si no existe, la app usa la fuente normal de Kivy y sigue funcionando."""
    regular = (_buscar_fuente(("sans", "regular"), ("italic",))
               or _buscar_fuente(("regular",), ("italic", "emoji")))
    if not regular:
        return
    negrita = _buscar_fuente(("sans", "bold"), ("italic",))
    try:
        LabelBase.register(name="Roboto", fn_regular=regular, fn_bold=negrita or regular)
    except Exception:
        traceback.print_exc()


registrar_fuentes()

# ---------- Metadatos ----------
APP_NOMBRE = "Cipher Chess Tournament"
APP_VERSION = "1.0.0"
APP_PAQUETE = "org.cipher.chesstournament"
APP_LICENCIA = "MIT"

# ---------- Paletas ----------
PALETAS = {
    "oscuro": {
        "AZUL": hx("#3F5FD0"),
        "CIAN": hx("#3CC8E8"),
        "MORADO": hx("#A33FE0"),
        "GRIS": hx("#A0A0A0"),
        "ROJO": hx("#E53935"),
        "VERDE": hx("#43A047"),
        "NARANJA": hx("#EF6C00"),
        "GRIS_CLARO": hx("#2B2B2B"),
        "FONDO_TARJ": hx("#1E1E1E"),
        "VENTANA": (0.1, 0.1, 0.1, 1),
        "TEXTO": (0.9, 0.9, 0.9, 1),
    },
    "claro": {
        "AZUL": hx("#3F5FD0"),
        "CIAN": hx("#1E9DB8"),
        "MORADO": hx("#A33FE0"),
        "GRIS": hx("#555555"),
        "ROJO": hx("#E53935"),
        "VERDE": hx("#43A047"),
        "NARANJA": hx("#EF6C00"),
        "GRIS_CLARO": hx("#DDDDDD"),
        "FONDO_TARJ": hx("#F4F6FC"),
        "VENTANA": (1, 1, 1, 1),
        "TEXTO": (0.2, 0.2, 0.2, 1),
    },
}

LOGO = os.path.join(QUIEN, "logo.png")
LOGO2 = os.path.join(QUIEN, "cipher.png")

TELEGRAM = "https://t.me/CipherlosAltos"
BLOG = "https://norbhdz.blogspot.com"
GITHUB = "https://github.com/Norbhdz14"
PAYPAL = "https://paypal.me/norbhdz14"
KOFI = "https://ko-fi.com/cipherlosaltos"
# Marcadores de posición: cámbialos cuando publiques el repositorio / la ficha de F-Droid
GITHUB_REPO = "https://github.com/Norbhdz14/cipher-chess-tournament"
FDROID = "https://f-droid.org/packages/org.cipher.chesstournament"

MAX_NOMBRE = 20
MAX_JUGADORES = 64
MAX_HISTORIAL = 2000

# Resultados internos -> texto mostrado
RES_TXT = {"1-0": "1-0", "1/2": "½-½", "0-1": "0-1"}
RES_PUNTOS = {"1-0": (1.0, 0.0), "1/2": (0.5, 0.5), "0-1": (0.0, 1.0)}

# Controles de tiempo estándar: (categoría, segundos base, incremento Fischer en segundos)
CONTROLES = [
    ("cat_bullet", 60, 0),
    ("cat_bullet", 120, 1),
    ("cat_blitz", 180, 2),
    ("cat_blitz", 300, 0),
    ("cat_rapid", 600, 0),
    ("cat_rapid", 900, 10),
    ("cat_rapid", 1800, 0),
    ("cat_clasico", 5400, 30),
]
CONTROL_DEFECTO = 4  # Rápida 10+0

# ---------- Textos (ES y EN) ----------
TEXTOS = {
    "es": {
        "titulo": "Chess Tournament",
        "sub": "Cipher · IoT & Sistemas",
        "tab_jug": "Jugadores",
        "tab_rondas": "Rondas",
        "tab_reloj": "Reloj",
        "tab_clas": "Tabla",
        "tema_claro": "Claro",
        "tema_oscuro": "Oscuro",
        "torneo_def": "Torneo de Ajedrez",
        "hint_torneo": "Nombre del torneo (opcional)",
        "hint_jugador": "Nombre del jugador",
        "btn_add": "Añadir",
        "jugadores_n": "Jugadores inscritos: {n}",
        "nota_inscripcion": "El orden de inscripción es la siembra de la ronda 1.",
        "nota_bloqueado": "El torneo ya inició: la lista de jugadores está bloqueada.",
        "estado_torneo": "{nom} · Ronda {r} de {t}",
        "rondas_label": "Rondas:",
        "btn_iniciar": "Iniciar torneo",
        "btn_nuevo": "Nuevo torneo",
        "confirmar_nuevo": "¿Borrar jugadores, rondas e historial y empezar un torneo nuevo?",
        "si": "Sí",
        "no": "No",
        "err_min": "Se necesitan al menos 2 jugadores.",
        "err_dup": "Ese jugador ya está inscrito.",
        "err_max": "Se alcanzó el máximo de jugadores.",
        "sin_ronda": "Aún no hay rondas.\nInscribe jugadores e inicia el torneo.",
        "ronda_titulo": "Ronda {r} de {t}",
        "progreso": "Resultados capturados: {c}/{n}",
        "mesa": "Mesa {n}",
        "descansa": "{nom} descansa (+1 pt)",
        "blancas_c": "B",
        "negras_c": "N",
        "btn_sig_ronda": "Generar ronda {n}",
        "btn_ver_clas": "Ver clasificación",
        "falta_result": "Captura todos los resultados para generar la siguiente ronda.",
        "torneo_fin": "¡Torneo finalizado!",
        "campeon": "Campeón: {nom} ({p} pts)",
        "ctrl_tiempo": "Control de tiempo",
        "cat_bullet": "Bullet",
        "cat_blitz": "Blitz",
        "cat_rapid": "Rápida",
        "cat_clasico": "Clásico",
        "lado_blancas": "Blancas",
        "lado_negras": "Negras",
        "reloj_libre": "Partida libre (sin mesa vinculada)",
        "reloj_mesa": "Mesa {m} · Ronda {r}",
        "btn_pausa": "Pausa",
        "btn_reanudar": "Reanudar",
        "btn_reset_reloj": "Reiniciar",
        "jugadas": "Jugadas  {a} · {b}",
        "toca_iniciar": "Toca tu lado para iniciar",
        "pausado": "Pausado",
        "bandera_titulo": "¡Se acabó el tiempo!",
        "bandera_msg": "{nom} se quedó sin tiempo.",
        "btn_reg": "Registrar {res}",
        "btn_reg_tablas": "Registrar ½-½",
        "clas_titulo": "Clasificación",
        "col_jug": "Jugador",
        "col_vtd": "V-T-D",
        "leyenda": "Pts: puntos · Bch: Buchholz · SB: Sonneborn-Berger · V-T-D: victorias-tablas-derrotas. "
                   "Desempate: Pts, Buchholz, SB, victorias.",
        "btn_datos": "Datos",
        "hist_titulo": "Historial y Reportes",
        "tab_resumen": "Resumen",
        "tab_historial": "Historial",
        "tab_reporte": "Reporte",
        "res_jugadores": "Jugadores: {n}",
        "res_ronda": "Ronda actual: {r} de {t}",
        "res_jugadas": "Partidas jugadas: {n}",
        "res_tablas": "Tablas: {n}",
        "graf_pts_titulo": "Puntos (Top 6)",
        "btn_copiar": "Copiar",
        "btn_txt": "TXT",
        "btn_csv_tabla": "CSV Tabla",
        "btn_csv_part": "CSV Partidas",
        "copiado": "Reporte copiado al portapapeles.",
        "guardado": "Archivo guardado",
        "err_guardar": "No se pudo guardar el archivo.",
        "err_ui": "Ocurrió un error inesperado. Intenta de nuevo.",
        "error": "Error",
        "listo": "Listo",
        "entendido": "Entendido",
        "enlace_copiado": "Enlace copiado",
        "contacto_titulo": "Acerca de / Contacto",
        "info_servicios": "[b]Cipher Chess Tournament[/b]\nIng. Norberto Hernández\nCédula profesional: 15061201\n"
                          "Torneos de ajedrez, sistema suizo y relojes · Soluciones IoT.\nArandas, Jalisco",
        "licencia_txt": "Licencia MIT · v{v}",
        "btn_telegram": "Telegram: ",
        "btn_blog": "Visitar Blog",
        "btn_github": "GitHub (Código Fuente)",
        "btn_fdroid": "F-Droid (próximamente)",
        "lbl_apoyo": "Apoya el Desarrollo",
        "txt_apoyo": "Aplicación libre y gratuita para la comunidad ajedrecista. Considera apoyar el proyecto:",
        "btn_paypal": "Donar vía PayPal",
        "btn_kofi": "Apoyar en Ko-fi",
        "desarrollado": "Desarrollado por Ing. Norberto Hernández",
        "cerrar": "Cerrar",
        "ev_inicio": "--- {nom}: {j} jugadores, {r} rondas ---",
        "ev_ronda": "--- Ronda {r} generada ---",
        "ev_resultado": "R{r}·M{m}: {b} vs {n} -> {res}",
        "ev_borrado": "R{r}·M{m}: resultado eliminado ({b} vs {n})",
        "ev_bye": "R{r}: {nom} descansa (+1 pt)",
        "ev_bandera": "Bandera: {nom} se quedó sin tiempo",
        "ev_fin": "Torneo finalizado. Campeón: {nom}",
        "pendiente": "pendiente",
        "csv_cols_tabla": ["posicion", "jugador", "puntos", "buchholz", "sonneborn_berger",
                           "victorias", "tablas", "derrotas"],
        "csv_cols_part": ["ronda", "mesa", "blancas", "negras", "resultado"],
    },
    "en": {
        "titulo": "Chess Tournament",
        "sub": "Cipher · IoT & Systems",
        "tab_jug": "Players",
        "tab_rondas": "Rounds",
        "tab_reloj": "Clock",
        "tab_clas": "Standings",
        "tema_claro": "Light",
        "tema_oscuro": "Dark",
        "torneo_def": "Chess Tournament",
        "hint_torneo": "Tournament name (optional)",
        "hint_jugador": "Player name",
        "btn_add": "Add",
        "jugadores_n": "Registered players: {n}",
        "nota_inscripcion": "Registration order is the round 1 seeding.",
        "nota_bloqueado": "The tournament has started: the player list is locked.",
        "estado_torneo": "{nom} · Round {r} of {t}",
        "rondas_label": "Rounds:",
        "btn_iniciar": "Start tournament",
        "btn_nuevo": "New tournament",
        "confirmar_nuevo": "Delete players, rounds and history and start a new tournament?",
        "si": "Yes",
        "no": "No",
        "err_min": "At least 2 players are required.",
        "err_dup": "That player is already registered.",
        "err_max": "Maximum number of players reached.",
        "sin_ronda": "No rounds yet.\nRegister players and start the tournament.",
        "ronda_titulo": "Round {r} of {t}",
        "progreso": "Results entered: {c}/{n}",
        "mesa": "Board {n}",
        "descansa": "{nom} has a bye (+1 pt)",
        "blancas_c": "W",
        "negras_c": "B",
        "btn_sig_ronda": "Generate round {n}",
        "btn_ver_clas": "View standings",
        "falta_result": "Enter all results to generate the next round.",
        "torneo_fin": "Tournament finished!",
        "campeon": "Champion: {nom} ({p} pts)",
        "ctrl_tiempo": "Time control",
        "cat_bullet": "Bullet",
        "cat_blitz": "Blitz",
        "cat_rapid": "Rapid",
        "cat_clasico": "Classical",
        "lado_blancas": "White",
        "lado_negras": "Black",
        "reloj_libre": "Free game (no board linked)",
        "reloj_mesa": "Board {m} · Round {r}",
        "btn_pausa": "Pause",
        "btn_reanudar": "Resume",
        "btn_reset_reloj": "Reset",
        "jugadas": "Moves  {a} · {b}",
        "toca_iniciar": "Tap your side to start",
        "pausado": "Paused",
        "bandera_titulo": "Time's up!",
        "bandera_msg": "{nom} ran out of time.",
        "btn_reg": "Record {res}",
        "btn_reg_tablas": "Record ½-½",
        "clas_titulo": "Standings",
        "col_jug": "Player",
        "col_vtd": "W-D-L",
        "leyenda": "Pts: points · Bch: Buchholz · SB: Sonneborn-Berger · W-D-L: wins-draws-losses. "
                   "Tie-breaks: Pts, Buchholz, SB, wins.",
        "btn_datos": "Data",
        "hist_titulo": "History & Reports",
        "tab_resumen": "Summary",
        "tab_historial": "History",
        "tab_reporte": "Report",
        "res_jugadores": "Players: {n}",
        "res_ronda": "Current round: {r} of {t}",
        "res_jugadas": "Games played: {n}",
        "res_tablas": "Draws: {n}",
        "graf_pts_titulo": "Points (Top 6)",
        "btn_copiar": "Copy",
        "btn_txt": "TXT",
        "btn_csv_tabla": "CSV Standings",
        "btn_csv_part": "CSV Games",
        "copiado": "Report copied to clipboard.",
        "guardado": "File saved",
        "err_guardar": "Could not save the file.",
        "err_ui": "An unexpected error occurred. Please try again.",
        "error": "Error",
        "listo": "Done",
        "entendido": "Got it",
        "enlace_copiado": "Link copied",
        "contacto_titulo": "About / Contact",
        "info_servicios": "[b]Cipher Chess Tournament[/b]\nEng. Norberto Hernández\nProfessional License: 15061201\n"
                          "Chess tournaments, Swiss system and clocks · IoT Solutions.\nArandas, Jalisco",
        "licencia_txt": "MIT License · v{v}",
        "btn_telegram": "Telegram: ",
        "btn_blog": "Visit Blog",
        "btn_github": "GitHub (Source Code)",
        "btn_fdroid": "F-Droid (coming soon)",
        "lbl_apoyo": "Support Development",
        "txt_apoyo": "Free and open source app for the chess community. Consider supporting the project:",
        "btn_paypal": "Donate via PayPal",
        "btn_kofi": "Support on Ko-fi",
        "desarrollado": "Developed by Eng. Norberto Hernández",
        "cerrar": "Close",
        "ev_inicio": "--- {nom}: {j} players, {r} rounds ---",
        "ev_ronda": "--- Round {r} generated ---",
        "ev_resultado": "R{r}·B{m}: {b} vs {n} -> {res}",
        "ev_borrado": "R{r}·B{m}: result removed ({b} vs {n})",
        "ev_bye": "R{r}: {nom} has a bye (+1 pt)",
        "ev_bandera": "Flag: {nom} ran out of time",
        "ev_fin": "Tournament finished. Champion: {nom}",
        "pendiente": "pending",
        "csv_cols_tabla": ["rank", "player", "points", "buchholz", "sonneborn_berger",
                           "wins", "draws", "losses"],
        "csv_cols_part": ["round", "board", "white", "black", "result"],
    },
}


# ---------- Blindaje contra excepciones de UI ----------
def blindado(fn):
    """Evita que una excepción dentro de un callback de UI cierre la app."""
    @wraps(fn)
    def envoltura(*a, **kw):
        try:
            return fn(*a, **kw)
        except Exception:
            traceback.print_exc()
            try:
                app = App.get_running_app()
                if app:
                    app.aviso(app.t("error"), app.t("err_ui"))
            except Exception:
                traceback.print_exc()
            return None
    return envoltura


# ---------- Utilidades de formato ----------
def num(x):
    """3.0 -> '3', 3.5 -> '3.5', 2.25 -> '2.25'."""
    return ("%.2f" % x).rstrip("0").rstrip(".")


def fmt_tiempo(s):
    """mm:ss, h:mm:ss o mm:ss.d cuando quedan menos de 20 segundos."""
    s = max(0.0, s)
    if s < 20:
        d = int(s * 10)
        ent, dec = d // 10, d % 10
        return f"{ent // 60:02d}:{ent % 60:02d}.{dec}"
    ent = int(math.ceil(s))
    if ent >= 3600:
        return f"{ent // 3600}:{(ent % 3600) // 60:02d}:{ent % 60:02d}"
    return f"{ent // 60:02d}:{ent % 60:02d}"


def etiqueta_control(c, t):
    return f"{t(c[0])} {c[1] // 60}+{c[2]}"


def pantalla_encendida(activa):
    """Mantiene la pantalla encendida mientras corre un reloj (solo Android; en PC no hace nada).
    La ventana de Android solo se toca desde su hilo de UI, por eso run_on_ui_thread."""
    try:
        from android.runnable import run_on_ui_thread
        from jnius import autoclass
    except Exception:
        return

    @run_on_ui_thread
    def _aplicar():
        try:
            act = autoclass("org.kivy.android.PythonActivity").mActivity
            flag = autoclass("android.view.WindowManager$LayoutParams").FLAG_KEEP_SCREEN_ON
            ventana = act.getWindow()
            if activa:
                ventana.addFlags(flag)
            else:
                ventana.clearFlags(flag)
        except Exception:
            traceback.print_exc()

    _aplicar()


# =====================================================================
#  LÓGICA PURA (sin Kivy): jugadores, sistema suizo, desempates, reloj
# =====================================================================
class Jugador:
    def __init__(self, jid, nombre):
        self.id = jid
        self.nombre = nombre
        self.reset_stats()

    def reset_stats(self):
        self.puntos = 0.0
        self.victorias = 0
        self.tablas = 0
        self.derrotas = 0
        self.byes = 0
        self.oponentes = []    # todos los emparejados (para no repetir rivales)
        self.colores = []      # +1 blancas, -1 negras
        self.partidas = []     # (id_rival, mis_puntos) solo de partidas con resultado
        self.buchholz = 0.0
        self.sb = 0.0


class Torneo:
    """
    Torneo suizo. Las rondas son listas de partidas:
        {"mesa": int, "b": id_blancas, "n": id_negras | None (descanso), "res": None|"1-0"|"1/2"|"0-1"|"bye"}
    Todas las estadísticas se recalculan desde las rondas, así que corregir un
    resultado pasado nunca deja los puntos desfasados.
    """

    def __init__(self):
        self.nombre = ""
        self.jugadores = []
        self.rondas = []
        self.total_rondas = 0
        self.siguiente_id = 1

    # ----- Consultas -----
    @property
    def iniciado(self):
        return bool(self.rondas)

    def por_id(self):
        return {j.id: j for j in self.jugadores}

    def nombre_de(self, jid):
        return self.por_id()[jid].nombre

    def existe(self, nombre):
        n = nombre.strip().lower()
        return any(j.nombre.lower() == n for j in self.jugadores)

    @staticmethod
    def rondas_max(n):
        if n < 2:
            return 1
        return min(12, n - 1 if n % 2 == 0 else n)

    @staticmethod
    def rondas_sugeridas(n):
        return max(1, math.ceil(math.log2(n))) if n > 1 else 1

    # ----- Inscripción -----
    def agregar(self, nombre):
        nombre = nombre.strip()[:MAX_NOMBRE]
        if not nombre or self.iniciado:
            return None
        j = Jugador(self.siguiente_id, nombre)
        self.siguiente_id += 1
        self.jugadores.append(j)
        return j

    def quitar(self, jid):
        if not self.iniciado:
            self.jugadores = [j for j in self.jugadores if j.id != jid]

    # ----- Estadísticas -----
    def recalcular(self):
        idx = self.por_id()
        for j in self.jugadores:
            j.reset_stats()
        for ronda in self.rondas:
            for p in ronda:
                b = idx[p["b"]]
                if p["n"] is None:                 # descanso: 1 punto, sin rival
                    b.puntos += 1.0
                    b.byes += 1
                    continue
                n = idx[p["n"]]
                b.colores.append(1)
                n.colores.append(-1)
                b.oponentes.append(n.id)
                n.oponentes.append(b.id)
                res = p["res"]
                if res in RES_PUNTOS:
                    pb, pn = RES_PUNTOS[res]
                    b.puntos += pb
                    n.puntos += pn
                    b.partidas.append((n.id, pb))
                    n.partidas.append((b.id, pn))
                    if res == "1-0":
                        b.victorias += 1
                        n.derrotas += 1
                    elif res == "0-1":
                        n.victorias += 1
                        b.derrotas += 1
                    else:
                        b.tablas += 1
                        n.tablas += 1
        for j in self.jugadores:
            j.buchholz = sum(idx[o].puntos for o, _ in j.partidas)
            j.sb = sum(idx[o].puntos * s for o, s in j.partidas)

    def clasificacion(self):
        return sorted(self.jugadores,
                      key=lambda j: (-j.puntos, -j.buchholz, -j.sb, -j.victorias, j.nombre.lower()))

    # ----- Estado de las rondas -----
    def ronda_completa(self, i):
        return all(p["res"] is not None for p in self.rondas[i])

    def progreso(self, i):
        jugables = [p for p in self.rondas[i] if p["n"] is not None]
        return sum(1 for p in jugables if p["res"] is not None), len(jugables)

    def finalizado(self):
        return (bool(self.rondas) and len(self.rondas) >= self.total_rondas
                and self.ronda_completa(len(self.rondas) - 1))

    def puede_generar(self):
        if len(self.jugadores) < 2:
            return False
        if not self.rondas:
            return True
        return len(self.rondas) < self.total_rondas and self.ronda_completa(len(self.rondas) - 1)

    def poner_resultado(self, r, m, res):
        """res = '1-0' | '1/2' | '0-1' | None (borra el resultado)."""
        p = self.rondas[r][m]
        if p["n"] is None:
            return False
        p["res"] = res
        self.recalcular()
        return True

    # ----- Emparejamiento suizo -----
    def _emparejar(self, orden, max_rep):
        """Backtracking sobre la lista ordenada: cada jugador busca al rival más cercano
        en la tabla. Permite como máximo `max_rep` revanchas. Tope de nodos para no
        congelar la UI; devuelve None si no hay solución dentro del tope."""
        limite = [20000]

        def resolver(pend, rep_left):
            if not pend:
                return []
            limite[0] -= 1
            if limite[0] < 0:
                return None
            a = pend[0]
            for k in range(1, len(pend)):
                b = pend[k]
                repetido = b.id in a.oponentes
                if repetido and rep_left <= 0:
                    continue
                r = resolver(pend[1:k] + pend[k + 1:], rep_left - (1 if repetido else 0))
                if r is not None:
                    return [(a, b)] + r
            return None

        return resolver(list(orden), max_rep)

    def _emparejar_suizo(self, orden):
        """Primero sin revanchas; si es imposible, con las mínimas posibles."""
        for max_rep in (0, 1, 2, 3, 4):
            pares = self._emparejar(orden, max_rep)
            if pares is not None:
                return pares
        return self._emparejar(orden, len(orden))

    @staticmethod
    def _asignar_colores(a, b, mesa_idx):
        """Quien tenga más negras acumuladas recibe blancas; si empatan, quien jugó con negras
        la última vez; si siguen empatados, se alterna por mesa."""
        ba, bb = sum(a.colores), sum(b.colores)
        if ba != bb:
            blanco = a if ba < bb else b
        else:
            ua = a.colores[-1] if a.colores else 0
            ub = b.colores[-1] if b.colores else 0
            if ua != ub:
                blanco = a if ua < ub else b
            else:
                blanco = a if mesa_idx % 2 == 0 else b
        return blanco, (b if blanco is a else a)

    def generar_ronda(self):
        if not self.puede_generar():
            return None
        self.recalcular()
        n_r = len(self.rondas)
        orden = sorted(self.jugadores, key=lambda j: (-j.puntos, -j.buchholz, j.id))

        bye = None
        if len(orden) % 2 == 1:   # el de menor rango que aún no haya descansado
            for j in reversed(orden):
                if j.byes == 0:
                    bye = j
                    break
            if bye is None:
                bye = orden[-1]
            orden = [j for j in orden if j.id != bye.id]

        if n_r == 0:              # ronda 1: mitad superior contra mitad inferior
            mitad = len(orden) // 2
            pares = [(orden[i], orden[i + mitad]) for i in range(mitad)]
        else:
            pares = self._emparejar_suizo(orden)

        ronda = []
        for i, (a, b) in enumerate(pares):
            bl, ne = self._asignar_colores(a, b, i)
            ronda.append({"mesa": i + 1, "b": bl.id, "n": ne.id, "res": None})
        if bye is not None:
            ronda.append({"mesa": len(pares) + 1, "b": bye.id, "n": None, "res": "bye"})
        self.rondas.append(ronda)
        self.recalcular()
        return ronda

    # ----- Persistencia -----
    def a_dict(self):
        return {"nombre": self.nombre, "total_rondas": self.total_rondas,
                "siguiente_id": self.siguiente_id,
                "jugadores": [{"id": j.id, "nombre": j.nombre} for j in self.jugadores],
                "rondas": self.rondas}

    @classmethod
    def de_dict(cls, d):
        t = cls()
        t.nombre = str(d.get("nombre", ""))
        t.total_rondas = int(d.get("total_rondas", 0))
        t.jugadores = [Jugador(int(j["id"]), str(j["nombre"])) for j in d.get("jugadores", [])]
        t.siguiente_id = int(d.get("siguiente_id", len(t.jugadores) + 1))
        t.rondas = d.get("rondas", [])
        t.recalcular()
        return t


class RelojAjedrez:
    """
    Reloj de dos lados con incremento Fischer. Lado 0 = blancas (abajo), 1 = negras (arriba).
    Usa time.monotonic(): no se desfasa aunque Kivy pierda frames.
    """

    def __init__(self, base=600, inc=0):
        self.configurar(base, inc)

    def configurar(self, base, inc):
        self.base = float(base)
        self.inc = float(inc)
        self.reiniciar()

    def reiniciar(self):
        self.t = [self.base, self.base]
        self.activo = None      # lado cuyo tiempo corre
        self.pausado = False
        self.caido = None       # lado que cayó por tiempo
        self.jugadas = [0, 0]
        self._marca = None

    @property
    def en_marcha(self):
        return self.activo is not None and not self.pausado and self.caido is None

    def actualizar(self):
        """Descuenta lo transcurrido al lado activo. Devuelve el lado caído (o None)."""
        ahora = time.monotonic()
        if self._marca is not None and self.en_marcha:
            self.t[self.activo] -= ahora - self._marca
            if self.t[self.activo] <= 0:
                self.t[self.activo] = 0.0
                self.caido = self.activo
        self._marca = ahora
        return self.caido

    def pulsar(self, lado):
        """El jugador de `lado` toca su botón. El primer toque arranca el reloj del rival."""
        if self.caido is not None or self.pausado:
            return False
        self.actualizar()
        if self.caido is not None:
            return False
        if self.activo is None:
            self.activo = 1 - lado
            self._marca = time.monotonic()
            return True
        if lado != self.activo:
            return False
        self.t[lado] += self.inc
        self.jugadas[lado] += 1
        self.activo = 1 - lado
        self._marca = time.monotonic()
        return True

    def alternar_pausa(self):
        if self.activo is None or self.caido is not None:
            return
        self.actualizar()
        self.pausado = not self.pausado
        self._marca = time.monotonic()


# =====================================================================
#  UTILIDADES GRÁFICAS (heredadas)
# =====================================================================
def degradado(colores, n=64):
    tex = Texture.create(size=(n, 1), colorfmt="rgba")
    buf = bytearray()
    seg = len(colores) - 1
    for i in range(n):
        p = i / (n - 1) * seg
        k = min(int(p), seg - 1)
        f = p - k
        a, b = colores[k], colores[k + 1]
        for c in range(4):
            buf.append(int((a[c] + (b[c] - a[c]) * f) * 255))
    tex.blit_buffer(bytes(buf), colorfmt="rgba", bufferfmt="ubyte")
    return tex


TEX = degradado([hx("#3F5FD0"), hx("#3CC8E8"), hx("#A33FE0")])


def etiqueta(texto, halign="center", **kw):
    """Label que ajusta el texto al ancho y su altura al contenido."""
    kw.setdefault("size_hint_y", None)
    lb = Label(text=texto, halign=halign, **kw)
    lb.bind(width=lambda i, w: setattr(i, "text_size", (w, None)))
    lb.bind(texture_size=lambda i, s: setattr(i, "height", s[1] + dp(6)))
    return lb


def lbl(texto, **kw):
    """Label de una línea con text_size ligado a su tamaño (alineación y shorten correctos)."""
    kw.setdefault("halign", "left")
    kw.setdefault("valign", "middle")
    lb = Label(text=texto, **kw)
    lb.bind(size=lambda i, s: setattr(i, "text_size", s))
    return lb


def campo(pal, **kw):
    """TextInput plano, con colores del tema y texto centrado verticalmente."""
    kw.setdefault("multiline", False)
    kw.setdefault("write_tab", False)
    kw.setdefault("font_size", sp(15))
    return TextInput(background_normal="", background_active="",
                     background_color=pal["GRIS_CLARO"], foreground_color=pal["TEXTO"],
                     hint_text_color=pal["GRIS"], cursor_color=pal["CIAN"],
                     padding=[dp(10), dp(10), dp(10), dp(10)], **kw)


def btn_plano(texto, color, txt=(1, 1, 1, 1), **kw):
    kw.setdefault("bold", True)
    return Button(text=texto, background_normal="", background_color=color, color=txt, **kw)


class BotonGrad(Button):
    def __init__(self, **kw):
        super().__init__(background_normal="", background_down="",
                         background_color=(0, 0, 0, 0),
                         color=(1, 1, 1, 1), bold=True,
                         halign="center", valign="middle", **kw)
        with self.canvas.before:
            self.c = Color(1, 1, 1, 1)
            self.r = RoundedRectangle(texture=TEX, radius=[dp(10)])
        self.bind(pos=self._u, size=self._u)
        self.bind(size=lambda i, s: setattr(i, "text_size", (s[0] - dp(8), s[1])))

    def _u(self, *a):
        self.r.pos, self.r.size = self.pos, self.size

    def estilo(self, grad=True, color=None, txt=None):
        if grad:
            self.c.rgba = (1, 1, 1, 1)
            self.r.texture = TEX
        else:
            self.c.rgba = color
            self.r.texture = None
        if txt:
            self.color = txt


def fila_tabla(vals, pal, cabecera=False, par=False, destacado=False):
    """Fila de la tabla de clasificación: #, jugador, Pts, Bch, SB, V-T-D."""
    fila = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(2), padding=(dp(4), 0))
    with fila.canvas.before:
        if cabecera:
            Color(*pal["AZUL"])
        elif par:
            Color(*pal["FONDO_TARJ"])
        else:
            Color(*pal["GRIS_CLARO"])
        rect = RoundedRectangle(pos=fila.pos, size=fila.size, radius=[dp(6)])
    fila.bind(pos=lambda i, v: setattr(rect, "pos", v),
              size=lambda i, v: setattr(rect, "size", v))
    anchos = (dp(26), None, dp(40), dp(42), dp(46), dp(58))
    for k, (v, ancho) in enumerate(zip(vals, anchos)):
        col = (1, 1, 1, 1) if cabecera else (pal["CIAN"] if destacado else pal["TEXTO"])
        lb = Label(text=str(v), color=col, bold=cabecera or destacado, font_size=sp(12),
                   halign="left" if k == 1 else "center", valign="middle",
                   shorten=True, shorten_from="right")
        if ancho:
            lb.size_hint_x = None
            lb.width = ancho
        lb.bind(size=lambda i, s: setattr(i, "text_size", s))
        fila.add_widget(lb)
    return fila


# ---------- Gráfica de barras ----------
class GraficaBarras(Widget):
    """
    Dibuja barras directamente en su propio canvas.
    - Nunca dibuja si width/height <= 0.
    - El redibujado se agenda con Clock (una sola vez por frame).
    - Cualquier error de dibujo se captura: una gráfica rota no cierra la app.
    """

    def __init__(self, valores, max_val, colores, pal, **kw):
        kw.setdefault("size_hint_y", None)
        kw.setdefault("height", dp(120))
        super().__init__(**kw)
        self.valores = [max(0.0, float(v)) for v in valores]
        self.max_val = max(1.0, float(max_val), max(self.valores, default=0.0))
        self.colores = list(colores) if colores else [hx("#3F5FD0"), hx("#3CC8E8")]
        self.pal = pal
        self._ev = None
        self.bind(pos=self._pedir_dibujo, size=self._pedir_dibujo)
        self._pedir_dibujo()

    def _pedir_dibujo(self, *a):
        if self._ev is None:
            self._ev = Clock.schedule_once(self._dibujar, 0)

    def on_parent(self, inst, parent):
        if parent is None and self._ev is not None:
            self._ev.cancel()
            self._ev = None

    def _dibujar(self, *a):
        self._ev = None
        try:
            w, h = self.size
            if w <= 0 or h <= 0:
                return
            izq, abajo, arriba = dp(16), dp(8), dp(14)
            aw, ah = w - 2 * izq, h - abajo - arriba
            n = len(self.valores)
            if n == 0 or aw <= 0 or ah <= 0:
                return

            slot = aw / float(n)
            bw = min(slot * 0.45, dp(50))

            self.canvas.clear()
            with self.canvas:
                Color(*self.pal["FONDO_TARJ"])
                RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
                for i, v in enumerate(self.valores):
                    cx = self.x + izq + slot * (i + 0.5)
                    alto = max(dp(6), min(1.0, v / float(self.max_val)) * ah)
                    Color(*self.colores[i % len(self.colores)])
                    RoundedRectangle(pos=(cx - bw / 2.0, self.y + abajo),
                                     size=(bw, alto), radius=[dp(4)])
        except Exception:
            traceback.print_exc()


class ContenedorGrafica(BoxLayout):
    """Título + barras + una columna (nombre / valor) por barra."""

    def __init__(self, titulo, etiquetas, valores, max_val, colores, pal, **kw):
        super().__init__(orientation="vertical", size_hint_y=None, height=dp(210),
                         spacing=dp(4), padding=dp(4), **kw)
        self.add_widget(Label(text=titulo, bold=True, font_size=sp(13), color=pal["AZUL"],
                              size_hint_y=None, height=dp(22), halign="center"))
        self.add_widget(GraficaBarras(valores, max_val, colores, pal))

        fila = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
        for i, etq in enumerate(etiquetas):
            val = valores[i] if i < len(valores) else 0
            col = BoxLayout(orientation="vertical")
            col.add_widget(lbl(str(etq), color=pal["TEXTO"], font_size=sp(11), bold=True,
                               halign="center", shorten=True))
            col.add_widget(lbl(num(val), color=pal["TEXTO"], font_size=sp(12), halign="center"))
            fila.add_widget(col)
        self.add_widget(fila)


# =====================================================================
#  RELOJ: tarjeta (un lado) y página
# =====================================================================
class TarjetaReloj(Scatter):
    """Un lado del reloj. El lado de arriba se gira 180° para quien juega enfrente."""

    def __init__(self, lado, app, **kw):
        super().__init__(do_rotation=False, do_scale=False, do_translation=False,
                         auto_bring_to_front=False, **kw)
        self.size_hint = (1, 1)
        self.lado = lado
        self.app = app
        self.rotado = (lado == 1)
        self._ult = None

        self.caja = BoxLayout(size_hint=(None, None), padding=dp(2))
        self.add_widget(self.caja)
        self.btn = Button(markup=True, halign="center", valign="middle",
                          background_normal="", font_size=sp(16))
        self.btn.bind(on_release=lambda *_: app.tocar_reloj(self.lado))
        self.caja.add_widget(self.btn)
        self.bind(size=self._actualizar_tam)

    def _actualizar_tam(self, *a):
        self.caja.size = self.size
        if self.rotado:
            Clock.schedule_once(self._reaplicar_rotacion, 0)

    def _reaplicar_rotacion(self, *a):
        if self.rotado:
            self.rotation = 0
            self.rotation = 180

    def pintar(self, nombre, tiempo, fondo, texto):
        clave = (nombre, tiempo, tuple(fondo), tuple(texto))
        if clave == self._ult:      # evita reconstruir la textura si nada cambió
            return
        self._ult = clave
        self.btn.background_color = fondo
        self.btn.color = texto
        self.btn.text = (f"[size={int(sp(16))}]{escape_markup(nombre)}[/size]\n"
                         f"[size={int(sp(64))}][b]{tiempo}[/b][/size]")


class PaginaReloj(BoxLayout):
    def __init__(self, app, **kw):
        super().__init__(orientation="vertical", spacing=dp(6), **kw)
        self.app = app
        pal, t = app.pal, app.t

        # Control de tiempo
        fila = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(6))
        fila.add_widget(lbl(t("ctrl_tiempo"), color=pal["TEXTO"], size_hint_x=None,
                            width=dp(110), font_size=sp(12)))
        self._etiquetas = [etiqueta_control(c, t) for c in CONTROLES]
        self.sp_ctrl = Spinner(text=self._etiquetas[app.control_idx], values=self._etiquetas,
                               background_normal="", background_color=pal["AZUL"],
                               color=(1, 1, 1, 1))
        self.sp_ctrl.bind(text=self._cambiar_control)
        fila.add_widget(self.sp_ctrl)
        self.add_widget(fila)

        # Mesa vinculada
        vin = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(6))
        nb, nn = app.nombres_reloj()
        if app.reloj_mesa is not None:
            r, m = app.reloj_mesa
            txt = f"{t('reloj_mesa', m=app.torneo.rondas[r][m]['mesa'], r=r + 1)}: {nb} vs {nn}"
        else:
            txt = t("reloj_libre")
        vin.add_widget(lbl(txt, color=pal["MORADO"], font_size=sp(11), bold=True, shorten=True))
        if app.reloj_mesa is not None:
            b_x = btn_plano("X", pal["GRIS_CLARO"], txt=pal["TEXTO"], size_hint_x=None, width=dp(34))
            b_x.bind(on_release=lambda *_: app.desvincular_reloj())
            vin.add_widget(b_x)
        self.add_widget(vin)

        self.arriba = TarjetaReloj(1, app)
        self.add_widget(self.arriba)

        barra = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        self.b_pausa = BotonGrad(text=t("btn_pausa"), font_size=sp(12), size_hint_x=None, width=dp(112))
        self.b_pausa.bind(on_release=lambda *_: app.pausar_reloj())
        self.lbl_estado = lbl("", color=pal["MORADO"], bold=True, font_size=sp(11), halign="center")
        b_reset = btn_plano(t("btn_reset_reloj"), pal["ROJO"], size_hint_x=None, width=dp(112),
                            font_size=sp(12))
        b_reset.bind(on_release=lambda *_: app.reiniciar_reloj())
        for w in (self.b_pausa, self.lbl_estado, b_reset):
            barra.add_widget(w)
        self.add_widget(barra)

        self.abajo = TarjetaReloj(0, app)
        self.add_widget(self.abajo)

        app.ui_reloj = self
        self.refrescar()

    def _cambiar_control(self, spinner, texto):
        try:
            idx = self._etiquetas.index(texto)
        except ValueError:
            return
        app = self.app
        if idx == app.control_idx:
            return
        app.control_idx = idx
        app.reloj.configurar(*CONTROLES[idx][1:])
        app.reloj_avisado = False
        self.refrescar()
        app.guardar_estado()

    def refrescar(self):
        app, pal, t, rl = self.app, self.app.pal, self.app.t, self.app.reloj
        nb, nn = app.nombres_reloj()
        blanco = (1, 1, 1, 1)
        for lado, tarjeta, nom in ((0, self.abajo, nb), (1, self.arriba, nn)):
            if rl.caido == lado:
                fondo, txt = pal["ROJO"], blanco
            elif rl.activo == lado and rl.pausado:
                fondo, txt = pal["AZUL"], blanco
            elif rl.activo == lado:
                fondo = pal["NARANJA"] if rl.t[lado] < 15 else pal["VERDE"]
                txt = blanco
            else:
                fondo, txt = pal["GRIS_CLARO"], pal["TEXTO"]
            tarjeta.pintar(nom, fmt_tiempo(rl.t[lado]), fondo, txt)

        self.b_pausa.text = t("btn_reanudar") if rl.pausado else t("btn_pausa")
        self.b_pausa.disabled = rl.activo is None or rl.caido is not None
        if rl.caido is not None:
            self.lbl_estado.text = t("bandera_titulo")
        elif rl.pausado:
            self.lbl_estado.text = t("pausado")
        elif rl.activo is None:
            self.lbl_estado.text = t("toca_iniciar")
        else:
            self.lbl_estado.text = t("jugadas", a=rl.jugadas[0], b=rl.jugadas[1])


# =====================================================================
#  JUGADORES
# =====================================================================
class PaginaJugadores(BoxLayout):
    def __init__(self, app, **kw):
        super().__init__(orientation="vertical", spacing=dp(6), **kw)
        self.app = app
        pal, t, tor = app.pal, app.t, app.torneo

        self.in_torneo = campo(pal, text=tor.nombre, hint_text=t("hint_torneo"),
                               size_hint_y=None, height=dp(42))
        self.in_torneo.bind(text=lambda i, v: setattr(tor, "nombre", v.strip()[:40]))
        self.add_widget(self.in_torneo)

        if not tor.iniciado:
            fila = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
            self.in_jug = campo(pal, hint_text=t("hint_jugador"))
            self.in_jug.bind(on_text_validate=self.agregar)
            b_add = BotonGrad(text=t("btn_add"), size_hint_x=None, width=dp(90))
            b_add.bind(on_release=self.agregar)
            fila.add_widget(self.in_jug)
            fila.add_widget(b_add)
            self.add_widget(fila)
            self.add_widget(lbl(t("nota_inscripcion"), color=pal["GRIS"], font_size=sp(10),
                                size_hint_y=None, height=dp(18)))
        else:
            self.add_widget(etiqueta(t("nota_bloqueado"), color=pal["GRIS"], font_size=sp(11)))

        self.lbl_n = lbl("", bold=True, color=pal["AZUL"], font_size=sp(13),
                         size_hint_y=None, height=dp(22))
        self.add_widget(self.lbl_n)

        sv = ScrollView()
        self.lista = GridLayout(cols=1, spacing=dp(4), size_hint_y=None)
        self.lista.bind(minimum_height=self.lista.setter("height"))
        sv.add_widget(self.lista)
        self.add_widget(sv)

        self.ctrl = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        self.add_widget(self.ctrl)

        b_nuevo = btn_plano(t("btn_nuevo"), pal["ROJO"], size_hint_y=None, height=dp(38),
                            font_size=sp(12))
        b_nuevo.bind(on_release=self.confirmar_nuevo)
        self.add_widget(b_nuevo)

        self.refrescar()

    def refrescar(self):
        app, pal, t, tor = self.app, self.app.pal, self.app.t, self.app.torneo
        self.lbl_n.text = t("jugadores_n", n=len(tor.jugadores))

        self.lista.clear_widgets()
        for i, j in enumerate(tor.jugadores, 1):
            f = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(6))
            f.add_widget(lbl(f"{i}. {j.nombre}", color=pal["TEXTO"], shorten=True,
                             shorten_from="right"))
            if not tor.iniciado:
                b = btn_plano("X", pal["ROJO"], size_hint_x=None, width=dp(40))
                b.bind(on_release=lambda _, jid=j.id: self.quitar(jid))
                f.add_widget(b)
            self.lista.add_widget(f)

        self.ctrl.clear_widgets()
        if not tor.iniciado:
            n = len(tor.jugadores)
            maxr = Torneo.rondas_max(n)
            sug = min(Torneo.rondas_sugeridas(n), maxr)
            self.ctrl.add_widget(lbl(t("rondas_label"), color=pal["TEXTO"], size_hint_x=None,
                                     width=dp(64)))
            self.sp_r = Spinner(text=str(sug), values=[str(k) for k in range(1, maxr + 1)],
                                size_hint_x=None, width=dp(64), background_normal="",
                                background_color=pal["AZUL"], color=(1, 1, 1, 1))
            self.ctrl.add_widget(self.sp_r)
            b = BotonGrad(text=t("btn_iniciar"))
            b.bind(on_release=self.iniciar)
            self.ctrl.add_widget(b)
        else:
            self.ctrl.add_widget(lbl(t("estado_torneo", nom=tor.nombre or t("torneo_def"),
                                       r=len(tor.rondas), t=tor.total_rondas),
                                     color=pal["MORADO"], bold=True, font_size=sp(12),
                                     shorten=True))

    @blindado
    def agregar(self, *a):
        app, t, tor = self.app, self.app.t, self.app.torneo
        nombre = self.in_jug.text.strip()
        if not nombre:
            return
        if tor.existe(nombre):
            app.aviso(t("error"), t("err_dup"))
            return
        if len(tor.jugadores) >= MAX_JUGADORES:
            app.aviso(t("error"), t("err_max"))
            return
        tor.agregar(nombre)
        self.in_jug.text = ""
        app.guardar_estado()
        self.refrescar()
        Clock.schedule_once(lambda *_: setattr(self.in_jug, "focus", True), 0.1)

    @blindado
    def quitar(self, jid):
        self.app.torneo.quitar(jid)
        self.app.guardar_estado()
        self.refrescar()

    @blindado
    def iniciar(self, *a):
        app, t = self.app, self.app.t
        if len(app.torneo.jugadores) < 2:
            app.aviso(t("error"), t("err_min"))
            return
        app.iniciar_torneo(int(self.sp_r.text))

    @blindado
    def confirmar_nuevo(self, *a):
        app, pal, t = self.app, self.app.pal, self.app.t
        cont = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))
        cont.add_widget(lbl(t("confirmar_nuevo"), color=pal["TEXTO"], halign="center"))
        fila = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        b_si = btn_plano(t("si"), pal["ROJO"])
        b_no = btn_plano(t("no"), pal["GRIS_CLARO"], txt=pal["TEXTO"])
        fila.add_widget(b_si)
        fila.add_widget(b_no)
        cont.add_widget(fila)
        p = Popup(title=t("btn_nuevo"), content=cont, size_hint=(0.85, 0.35), background="",
                  background_color=pal["VENTANA"], title_color=pal["AZUL"])

        def hacer(*_):
            p.dismiss()
            app.nuevo_torneo()

        b_si.bind(on_release=hacer)
        b_no.bind(on_release=p.dismiss)
        p.open()


# =====================================================================
#  RONDAS
# =====================================================================
class TarjetaPartida(BoxLayout):
    def __init__(self, pagina, app, ridx, midx, **kw):
        p = app.torneo.rondas[ridx][midx]
        bye = p["n"] is None
        super().__init__(orientation="vertical", size_hint_y=None,
                         height=dp(70) if bye else dp(116),
                         padding=dp(8), spacing=dp(4), **kw)
        self.p = p
        self.pagina, self.app, self.ridx, self.midx = pagina, app, ridx, midx
        self.botones = {}
        with self.canvas.before:
            Color(*app.pal["FONDO_TARJ"])
            self._fondo = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
        self.bind(pos=self._u, size=self._u)
        self.construir()

    def _u(self, *a):
        self._fondo.pos, self._fondo.size = self.pos, self.size

    def construir(self):
        app, pal, t, tor, p = self.app, self.app.pal, self.app.t, self.app.torneo, self.p
        cab = BoxLayout(size_hint_y=None, height=dp(26), spacing=dp(6))
        cab.add_widget(lbl(t("mesa", n=p["mesa"]), bold=True, color=pal["MORADO"], font_size=sp(12)))
        if p["n"] is not None:
            bt = btn_plano(t("tab_reloj"), pal["AZUL"], size_hint_x=None, width=dp(64), font_size=sp(11))
            bt.bind(on_release=lambda *_: app.vincular_reloj(self.ridx, self.midx))
            cab.add_widget(bt)
        self.add_widget(cab)

        if p["n"] is None:
            self.add_widget(lbl(t("descansa", nom=tor.nombre_de(p["b"])), color=pal["VERDE"],
                                bold=True, font_size=sp(13), halign="center", shorten=True))
            return

        nb, nn = tor.nombre_de(p["b"]), tor.nombre_de(p["n"])
        txt = (f"[b]{escape_markup(nb)}[/b] ({t('blancas_c')})  vs  "
               f"[b]{escape_markup(nn)}[/b] ({t('negras_c')})")
        self.add_widget(lbl(txt, markup=True, color=pal["TEXTO"], font_size=sp(14),
                            halign="center", shorten=True))

        fila = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(6))
        for res in ("1-0", "1/2", "0-1"):
            b = Button(text=RES_TXT[res], background_normal="", bold=True, font_size=sp(14))
            b.bind(on_release=lambda _, r=res: self.pagina.elegir(self, r))
            self.botones[res] = b
            fila.add_widget(b)
        self.add_widget(fila)
        self.pintar()

    def pintar(self):
        pal = self.app.pal
        for res, b in self.botones.items():
            sel = self.p["res"] == res
            b.background_color = pal["VERDE"] if sel else pal["GRIS_CLARO"]
            b.color = (1, 1, 1, 1) if sel else pal["TEXTO"]


class PaginaRondas(BoxLayout):
    def __init__(self, app, **kw):
        super().__init__(orientation="vertical", spacing=dp(6), **kw)
        self.app = app
        pal, t, tor = app.pal, app.t, app.torneo

        if not tor.rondas:
            self.add_widget(lbl(t("sin_ronda"), color=pal["GRIS"], halign="center"))
            return

        self.r = max(0, min(app.ronda_vista, len(tor.rondas) - 1))

        nav = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        b_prev = btn_plano("<", pal["GRIS_CLARO"], txt=pal["TEXTO"], size_hint_x=None, width=dp(48))
        b_next = btn_plano(">", pal["GRIS_CLARO"], txt=pal["TEXTO"], size_hint_x=None, width=dp(48))
        b_prev.bind(on_release=lambda *_: self.cambiar(-1))
        b_next.bind(on_release=lambda *_: self.cambiar(1))
        b_prev.disabled = self.r == 0
        b_next.disabled = self.r >= len(tor.rondas) - 1
        nav.add_widget(b_prev)
        nav.add_widget(lbl(t("ronda_titulo", r=self.r + 1, t=tor.total_rondas), bold=True,
                           color=pal["AZUL"], font_size=sp(16), halign="center"))
        nav.add_widget(b_next)
        self.add_widget(nav)

        self.lbl_prog = lbl("", color=pal["TEXTO"], font_size=sp(12), halign="center",
                            size_hint_y=None, height=dp(20))
        self.add_widget(self.lbl_prog)

        sv = ScrollView()
        self.lista = GridLayout(cols=1, spacing=dp(8), size_hint_y=None, padding=(0, 0, 0, dp(4)))
        self.lista.bind(minimum_height=self.lista.setter("height"))
        for m in range(len(tor.rondas[self.r])):
            self.lista.add_widget(TarjetaPartida(self, app, self.r, m))
        sv.add_widget(self.lista)
        self.add_widget(sv)

        self.pie = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(48),
                             spacing=dp(4))
        self.add_widget(self.pie)
        self.refrescar_pie()

    def cambiar(self, delta):
        self.app.ronda_vista = max(0, self.r + delta)
        self.app.mostrar(1)

    @blindado
    def elegir(self, tarjeta, res):
        nuevo = None if tarjeta.p["res"] == res else res   # tocar de nuevo = borrar
        self.app.registrar_resultado(self.r, tarjeta.midx, nuevo)
        tarjeta.pintar()
        self.refrescar_pie()

    def refrescar_pie(self):
        app, pal, t, tor = self.app, self.app.pal, self.app.t, self.app.torneo
        c, n = tor.progreso(self.r)
        self.lbl_prog.text = t("progreso", c=c, n=n)
        self.pie.clear_widgets()
        if tor.finalizado():
            camp = tor.clasificacion()[0]
            self.pie.height = dp(92)
            self.pie.add_widget(lbl(t("campeon", nom=camp.nombre, p=num(camp.puntos)), bold=True,
                                    color=pal["VERDE"], halign="center", shorten=True))
            b = BotonGrad(text=t("btn_ver_clas"), size_hint_y=None, height=dp(44))
            b.bind(on_release=lambda *_: app.mostrar(3))
            self.pie.add_widget(b)
        elif self.r == len(tor.rondas) - 1:
            self.pie.height = dp(48)
            if tor.puede_generar():
                b = BotonGrad(text=t("btn_sig_ronda", n=len(tor.rondas) + 1))
                b.bind(on_release=lambda *_: app.generar_siguiente())
                self.pie.add_widget(b)
            else:
                self.pie.add_widget(lbl(t("falta_result"), color=pal["GRIS"], font_size=sp(11),
                                        halign="center"))
        else:
            self.pie.height = 0


# =====================================================================
#  CLASIFICACIÓN
# =====================================================================
class PaginaClasificacion(BoxLayout):
    def __init__(self, app, **kw):
        super().__init__(orientation="vertical", spacing=dp(6), **kw)
        pal, t, tor = app.pal, app.t, app.torneo

        self.add_widget(lbl(tor.nombre or t("torneo_def"), bold=True, color=pal["AZUL"],
                            font_size=sp(16), halign="center", size_hint_y=None, height=dp(26),
                            shorten=True))
        if tor.rondas:
            sub = t("ronda_titulo", r=len(tor.rondas), t=tor.total_rondas)
            self.add_widget(lbl(sub, color=pal["MORADO"], font_size=sp(12), halign="center",
                                size_hint_y=None, height=dp(18)))

        self.add_widget(fila_tabla(["#", t("col_jug"), "Pts", "Bch", "SB", t("col_vtd")],
                                   pal, cabecera=True))
        sv = ScrollView()
        box = GridLayout(cols=1, spacing=dp(2), size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))
        for i, j in enumerate(tor.clasificacion(), 1):
            vals = [i, j.nombre, num(j.puntos), num(j.buchholz), num(j.sb),
                    f"{j.victorias}-{j.tablas}-{j.derrotas}"]
            box.add_widget(fila_tabla(vals, pal, par=(i % 2 == 0), destacado=(i == 1 and bool(tor.rondas))))
        sv.add_widget(box)
        self.add_widget(sv)

        self.add_widget(etiqueta(t("leyenda"), color=pal["GRIS"], font_size=sp(10)))
        b = BotonGrad(text=t("btn_datos"), size_hint_y=None, height=dp(44), font_size=sp(12))
        b.bind(on_release=app.abrir_datos)
        self.add_widget(b)


# =====================================================================
#  CENTRO DE DATOS (resumen / historial / reporte / exportar)
# =====================================================================
class CentroDatos(Popup):
    def __init__(self, app, **kw):
        pal = app.pal
        caja = BoxLayout(orientation="vertical", padding=dp(6), spacing=dp(6))
        tabs = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
        cont = BoxLayout()
        b_cerrar = BotonGrad(text=app.t("cerrar"), size_hint_y=None, height=dp(40))

        for w in (tabs, cont, b_cerrar):
            caja.add_widget(w)

        super().__init__(title=app.t("hist_titulo"), content=caja,
                         size_hint=(0.95, 0.9), background="",
                         background_color=pal["VENTANA"], title_color=pal["AZUL"],
                         separator_color=pal["MORADO"], **kw)
        self.app, self.cont = app, cont
        self.txt_reporte = ""
        self.b_tab = []

        for i, k in enumerate(("tab_resumen", "tab_historial", "tab_reporte")):
            b = BotonGrad(text=app.t(k), font_size=sp(12))
            b.bind(on_release=lambda _, i=i: self.mostrar(i))
            tabs.add_widget(b)
            self.b_tab.append(b)

        b_cerrar.bind(on_release=self.dismiss)
        self.mostrar(0)

    @blindado
    def mostrar(self, i):
        pal = self.app.pal
        for j, b in enumerate(self.b_tab):
            if j == i:
                b.estilo(grad=True, txt=(1, 1, 1, 1))
            else:
                b.estilo(grad=False, color=pal["GRIS_CLARO"], txt=pal["TEXTO"])
        self.cont.clear_widgets()
        self.cont.add_widget((self.pag_resumen, self.pag_historial, self.pag_reporte)[i]())

    def pag_resumen(self):
        app, pal, t, tor = self.app, self.app.pal, self.app.t, self.app.torneo
        sv = ScrollView()
        caja = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10), size_hint_y=None)
        caja.bind(minimum_height=caja.setter("height"))

        jugadas = sum(p["res"] in RES_PUNTOS for ronda in tor.rondas for p in ronda)
        tablas = sum(p["res"] == "1/2" for ronda in tor.rondas for p in ronda)
        for texto, col, neg in (
                (t("res_jugadores", n=len(tor.jugadores)), pal["AZUL"], True),
                (t("res_ronda", r=len(tor.rondas), t=tor.total_rondas), pal["MORADO"], True),
                (t("res_jugadas", n=jugadas), pal["TEXTO"], False),
                (t("res_tablas", n=tablas), pal["TEXTO"], False)):
            caja.add_widget(Label(text=texto, color=col, font_size=sp(13), bold=neg,
                                  size_hint_y=None, height=dp(22)))

        top = tor.clasificacion()[:6]
        if top:
            caja.add_widget(ContenedorGrafica(
                t("graf_pts_titulo"), [j.nombre for j in top], [j.puntos for j in top],
                max(1, len(tor.rondas)), [pal["AZUL"], pal["CIAN"], pal["MORADO"]], pal))
        sv.add_widget(caja)
        return sv

    def pag_historial(self):
        app, pal = self.app, self.app.pal
        sv = ScrollView()
        box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(2))
        box.bind(minimum_height=box.setter("height"))
        for h in reversed(app.historial):
            box.add_widget(etiqueta(app.texto_evento(h), halign="left",
                                    color=pal["TEXTO"], font_size=sp(12)))
        sv.add_widget(box)
        return sv

    def pag_reporte(self):
        app, pal, t = self.app, self.app.pal, self.app.t
        self.txt_reporte = app.texto_reporte()
        caja = BoxLayout(orientation="vertical", spacing=dp(6))
        sv = ScrollView()
        sv.add_widget(etiqueta(self.txt_reporte, halign="left", valign="top",
                               color=pal["TEXTO"], font_size=sp(12)))
        caja.add_widget(sv)

        fila = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(4))
        for clave, fn in (("btn_copiar", self.copiar), ("btn_txt", self.guardar_txt),
                          ("btn_csv_tabla", self.guardar_csv_tabla),
                          ("btn_csv_part", self.guardar_csv_partidas)):
            b = BotonGrad(text=t(clave), font_size=sp(11))
            b.bind(on_release=fn)
            fila.add_widget(b)
        caja.add_widget(fila)
        return caja

    @blindado
    def copiar(self, *a):
        Clipboard.copy(self.txt_reporte)
        self.app.aviso(self.app.t("listo"), self.app.t("copiado"))

    @blindado
    def guardar_txt(self, *a):
        ruta = self.app.guardar_archivo("reporte_torneo.txt", self.txt_reporte)
        self._avisar_guardado(ruta)

    @blindado
    def guardar_csv_tabla(self, *a):
        app, t, tor = self.app, self.app.t, self.app.torneo
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(t("csv_cols_tabla"))
        for i, j in enumerate(tor.clasificacion(), 1):
            w.writerow([i, j.nombre, num(j.puntos), num(j.buchholz), num(j.sb),
                        j.victorias, j.tablas, j.derrotas])
        self._avisar_guardado(app.guardar_archivo("clasificacion_torneo.csv", buf.getvalue(), bom=True))

    @blindado
    def guardar_csv_partidas(self, *a):
        app, t, tor = self.app, self.app.t, self.app.torneo
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(t("csv_cols_part"))
        for r, ronda in enumerate(tor.rondas, 1):
            for p in ronda:
                nn = tor.nombre_de(p["n"]) if p["n"] is not None else ""
                res = "bye" if p["n"] is None else RES_TXT.get(p["res"], "")
                w.writerow([r, p["mesa"], tor.nombre_de(p["b"]), nn, res])
        self._avisar_guardado(app.guardar_archivo("partidas_torneo.csv", buf.getvalue(), bom=True))

    def _avisar_guardado(self, ruta):
        t = self.app.t
        if ruta:
            self.app.aviso(t("guardado"), ruta)
        else:
            self.app.aviso(t("listo"), t("err_guardar"))


# =====================================================================
#  APLICACIÓN
# =====================================================================
class ChessTournamentApp(App):
    title = APP_NOMBRE

    def build(self):
        self.lang = "es"
        self.modo_oscuro = True
        self.pal = PALETAS["oscuro"]
        Window.clearcolor = self.pal["VENTANA"]
        try:
            Window.softinput_mode = "below_target"
        except Exception:
            pass

        self.torneo = Torneo()
        self.historial = []
        self.reloj = RelojAjedrez()
        self.control_idx = CONTROL_DEFECTO
        self.reloj_mesa = None        # (ronda_idx, partida_idx) o None = partida libre
        self.reloj_avisado = False
        self.ui_reloj = None
        self.ronda_vista = 0
        self.pagina = 0
        self._popup_datos = None
        self._pantalla_on = False
        self._ev_reloj = None

        self.cargar_estado()
        self.reloj.configurar(*CONTROLES[self.control_idx][1:])

        self.raiz = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(6))
        self.armar_ui()
        return self.raiz

    def on_start(self):
        self._ev_reloj = Clock.schedule_interval(self.tick_reloj, 0.1)

    def on_pause(self):
        self.guardar_estado()
        return True            # Android: no cerrar la app al pasar a segundo plano

    def on_resume(self):
        pass

    def on_stop(self):
        if self._ev_reloj is not None:
            self._ev_reloj.cancel()
        self.guardar_estado()
        pantalla_encendida(False)

    # ----- Idioma -----
    def t(self, clave, **kw):
        txt = TEXTOS[self.lang].get(clave, clave)
        return txt.format(**kw) if kw and isinstance(txt, str) else txt

    # ----- Persistencia (JSON en la carpeta privada de la app) -----
    def ruta_estado(self):
        return os.path.join(self.user_data_dir, "torneo_estado.json")

    def guardar_estado(self):
        try:
            datos = {"v": 1, "torneo": self.torneo.a_dict(),
                     "historial": self.historial[-MAX_HISTORIAL:],
                     "lang": self.lang, "oscuro": self.modo_oscuro,
                     "control": self.control_idx, "ronda_vista": self.ronda_vista}
            ruta = self.ruta_estado()
            os.makedirs(os.path.dirname(ruta), exist_ok=True)
            tmp = ruta + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False)
            os.replace(tmp, ruta)       # escritura atómica: nunca queda un JSON a medias
        except Exception:
            traceback.print_exc()

    def cargar_estado(self):
        try:
            ruta = self.ruta_estado()
            if not os.path.exists(ruta):
                return
            with open(ruta, encoding="utf-8") as f:
                d = json.load(f)
            self.torneo = Torneo.de_dict(d["torneo"])
            self.historial = list(d.get("historial", []))
            if d.get("lang") in TEXTOS:
                self.lang = d["lang"]
            self.modo_oscuro = bool(d.get("oscuro", True))
            self.pal = PALETAS["oscuro" if self.modo_oscuro else "claro"]
            Window.clearcolor = self.pal["VENTANA"]
            self.control_idx = min(max(int(d.get("control", CONTROL_DEFECTO)), 0), len(CONTROLES) - 1)
            self.ronda_vista = int(d.get("ronda_vista", 0))
            self.pagina = 1 if self.torneo.iniciado else 0
        except Exception:
            traceback.print_exc()

    # ----- Interfaz principal -----
    def armar_ui(self):
        pal, t = self.pal, self.t
        self.raiz.clear_widgets()

        cab = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(6))
        if os.path.exists(LOGO):
            cab.add_widget(Image(source=LOGO, size_hint=(None, None), size=(dp(44), dp(44))))

        t_box = BoxLayout(orientation="vertical")
        for texto, col, tam, neg in ((t("titulo"), pal["AZUL"], 16, True),
                                     (t("sub"), pal["GRIS"], 10, False)):
            t_box.add_widget(lbl(texto, color=col, font_size=sp(tam), bold=neg))
        cab.add_widget(t_box)

        b_tema = BotonGrad(text=t("tema_claro") if self.modo_oscuro else t("tema_oscuro"),
                           size_hint_x=None, width=dp(58), font_size=sp(10))
        b_tema.bind(on_release=self.alternar_tema)
        cab.add_widget(b_tema)

        b_lang = BotonGrad(text="EN" if self.lang == "es" else "ES",
                           size_hint_x=None, width=dp(44), font_size=sp(11))
        b_lang.bind(on_release=self.alternar_idioma)
        cab.add_widget(b_lang)

        b_info = BotonGrad(text="INFO", size_hint_x=None, width=dp(52), font_size=sp(12))
        b_info.bind(on_release=self.abrir_contacto)
        cab.add_widget(b_info)
        self.raiz.add_widget(cab)

        self.cuerpo = BoxLayout()
        self.raiz.add_widget(self.cuerpo)

        nav = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(4))
        self.b_nav = []
        for i, k in enumerate(("tab_jug", "tab_rondas", "tab_reloj", "tab_clas")):
            b = BotonGrad(text=t(k), font_size=sp(11))
            b.bind(on_release=lambda _, i=i: self.mostrar(i))
            nav.add_widget(b)
            self.b_nav.append(b)
        self.raiz.add_widget(nav)

        self.mostrar(self.pagina)

    @blindado
    def mostrar(self, i):
        pal = self.pal
        self.pagina = i
        self.ui_reloj = None
        for j, b in enumerate(self.b_nav):
            if j == i:
                b.estilo(grad=True, txt=(1, 1, 1, 1))
            else:
                b.estilo(grad=False, color=pal["GRIS_CLARO"], txt=pal["TEXTO"])
        self.cuerpo.clear_widgets()
        clase = (PaginaJugadores, PaginaRondas, PaginaReloj, PaginaClasificacion)[i]
        self.cuerpo.add_widget(clase(self))

    @blindado
    def alternar_idioma(self, *a):
        self.lang = "en" if self.lang == "es" else "es"
        self.armar_ui()
        self.guardar_estado()

    @blindado
    def alternar_tema(self, *a):
        self.modo_oscuro = not self.modo_oscuro
        self.pal = PALETAS["oscuro" if self.modo_oscuro else "claro"]
        Window.clearcolor = self.pal["VENTANA"]
        self.armar_ui()
        self.guardar_estado()

    # ----- Historial -----
    def log(self, tipo, **datos):
        self.historial.append({"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                               "tipo": tipo, "d": datos})

    def texto_evento(self, h, con_hora=True):
        """Convierte un evento guardado en texto, en el idioma actual."""
        t, d, tp = self.t, h["d"], h["tipo"]
        if tp == "inicio":
            cuerpo = t("ev_inicio", nom=d.get("nom") or t("torneo_def"), j=d["j"], r=d["r"])
        elif tp == "ronda":
            cuerpo = t("ev_ronda", r=d["r"])
        elif tp == "resultado":
            cuerpo = t("ev_resultado", r=d["r"], m=d["m"], b=d["b"], n=d["n"], res=RES_TXT[d["res"]])
        elif tp == "borrado":
            cuerpo = t("ev_borrado", r=d["r"], m=d["m"], b=d["b"], n=d["n"])
        elif tp == "bye":
            cuerpo = t("ev_bye", r=d["r"], nom=d["nom"])
        elif tp == "bandera":
            cuerpo = t("ev_bandera", nom=d["nom"])
        elif tp == "fin":
            cuerpo = t("ev_fin", nom=d["nom"])
        else:
            cuerpo = str(tp)
        return f"[{h['ts'][11:]}] {cuerpo}" if con_hora else cuerpo

    def texto_partida(self, p):
        t, tor = self.t, self.torneo
        if p["n"] is None:
            return t("descansa", nom=tor.nombre_de(p["b"]))
        res = RES_TXT.get(p["res"], t("pendiente"))
        return (f"{t('mesa', n=p['mesa'])}: {tor.nombre_de(p['b'])} ({t('blancas_c')}) vs "
                f"{tor.nombre_de(p['n'])} ({t('negras_c')})  ->  {res}")

    def texto_reporte(self):
        t, tor = self.t, self.torneo
        L = [f"{tor.nombre or t('torneo_def')} · {APP_NOMBRE}",
             datetime.now().strftime("%Y-%m-%d %H:%M"), "",
             t("clas_titulo").upper()]
        for i, j in enumerate(tor.clasificacion(), 1):
            L.append(f"{i:>2}. {j.nombre} | {num(j.puntos)} pts | Bch {num(j.buchholz)} | "
                     f"SB {num(j.sb)} | {j.victorias}-{j.tablas}-{j.derrotas}")
        for r, ronda in enumerate(tor.rondas, 1):
            L.append("")
            L.append(t("ronda_titulo", r=r, t=tor.total_rondas).upper())
            for p in ronda:
                L.append("  " + self.texto_partida(p))
        return "\n".join(L)

    # ----- Flujo del torneo -----
    def iniciar_torneo(self, total):
        tor = self.torneo
        tor.total_rondas = total
        self.log("inicio", nom=tor.nombre, j=len(tor.jugadores), r=total)
        self._generar()
        self.mostrar(1)

    def _generar(self):
        tor = self.torneo
        ronda = tor.generar_ronda()
        if ronda is None:
            return
        n = len(tor.rondas)
        self.log("ronda", r=n)
        for p in ronda:
            if p["n"] is None:
                self.log("bye", r=n, nom=tor.nombre_de(p["b"]))
        self.ronda_vista = n - 1
        self.guardar_estado()

    @blindado
    def generar_siguiente(self, *a):
        if not self.torneo.puede_generar():
            self.aviso(self.t("error"), self.t("falta_result"))
            return
        self._generar()
        self.mostrar(1)

    def registrar_resultado(self, r, m, res):
        tor = self.torneo
        p = tor.rondas[r][m]
        if p["n"] is None:
            return
        estaba = tor.finalizado()
        tor.poner_resultado(r, m, res)
        b, n = tor.nombre_de(p["b"]), tor.nombre_de(p["n"])
        if res is None:
            self.log("borrado", r=r + 1, m=p["mesa"], b=b, n=n)
        else:
            self.log("resultado", r=r + 1, m=p["mesa"], b=b, n=n, res=res)
        if tor.finalizado() and not estaba:
            camp = tor.clasificacion()[0]
            self.log("fin", nom=camp.nombre)
            self.aviso(self.t("torneo_fin"), self.t("campeon", nom=camp.nombre, p=num(camp.puntos)))
        self.guardar_estado()

    def nuevo_torneo(self):
        self.torneo = Torneo()
        self.historial = []
        self.reloj_mesa = None
        self.reloj.reiniciar()
        self.reloj_avisado = False
        self.ronda_vista = 0
        self.guardar_estado()
        self.mostrar(0)

    # ----- Reloj -----
    def nombres_reloj(self):
        """(nombre de abajo = blancas, nombre de arriba = negras)."""
        t = self.t
        if self.reloj_mesa is not None:
            try:
                r, m = self.reloj_mesa
                p = self.torneo.rondas[r][m]
                return self.torneo.nombre_de(p["b"]), self.torneo.nombre_de(p["n"])
            except Exception:
                self.reloj_mesa = None
        return t("lado_blancas"), t("lado_negras")

    @blindado
    def vincular_reloj(self, r, m):
        self.reloj_mesa = (r, m)
        self.reloj.reiniciar()
        self.reloj_avisado = False
        self.mostrar(2)

    @blindado
    def desvincular_reloj(self, *a):
        self.reloj_mesa = None
        self.mostrar(2)

    @blindado
    def tocar_reloj(self, lado):
        self.reloj.pulsar(lado)
        if self.ui_reloj is not None:
            self.ui_reloj.refrescar()

    @blindado
    def pausar_reloj(self, *a):
        self.reloj.alternar_pausa()
        if self.ui_reloj is not None:
            self.ui_reloj.refrescar()

    @blindado
    def reiniciar_reloj(self, *a):
        self.reloj.reiniciar()
        self.reloj_avisado = False
        if self.ui_reloj is not None:
            self.ui_reloj.refrescar()

    def tick_reloj(self, dt):
        """Se ejecuta cada 0.1 s en el hilo principal de Kivy (no hay hilos de fondo)."""
        try:
            lado = self.reloj.actualizar()
            en_marcha = self.reloj.en_marcha
            if en_marcha != self._pantalla_on:
                self._pantalla_on = en_marcha
                pantalla_encendida(en_marcha)
            if lado is not None and not self.reloj_avisado:
                self.reloj_avisado = True
                self.bandera(lado)
            if self.ui_reloj is not None:
                self.ui_reloj.refrescar()
        except Exception:
            traceback.print_exc()

    def bandera(self, lado):
        pal, t = self.pal, self.t
        nb, nn = self.nombres_reloj()
        perdedor = nb if lado == 0 else nn
        vinculada = self.reloj_mesa is not None
        if vinculada:
            self.log("bandera", nom=perdedor)
            self.guardar_estado()

        cont = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        cont.add_widget(lbl(t("bandera_msg", nom=perdedor), color=pal["TEXTO"], halign="center",
                            font_size=sp(16), bold=True))
        p = Popup(title=t("bandera_titulo"), content=cont,
                  size_hint=(0.9, 0.42 if vinculada else 0.3), background="",
                  background_color=pal["VENTANA"], title_color=pal["ROJO"], auto_dismiss=False)

        if vinculada:
            res = "0-1" if lado == 0 else "1-0"
            r, m = self.reloj_mesa

            def registrar(valor):
                p.dismiss()
                self.registrar_resultado(r, m, valor)
                self.mostrar(self.pagina)

            b1 = BotonGrad(text=t("btn_reg", res=RES_TXT[res]), size_hint_y=None, height=dp(42))
            b1.bind(on_release=lambda *_: registrar(res))
            b2 = btn_plano(t("btn_reg_tablas"), pal["GRIS_CLARO"], txt=pal["TEXTO"],
                           size_hint_y=None, height=dp(40))
            b2.bind(on_release=lambda *_: registrar("1/2"))
            cont.add_widget(b1)
            cont.add_widget(b2)
        b_c = btn_plano(t("cerrar"), pal["GRIS_CLARO"], txt=pal["TEXTO"], size_hint_y=None,
                        height=dp(40))
        b_c.bind(on_release=p.dismiss)
        cont.add_widget(b_c)
        p.open()

    # ----- Datos, archivos y avisos -----
    @blindado
    def abrir_datos(self, *a):
        if self._popup_datos is not None:
            return
        p = CentroDatos(self)
        self._popup_datos = p
        p.bind(on_dismiss=lambda *_: setattr(self, "_popup_datos", None))
        p.open()

    def guardar_archivo(self, nombre, contenido, bom=False):
        """Guarda en Descargas (Android) o, si no se puede, en la carpeta de la app."""
        carpetas = [c for c in ("/storage/emulated/0/Download", "/sdcard/Download") if os.path.isdir(c)]
        try:
            carpetas.append(self.user_data_dir)
        except Exception:
            pass
        carpetas.append(QUIEN)

        base, ext = os.path.splitext(nombre)
        sello = datetime.now().strftime("%Y%m%d_%H%M%S")
        for carpeta in carpetas:
            try:
                os.makedirs(carpeta, exist_ok=True)
                ruta = os.path.join(carpeta, f"{base}_{sello}{ext}")
                with open(ruta, "w", encoding="utf-8-sig" if bom else "utf-8", newline="") as f:
                    f.write(contenido)
                return ruta
            except Exception:
                continue
        return None

    def abrir(self, url):
        try:
            import webbrowser
            if not webbrowser.open(url):
                raise RuntimeError("sin navegador")
        except Exception:
            Clipboard.copy(url)
            self.aviso(self.t("enlace_copiado"), url)

    def aviso(self, titulo, texto):
        pal = self.pal
        cont = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))
        lb = Label(text=texto or "", color=pal["TEXTO"], halign="center", valign="middle")
        lb.bind(size=lambda i, s: setattr(i, "text_size", s))
        b = BotonGrad(text=self.t("entendido"), size_hint_y=None, height=dp(44))
        cont.add_widget(lb)
        cont.add_widget(b)
        p = Popup(title=titulo, content=cont, size_hint=(0.9, 0.4), background="",
                  background_color=pal["VENTANA"], title_color=pal["AZUL"])
        b.bind(on_release=p.dismiss)
        p.open()

    @blindado
    def abrir_contacto(self, *a):
        pal, t = self.pal, self.t
        cont = ScrollView(size_hint=(1, 1))
        caja = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10), size_hint_y=None)
        caja.bind(minimum_height=caja.setter("height"))

        if os.path.exists(LOGO2):
            caja.add_widget(Image(source=LOGO2, size_hint=(None, None), size=(dp(120), dp(120)),
                                  pos_hint={'center_x': 0.5}))

        caja.add_widget(etiqueta(t("info_servicios"), markup=True, color=pal["TEXTO"]))
        caja.add_widget(etiqueta(t("licencia_txt", v=APP_VERSION), color=pal["GRIS"], font_size=sp(11)))

        for texto, url in ((t("btn_telegram") + "t.me/CipherlosAltos", TELEGRAM),
                           (t("btn_blog"), BLOG),
                           (t("btn_github"), GITHUB_REPO),
                           (t("btn_fdroid"), FDROID)):
            b = BotonGrad(text=texto, size_hint_y=None, height=dp(44))
            b.bind(on_release=lambda *_, u=url: self.abrir(u))
            caja.add_widget(b)

        caja.add_widget(Label(text=t("lbl_apoyo"), bold=True, color=pal["MORADO"],
                              size_hint_y=None, height=dp(30)))
        caja.add_widget(etiqueta(t("txt_apoyo"), color=pal["TEXTO"]))

        for texto, url in ((t("btn_paypal"), PAYPAL), (t("btn_kofi"), KOFI)):
            b = BotonGrad(text=texto, size_hint_y=None, height=dp(44))
            b.bind(on_release=lambda *_, u=url: self.abrir(u))
            caja.add_widget(b)

        cerrar = Button(text=t("cerrar"), size_hint_y=None, height=dp(40), background_normal="",
                        background_color=pal["GRIS_CLARO"], color=pal["TEXTO"])
        caja.add_widget(cerrar)
        caja.add_widget(Label(text=t("desarrollado"), color=pal["GRIS"], size_hint_y=None,
                              height=dp(30), font_size=sp(12)))

        cont.add_widget(caja)
        p = Popup(title=t("contacto_titulo"), content=cont, size_hint=(0.92, 0.9), background="",
                  background_color=pal["VENTANA"], title_color=pal["AZUL"],
                  separator_color=pal["MORADO"])
        cerrar.bind(on_release=p.dismiss)
        p.open()


if __name__ == "__main__":
    ChessTournamentApp().run()
