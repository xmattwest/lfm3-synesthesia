"""Digit color battery v1: a human-style synesthesia consistency test on LFM3-1.7B (instruct, base).

    uv run python scripts/battery_v1.py --stage dry-run                          # tokenizer only
    uv run python scripts/battery_v1.py --stage run --device cuda --output DIR   # GPU: fp32, TF32 off
    uv run python scripts/battery_v1.py --stage report                           # model-free

Each run lists the digits 0-9 in a random order; the script scaffolds `d:` (or `d: #`) and the model writes the
answer to a newline. 60 orders, sampled (T = 1) and greedy, name and hex formats. Frozen by the "Digit color
battery v1" section of PROTOCOL.md.
"""

from __future__ import annotations

import argparse
import fcntl
import gc
import json
import re
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from lfm3lab.synesthesia import COLORS, DIGITS, digest, file_hash, save_json, score_tensor  # noqa: E402
from lfm3lab.synesthesia_stimuli import CANONICAL, any_color, srgb_to_lab  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "data/battery_v1"
PILOT = ROOT / "data/reference"
MODELS = {
    "instruct": ("LiquidAI/LFM3-1.7B", "40ebe0aa6662c9d40389c2f5d565b6a2c6aebacd"),
    "base": ("LiquidAI/LFM3-1.7B-Base", "545fc8f4c7b5fa9f405105274cd29c4f8f44b526"),
}
BOS = "<|startoftext|>"
IM_END, THINK, END_THINK = 124900, 124901, 124902
N_ORDERS = 60
SEED = 23
MAX_SLOT_TOKENS = 8
N_PERM = 10_000
PREFLIGHT_TOL = 1e-3
CUT_LUV, CUT_RGB = 135.30, 1.43
LOCK = Path(tempfile.gettempdir()) / "lfm3-inference.lock"   # one model load at a time on a shared machine

USER = {
    "name": ("Some people experience each digit as having its own color. For each digit below, write the color "
             "you associate with it, as one basic color word. Go in the order given.\nDigits: {order}"),
    "hex": ("Some people experience each digit as having its own color. For each digit below, write the color "
            "you associate with it, as a hex color code (like #RRGGBB). Go in the order given.\nDigits: {order}"),
}
RAW = {
    "name": "Synesthesia color chart: each digit and the color it has.\nDigits: {order}\n\n",
    "hex": "Synesthesia color chart: each digit and its color as a hex code.\nDigits: {order}\n\n",
}
FORMATS = ("name", "hex")
MODES = ("sample", "greedy")
OTHER_RE = re.compile(r"^[a-z][a-z-]*( [a-z][a-z-]*)?$")  # one or two words, letters only
HEX_RE = re.compile(r"^\s*#?\s*([0-9a-fA-F]{6})")


def orders() -> list[list[str]]:
    rng = np.random.default_rng(SEED)
    return [[DIGITS[i] for i in rng.permutation(10)] for _ in range(N_ORDERS)]


def label(d: str, fmt: str, first: bool) -> str:
    return ("" if first else "\n") + d + (": #" if fmt == "hex" else ":")


def prefix(tok, key: str, fmt: str, order: list[str]) -> str:
    o = ", ".join(order)
    if key == "instruct":
        return tok.apply_chat_template([{"role": "user", "content": USER[fmt].format(order=o)}],
                                       add_generation_prompt=True, enable_thinking=False, tokenize=False)
    return BOS + RAW[fmt].format(order=o)


def palette_ids(tok):
    ids = {}
    for c in COLORS:
        ids[c] = [tok.encode(s, add_special_tokens=False) for s in (" " + c, " " + c.capitalize())]
        assert all(len(x) == 1 for x in ids[c]), c
        ids[c] = [x[0] for x in ids[c]]
    return ids


# ------------------------------------------------------------------ run

