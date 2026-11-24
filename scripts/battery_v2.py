"""Digit color battery v2: 1,000 orders, instruct, name format, sampled (T = 1) only.

    uv run python scripts/battery_v2.py --stage dry-run                                  # tokenizer only
    uv run python scripts/battery_v2.py --stage run --device cuda --output DIR [--quick]  # GPU: fp32, TF32 off
    uv run python scripts/battery_v2.py --stage report                                   # model-free

Same protocol as battery v1's instruct name|sample condition (prompt, scaffold, decoding, parsing, slot
probabilities, banned think tokens), reused from scripts/battery_v1.py. Only the number of orders (1,000),
their seed (2311) and chunked batching change. The palette figure (scripts/figure.py) is built from this data.
Frozen by the "Battery v2" section of PROTOCOL.md.
"""

from __future__ import annotations

import argparse
import fcntl
import gc
import importlib.util
import json
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lfm3lab.synesthesia import COLORS, DIGITS, digest, file_hash, save_json  # noqa: E402

_spec = importlib.util.spec_from_file_location("battery23", ROOT / "scripts/battery_v1.py")
bat = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bat)

DEFAULT_OUT = ROOT / "data/battery_v2"
V1 = ROOT / "data/battery_v1/battery_instruct.json"
KEY = "instruct"
REPO, REVISION = bat.MODELS[KEY]
FMT, MODE = "name", "sample"
N_ORDERS, SEED, CHUNK = 1000, 2311, 125
QUICK_ORDERS, QUICK_CHUNK = 10, 5          # two chunks, so the smoke run exercises chunking and resume
N_PERM, N_BOOT = 10_000, 5_000
PREFLIGHT_ORDERS = 8
CATS = list(COLORS) + ["other"]


