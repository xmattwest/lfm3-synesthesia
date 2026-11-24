# Protocol

Two batteries on LFM3-1.7B. Battery v1 tested the procedure in two answer formats on the instruct and base models. Battery v2 repeated the instruct color-word condition on 1,000 new orders to measure each digit's palette precisely. The design, statistics and predictions below were written before each run.

## Battery v1

**Question.** In a human-style synesthesia battery, does LFM3 tie colors to digits? Are a digit's colors consistent across runs, beyond what the same colors would give if reassigned at random between digits? Does the battery reproduce the reference palette from the earlier likelihood test?

**Human reference.** The Synesthesia Battery shows each grapheme 3 times in random order and the participant picks a color each time ([Eagleman et al. 2007](https://pubmed.ncbi.nlm.nih.gov/16919755)). Consistency is the distance between a grapheme's 3 picks, averaged over graphemes; lower is more consistent. [Rothen et al. 2013](http://www.daysyn.com/Rothen_Seth_Witzel_Ward_2013.pdf) give ROC cut-offs: CIELUV Euclidean 135.30, and RGB city-block 1.43 with RGB scaled to 0 to 1. The score here sums the three pairwise distances per grapheme (Eagleman's convention) and averages over the 10 digits. Rothen's text does not say whether pairs are summed or averaged, so cut-off comparisons are descriptive. Humans are scored on letters and digits; only digits are scored here.

### Design

- **Models.** `LiquidAI/LFM3-1.7B` at `40ebe0aa6662c9d40389c2f5d565b6a2c6aebacd` (instruct, chat template, primary) and `LiquidAI/LFM3-1.7B-Base` at `545fc8f4c7b5fa9f405105274cd29c4f8f44b526` (plain text, secondary). float32, TF32 off, SDPA attention, one model loaded at a time.
- **Orders.** 60 random permutations of 0 to 9 (seed 23), the same for every model, format and decoding mode. Consecutive triplets of orders form 20 "participants" with 3 trials per digit.
- **Procedure.** The prompt lists the digits in the run's order. The script writes the label `7:` (`7: #` for hex) and the model writes until a newline; then the script appends `\n2:`, and so on. Each answer conditions on the earlier ones, as in a single sitting. A slot stops at a newline, end of turn, or 8 new tokens. `<think>` and `</think>` are banned for the instruct model so answers stay in the scaffold.
- **Prompts.**
  - Instruct, name format: "Some people experience each digit as having its own color. For each digit below, write the color you associate with it, as one basic color word. Go in the order given.\nDigits: {order}"
  - Instruct, hex format: the same with "as a hex color code (like #RRGGBB)".
  - Base, name format: "Synesthesia color chart: each digit and the color it has.\nDigits: {order}\n\n", then the scaffold. Hex: "each digit and its color as a hex code".
- **Decoding.** Sampled at temperature 1.0 with top-k and top-p off and no repetition penalty, and greedy on the same orders.
- **Slot probabilities (name format).** At the first token of each slot, the probabilities of the 11 basic color words (" red" and " Red" pooled, renormalized over the 11) are recorded under the run's own history.
- **Parsing.** Name: the first of the 11 basic color words in the answer (grey counts as gray). Other answers of one or two letter-only words count as "other". Hex: the first 6 hex characters. Anything else is unparsed, counted and excluded.
- **Hex to name.** Each hex code is also mapped to the nearest of 11 reference colors by CIE76 distance, so both formats can be compared with the reference palette.
- **Checks before collecting answers.** Padded and single-sequence next-token log-probabilities agree within 0.001 nats, a repeated batch is exact, and the scaffolded greedy loop gives the same answers batched and one order at a time.

### Statistics

- **Digit specificity (primary; instruct, name format, sampled).** Cramér's V between digit and answer (11 colors and "other"). Null: shuffle the digit labels within each run, which keeps each run's colors and slot positions (10,000 permutations).
- **Battery consistency (hex).** Per participant, the mean over digits of the summed pairwise CIELUV distances (and RGB city-block). Reported as the median participant and the share below the cut-offs. Null: the same within-run shuffle.
- **Palette match.** B is the digit-centered log of the mean slot probabilities, 10 digits × 11 colors. The reference palette M is the same digit-centered profile from the earlier likelihood test (`data/reference`). r(B, M) over all cells, with a null that permutes B's digit rows. Hits: an achromatic color is 0's top; white for 1, yellow for 4 and purple for 7 are each in that digit's top 2.

### Predictions and outcomes

| # | Prediction | Outcome | |
| --- | --- | --- | --- |
| 1 | Parse rate ≥ 95% for instruct (both formats), ≥ 80% for base; all checks pass | Instruct name 94.8%, hex 98.5%; base 82.3%, 92.2%; checks pass | Missed by 0.2 points |
| 2 | Instruct name-format V above the null, p < 0.01 | V = 0.30, null mean 0.14, p = 0.0001 | Held |
| 3 | Sampled hex more consistent than shuffled (p < 0.05) but median participant above 135.30; greedy lower, median below 135.30 | Sampled 358 vs shuffled 366, p = 0.10; median 355; greedy 285 but median 294 | Failed |
| 4 | r(B, M) > 0 with p < 0.05, and at least 3 of 4 hits | r = 0.74, p = 0.0001, 4 of 4 | Held |
| 5 | At least 70% of sampled instruct runs use 7 or more distinct colors | 85%, median 8 | Held |
| 6 | Base and instruct slot profiles correlate | r = 0.71, p = 0.0001 | Held |

**Reading.** The color-word palette is real and matches the reference. As hex codes it mostly disappears: the sampled codes are no more consistent than shuffled ones, and they map only weakly back to the palette (V = 0.21 against a shuffled null of 0.13). Greedy hex codes beat the shuffle, but only 1 of 20 participants falls under the CIELUV cut-off. Sampled base answers show no digit specificity (V = 0.15, p = 0.36), and greedy base fills the slots in a fixed order by position. Its slot probabilities still carry the palette (r = 0.77 with M).

## Battery v2

**Why.** With 60 runs, each digit has 60 answers, which is too few for per-digit shares: 7 was named purple 9 of 60 times (95% interval 8% to 26%). The slot probabilities showed that the spread comes from the order and earlier answers, not from sampling noise, so v2 adds orders rather than repeat samples.

**Design.** Battery v1's instruct, name-format, sampled condition, unchanged: prompt, scaffold, decoding, parsing, slot probabilities and banned tokens. Only three things change. There are 1,000 new orders (seed 2311, none shared with v1), run in 8 chunks of 125, with one random generator per chunk (seed 2311 × 1000 + chunk) so a resumed chunk reproduces exactly. The pre-run checks add one: greedy answers on the first 8 orders must be identical batched and one at a time.

**Added statistics.** Per-digit shares of each answer with Wilson 95% intervals; exact palette shares from the slot probabilities with a 95% interval from 5,000 bootstrap resamples of runs; r between the v1 and v2 profiles with the digit-row null.

### Predictions and outcomes

| # | Prediction | Outcome | |
| --- | --- | --- | --- |
| 1 | Parse rate ≥ 95%; all checks pass | 95.4%; checks pass | Held |
| 2 | V above the null with p < 0.001, null mean below 0.06, V between 0.20 and 0.35 | V = 0.261, null mean 0.035, p = 0.0001 | Held |
| 3 | r(B_v2, B_v1) > 0.8, r(B_v2, M) > 0.6, at least 3 of 4 hits | 0.967, 0.750, 4 of 4 | Held |
| 4 | Purple is 7's top digit-relative color; its sampled share is 10% to 25% and its exact palette share 0.19 to 0.32 | Purple; 21.8%; 0.231 | Held |

**Reading.** The palette replicates on fresh orders. The digit-relative top color (the color a digit gets more than the average digit) is black for 0 and 8, white for 1, yellow for 2 and 4, blue for 3, gray for 5, brown for 6, and purple for 7 and 9. A digit-relative top can be a rarely named color: gray is 5's top at 3.8% of its answers.

## Limits

- A run's answers are samples and orders, not sessions over time. Consistency here means the association survives resampling and a change of context. It is not memory.
- A digit's color can depend on the colors already used in the run; the model rarely repeats the previous answer. The within-run shuffle controls for run-level and position effects but not for that dependency.
- The human cut-offs were tuned to separate self-reported synesthetes from controls. Here they are only a ruler.
- Results come from one model family, one prompt wording per format and 11 basic color words.
