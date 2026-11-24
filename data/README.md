# Data

Every answer the batteries collected, the settings they ran with, and the analyses computed from them. `SHA256SUMS` lists a hash for each file.

| Path | Contents |
| --- | --- |
| `battery_v1/battery_instruct.json`, `battery_base.json` | 60 runs per condition: `name\|sample`, `name\|greedy`, `hex\|sample`, `hex\|greedy` |
| `battery_v2/battery_instruct.json` | 1,000 runs of `name\|sample` |
| `*/run_config.json` | Model revision, prompts, orders or their digest, decoding, banned tokens, package versions and source hashes |
| `*/preflight*.json` | The numerical checks run before collecting answers |
| `*/analysis.json`, `*/findings.md` | Output of each script's `report` stage |
| `reference/scores_*.json` | Likelihood scores from the earlier LFM3 test that defines the reference palette |
| `reference/config.json` | Settings for that test |

## Run format

Each run in a `battery_*.json` file is one sitting:

```json
{"order": ["7", "2", "0", ...], "answers": [" purple", " yellow", " black", ...], "slot_logprobs": [[...11 values...], ...]}
```

`answers[i]` is the raw text the model wrote after the label for `order[i]`. `slot_logprobs[i]` holds the log-probabilities of the 11 basic color words (in the order of `COLORS` in `src/lfm3lab/synesthesia.py`) at the first token of that slot. It is `null` in the hex format.

## Reference palette

`reference/` holds scores from a likelihood test that ran before both batteries. That test scored the 11 color words after six wordings of "what color is this digit?" on the instruct model (chat and plain text) and the base model. The batteries use only its digit-to-color scores, through `reference_palette()` in `scripts/battery_v1.py`; the other entries (moods, data types and controls) are unused here. The script for that test is not part of this repository.

## Provenance

- The answer, settings and check files hash to the values recorded when they were copied off the GPU machine.
- `src/lfm3lab/synesthesia.py` and `synesthesia_stimuli.py` are byte-identical to the versions in each `run_config.json`.
- `scripts/battery_v1.py` and `battery_v2.py` were `experiments/23_battery.py` and `experiments/23_battery_v2.py` in the research codebase, which is where `run_config.json` records their hashes. They differ only in file paths, docstrings and the location of a lock file. Their `report` stages reproduce `analysis.json` and `findings.md` byte for byte (`scripts/verify.py`).

## License

CC BY 4.0; see `LICENSE`. The answers were generated with LFM3 models, released by Liquid AI under the LFM Open License v1.0.
