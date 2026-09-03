# PREREGISTRATION — Instance `rotation-gap-fano-s1`

> **Document Status:** Draft — SPREMNO ZA GEJT (not ratified)  
> **Version:** v1.0.0  
> **Instance Identifier:** `rotation-gap-fano-s1`  
> **Frozen:** this file MUST be committed and git-timestamped BEFORE this instance
> reads a single byte of the Google Willow archive. Any byte read prior to the
> freeze commit renders every verdict below void and the work becomes
> `Exploratory (not pre-registered)`.

---

## 1. Central Claim Under Test

Source, read in the original on 2026-09-03:
Stenberg, S., *The Rotation Gap Is Not An Error — Ternary Structure in IBM Quantum
Hardware*, arXiv:2604.11963v1, dated March 2026. Section II F and Table III.

Four sub-claims are admitted. Each is quoted at the precision printed in the source.

| ID | Sub-claim as stated | Source location |
|----|---------------------|-----------------|
| `W1` | Overall Fano factor on the Google Willow archive is `F = 2.42 ± 0.36`, over `N = 420` experiments | §II F, Table III, Abstract |
| `W2` | Fano factor by code distance: `d=3 → 2.29`, `d=5 → 2.59`, `d=7 → 2.80` | §II F |
| `W3` | One-way ANOVA across code distances gives F-statistic `= 59.1`, `p ≈ 0` | §II F |
| `W4` | One-sample t-statistic against Poisson (`F = 1`) is `t = +80` | §II F |

`W1` is the primary claim. `W2`–`W4` are secondary and carry independent verdicts.

---

## 2. Estimator — Frozen Definition

The estimator is taken verbatim from the author's published analysis script
`willow/willow_fano_analysis.py` (245 lines, MIT, repository accessed 2026-09-03).
It is frozen here so that the reproduction tests the author's own operation and not
a substituted one.

```python
line 59:  fano = var_c / mean_c if mean_c > 0 else np.nan
line 93:  se = np.std(all_fanos) / np.sqrt(len(all_fanos))
line 94:  t_vs_1 = (np.mean(all_fanos) - 1.0) / se
line 97:  F_overall = np.mean(all_fanos)
```

Operationally:

1. For each experiment, obtain the per-shot detection-event count vector `c`.
2. Per-experiment Fano `F_i = Var(c) / Mean(c)`.
3. `F_overall` = **unweighted arithmetic mean** of `F_i` across all admitted experiments.
4. Reported spread = `np.std(F_i)` (population standard deviation of the per-experiment
   values, **not** a standard error of the mean).
5. `t = (F_overall − 1.0) / (std(F_i) / sqrt(N))`.

No alternative estimator is admitted under `R1`–`R4`. A different estimator produces a
different quantity and cannot bear on the reported number.

---

## 3. Premises

Each premise is stated so that it can be falsified at Step 0. If any premise marked
**HALTING** is falsified, execution stops, no verdict is issued, and this file is
revised and re-frozen before any further data is read (Premise Invalidation Gate).

| ID | Premise | Halting? | Status at freeze |
|----|---------|----------|------------------|
| `P1` | The archive at DOI `10.5281/zenodo.13273331` contains exactly 420 surface-code experiments spanning `d ∈ {3, 5, 7}` | **HALTING** | Untested |
| `P2` | Per-shot detection-event counts are recoverable from the archive with no preprocessing beyond decoding the packed detector records | **HALTING** | Untested |
| `P3` | The same 420 experiments underlie `W1`, `W2`, `W3` and `W4` | **HALTING** | Untested |
| `P4` | The author's repository contains no committed output file from `willow/willow_fano_analysis.py` | Non-halting | **FALSIFIED-AS-PREDICTED (measured 2026-09-03)** |
| `P5` | The archive bytes are identical to those used in `willow-decoder-audit-s1` | Non-halting | Untested |

### Note on `P4`

The source states that all output files are included in the repository. Measured
inventory of `outputs/` at commit fetched 2026-09-03:

```text
./outputs/test_tau1.json
./outputs/triangle_results.json
```

No output artefact from any script under `willow/` is present. `P4` is therefore
recorded as a measured condition of the artefact at freeze time, and is the reason
this instance exists. It is **not** a verdict on `W1`–`W4` and does not by itself
falsify any of them.

---

## 4. Decision Rules — Frozen Thresholds

Thresholds are fixed here and may not be adjusted after any data is read.

### Primary — `W1`

Let `F_rec` be the recomputed overall Fano factor under §2.

| Rule | Condition | Verdict on `W1` |
|------|-----------|-----------------|
| `R1` | `|F_rec − 2.42| < 0.005` | `Verified` |
| `R2` | `0.005 ≤ |F_rec − 2.42| ≤ 0.36` | `Verified with Limitations` |
| `R3` | `|F_rec − 2.42| > 0.36` | `Not Verified` |
| `R4` | `P1`, `P2` or `P3` falsified | No verdict; halt and re-freeze |

`0.005` is the half-width of the last printed digit: a value that rounds to `2.42` at
two decimal places. `0.36` is the spread printed in the source and is used here only
as the outer admissible band, not as an uncertainty on the mean.

### Secondary — `W2`, `W3`, `W4`

| Rule | Condition | Verdict |
|------|-----------|---------|
| `R5` | All three per-distance values reproduce within `< 0.005` | `W2: Verified` |
| `R6` | Any per-distance value outside `± 0.05` | `W2: Not Verified` |
| `R7` | Recomputed ANOVA F-statistic within `± 0.5` of `59.1` | `W3: Verified` |
| `R8` | Recomputed `t` within `± 2` of `+80` | `W4: Verified` |

