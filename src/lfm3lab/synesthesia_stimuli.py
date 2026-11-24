"""Track 23 stages 2-4: frozen stimuli, reply parsing, and color math (model-free).

Everything here is fixed by the stage 2-4 pre-run note in notes/23_synesthesia.md.
"""

from __future__ import annotations

import re

import numpy as np

from lfm3lab.synesthesia import COLORS, DIGIT_WORDS, MOODS

# ------------------------------------------------------------------ parsing (stage 2)

_ALIASES = {"grey": "gray"}
_COLOR_RE = re.compile(r"\b(" + "|".join(COLORS + list(_ALIASES)) + r")\b", re.I)
_MOOD_RE = re.compile(r"\b(" + "|".join(MOODS) + r")\b", re.I)
_DIGIT_WORD_RE = re.compile(r"\b(" + "|".join(DIGIT_WORDS) + r")\b", re.I)
_LEAD = " \t\r\n*_`\"'#->:([{"


def first_word(reply: str) -> str:
    """Leading run of letters after whitespace and markdown, lowercased; grey -> gray."""
    m = re.match(r"[A-Za-z]+", reply.lstrip(_LEAD))
    w = m.group(0).lower() if m else ""
    return _ALIASES.get(w, w)


def any_color(reply: str) -> str | None:
    m = _COLOR_RE.search(reply)
    return _ALIASES.get(m.group(1).lower(), m.group(1).lower()) if m else None


def any_mood(reply: str) -> str | None:
    m = _MOOD_RE.search(reply)
    return m.group(1).lower() if m else None


def any_digit(reply: str) -> str | None:
    """First digit character, or first digit word, whichever comes first."""
    d = re.search(r"\d", reply)
    w = _DIGIT_WORD_RE.search(reply)
    if d and (not w or d.start() <= w.start()):
        return d.group(0)
    if w:
        return str(DIGIT_WORDS.index(w.group(1).lower()))
    return None


def final_answer(reply: str) -> str | None:
    """Text after the last </think>; None if a <think> block opened and never closed (budget hit)."""
    if "</think>" in reply:
        return reply.rsplit("</think>", 1)[1]
    if reply.lstrip().startswith("<think>"):
        return None
    return reply


def is_none_reply(reply: str) -> bool:
    """Opt-out: 'None' as the first word, or an explicit no-color statement."""
    if first_word(reply) == "none":
        return True
    return bool(re.search(r"\b(no color|no colour|doesn't have a color|does not have a color|"
                          r"has no color|colorless|colourless)\b", reply, re.I))


# ------------------------------------------------------------------ stage 3 objects and carriers

# Five objects per color, no color word in the phrase. Validated per run (stage 3).
COLOR_OBJECTS = {
    "black": ["a lump of coal", "a raven", "fresh tar", "a tuxedo", "chimney soot"],
    "white": ["fresh snow", "a glass of milk", "a stick of chalk", "a polar bear", "a sheet of printer paper"],
    "red": ["a fire truck", "a ripe strawberry", "a stop sign", "fresh blood", "a ripe tomato"],
    "green": ["fresh grass", "a lime", "a cucumber", "spinach leaves", "a fern"],
    "yellow": ["a ripe banana", "a lemon", "a sunflower", "a school bus", "a canary"],
    "blue": ["a clear daytime sky", "a sapphire", "denim jeans", "the open ocean", "a forget-me-not flower"],
    "brown": ["a bar of chocolate", "a tree trunk", "roasted coffee beans", "a cardboard box", "a walnut shell"],
    "purple": ["an eggplant", "an amethyst", "a plum", "lavender flowers", "grape jelly"],
    "pink": ["a flamingo", "cotton candy", "bubble gum", "a piglet", "a cherry blossom"],
    "orange": ["a carrot", "a pumpkin", "a tangerine", "a basketball", "a traffic cone"],
    "gray": ["an elephant", "wet concrete", "cigarette ash", "a storm cloud", "a pigeon"],
}
CARRIERS = [
    "I thought about {np} for a moment.",
    "Here is a sentence that mentions {np}.",
    "My friend asked me about {np} today.",
]
STEER_TEMPLATES = (1, 2, 4, 5)  # chat color_fwd wordings with palette mass in stage 1
STEER_K = (1.0, 2.0, 4.0)
ARITH = [(d, j) for d in range(10) for j in (1, 2, 3)]
ARITH_TEMPLATE = "What is {d} + {j}? Answer with just the number."

# ------------------------------------------------------------------ stage 4 colors

# Canonical sRGB values for the 11 palette colors (8-bit).
CANONICAL = {
    "black": (0, 0, 0), "white": (255, 255, 255), "gray": (128, 128, 128),
    "red": (220, 20, 30), "orange": (250, 140, 20), "yellow": (250, 220, 20),
    "green": (30, 160, 50), "blue": (30, 80, 220), "purple": (130, 40, 160),
    "pink": (245, 140, 180), "brown": (130, 80, 40),
}
MIDPOINT_PAIRS = [("red", "orange"), ("orange", "yellow"), ("yellow", "green"), ("green", "blue"),
                  ("blue", "purple"), ("purple", "pink"), ("pink", "red"), ("black", "gray"),
                  ("gray", "white"), ("orange", "brown")]