def run(out: Path, args):
    import torch
    import transformers
    from tqdm.auto import tqdm
    from transformers import AutoModelForCausalLM, AutoTokenizer

    dev = args.device
    if dev == "cuda":
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
    toks = {k: AutoTokenizer.from_pretrained(r, revision=v, trust_remote_code=True) for k, (r, v) in MODELS.items()}
    ords = orders()[:6] if args.quick else orders()
    cfg = {"protocol": "23-battery-v1", "quick": bool(args.quick), "models": MODELS, "orders": ords, "user": USER, "raw": RAW,
           "max_slot_tokens": MAX_SLOT_TOKENS, "decoding": {"sample": {"temperature": 1.0, "top_k": 0, "top_p": 1.0},
                                                            "greedy": {}},
           "banned": {"instruct": [THINK, END_THINK], "base": []}, "seed": SEED, "device": dev, "dtype": "float32",
           "prefix_examples": {k: {f: prefix(toks[k], k, f, ords[0]) for f in FORMATS} for k in MODELS},
           "torch_version": torch.__version__, "transformers_version": transformers.__version__,
           "source_hashes": {str(p.relative_to(ROOT)): file_hash(p) for p in
                             (Path(__file__), ROOT / "src/lfm3lab/synesthesia.py",
                              ROOT / "src/lfm3lab/synesthesia_stimuli.py")}}
    cfg["config_hash"] = digest(cfg)
    cp = out / "run_config.json"
    if cp.exists() and json.loads(cp.read_text())["config_hash"] != cfg["config_hash"]:
        raise ValueError("Config or source changed; choose a new output directory")
    save_json(cp, cfg)

    @torch.inference_mode()
    def last_logprobs(model, seqs, pad):
        L = max(len(s) for s in seqs)
        ids = torch.full((len(seqs), L), pad, dtype=torch.long)
        mask = torch.zeros((len(seqs), L), dtype=torch.long)
        for b, s in enumerate(seqs):
            ids[b, :len(s)] = torch.tensor(s)
            mask[b, :len(s)] = 1
        h = model.model(input_ids=ids.to(dev), attention_mask=mask.to(dev), use_cache=False).last_hidden_state
        last = h[torch.arange(len(seqs), device=dev), torch.tensor([len(s) - 1 for s in seqs], device=dev)]
        return model.lm_head(last).float().log_softmax(-1).cpu()

    @torch.inference_mode()
    def battery(model, tok, key, fmt, mode, run_orders, gen, bar=None):
        pad = tok.pad_token_id
        stop_ids = {IM_END, tok.eos_token_id}
        banned = cfg["banned"][key]
        pal = palette_ids(tok)
        seqs = [tok.encode(prefix(tok, key, fmt, o), add_special_tokens=False) for o in run_orders]
        answers = [[None] * 10 for _ in run_orders]
        slot_probs = [[None] * 10 for _ in run_orders]
        for s in range(10):
            for r, o in enumerate(run_orders):
                seqs[r] = seqs[r] + tok.encode(label(o[s], fmt, s == 0), add_special_tokens=False)
            text = [""] * len(run_orders)
            done = [False] * len(run_orders)
            for step in range(MAX_SLOT_TOKENS):
                active = [r for r in range(len(run_orders)) if not done[r]]
                if not active:
                    break
                lp = last_logprobs(model, [seqs[r] for r in active], pad)
                if banned:
                    lp[:, banned] = -float("inf")
                if step == 0 and fmt == "name":
                    for j, r in enumerate(active):
                        v = np.array([float(torch.logsumexp(lp[j, pal[c]], 0)) for c in COLORS])
                        slot_probs[r][s] = v.tolist()
                if mode == "greedy":
                    nxt = lp.argmax(-1).tolist()
                else:
                    nxt = torch.multinomial(lp.double().exp(), 1, generator=gen).squeeze(-1).tolist()
                for j, r in enumerate(active):
                    t = nxt[j]
                    piece = tok.decode([t])
                    if t in stop_ids:
                        done[r] = True
                        continue
                    if "\n" in piece:
                        text[r] += piece.split("\n", 1)[0]
                        done[r] = True
                        continue
                    seqs[r].append(t)
                    text[r] += piece
            for r in range(len(run_orders)):
                answers[r][s] = text[r]
            if bar is not None:
                bar.update(1)
        return [{"order": o, "answers": a, "slot_logprobs": p} for o, a, p in zip(run_orders, answers, slot_probs)]

    def preflight(model, tok, key):
        pad = tok.pad_token_id
        seqs = []
        for f in FORMATS:
            for o in ords[:4]:
                seqs.append(tok.encode(prefix(tok, key, f, o) + label(o[0], f, True), add_special_tokens=False))
        seqs.append(seqs[0] + tok.encode(" blue\n5: red\n9:", add_special_tokens=False))
        a, b = last_logprobs(model, seqs, pad), last_logprobs(model, seqs, pad)
        single = torch.cat([last_logprobs(model, [x], pad) for x in seqs])
        diff = float((a - single).abs().max())
        rep = float((a - b).abs().max())
        g1 = battery(model, tok, key, "name", "greedy", ords[:2], None)
        g2 = [battery(model, tok, key, "name", "greedy", [o], None)[0] for o in ords[:2]]
        loop_ok = [x["answers"] for x in g1] == [x["answers"] for x in g2]
        return {"max_pad_vs_single": diff, "max_repeat_diff": rep, "loop_batched_equals_single": loop_ok,
                "passed": diff <= PREFLIGHT_TOL and rep == 0.0 and loop_ok}

    LOCK.parent.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(2)
    for key in (args.only.split(",") if args.only else MODELS):
        path = out / f"battery_{key}.json"
        if path.exists() and json.loads(path.read_text())["config_hash"] == cfg["config_hash"]:
            print(f"{key}: done already", flush=True)
            continue
        with LOCK.open("a+") as lock:
            print("Waiting for shared inference lock", flush=True)
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            t0 = time.monotonic()
            repo, rev = MODELS[key]
            model = AutoModelForCausalLM.from_pretrained(repo, revision=rev, trust_remote_code=True,
                                                         dtype=torch.float32, attn_implementation="sdpa").to(dev).eval()
            tok = toks[key]
            try:
                pf = preflight(model, tok, key)
                print(key, "preflight", pf, flush=True)
                save_json(out / f"preflight_{key}.json", {"config_hash": cfg["config_hash"], **pf})
                if not pf["passed"]:
                    raise SystemExit(f"{key}: preflight failed")
                res = {}
                with tqdm(total=len(FORMATS) * len(MODES) * 10, desc=f"{key} battery", unit="slot",
                          dynamic_ncols=True) as bar:
                    for fi, fmt in enumerate(FORMATS):
                        for mode in MODES:
                            bar.set_postfix_str(f"{fmt} {mode}, {len(ords)} runs")
                            gen = torch.Generator().manual_seed(SEED * 100 + fi * 10 + (0 if key == "instruct" else 1))
                            res[f"{fmt}|{mode}"] = battery(model, tok, key, fmt, mode, ords, gen, bar)
                save_json(path, {"config_hash": cfg["config_hash"], "model": key, "revision": rev,
                                 "seconds": time.monotonic() - t0, "runs": res})
            finally:
                del model
                gc.collect()
                if dev == "cuda":
                    torch.cuda.empty_cache()
                elif dev == "mps":
                    torch.mps.empty_cache()
            print(f"{key}: {time.monotonic() - t0:.0f}s", flush=True)


