# Rotation Gap Willow Fano Factor Audit (`rotation-gap-fano-s1`)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Source Dataset DOI](https://img.shields.io/badge/Source%20Dataset%20DOI-10.5281%2Fzenodo.13273331-blue)](https://doi.org/10.5281/zenodo.13273331)

Pre-registered independent baseline audit and mathematical reproduction of the syndrome noise Fano factor analysis published by Selina Stenberg (*The Rotation Gap Is Not An Error*, arXiv:2604.11963v1, Section II F & Table III) computed from 420 raw surface-code detector telemetry runs in the Google Willow dataset (`10.5281/zenodo.13273331`).

---

## 1. Central Claim Under Audit

Stenberg (2026) reports that syndrome detection events on the Google Willow processor exhibit super-Poissonian statistics with an overall Fano factor $F = 2.42 \pm 0.36$ ($N = 420$), increasing monotonically with code distance ($d=3 \to 2.29$, $d=5 \to 2.59$, $d=7 \to 2.80$, ANOVA $F = 59.1, p \approx 0$).

**This audit evaluates whether Stenberg's published figures recompute directly from raw physical detector records under pre-frozen decision rules.**

---

## 2. What Would Falsify It (Pre-Frozen Decision Rules)

Evaluation criteria were pre-registered and cryptographically locked in [`PREREGISTRATION.md`](PREREGISTRATION.md) (Commit [`ff84608`](https://github.com/VolMax-Studio/rotation-gap-fano-s1/commit/ff84608)):

* **Claim W1 (Overall Fano Factor):** $|F_{\text{rec}} - 2.42| < 0.005 \implies$ **`Verified`** ($|F_{\text{rec}} - 2.42| > 0.36 \implies$ `Not Verified`).
* **Claim W2 (Per-Distance Fano):** All 3 distances ($d \in \{3, 5, 7\}$) within $< 0.005 \implies$ **`Verified`** (any $> 0.05 \implies$ `Not Verified`).
* **Claim W3 (One-way ANOVA):** $|F_{\text{stat}} - 59.1| \le 0.5 \implies$ **`Verified`**.
* **Claim W4 (One-sample t-statistic vs $F=1$):** $|t - 80| \le 2.0 \implies$ **`Verified`**.

---

## 3. What Was Measured (Audit Results)

```text
========================================================================================================================
ROTATION GAP WILLOW FANO FACTOR AUDIT RESULTS (420 Experiments, 14 Subgrids, 15 Rounds, 2 Bases)
========================================================================================================================
CLAIM               | RECOMPUTED                  | PUBLISHED           | VERDICT
--------------------+-----------------------------+---------------------+------------------------------------------------
W1 (Overall Fano)   | 2.4157 +/- 0.3620           | 2.42 +/- 0.36       | Verified (Rule R1: |2.4157 - 2.42| = 0.0043 < 0.005)
W2 (d=3 / 5 / 7)    | 2.2942 / 2.5935 / 2.7978    | 2.29 / 2.59 / 2.80  | Verified (Rule R5: max |delta| = 0.0042 < 0.005)
W3 (One-Way ANOVA)  | F = 59.1337 (p = 2.46e-23)  | F = 59.1 (p ~ 0)    | Verified (Rule R7: |59.1337 - 59.1| = 0.0337 <= 0.5)
W4 (One-Sample t)   | t = +80.15                  | t = +80             | Verified (Rule R8: |80.15 - 80| = 0.1510 <= 2.0)
--------------------+-----------------------------+---------------------+------------------------------------------------
SCOPE TEST (R9/R10) | Aggregate stable under reweighting (null result: threshold 0.36 exceeds composition delta 0.146)
========================================================================================================================
```

---

## 4. Key Findings & Epistemic Boundaries

1. **Numerical Reproducibility of Table III:**
   * All 4 reported numbers reproduce within pre-registered tight numerical tolerance from raw physical detector bitstreams (`detection_events.b8` and `circuit_ideal.stim`).
2. **Archive Composition vs Hardware Invariance ([`LIMITATIONS.md`](LIMITATIONS.md)):**
   * The overall figure $F = 2.42$ is an unweighted arithmetic mean over an archive consisting of 64.3% $d=3$ (9 patches), 28.6% $d=5$ (4 patches), and 7.1% $d=7$ (1 patch).
   * Reweighting equally across code distances yields $F_{\text{uniform}} = 2.56$. The reported $2.42$ denotes the composition of Google's public archive.
3. **Strict Epistemic Isolation:**
   * Zero endorsement, validation, or evaluation is transferred to any theoretical physics interpretations, standard model identities, or IBM hardware claims outside Section II F.

---

## 5. Provenance & Software Verification

* **Pre-Registration Commit:** [`ff84608`](https://github.com/VolMax-Studio/rotation-gap-fano-s1/commit/ff84608)
* **Manifest Verification:** 1260/1260 SHA-256 digests pinned in [`data_manifest.json`](data_manifest.json).
* **Deterministic Results:** Canonical output recorded in [`results/results.json`](results/results.json).

---

## 6. Reproduce It

```bash
pip install -r requirements-minimal.txt
python3 reproduce.py --archive /path/to/google_105Q_surface_code_d3_d5_d7.zip
```