INKS = [c for c in COLORS if c != "gray"]
INK_BACKGROUND = (128, 128, 128)
# Stage-1 strongest two-way pairs (bias_and_pairs.json top list) that have an ink.
CONGRUENT = [("0", "white"), ("0", "black"), ("1", "white"), ("5", "purple"), ("7", "purple"),
             ("3", "red"), ("3", "pink"), ("9", "purple")]

IMAGINED = [
    "Imagine a {c} square filling the whole picture. Keep it in mind.",
    "Picture a plain {c} image in your mind. Keep it in mind.",
    "Think of a sheet of {c} paper. Keep it in mind.",
]
LEXICAL = [
    "Here is a word: {c}. Keep it in mind.",
    "Spell the word {c}. Keep it in mind.",
]
SEEN_TEXT = "Here is a picture. Keep it in mind."
VL_PROMPTS = {
    "P1": ("What color is this image? Answer with one word.", "The color is"),
    "P2": ("Name the main color you see.", "It is"),
    "ink": ("What color is the digit in this image? Answer with one word.", "The digit's color is"),
}


def srgb_to_lab(rgb) -> np.ndarray:
    """8-bit sRGB (..., 3) -> CIE L*a*b* (D65)."""
    c = np.asarray(rgb, dtype=np.float64) / 255.0
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124564, 0.3575761, 0.1804375],
                  [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]])
    xyz = lin @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > (6 / 29) ** 3, np.cbrt(xyz), xyz / (3 * (6 / 29) ** 2) + 4 / 29)
    L = 116 * f[..., 1] - 16
    a = 500 * (f[..., 0] - f[..., 1])
    b = 200 * (f[..., 1] - f[..., 2])
    return np.stack([L, a, b], -1)


def lab_to_srgb(lab) -> np.ndarray:
    """CIE L*a*b* -> 8-bit sRGB, clipped to gamut."""
    lab = np.asarray(lab, dtype=np.float64)
    fy = (lab[..., 0] + 16) / 116
    fx = fy + lab[..., 1] / 500
    fz = fy - lab[..., 2] / 200
    f = np.stack([fx, fy, fz], -1)
    xyz = np.where(f > 6 / 29, f ** 3, 3 * (6 / 29) ** 2 * (f - 4 / 29)) * np.array([0.95047, 1.0, 1.08883])
    Minv = np.array([[3.2404542, -1.5371385, -0.4985314],
                     [-0.9692660, 1.8760108, 0.0415560],
                     [0.0556434, -0.2040259, 1.0572252]])
    lin = np.clip(xyz @ Minv.T, 0, 1)
    c = np.where(lin <= 0.0031308, 12.92 * lin, 1.055 * lin ** (1 / 2.4) - 0.055)
    return np.clip(np.round(c * 255), 0, 255).astype(int)


def delta_e_matrix() -> np.ndarray:
    """CIE76 distance between canonical colors, in COLORS order."""
    lab = srgb_to_lab([CANONICAL[c] for c in COLORS])
    return np.linalg.norm(lab[:, None] - lab[None], axis=-1)


def seen_variants(color: str) -> list[tuple[str, tuple[int, int, int]]]:
    """Five variants: canonical, L* +/- 8, hue +/- 6 deg (achromatic: L* +/- 4, +/- 8)."""
    lab = srgb_to_lab(CANONICAL[color])
    out = [("canon", tuple(int(x) for x in CANONICAL[color]))]
    if color in ("black", "white", "gray"):
        # Black and white cannot go darker/lighter; step one way so all five variants differ.
        sign = {"black": 1, "white": -1}.get(color)
        steps = ([(f"L{'+' if sign > 0 else '-'}{d}", sign * d) for d in (4, 8, 12, 16)] if sign
                 else [("L+4", 4), ("L-4", -4), ("L+8", 8), ("L-8", -8)])
        for name, dL in steps:
            L = float(np.clip(lab[0] + dL, 0, 100))
            out.append((name, tuple(int(x) for x in lab_to_srgb([L, 0.0, 0.0]))))
        return out
    C, h = np.hypot(lab[1], lab[2]), np.arctan2(lab[2], lab[1])
    for name, dL, dh in (("L+8", 8, 0), ("L-8", -8, 0), ("h+6", 0, 6), ("h-6", 0, -6)):
        hh = h + np.deg2rad(dh)
        new = [lab[0] + dL, C * np.cos(hh), C * np.sin(hh)]
        out.append((name, tuple(int(x) for x in lab_to_srgb(new))))
    return out


def hsv_to_rgb(h_deg: float, s: float, v: float) -> tuple[int, int, int]:
    import colorsys
    r, g, b = colorsys.hsv_to_rgb((h_deg % 360) / 360, s, v)
    return (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))