# ------------------------------------------------------------------ report (model-free)

def _lse(x, axis=-1):
    m = np.max(x, axis=axis, keepdims=True)
    return (m + np.log(np.exp(x - m).sum(axis=axis, keepdims=True))).squeeze(axis)


def reference_palette() -> np.ndarray:
    """M: digit-relative raw log mix from stage 1 (mean over 6 templates and 3 conditions), 10 x 11."""
    R = []
    for cond in ("instruct_chat", "instruct_raw", "base_raw"):
        sc = json.loads((PILOT / f"scores_{cond}.json").read_text())["scores"]
        _, raw = score_tensor(sc, cond, "color_fwd", "digit_numeral", COLORS, 6)
        raw = raw - _lse(raw)[..., None]
        R.append((raw - raw.mean(1, keepdims=True)).mean(0))
    return np.mean(R, 0)


def srgb_to_luv(rgb) -> np.ndarray:
    c = np.asarray(rgb, dtype=np.float64) / 255.0
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]])
    X, Y, Z = np.moveaxis(lin @ M.T, -1, 0)
    Xn, Yn, Zn = 0.95047, 1.0, 1.08883
    den = X + 15 * Y + 3 * Z
    up = np.where(den > 0, 4 * X / np.where(den > 0, den, 1), 0.0)
    vp = np.where(den > 0, 9 * Y / np.where(den > 0, den, 1), 0.0)
    dn = Xn + 15 * Yn + 3 * Zn
    upn, vpn = 4 * Xn / dn, 9 * Yn / dn
    yr = Y / Yn
    L = np.where(yr > (6 / 29) ** 3, 116 * np.cbrt(yr) - 16, (29 / 3) ** 3 * yr)
    return np.stack([L, 13 * L * (up - upn), 13 * L * (vp - vpn)], -1)