def orders(n=N_ORDERS):
    rng = np.random.default_rng(SEED)
    return [[DIGITS[i] for i in rng.permutation(10)] for _ in range(n)]


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
    tok = AutoTokenizer.from_pretrained(REPO, revision=REVISION, trust_remote_code=True)
    n, chunk = (QUICK_ORDERS, QUICK_CHUNK) if args.quick else (N_ORDERS, CHUNK)
    ords = orders(n)
    cfg = {"protocol": "23-battery-v2", "quick": bool(args.quick), "model": KEY, "repo": REPO, "revision": REVISION,
           "format": FMT, "mode": MODE, "n_orders": n, "chunk": chunk, "seed": SEED,
           "orders_digest": digest(ords), "user": bat.USER[FMT], "max_slot_tokens": bat.MAX_SLOT_TOKENS,
           "decoding": {"temperature": 1.0, "top_k": 0, "top_p": 1.0}, "banned": [bat.THINK, bat.END_THINK],
           "generator_seed": "SEED * 1000 + chunk index", "device": dev, "dtype": "float32",
           "prefix_example": bat.prefix(tok, KEY, FMT, ords[0]),
           "torch_version": torch.__version__, "transformers_version": transformers.__version__,
           "source_hashes": {str(p.relative_to(ROOT)): file_hash(p) for p in
                             (Path(__file__).resolve(), ROOT / "scripts/battery_v1.py",
                              ROOT / "src/lfm3lab/synesthesia.py",
                              ROOT / "src/lfm3lab/synesthesia_stimuli.py")}}
    cfg["config_hash"] = digest(cfg)
    out.mkdir(parents=True, exist_ok=True)
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
    def battery(model, run_orders, greedy, gen, bar=None):
        """battery v1's scaffolded loop for instruct / name format (same code path, one format)."""
        pad = tok.pad_token_id
        stop_ids = {bat.IM_END, tok.eos_token_id}
        banned = cfg["banned"]
        pal = bat.palette_ids(tok)
        seqs = [tok.encode(bat.prefix(tok, KEY, FMT, o), add_special_tokens=False) for o in run_orders]
        answers = [[None] * 10 for _ in run_orders]
        slot_probs = [[None] * 10 for _ in run_orders]
        for s in range(10):
            for r, o in enumerate(run_orders):
                seqs[r] = seqs[r] + tok.encode(bat.label(o[s], FMT, s == 0), add_special_tokens=False)
            text = [""] * len(run_orders)
            done = [False] * len(run_orders)
            for step in range(bat.MAX_SLOT_TOKENS):
                active = [r for r in range(len(run_orders)) if not done[r]]
                if not active:
                    break
                lp = last_logprobs(model, [seqs[r] for r in active], pad)
                lp[:, banned] = -float("inf")
                if step == 0:
                    for j, r in enumerate(active):
                        slot_probs[r][s] = [float(torch.logsumexp(lp[j, pal[c]], 0)) for c in COLORS]
                if greedy:
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
                bar.update(len(run_orders))
        return [{"order": o, "answers": a, "slot_logprobs": p} for o, a, p in zip(run_orders, answers, slot_probs)]

    def preflight(model):
        pad = tok.pad_token_id
        few = ords[:min(PREFLIGHT_ORDERS, len(ords))]
        seqs = [tok.encode(bat.prefix(tok, KEY, FMT, o) + bat.label(o[0], FMT, True), add_special_tokens=False)
                for o in few]
        seqs.append(seqs[0] + tok.encode(" blue\n5: red\n9:", add_special_tokens=False))
        a, b = last_logprobs(model, seqs, pad), last_logprobs(model, seqs, pad)
        single = torch.cat([last_logprobs(model, [x], pad) for x in seqs])
        g_batch = battery(model, few, True, None)
        g_single = [battery(model, [o], True, None)[0] for o in few]
        same = [x["answers"] == y["answers"] for x, y in zip(g_batch, g_single)]
        slot_diff = max(abs(u - v) for x, y in zip(g_batch, g_single)
                        for ps, qs in zip(x["slot_logprobs"], y["slot_logprobs"]) for u, v in zip(ps, qs))
        pf = {"max_pad_vs_single": float((a - single).abs().max()), "max_repeat_diff": float((a - b).abs().max()),
              "greedy_batched_equals_single": all(same), "n_orders_checked": len(few),
              "n_orders_identical": int(sum(same)), "max_slot_logprob_batched_vs_single": float(slot_diff)}
        pf["passed"] = (pf["max_pad_vs_single"] <= bat.PREFLIGHT_TOL and pf["max_repeat_diff"] == 0.0
                        and pf["greedy_batched_equals_single"])
        return pf

    bat.LOCK.parent.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(2)
    starts = list(range(0, n, chunk))
    cdir = out / "chunks"
    cdir.mkdir(exist_ok=True)

    def chunk_done(c):
        p = cdir / f"chunk_{c:03d}.json"
        return p.exists() and json.loads(p.read_text())["config_hash"] == cfg["config_hash"]

    session = {"config_hash": cfg["config_hash"], "completed": False}
    t0 = time.monotonic()
    with bat.LOCK.open("a+") as lock:
        print("Waiting for shared inference lock", flush=True)
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        model = AutoModelForCausalLM.from_pretrained(REPO, revision=REVISION, trust_remote_code=True,
                                                     dtype=torch.float32, attn_implementation="sdpa").to(dev).eval()
        try:
            pp = out / "preflight.json"
            if pp.exists() and json.loads(pp.read_text())["config_hash"] == cfg["config_hash"]:
                pf = json.loads(pp.read_text())
                print("preflight (saved)", pf, flush=True)
            else:
                pf = preflight(model)
                print("preflight", pf, flush=True)
                save_json(pp, {"config_hash": cfg["config_hash"], **pf})
            if not pf["passed"]:
                raise SystemExit("preflight failed")
            todo = [c for c in range(len(starts)) if not chunk_done(c)]
            with tqdm(total=n * 10, desc="battery v2", unit="answer", dynamic_ncols=True) as bar:
                for c in range(len(starts)):
                    lo, hi = starts[c], min(starts[c] + chunk, n)
                    if c not in todo:
                        bar.update((hi - lo) * 10)
                        continue
                    bar.set_postfix_str(f"chunk {c + 1}/{len(starts)}, orders {lo + 1}-{hi}")
                    gen = torch.Generator().manual_seed(SEED * 1000 + c)
                    tc = time.monotonic()
                    res = battery(model, ords[lo:hi], False, gen, bar)
                    save_json(cdir / f"chunk_{c:03d}.json", {"config_hash": cfg["config_hash"], "chunk": c,
                                                              "start": lo, "seconds": time.monotonic() - tc,
                                                              "runs": res})
            runs = []
            for c in range(len(starts)):
                d = json.loads((cdir / f"chunk_{c:03d}.json").read_text())
                assert d["config_hash"] == cfg["config_hash"] and d["start"] == starts[c]
                runs += d["runs"]
            assert [r["order"] for r in runs] == ords
            save_json(out / f"battery_{KEY}.json", {"config_hash": cfg["config_hash"], "model": KEY,
                                                    "revision": REVISION, "seconds": time.monotonic() - t0,
                                                    "runs": {f"{FMT}|{MODE}": runs}})
            session["completed"] = True
        finally:
            del model
            gc.collect()
            if dev == "cuda":
                torch.cuda.empty_cache()
            elif dev == "mps":
                torch.mps.empty_cache()
            session["seconds"] = time.monotonic() - t0
            save_json(out / "sessions" / f"{time.time_ns()}.json", session)
    print(f"battery v2 done: {session['seconds']:.0f}s", flush=True)


