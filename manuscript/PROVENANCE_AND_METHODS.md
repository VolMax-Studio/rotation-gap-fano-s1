# Implementation Provenance & Control-Flow Specification (`rotation-gap-fano-s1`)

> **Governing Semantic Decision:** `PARTIAL REPLICATION WITH MIXED IMPLEMENTATION PROVENANCE`  
> **ReScience C Metadata Type:** `Replication`  
> **Scientific Scope:** Strictly Claims $W_1$–$W_4$ from arXiv:2604.11963v1 (Section II F & Table III)  
> **Target Dataset:** Zenodo DOI `10.5281/zenodo.13273331` (105-qubit Google Willow, $N=420, d \in \{3, 5, 7\}$)

---

## 1. Three-Layer Provenance Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER A — INDEPENDENTLY IMPLEMENTED INFRASTRUCTURE                         │
│ • Archive integrity pinning (MD5, size) and PREREGISTRATION.md SHA-256 pin  │
│ • Cryptographic SHA-256 manifest verification (data_manifest.json, 1,260)   │
│ • Step 0 premise checking harness and halting invalidation gates (P1–P5)    │
│ • Primary fast vectorized popcount decoder                                  │
│   (read_detection_counts_fast: np.unpackbits with bitorder="little")       │
│ • Mechanical decision logic & automated tolerance rules (R1–R10)           │
│ • Determinism & CI harness (byte-identical JSON reproduction verification) │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER B — AUTHOR-DERIVED CONVENTIONS & ESTIMATOR (ANALYTICAL PATH)         │
│ (Path/counting conventions & operations transcribed under PREREG §2)        │
│ • Experiment path/layout convention (willow_fano_analysis.py lines 32, 48–54│
│   in enumerate_experiments())                                              │
│ • Detector count string extraction (count_detectors() from Stim circuit)   │
│ • Sample variance with Bessel correction (np.var(counts, ddof=1))          │
│ • Per-experiment Fano factor computation (var_c / mean_c)                  │
│ • Overall aggregate unweighted mean (np.mean(all_fanos))                   │
│ • Standard error of the mean (np.std(all_fanos) / sqrt(N))                 │
│ • One-sample t-statistic vs Poisson F=1 ((mean - 1.0) / se)                │
│ • Per-distance mean aggregates (np.mean(fanos))                            │
│ • One-way ANOVA across distance groups (sp_stats.f_oneway)                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER C — AUTHOR-DERIVED REFERENCE DECODER OFF ANALYTICAL PATH              │
│ • Reference bit-shift decoder loop (read_detection_counts_author)          │
│ • Used exclusively off-path under --verify-popcount to prove 10/10 exact   │
│   integer equality (Δ = 0) with the fast vectorized decoder                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Definitive Provenance Statement

> **"The primary detector decoding path is independently implemented; the statistical estimator on the analytical path deliberately transcribes the author's published operations under the preregistered design."**

*We do not claim a pure independent reimplementation of the analytical estimator, a whole-paper replication, whole Table III replication, IBM hardware replication, or validation of theoretical physics conjectures.*

---

## 3. Arithmetic Verification Summary (Canonical from `results/results.json`)

| Claim ID | Source Reported Value | Recomputed Value | Absolute Delta $|\Delta|$ | Pre-Registered Tolerance Band | Verdict |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **$W_1$** | $F = 2.42 \pm 0.36$ | $F = 2.4157 \pm 0.3620$ | $0.0043$ | Rule $R_1$: $|\Delta| < 0.005$ | **`Verified`** |
| **$W_2$** | $d=3 \to 2.29$ | $d=3 \to 2.2942$ | $0.0042$ | Rule $R_5$: $|\Delta| < 0.005$ | **`Verified`** |
| **$W_2$** | $d=5 \to 2.59$ | $d=5 \to 2.5935$ | $0.0035$ | Rule $R_5$: $|\Delta| < 0.005$ | **`Verified`** |
| **$W_2$** | $d=7 \to 2.80$ | $d=7 \to 2.7978$ | $0.0022$ | Rule $R_5$: $|\Delta| < 0.005$ | **`Verified`** |
| **$W_3$** | $\text{ANOVA } F = 59.1$ | $\text{ANOVA } F = 59.1337$ | $0.0337$ | Rule $R_7$: $|\Delta| \le 0.500$ | **`Verified`** |
| **$W_4$** | $t = +80.0$ | $t = +80.1510$ | $0.1510$ | Rule $R_8$: $|\Delta| \le 2.000$ | **`Verified`** |

* One-way ANOVA $p$-value: $p = 2.4624 \times 10^{-23}$ (source printed "$p \approx 0$").
* Total admitted experiments: $N = 420$ ($d=3: 270, d=5: 120, d=7: 30$).

---

## 4. Epistemic Findings & Limitations

1. **Zero-Power Round Sensitivity Test ($R_9/R_{10}$):**
   * Formula: $|F_{\text{uniform, rounds}} - F_{\text{native}}| = 0.000000$.
   * Cause: Google Willow archive contains exactly $N_r = 28$ samples for all 15 round configurations ($r \in [1, 250]$). The test fired formally due to experimental design balance, not empirical round invariance.
2. **Exploratory Distance Composition Shift:**
   * Equal distance weighting ($1/3$ per distance):
     $$F_{\text{distance-uniform}} = \frac{2.2942 + 2.5935 + 2.7978}{3} = \mathbf{2.5618} \quad (|\Delta| = 0.1461)$$
   * Finding: The headline figure $F = 2.42$ reflects the $64.29\%$ dominance of distance $d=3$ experiments in Google's public archive.