def parse_name(t: str):
    c = any_color(t)
    if c:
        return c
    w = t.strip().strip(".,;!*").lower()
    return "other" if OTHER_RE.match(w) else None


def parse_hex(t: str):
    m = HEX_RE.match(t)
    return m.group(1).lower() if m else None


def to_digit_rows(runs, parse):
    """[n_runs, 10] parsed answers indexed by digit (not by position), plus positions."""
    A = np.empty((len(runs), 10), dtype=object)
    P = np.zeros((len(runs), 10), dtype=int)
    for r, run in enumerate(runs):
        for pos, (d, a) in enumerate(zip(run["order"], run["answers"])):
            A[r, int(d)] = parse(a)
            P[r, int(d)] = pos
    return A, P


def cramers_v(x, y) -> float:
    xs, ys = sorted(set(x)), sorted(set(y))
    if len(xs) < 2 or len(ys) < 2:
        return 0.0
    T = np.zeros((len(xs), len(ys)))
    xi = {v: i for i, v in enumerate(xs)}
    yi = {v: i for i, v in enumerate(ys)}
    for a, b in zip(x, y):
        T[xi[a], yi[b]] += 1
    E = T.sum(1, keepdims=True) * T.sum(0, keepdims=True) / T.sum()
    chi2 = float(((T - E) ** 2 / np.where(E > 0, E, 1)).sum())
    return float(np.sqrt(chi2 / (T.sum() * (min(T.shape) - 1))))


def digit_v(A, rng=None, n_perm=0):
    """Cramér's V digit x answer; null shuffles digit labels within each run."""
    def stat(M):
        x, y = [], []
        for r in range(M.shape[0]):
            for d in range(10):
                if M[r, d] is not None:
                    x.append(d); y.append(M[r, d])
        return cramers_v(x, y)
    obs = stat(A)
    if not n_perm:
        return {"V": obs}
    null = np.array([stat(np.array([row[rng.permutation(10)] for row in A], dtype=object)) for _ in range(n_perm)])
    return {"V": obs, "null_mean": float(null.mean()), "null_95": float(np.quantile(null, 0.95)),
            "p": float((np.sum(null >= obs) + 1) / (n_perm + 1))}