# ------------------------------------------------------------------ report (model-free)

def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None]
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [float(c - h), float(c + h)]


def codes(A):
    """[n, 10] answer codes by digit; -1 for unparsed."""
    idx = {c: i for i, c in enumerate(CATS)}
    return np.array([[idx.get(a, -1) if a is not None else -1 for a in row] for row in A], dtype=int)


def v_fast(C):
    """Cramér's V digit x answer over the parsed cells of C [n, 10] (same statistic as battery v1's cramers_v)."""
    d = np.broadcast_to(np.arange(10), C.shape)
    m = C >= 0
    K = len(CATS)
    T = np.bincount(d[m] * K + C[m], minlength=10 * K).reshape(10, K).astype(float)
    T = T[T.sum(1) > 0][:, T.sum(0) > 0]
    if min(T.shape) < 2:
        return 0.0
    N = T.sum()
    E = T.sum(1, keepdims=True) * T.sum(0, keepdims=True) / N
    return float(np.sqrt(((T - E) ** 2 / E).sum() / (N * (min(T.shape) - 1))))


def digit_v(C, rng, n_perm):
    obs = v_fast(C)
    null = np.empty(n_perm)
    for k in range(n_perm):
        perm = np.argsort(rng.random(C.shape), axis=1)   # shuffle digit labels within each run
        null[k] = v_fast(np.take_along_axis(C, perm, 1))
    return {"V": obs, "null_mean": float(null.mean()), "null_95": float(np.quantile(null, 0.95)),
            "p": float((np.sum(null >= obs) + 1) / (n_perm + 1))}


def palette_probs(runs):
    """[n, 10, 11] renormalized slot palette distribution, indexed by digit."""
    P = np.zeros((len(runs), 10, len(COLORS)))
    for r, run in enumerate(runs):
        for d, v in zip(run["order"], run["slot_logprobs"]):
            v = np.array(v)
            P[r, int(d)] = np.exp(v - bat._lse(v))
    return P


