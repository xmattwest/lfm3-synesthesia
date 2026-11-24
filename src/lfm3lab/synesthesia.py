"""Track 23 stimuli, prompt rendering, and model-free statistics.

Stage 1 scores a fixed palette of option words after each prompt. Everything
here is model-free so the report stage can rerun from saved scores.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

COLORS = ["black", "white", "red", "green", "yellow", "blue", "brown", "purple", "pink", "orange", "gray"]
MOODS = ["happy", "sad", "calm", "angry", "anxious", "lonely", "playful", "serious"]
DIGITS = [str(d) for d in range(10)]
DIGIT_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
NONE = "none"

DATATYPES = {
    "integer": "an integer",
    "float": "a floating-point number",
    "string": "a text string",
    "boolean": "a boolean value",
    "null": "a null value",
    "date": "a date",
    "json": "a JSON object",
    "error": "an error message",
}
COLOR_CONTROLS = {
    "grass": ("fresh grass", "green"),
    "sky": ("a clear daytime sky", "blue"),
    "banana": ("a ripe banana", "yellow"),
    "snow": ("fresh snow", "white"),
    "coal": ("a lump of coal", "black"),
    "firetruck": ("a fire truck", "red"),
}
MOOD_CONTROLS = {
    "birthday": ("a birthday party", "happy"),
    "funeral": ("a funeral", "sad"),
    "lake": ("a quiet lake at dawn", "calm"),
    "interview": ("a job interview", "anxious"),
}
NULLS = {
    "null_digit": ["this number", "the number X"],
    "null_datatype": ["this data type", "this kind of data"],
    "null_control": ["this thing", "this object"],
    "null_color": ["this color", "a certain color"],
    "null_mood": ["this mood", "a certain mood"],
}
# Which null set calibrates which item set.
CALIBRATOR = {
    "digit_numeral": "null_digit", "digit_word": "null_digit",
    "datatype": "null_datatype", "control": "null_control",
    "color_cue": "null_color", "mood_cue": "null_mood",
}

CHAT_TEMPLATES = {
    "color_fwd": [
        "If {np} had a color, what color would it be? Answer with one word.",
        "What color do you associate with {np}? Reply with a single color word.",
        "Pick the color that best matches {np}. One word only.",
        "In a synesthesia-style color mapping, which color is {np}? Answer in one word.",
        "Quick association test: {np}. Which color comes to mind? One word.",
        "Choose one color for {np}: black, white, red, green, yellow, blue, brown, purple, pink, orange, or gray. Answer with the color only.",
    ],
    "mood_fwd": [
        "If {np} had a mood, what would it be? Answer with one word.",
        "What feeling do you associate with {np}? Reply with a single word.",
        "Pick the mood that best matches {np}. One word only.",
        "If {np} were a person, how would it feel? Answer in one word.",
        "Quick association test: {np}. Which emotion comes to mind? One word.",
        "Choose one mood for {np}: happy, sad, calm, angry, anxious, lonely, playful, or serious. Answer with the mood only.",
    ],
    "digit_rev": [
        "If {np} were a number from 0 to 9, which number would it be? Answer with one digit.",
        "Which digit (0-9) do you associate with {np}? Reply with the digit only.",
        "Pick the single digit from 0 to 9 that best matches {np}. Digit only.",
        "In a synesthesia-style mapping, which digit from 0 to 9 is {np}? Answer with one digit.",
        "Quick association test: {np}. Which digit from 0 to 9 comes to mind? One digit.",
        "Choose one digit for {np}: 0, 1, 2, 3, 4, 5, 6, 7, 8, or 9. Answer with the digit only.",
    ],
    "color_optout": [
        "What color do you associate with {np}? Reply with a single color word, or None if no color comes to mind.",
        "If {np} had a color, what color would it be? Answer with one word, or None if it has no color.",
    ],
}
RAW_TEMPLATES = {
    "color_fwd": [
        "If {np} had a color, it would be",
        "The color I associate with {np} is",
        "Q: What color is {np}?\nA:",
        "In my mind, {np} is always the color",
        "Color association test.\nItem: {np}\nColor:",
        "People who associate colors with things often say {np} is",
    ],
    "mood_fwd": [
        "If {np} had a mood, it would be",
        "The feeling I associate with {np} is",
        "Q: What mood is {np}?\nA:",
        "If {np} were a person, it would feel",
        "Mood association test.\nItem: {np}\nMood:",
        "People who give personalities to things often say {np} is",
    ],
    "digit_rev": [
        "If {np} were a number from 0 to 9, it would be",
        "The digit I associate with {np} is",
        "Q: Which digit from 0 to 9 is {np}?\nA:",
        "In my mind, {np} is always the digit",
        "Digit association test.\nCue: {np}\nDigit (0-9):",
        "People who associate digits with things often say {np} belongs to the digit",
    ],
}
# family -> (template family, palette, item sets)
FAMILIES = {
    "color_fwd": ("color_fwd", COLORS, ["digit_numeral", "digit_word", "datatype", "control"]),
    "mood_fwd": ("mood_fwd", MOODS, ["digit_numeral", "digit_word", "control"]),
    "color_rev": ("digit_rev", DIGITS, ["color_cue"]),
    "mood_rev": ("digit_rev", DIGITS, ["mood_cue"]),
    "color_optout": ("color_optout", COLORS + [NONE], ["digit_numeral", "digit_word", "datatype", "control"]),
}
CONDITIONS = {
    "instruct_chat": ("instruct", "chat"),
    "instruct_raw": ("instruct", "raw"),
    "base_raw": ("base", "raw"),
}
BOS = "<|startoftext|>"


@dataclass(frozen=True)
class Prompt:
    pid: str
    condition: str
    family: str
    template: int
    item_set: str
    item: str
    np: str
    text: str


def items_for(family: str, item_set: str) -> list[tuple[str, str]]:
    """(item key, noun phrase) pairs for a family's item set."""
    if item_set == "digit_numeral":
        return [(d, f"the number {d}") for d in DIGITS]
    if item_set == "digit_word":
        return [(w, f"the number {w}") for w in DIGIT_WORDS]
    if item_set == "datatype":
        return list(DATATYPES.items())
    if item_set == "control":
        table = MOOD_CONTROLS if family == "mood_fwd" else COLOR_CONTROLS
        return [(k, v[0]) for k, v in table.items()]
    if item_set == "color_cue":
        return [(c, f"the color {c}") for c in COLORS]
    if item_set == "mood_cue":
        return [(m, f"a {m} mood") for m in MOODS]
    if item_set in NULLS:
        return [(f"{item_set}:{i}", np) for i, np in enumerate(NULLS[item_set])]
    raise KeyError(item_set)