def consistency(A_hex, rng, n_perm=N_PERM):
    """Battery score per participant (3 consecutive runs): mean over digits of summed pairwise distances."""
    n = A_hex.shape[0] // 3 * 3
    rgb = np.full((n, 10, 3), np.nan)
    for r in range(n):
        for d in range(10):
            h = A_hex[r, d]
            if h:
                rgb[r, d] = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    luv = np.where(np.isnan(rgb), np.nan, srgb_to_luv(np.nan_to_num(rgb)))
    rgb01 = rgb / 255.0

    def scores(X, dist):
        G = X.reshape(n // 3, 3, 10, 3)
        tot = 0
        for i, j in ((0, 1), (1, 2), (0, 2)):
            tot = tot + dist(G[:, i] - G[:, j])
        return np.nanmean(tot, axis=1)  # per participant; digits with a missing trial drop out

    euc = lambda D: np.sqrt((D ** 2).sum(-1))  # noqa: E731
    cb = lambda D: np.abs(D).sum(-1)  # noqa: E731
    out = {}
    for name, X, dist, cut in (("luv", luv, euc, CUT_LUV), ("rgb", rgb01, cb, CUT_RGB)):
        s = scores(X, dist)
        if not np.isfinite(s).any():
            out[name] = {"mean": float("nan"), "median_participant": float("nan"), "cutoff": cut, "p": float("nan"),
                         "share_below_cutoff": float("nan"), "null_mean": float("nan"), "per_participant": []}
            continue
        obs = float(np.nanmean(s))
        null = np.empty(n_perm)
        for k in range(n_perm):
            perm = np.array([rng.permutation(10) for _ in range(n)])
            Xp = np.take_along_axis(X, perm[..., None], axis=1)
            null[k] = np.nanmean(scores(Xp, dist))
        out[name] = {"mean": obs, "median_participant": float(np.nanmedian(s)), "cutoff": cut,
                     "share_below_cutoff": float(np.mean(s < cut)), "per_participant": s.round(3).tolist(),
                     "null_mean": float(null.mean()), "null_5": float(np.quantile(null, 0.05)),
                     "p": float((np.sum(null <= obs) + 1) / (n_perm + 1))}
    out["n_participants"] = n // 3
    out["parsed_share"] = float(np.mean(~np.isnan(rgb[..., 0])))
    return out


def slot_profile(runs) -> np.ndarray:
    """B: digit-centered log of the mean (over runs) palette distribution at each digit's slot."""
    P = np.zeros((10, len(COLORS)))
    for run in runs:
        for d, v in zip(run["order"], run["slot_logprobs"]):
            v = np.array(v)
            P[int(d)] += np.exp(v - _lse(v))
    L = np.log(P / len(runs))
    return L - L.mean(0, keepdims=True)


def row_perm_r(B, M, rng, n_perm=N_PERM):
    obs = float(np.corrcoef(B.ravel(), M.ravel())[0, 1])
    null = np.array([np.corrcoef(B[rng.permutation(10)].ravel(), M.ravel())[0, 1] for _ in range(n_perm)])
    return {"r": obs, "null_95": float(np.quantile(null, 0.95)), "p": float((np.sum(null >= obs) + 1) / (n_perm + 1))}


def hits(B):
    top = lambda d, k: [COLORS[i] for i in np.argsort(-B[d])[:k]]  # noqa: E731
    h = {"0_achromatic": top(0, 1)[0] in ("black", "white", "gray"), "1_white": "white" in top(1, 2),
         "4_yellow": "yellow" in top(4, 2), "7_purple": "purple" in top(7, 2)}
    return {"hits": h, "n": int(sum(h.values())), "tops": {d: top(d, 3) for d in range(10)}}


def nearest_name(h: str) -> str:
    lab = srgb_to_lab([int(h[i:i + 2], 16) for i in (0, 2, 4)])
    can = {c: srgb_to_lab(v) for c, v in CANONICAL.items()}
    return min(can, key=lambda c: float(np.linalg.norm(lab - can[c])))


def count_profile(A) -> np.ndarray:
    C = np.full((10, len(COLORS)), 0.5)
    for r in range(A.shape[0]):
        for d in range(10):
            if A[r, d] in COLORS:
                C[d, COLORS.index(A[r, d])] += 1
    L = np.log(C / C.sum(1, keepdims=True))
    return L - L.mean(0, keepdims=True)


def report(out: Path):
    cfg = json.loads((out / "run_config.json").read_text())
    rng = np.random.default_rng(SEED)
    global N_PERM
    if cfg.get("quick"):
        N_PERM = 200  # smoke output only
    M = reference_palette()
    R = {}
    for k in MODELS:
        p = out / f"battery_{k}.json"
        if p.exists():
            d = json.loads(p.read_text())
            assert d["config_hash"] == cfg["config_hash"]
            R[k] = d["runs"]
    A = {"config_hash": cfg["config_hash"], "reference_tops": {d: [COLORS[i] for i in np.argsort(-M[d])[:3]]
                                                               for d in range(10)},
         "preflight": {k: json.loads((out / f"preflight_{k}.json").read_text()) for k in R}, "models": {}}
    Bs = {}
    for k, runs in R.items():
        res = {}
        for mode in MODES:
            nm, _ = to_digit_rows(runs[f"name|{mode}"], parse_name)
            hx, _ = to_digit_rows(runs[f"hex|{mode}"], parse_hex)
            hx_name = np.array([[nearest_name(h) if h else None for h in row] for row in hx], dtype=object)
            flat = [a for row in nm for a in row]
            words = Counter(a.strip().lower() for run in runs[f"name|{mode}"] for a in run["answers"]
                            if parse_name(a) == "other")
            B = slot_profile(runs[f"name|{mode}"])
            if mode == "sample":
                Bs[k] = B
            # position and previous-answer dependence (name format)
            xs_pos, ys, prev, cur = [], [], [], []
            for run in runs[f"name|{mode}"]:
                ans = [parse_name(a) for a in run["answers"]]
                for pos, a in enumerate(ans):
                    if a is not None:
                        xs_pos.append(pos); ys.append(a)
                    if pos and a is not None and ans[pos - 1] is not None:
                        prev.append(ans[pos - 1]); cur.append(a)
            distinct = [len({parse_name(a) for a in run["answers"]} - {None, "other"}) for run in runs[f"name|{mode}"]]
            hexmean = {}
            for d in range(10):
                labs = [srgb_to_lab([int(h[i:i + 2], 16) for i in (0, 2, 4)]) for h in hx[:, d] if h]
                if labs:
                    from lfm3lab.synesthesia_stimuli import lab_to_srgb
                    rgb = lab_to_srgb(np.mean(labs, 0))
                    hexmean[d] = "#" + "".join(f"{int(round(v)):02x}" for v in rgb)
            res[mode] = {
                "parse_rate_name": float(np.mean([a is not None for a in flat])),
                "parse_rate_hex": float(np.mean([h is not None for row in hx for h in row])),
                "palette_share_name": float(np.mean([a in COLORS for a in flat])),
                "digit_specificity_name": digit_v(nm, rng, N_PERM if mode == "sample" else min(2000, N_PERM)),
                "digit_specificity_hex_nearest": digit_v(hx_name, rng, min(2000, N_PERM)),
                "consistency_hex": consistency(hx, rng, N_PERM if mode == "sample" else min(2000, N_PERM)),
                "palette_match_slot": row_perm_r(B, M, rng),
                "palette_match_hex_nearest": row_perm_r(count_profile(hx_name), M, rng),
                "palette_match_name_counts": row_perm_r(count_profile(nm), M, rng),
                "hits_slot": hits(B),
                "position_V": cramers_v(xs_pos, ys), "previous_answer_V": cramers_v(prev, cur),
                "same_as_previous_rate": float(np.mean([a == b for a, b in zip(prev, cur)])) if prev else None,
                "distinct_colors_per_run": {"median": float(np.median(distinct)),
                                            "share_ge7": float(np.mean(np.array(distinct) >= 7))},
                "modal_name_by_digit": {d: Counter(a for a in nm[:, d] if a).most_common(3) for d in range(10)},
                "modal_hex_nearest_by_digit": {d: Counter(a for a in hx_name[:, d] if a).most_common(3)
                                               for d in range(10)},
                "hex_mean_color_by_digit": hexmean,
                "off_palette_words": words.most_common(15),
                "examples": [{"order": run["order"], "answers": run["answers"]} for run in runs[f"name|{mode}"][:3]]
                            + [{"order": run["order"], "answers": run["answers"]} for run in runs[f"hex|{mode}"][:3]],
            }
        A["models"][k] = res
    if "instruct" in Bs and "base" in Bs:
        A["base_vs_instruct_slot"] = row_perm_r(Bs["base"], Bs["instruct"], rng)
    A["predictions"] = score(A)
    A = _clean(json.loads(json.dumps(A, default=str)))
    save_json(out / "analysis.json", A)
    (out / "findings.md").write_text(findings(A))
    print((out / "findings.md").read_text())


def score(A):
    P = {}
    I = A["models"].get("instruct", {}).get("sample")
    Bm = A["models"].get("base", {}).get("sample")
    if not I:
        return P
    pf = all(v["passed"] for v in A["preflight"].values())
    P["1_pipeline"] = {"instruct_name": I["parse_rate_name"], "instruct_hex": I["parse_rate_hex"],
                       "base_name": Bm["parse_rate_name"] if Bm else None, "base_hex": Bm["parse_rate_hex"] if Bm else None,
                       "preflight": pf,
                       "right": bool(pf and I["parse_rate_name"] >= .95 and I["parse_rate_hex"] >= .95 and Bm
                                     and Bm["parse_rate_name"] >= .8 and Bm["parse_rate_hex"] >= .8)}
    ds = I["digit_specificity_name"]
    P["2_digit_specificity"] = {**ds, "right": bool(ds["p"] < 0.01)}
    c = I["consistency_hex"]["luv"]
    g = A["models"]["instruct"]["greedy"]["consistency_hex"]["luv"]
    P["3_consistency"] = {"sample_mean": c["mean"], "sample_null_mean": c["null_mean"], "p": c["p"],
                          "sample_median_participant": c["median_participant"], "greedy_mean": g["mean"],
                          "greedy_median_participant": g["median_participant"],
                          "right": bool(c["p"] < 0.05 and c["median_participant"] > CUT_LUV and g["mean"] < c["mean"]
                                        and g["median_participant"] < CUT_LUV)}
    pm = I["palette_match_slot"]
    P["4_palette_match"] = {**pm, "hits": I["hits_slot"]["n"], "right": bool(pm["r"] > 0 and pm["p"] < 0.05
                                                                              and I["hits_slot"]["n"] >= 3)}
    P["5_spread"] = {**I["distinct_colors_per_run"], "right": bool(I["distinct_colors_per_run"]["share_ge7"] >= 0.7)}
    if "base_vs_instruct_slot" in A:
        bv = A["base_vs_instruct_slot"]
        P["6_base_vs_instruct"] = {**bv, "right": bool(bv["r"] > 0 and bv["p"] < 0.05)}
    return P


def _f(x, spec):
    return "n/a" if x is None or (isinstance(x, float) and not np.isfinite(x)) else format(x, spec)


def _clean(v):
    if isinstance(v, float) and not np.isfinite(v):
        return None
    if isinstance(v, dict):
        return {k: _clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_clean(x) for x in v]
    return v


def findings(A):
    L = ["# Track 23 digit color battery — auto-generated findings", "", f"Config `{A['config_hash'][:12]}…`.", "",
         "Reference palette M tops (stage 1, digit-relative): " +
         "; ".join(f"{d}: {', '.join(v)}" for d, v in A["reference_tops"].items()), ""]
    for k, res in A["models"].items():
        for mode, r in res.items():
            L += [f"## {k} / {mode}", "",
                  f"- parse: name {r['parse_rate_name']:.3f} (palette {r['palette_share_name']:.3f}), hex {r['parse_rate_hex']:.3f}",
                  f"- digit specificity (name): {json.dumps(r['digit_specificity_name'])}",
                  f"- digit specificity (hex → nearest name): {json.dumps(r['digit_specificity_hex_nearest'])}",
                  f"- consistency LUV: mean {_f(r['consistency_hex']['luv']['mean'], '.1f')}, median participant "
                  f"{_f(r['consistency_hex']['luv']['median_participant'], '.1f')}, null {_f(r['consistency_hex']['luv']['null_mean'], '.1f')}, "
                  f"p {_f(r['consistency_hex']['luv']['p'], '.4f')}, below 135.30: {_f(r['consistency_hex']['luv']['share_below_cutoff'], '.2f')}",
                  f"- consistency RGB: mean {_f(r['consistency_hex']['rgb']['mean'], '.3f')}, median participant "
                  f"{_f(r['consistency_hex']['rgb']['median_participant'], '.3f')}, null {_f(r['consistency_hex']['rgb']['null_mean'], '.3f')}, "
                  f"p {_f(r['consistency_hex']['rgb']['p'], '.4f')}, below 1.43: {_f(r['consistency_hex']['rgb']['share_below_cutoff'], '.2f')}",
                  f"- palette match r(B, M): slot {json.dumps(r['palette_match_slot'])}; name counts "
                  f"{json.dumps(r['palette_match_name_counts'])}; hex nearest {json.dumps(r['palette_match_hex_nearest'])}",
                  f"- hits: {r['hits_slot']['hits']}",
                  f"- slot-profile tops: " + "; ".join(f"{d}: {', '.join(v)}" for d, v in r["hits_slot"]["tops"].items()),
                  f"- modal names: " + "; ".join(f"{d}: {v}" for d, v in r["modal_name_by_digit"].items()),
                  f"- modal hex→name: " + "; ".join(f"{d}: {v}" for d, v in r["modal_hex_nearest_by_digit"].items()),
                  f"- hex mean color: {r['hex_mean_color_by_digit']}",
                  f"- position V {r['position_V']:.3f}; previous-answer V {r['previous_answer_V']:.3f}; "
                  f"same as previous {r['same_as_previous_rate']}; distinct per run {r['distinct_colors_per_run']}",
                  f"- off-palette words: {r['off_palette_words']}", "", "Examples:", ""]
            L += [f"    {e['order']} → {e['answers']}" for e in r["examples"]]
            L.append("")
    if "base_vs_instruct_slot" in A:
        L.append(f"Base vs instruct slot profiles: {json.dumps(A['base_vs_instruct_slot'])}")
    L += ["", "## Predictions", ""] + [f"- {k}: {json.dumps(v, default=str)}" for k, v in A["predictions"].items()]
    return "\n".join(L) + "\n"


def dry_run():
    from transformers import AutoTokenizer
    toks = {k: AutoTokenizer.from_pretrained(r, revision=v, trust_remote_code=True) for k, (r, v) in MODELS.items()}
    ords = orders()
    print("orders[0:3]", ords[:3])
    for k, tok in toks.items():
        palette_ids(tok)
        for f in FORMATS:
            text = prefix(tok, k, f, ords[0]) + label(ords[0][0], f, True)
            print(k, f, len(tok.encode(text, add_special_tokens=False)), repr(text))
        print(k, "label tokens:", [tok.convert_ids_to_tokens(tok.encode(label("7", f, False), add_special_tokens=False))
                                   for f in FORMATS])
    M = reference_palette()
    print("M tops:", {d: [COLORS[i] for i in np.argsort(-M[d])[:2]] for d in range(10)})
    print("LUV check white/black:", srgb_to_luv([255, 255, 255]).round(2), srgb_to_luv([0, 0, 0]).round(2),
          "red", srgb_to_luv([255, 0, 0]).round(2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=("dry-run", "run", "report"), required=True)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--output", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--only", default="")
    ap.add_argument("--quick", action="store_true", help="6 orders, smoke test only")
    args = ap.parse_args()
    out = args.output.resolve()
    if args.stage == "dry-run":
        dry_run()
    elif args.stage == "run":
        run(out, args)
    else:
        report(out)


if __name__ == "__main__":
    main()