def report(out: Path):
    cfg = json.loads((out / "run_config.json").read_text())
    n_perm, n_boot = (200, 200) if cfg["quick"] else (N_PERM, N_BOOT)
    rng = np.random.default_rng(SEED)
    d = json.loads((out / f"battery_{KEY}.json").read_text())
    assert d["config_hash"] == cfg["config_hash"]
    runs = d["runs"][f"{FMT}|{MODE}"]
    pf = json.loads((out / "preflight.json").read_text())
    n = len(runs)

    A, _ = bat.to_digit_rows(runs, bat.parse_name)
    C = codes(A)
    obs_check = bat.cramers_v([dg for r in range(n) for dg in range(10) if A[r, dg] is not None],
                              [A[r, dg] for r in range(n) for dg in range(10) if A[r, dg] is not None])
    assert abs(obs_check - v_fast(C)) < 1e-9, (obs_check, v_fast(C))
    flat = [a for row in A for a in row]
    parse_rate = float(np.mean([a is not None for a in flat]))

    M = bat.reference_palette()
    B = bat.slot_profile(runs)
    v1_runs = json.loads(V1.read_text())["runs"]["name|sample"]
    B1 = bat.slot_profile(v1_runs)
    hits = bat.hits(B)
    P = palette_probs(runs)
    Pm = P.mean(0)
    boot = np.empty((n_boot, 10, len(COLORS)))
    for k in range(n_boot):
        boot[k] = P[rng.integers(0, n, n)].mean(0)
    lo, hi = np.quantile(boot, 0.025, 0), np.quantile(boot, 0.975, 0)

    per_digit = {}
    for dg in range(10):
        cnt = Counter(a if a is not None else "unparsed" for a in A[:, dg])
        top = COLORS[int(np.argmax(B[dg]))]
        per_digit[dg] = {
            "n": n, "digit_relative_top": top,
            "digit_relative_tops3": [COLORS[i] for i in np.argsort(-B[dg])[:3]],
            "sampled_counts": dict(cnt.most_common()),
            "sampled_share_ci": {c: [cnt[c] / n, *wilson(cnt[c], n)] for c in CATS + ["unparsed"] if cnt[c]},
            "exact_palette_share_ci": {c: [float(Pm[dg, i]), float(lo[dg, i]), float(hi[dg, i])]
                                       for i, c in enumerate(COLORS)},
        }
    v1A, _ = bat.to_digit_rows(v1_runs, bat.parse_name)
    res = {
        "config_hash": cfg["config_hash"], "n_runs": n, "preflight": pf,
        "parse_rate_name": parse_rate, "palette_share_name": float(np.mean([a in COLORS for a in flat])),
        "digit_specificity_name": digit_v(C, rng, n_perm),
        "palette_match_slot_vs_M": bat.row_perm_r(B, M, rng, n_perm),
        "palette_match_slot_vs_v1": bat.row_perm_r(B, B1, rng, n_perm),
        "hits_slot": hits, "per_digit": per_digit,
        "numeral_fills": {dg: per_digit[dg]["digit_relative_top"] for dg in range(10)},
        "v1_numeral_fills": {dg: COLORS[int(np.argmax(B1[dg]))] for dg in range(10)},
        "v1_sampled_purple_for_7": int(sum(a == "purple" for a in v1A[:, 7])),
        "off_palette_words": Counter(a.strip().lower() for run in runs for a in run["answers"]
                                     if bat.parse_name(a) == "other").most_common(20),
        "distinct_colors_per_run_median": float(np.median(
            [len({bat.parse_name(a) for a in run["answers"]} - {None, "other"}) for run in runs])),
        "examples": [{"order": r["order"], "answers": r["answers"]} for r in runs[:5]],
    }
    res = json.loads(json.dumps(res, default=str))   # string keys, as in the saved analysis.json
    res["predictions"] = score(res)
    res = bat._clean(res)
    save_json(out / "analysis.json", res)
    (out / "findings.md").write_text(findings(res))
    print((out / "findings.md").read_text())


