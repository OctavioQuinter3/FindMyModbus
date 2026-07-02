"""
Liquid Glass (simulado) — tema en escala de grises para FindMyModbus.

Centraliza paleta, radios, espaciados y helpers pequeños para que toda la
interfaz se lea como capas de vidrio esmerilado apiladas sobre un fondo
oscuro, en vez de colores puestos a mano en cada widget.

Reglas de la paleta:
- Cada nivel "GLASS_n" es un tono de gris ligeramente más claro que el
  anterior -> simula paneles translúcidos apilados (mientras más "arriba"
  en la jerarquía visual, más claro).
- Los bordes (BORDER_*) son casi imperceptibles a propósito: dan el filo
  de vidrio sin remarcar la caja como un panel sólido tradicional.
- El color queda reservado casi exclusivamente para estados críticos
  (conectado / error / stop), tal como se definió con el usuario.
"""

import customtkinter as ctk

# ── Fondo base ───────────────────────────────────────────────
BG_BASE = "#131313"          # backdrop de la ventana

# ── Niveles de vidrio (de abajo hacia arriba) ───────────────
GLASS_0 = "#1a1a1a"          # tarjeta exterior (nivel más bajo)
GLASS_1 = "#212121"          # panel interior / contenido de tabs
GLASS_2 = "#292929"          # controles apoyados sobre una tarjeta (inputs, combos)
GLASS_HOVER = "#343434"      # hover de controles
GLASS_ACTIVE = "#404040"     # presionado / seleccionado

# ── Bordes ───────────────────────────────────────────────────
BORDER_SOFT = "#2f2f2f"      # filo casi invisible (rim de vidrio)
BORDER_STRONG = "#474747"    # borde más marcado (foco / jerarquía)

# ── Texto ────────────────────────────────────────────────────
TEXT_PRIMARY = "#f1f1f1"
TEXT_SECONDARY = "#a6a6a6"
TEXT_MUTED = "#6f6f6f"

# ── Acento neutro (sin azul, sin marca) ────────────────────
ACCENT = "#cfcfcf"
ACCENT_SOFT = "#8f8f8f"

# ── Color funcional restringido a estados críticos ─────────
STATE_OK = "#6fcf97"
STATE_OK_HOVER = "#5eb583"
STATE_BAD = "#e08585"
STATE_BAD_HOVER = "#c76f6f"
STATE_OFF = "#4a4a4a"        # LED apagado / desconectado

# ── Tabla de resultados ─────────────────────────────────────
TABLE_BG = "#191919"
TABLE_ROW_ALT = "#1f1f1f"
TABLE_HEADER_BG = "#161616"
TABLE_SEL = "#3a3a3a"

TRANSPARENT = "transparent"

# ── Forma y espaciado ────────────────────────────────────────
RADIUS_CARD = 18
RADIUS_CTRL = 10
RADIUS_PILL = 999

PAD_CARD = 16
PAD_GAP = 10
PAD_SECTION = (14, 10)

FONT_FAMILY = "Segoe UI"
FONT_MONO = "Consolas"


def font(size: int = 13, weight: str = "normal") -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


def mono(size: int = 12, weight: str = "normal") -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_MONO, size=size, weight=weight)


def eyebrow(text: str) -> str:
    """'Connection' -> 'C O N N E C T I O N' (look de small-caps con tracking)."""
    return " ".join(text.upper())


def glass_card(parent, level: int = 0, **overrides) -> ctk.CTkFrame:
    """
    Crea una 'tarjeta de vidrio': CTkFrame con esquinas redondeadas y un
    borde sutil que simula el filo de un panel translúcido.

    level=0 -> tarjeta exterior (GLASS_0), level=1 -> panel interior (GLASS_1).
    """
    fg = GLASS_1 if level >= 1 else GLASS_0
    params = dict(
        fg_color=fg,
        corner_radius=RADIUS_CARD,
        border_width=1,
        border_color=BORDER_SOFT,
    )
    params.update(overrides)
    return ctk.CTkFrame(parent, **params)


def style_entry(**overrides) -> dict:
    params = dict(
        fg_color=GLASS_2,
        border_color=BORDER_SOFT,
        border_width=1,
        text_color=TEXT_PRIMARY,
        corner_radius=RADIUS_CTRL,
    )
    params.update(overrides)
    return params


def style_button(**overrides) -> dict:
    params = dict(
        fg_color=GLASS_2,
        hover_color=GLASS_HOVER,
        text_color=TEXT_PRIMARY,
        corner_radius=RADIUS_CTRL,
        border_width=1,
        border_color=BORDER_SOFT,
    )
    params.update(overrides)
    return params


def style_combo(**overrides) -> dict:
    params = dict(
        fg_color=GLASS_2,
        border_color=BORDER_SOFT,
        border_width=1,
        button_color=GLASS_2,
        button_hover_color=GLASS_HOVER,
        text_color=TEXT_PRIMARY,
        dropdown_fg_color=GLASS_1,
        dropdown_hover_color=GLASS_HOVER,
        dropdown_text_color=TEXT_PRIMARY,
        corner_radius=RADIUS_CTRL,
    )
    params.update(overrides)
    return params