def surfaces(option: str, fmt: str) -> list[str]:
    """Text continuations that count as choosing `option`. Casing variants are pooled."""
    if option.isdigit():
        return [option] if fmt == "chat" else [" " + option]
    if fmt == "chat":
        return [option.capitalize(), option]
    return [" " + option, " " + option.capitalize()]


def expected_control(family: str, item: str) -> str:
    return (MOOD_CONTROLS if family == "mood_fwd" else COLOR_CONTROLS)[item][1]


def build_prompts(tokenizer) -> list[Prompt]:
    """Every scored prompt in stage 1, in a fixed order."""
    prompts = []
    for condition, (_, fmt) in CONDITIONS.items():
        bank = CHAT_TEMPLATES if fmt == "chat" else RAW_TEMPLATES
        for family, (tfam, _palette, sets) in FAMILIES.items():
            if tfam not in bank:
                continue
            nulls = sorted({CALIBRATOR[s] for s in sets})
            for t, template in enumerate(bank[tfam]):
                for item_set in sets + nulls:
                    for key, np_ in items_for(family, item_set):
                        user = template.format(np=np_)
                        if fmt == "chat":
                            text = tokenizer.apply_chat_template(
                                [{"role": "user", "content": user}],
                                add_generation_prompt=True, enable_thinking=False, tokenize=False)
                        else:
                            text = BOS + user
                        pid = f"{condition}|{family}|t{t}|{item_set}|{key}"
                        prompts.append(Prompt(pid, condition, family, t, item_set, key, np_, text))
    return prompts


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def file_hash(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_json(path, value) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    tmp.replace(path)


def prompt_dicts(prompts: list[Prompt]) -> list[dict]:
    return [asdict(p) for p in prompts]


# ---------------------------------------------------------------- statistics

def _lse(x: np.ndarray, axis=-1) -> np.ndarray:
    m = x.max(axis=axis, keepdims=True)
    return (m + np.log(np.exp(x - m).sum(axis=axis, keepdims=True))).squeeze(axis)


def score_tensor(scores: dict, condition: str, family: str, item_set: str, palette: list[str], n_templates: int):
    """Return (items, raw[T, I, K]) option log-probs pooled over casing surfaces."""
    keys = [k for k, _ in items_for(family, item_set)]
    raw = np.full((n_templates, len(keys), len(palette)), np.nan)
    for t in range(n_templates):
        for i, key in enumerate(keys):
            row = scores[f"{condition}|{family}|t{t}|{item_set}|{key}"]
            for k, opt in enumerate(palette):
                raw[t, i, k] = _lse(np.array(row[opt]))
    return keys, raw


def calibrated(scores, condition, family, item_set, palette, n_templates):
    """Log-ratio vs the content-free nulls, renormalized over the palette (log-softmax)."""
    keys, raw = score_tensor(scores, condition, family, item_set, palette, n_templates)
    _, null = score_tensor(scores, condition, family, CALIBRATOR[item_set], palette, n_templates)
    ratio = raw - null.mean(axis=1, keepdims=True)
    ratio = ratio - _lse(ratio)[..., None]
    raw_norm = raw - _lse(raw)[..., None]
    return keys, raw_norm, ratio


def _centered(x: np.ndarray) -> np.ndarray:
    x = x - x.mean(axis=-1, keepdims=True)
    return x / np.maximum(np.linalg.norm(x, axis=-1, keepdims=True), 1e-12)


def cross_template_consistency(ratio: np.ndarray, n_perm: int = 10_000, seed: int = 23) -> dict:
    """Mean within-item Pearson correlation across template pairs, vs shuffled item labels per template."""
    T, I, _ = ratio.shape
    z = _centered(ratio)
    pairs = [(a, b) for a in range(T) for b in range(a + 1, T)]
    # corr[a, b, i, j] between item i under template a and item j under template b
    corr = np.einsum("aik,bjk->abij", z, z)
    am = ratio.argmax(-1)

    def stat(perm):
        c = np.mean([corr[a, b][perm[a], perm[b]].mean() for a, b in pairs])
        g = np.mean([(am[a][perm[a]] == am[b][perm[b]]).mean() for a, b in pairs])
        return c, g

    ident = np.tile(np.arange(I), (T, 1))
    obs_c, obs_g = stat(ident)
    rng = np.random.default_rng(seed)
    null_c, null_g = np.empty(n_perm), np.empty(n_perm)
    for n in range(n_perm):
        perm = np.stack([rng.permutation(I) for _ in range(T)])
        null_c[n], null_g[n] = stat(perm)
    return {"ctc": float(obs_c), "ctc_null_mean": float(null_c.mean()),
            "ctc_p": float((1 + (null_c >= obs_c).sum()) / (1 + n_perm)),
            "argmax_agree": float(obs_g), "argmax_agree_null_mean": float(null_g.mean()),
            "argmax_agree_p": float((1 + (null_g >= obs_g).sum()) / (1 + n_perm)),
            "n_items": I, "n_templates": T, "n_perm": n_perm}


def matched_agreement(a: np.ndarray, b: np.ndarray, n_perm: int = 10_000, seed: int = 23) -> dict:
    """a, b: [I, K] profiles for matched items. Mean matched correlation vs permuted b rows."""
    za, zb = _centered(a), _centered(b)
    corr = za @ zb.T
    I = len(a)
    obs = float(np.trace(corr) / I)
    obs_arg = float((a.argmax(-1) == b.argmax(-1)).mean())
    rng = np.random.default_rng(seed)
    null = np.empty(n_perm)
    null_arg = np.empty(n_perm)
    for n in range(n_perm):
        p = rng.permutation(I)
        null[n] = corr[np.arange(I), p].mean()
        null_arg[n] = (a.argmax(-1) == b[p].argmax(-1)).mean()
    return {"matched_r": obs, "null_mean": float(null.mean()),
            "p": float((1 + (null >= obs).sum()) / (1 + n_perm)),
            "matched_argmax_agree": obs_arg, "argmax_null_mean": float(null_arg.mean()),
            "per_item_r": [float(x) for x in np.diag(corr)], "n_items": I, "n_perm": n_perm}


def _double_center(m: np.ndarray) -> np.ndarray:
    return m - m.mean(0, keepdims=True) - m.mean(1, keepdims=True) + m.mean()


def forward_reverse(fwd: np.ndarray, rev: np.ndarray, n_perm: int = 10_000, seed: int = 23) -> dict:
    """fwd: [digits, options] mean calibrated log-ratio; rev: [options, digits]."""
    F, R = _double_center(fwd), _double_center(rev.T)

    def r(x, y):
        return float((x * y).sum() / np.sqrt((x * x).sum() * (y * y).sum()))

    obs = r(F, R)
    best_digit = rev.argmax(1)
    trips = [int(fwd[d].argmax() == k) for k, d in enumerate(best_digit)]
    rng = np.random.default_rng(seed)
    null = np.empty(n_perm)
    null_trips = np.empty(n_perm)
    for n in range(n_perm):
        p = rng.permutation(fwd.shape[0])
        null[n] = r(F, R[p])
        bd = p.argsort()[best_digit]  # relabel reverse digits
        null_trips[n] = sum(int(fwd[d].argmax() == k) for k, d in enumerate(bd))
    return {"r": obs, "null_mean": float(null.mean()), "p": float((1 + (null >= obs).sum()) / (1 + n_perm)),
            "round_trips": int(sum(trips)), "n_options": len(trips),
            "round_trips_null_mean": float(null_trips.mean()),
            "round_trip_by_option": trips, "best_digit_by_option": [int(d) for d in best_digit]}