Values falling between the Verified and Not Verified bands in `R5`/`R6` receive
`Verified with Limitations`. `R7` and `R8` failing their band yield `Not Verified`
for that sub-claim only.

### Scope test — pre-registered, not exploratory

The source itself reports (§II F, Fig. 3) that the per-experiment Fano factor rises
with the number of QEC rounds, from `1.65–1.82` at `r = 1` to `2.4–3.3` at `r = 250`.
`F_overall` is an unweighted mean over an experiment population with heterogeneous `r`.
The question admitted here is whether the aggregate reported in the Abstract and in
Table III denotes a property of the hardware or a property of the archive's round
distribution.

Let `F_native` be `F_overall` computed over the archive as-is, and `F_uniform` be the
same estimator after reweighting experiments to be uniform over the distinct `r`
values present.

| Rule | Condition | Verdict on scope |
|------|-----------|------------------|
| `R9` | `|F_uniform − F_native| ≤ 0.36` | Aggregate is stable under reweighting; `W1` stands as reported |
| `R10` | `|F_uniform − F_native| > 0.36` | Aggregate is composition-dependent; the number is `Unfalsifiable-as-Stated` **as a hardware property**, while its verdict as an archive statistic under `R1`–`R3` is unaffected |

`R9`/`R10` do not overturn `R1`–`R3`. They record what the number denotes. The source
discusses round-dependence in its own text; `R10` firing would therefore not be a
finding against the analysis, only against the scope at which the number is carried
into the Abstract and Table III.

---

## 5. Data and Code Provenance (L0)

| Artefact | Identifier | Licence | Access date |
|----------|-----------|---------|-------------|
| Google Willow surface-code dataset | Zenodo DOI `10.5281/zenodo.13273331` | `Creative Commons Attribution 4.0 International (CC BY 4.0)` | 2026-09-01 (cleared in `willow-decoder-audit-s1`) |
| Author's analysis code | `github.com/SelinaAliens/The_Rotation_Gap_Is_Not_An_Error` | `MIT License`, `Copyright (c) 2026 Selina Stenberg` | 2026-09-03 |
| Source publication | `arXiv:2604.11963v1` | `Creative Commons Attribution 4.0 International (CC BY 4.0)` (`http://creativecommons.org/licenses/by/4.0/`) | 2026-09-03 |

Archive integrity pin, carried over from `willow-decoder-audit-s1`:

```text
archive MD5: 21fa6ad35b395d838ebcdbc92e364a12
archive size: 5716907033 bytes
```

Raw data does not enter this repository. A `data_manifest.json` with SHA-256 digests
of every consumed record is committed instead, and the harness aborts on any digest
mismatch against the committed manifest. A printed verification string is admissible
only where a comparison against a pinned value actually executes.

---

## 6. Determinism Requirement

The verdict is admissible only if the harness satisfies recreation-plus-identity:
rename the results directory, re-run from a clean git checkout in the environment
declared by `requirements-minimal.txt`, and diff recursively. The output file must be
**recreated** byte-identical. Identity without recreation is not a determinism proof.

---

## 7. Explicitly Out of Scope

No verdict is issued, implied, or transferable to any of the following. They are
named here so that no reader can construe silence as endorsement.

- All IBM Eagle r3 claims: `F = 0.856 ± 0.03`, `t = −131`, ANOVA `p = 0.79`, linear
  burst scaling `R² = 0.9999`, `T₁`/`T₂` Hurst exponents. These derive from a
  different dataset (Zenodo DOI `10.5281/zenodo.17881116`) with a separate, uncleared L0.
- The regime classifier decoder and its reported `7–19%` logical-error-rate improvement,
  including the null result reported on Willow.
- The mixed binary/ternary error model and the ternary fraction `f = 1 − F`.
- Appendix A in its entirety, including the identity `α_s = F / 7 = 5/42`, the
  correction term `1/936`, and any comparison to the PDG value.
- Every companion publication cited in the source, including but not limited to the
  derivations of the fine-structure constant, the Standard Model gauge group from
  `PSL(2,7)`, the Yang–Mills mass gap, and the Klein quartic construction.
- The direct IBM hardware validation runs (§II E) and the `rotation_gap_is_flat`
  repository.

A `Verified` verdict on `W1` would mean one thing only: that the number `2.42` is
recomputable from the public archive using the author's published estimator. It would
carry no weight on the interpretation placed on that number anywhere in the source or
its companion corpus.

---

## 8. What Would Falsify This Audit's Own Result

- Any byte of the archive read by this instance before this file's freeze commit.
- A recomputation that cannot be reproduced byte-identically from a clean checkout.
- Any digest in `data_manifest.json` that is written rather than compared.
- Any adjustment to the thresholds in §4 after data is read.

---

## 9. Governance

- Execution occurs only on branch `instances/rotation-gap-fano-s1`. Direct commits to
  `main` by any agent are prohibited.
- Maximum status any agent may assign this work is `SPREMNO ZA GEJT`.
- The word `Ratified` may enter this file only in a commit made after the human
  operator's merge action.
- Controlled verdict vocabulary: `Verified` | `Verified with Limitations` |
  `Not Verified` | `Not Demonstrated` | `Unfalsifiable-as-Stated` | `Deferred`.

---

*VolMax Studio Lab · Nestorov, Ivan · ORCID 0009-0006-7940-9539*
