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
│ • Telemetry Ingestion & Path Discovery (traverse metadata.json)            │
│ • Cryptographic SHA-256 Manifest Verification (1,260 member digests)        │
│ • Premise & Halting Invalidation Gates (P1–P5)                             │
│ • Primary Fast Vectorized Binary Popcount Decoder                          │
│   (read_detection_counts_fast: np.unpackbits with bitorder="little")       │
│ • Mechanical Decision Logic & Automated Gate Rules (R1–R10)                │
│ • Determinism & CI Harness (byte-identical JSON recreation verification)   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER B — AUTHOR-DERIVED ESTIMATOR OPERATIONS ON ANALYTICAL PATH           │
│ (Deliberately transcribed under PREREGISTRATION.md §2 to execute the        │
│ author's published estimator rather than substitute an alternative)         │
│ • Sample Variance with ddof=1 (line 58: np.var(counts, ddof=1))             │
│ • Per-Experiment Fano Factor (line 59: var_c / mean_c)                     │
│ • Overall Aggregate Mean (line 97: np.mean(all_fanos))                     │
│ • Standard Error of the Mean (line 93: np.std(all_fanos) / sqrt(N))        │
│ • One-Sample t-statistic vs Poisson F=1 (line 94: (mean - 1.0) / se)       │
│ • Per-Distance Mean Aggregates (lines 235–236: np.mean(fanos))             │
│ • One-Way ANOVA across Distance Groups (line 242: sp_stats.f_oneway)       │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER C — AUTHOR-DERIVED REFERENCE DECODER OFF ANALYTICAL PATH              │
│ • Reference Bit-Shift Decoder Loop (lines 14–23: read_detection_counts_    │
│   author)                                                                  │
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