def score(R):
    P = {}
    P["1_pipeline"] = {"parse_rate_name": R["parse_rate_name"], "preflight": R["preflight"]["passed"],
                       "right": bool(R["preflight"]["passed"] and R["parse_rate_name"] >= 0.95)}
    ds = R["digit_specificity_name"]
    P["2_digit_specificity"] = {**ds, "right": bool(ds["p"] < 0.001 and ds["null_mean"] < 0.06
                                                    and 0.20 <= ds["V"] <= 0.35)}
    a, b = R["palette_match_slot_vs_v1"], R["palette_match_slot_vs_M"]
    P["3_palette_replicates"] = {"r_v1": a["r"], "r_M": b["r"], "hits": R["hits_slot"]["n"],
                                 "right": bool(a["r"] > 0.8 and b["r"] > 0.6 and R["hits_slot"]["n"] >= 3)}
    s7 = R["per_digit"]["7"]
    samp = s7["sampled_share_ci"].get("purple", [0.0])[0]
    exact = s7["exact_palette_share_ci"]["purple"][0]
    P["4_seven_purple"] = {"top": s7["digit_relative_top"], "sampled_share": samp, "exact_share": exact,
                           "right": bool(s7["digit_relative_top"] == "purple" and 0.10 <= samp <= 0.25
                                         and 0.19 <= exact <= 0.32)}
    return P


def findings(R):
    L = ["# Track 23 digit color battery v2 — auto-generated findings", "",
         f"Config `{R['config_hash'][:12]}…`, {R['n_runs']} runs, instruct, name format, sampled (T = 1).", "",
         f"- preflight: {json.dumps(R['preflight'])}",
         f"- parse rate {R['parse_rate_name']:.4f}; palette share {R['palette_share_name']:.4f}",
         f"- digit specificity: {json.dumps(R['digit_specificity_name'])}",
         f"- r(B, M): {json.dumps(R['palette_match_slot_vs_M'])}",
         f"- r(B, B_v1): {json.dumps(R['palette_match_slot_vs_v1'])}",
         f"- hits: {R['hits_slot']['hits']}",
         "- numeral fills v2: " + ", ".join(f"{k} {v}" for k, v in R["numeral_fills"].items()),
         "- numeral fills v1: " + ", ".join(f"{k} {v}" for k, v in R["v1_numeral_fills"].items()),
         f"- median distinct colors per run: {R['distinct_colors_per_run_median']}",
         f"- off-palette words: {R['off_palette_words']}", "",
         "## Per digit (sampled share [95% Wilson]; exact palette share [95% context bootstrap])", ""]
    for dg, v in R["per_digit"].items():
        top3 = v["digit_relative_tops3"]
        samp = "; ".join(f"{c} {s:.3f} [{a:.3f}, {b:.3f}]" for c, (s, a, b) in
                         sorted(v["sampled_share_ci"].items(), key=lambda kv: -kv[1][0])[:5])
        ex = "; ".join(f"{c} {v['exact_palette_share_ci'][c][0]:.3f} [{v['exact_palette_share_ci'][c][1]:.3f}, "
                       f"{v['exact_palette_share_ci'][c][2]:.3f}]" for c in top3)
        L.append(f"- {dg}: digit-relative tops {top3} | sampled: {samp} | exact (tops): {ex}")
    L += ["", "Examples:", ""] + [f"    {e['order']} → {e['answers']}" for e in R["examples"]]
    L += ["", "## Predictions", ""] + [f"- {k}: {json.dumps(v, default=str)}" for k, v in R["predictions"].items()]
    return "\n".join(L) + "\n"


def dry_run():
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(REPO, revision=REVISION, trust_remote_code=True)
    ords = orders()
    v1 = bat.orders()
    print("orders[0:2]", ords[:2], "| overlap with v1's 60 orders:", sum(o in v1 for o in ords))
    bat.palette_ids(tok)
    lens = [len(tok.encode(bat.prefix(tok, KEY, FMT, o), add_special_tokens=False)) for o in ords[:20]]
    print("prefix tokens", min(lens), max(lens))
    print(repr(bat.prefix(tok, KEY, FMT, ords[0]) + bat.label(ords[0][0], FMT, True)))
    print("chunks", len(range(0, N_ORDERS, CHUNK)), "of", CHUNK)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=("dry-run", "run", "report"), required=True)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--output", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--quick", action="store_true", help="10 orders in 2 chunks, smoke test only")
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
