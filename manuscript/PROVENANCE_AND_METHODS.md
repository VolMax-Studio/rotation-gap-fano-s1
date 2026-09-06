# Implementation Provenance & Control-Flow Specification (`rotation-gap-fano-s1`)

> **ReScience C Replication Category:** Partial Replication (`W1`–`W4` of arXiv:2604.11963v1)  
> **Provenance Classification:** `MIXED_IMPLEMENTATION` (Independently implemented vectorized fast harness + Author-derived reference operations for bitwise equivalence verification and underspecified detail interpretation).

---

## 1. Provenance Breakdown Table

| Pipeline Component / Operation | Source Lineage / Author File Reference | Harness Implementation (`reproduce.py`) | Classification & Verification Mode |
| :--- | :--- | :--- | :--- |
| **Archive Layout & Path Discovery** | `willow_fano_analysis.py` (lines 32, 48–54) | `enumerate_experiments()` (lines 237–255) | **Author-Derived:** Traverses `metadata.json` and parses `parts[1]` (patch) and `parts[:4]` (prefix for `.stim` and `.b8`). |
| **Detector Count Extraction** | `willow_fano_analysis.py` (line 28) | `count_detectors()` (lines 346–349) | **Author-Derived:** Substring count of `DETECTOR` in `circuit_ideal.stim`. |
| **Primary Bitstream Popcount Decoder** | Paper §II F description (packed binary detector bits) | `read_detection_counts_fast()` (lines 363–371) | **Independently Implemented:** Vectorized bit unpack (`np.unpackbits(..., bitorder="little")`) and row sum across shots. Default production path. |
| **Reference Bitstream Popcount Decoder** | `willow_fano_analysis.py` (lines 14–23) | `read_detection_counts_author()` (lines 351–360) | **Author-Derived:** Nested byte/bit shift loop (`(byte_col >> bit) & 1`). Activated strictly under `--verify-popcount N` to prove exact bitwise equality. |
| **Per-Shot Event Sample Variance** | `willow_fano_analysis.py` (line 58: `np.var(..., ddof=1)`) | `step0_and_compute()` (line 429) | **Author-Derived:** `ddof=1` convention for unbiased sample variance estimator. |
| **Per-Experiment Fano Estimator** | `willow_fano_analysis.py` (line 59: `var_c / mean_c`) | `step0_and_compute()` (line 430) | **Author-Derived:** Direct evaluation of $F_i = \text{Var}(c) / \text{Mean}(c)$. |
| **Overall Fano Factor $F$** | `willow_fano_analysis.py` (line 97: `np.mean(all_fanos)`) | `step0_and_compute()` / Results | **Author-Derived:** Unweighted arithmetic mean over admitted experiments. |
| **Standard Error of the Mean** | `willow_fano_analysis.py` (line 93: `np.std / sqrt(N)`) | `step0_and_compute()` (line 470) | **Author-Derived:** Sample standard error of per-experiment Fano distribution. |
| **One-Sample $t$-statistic vs Poisson** | `willow_fano_analysis.py` (line 94: `(mean - 1.0) / se`) | `step0_and_compute()` (line 471) | **Author-Derived:** $t$-score against theoretical Poisson variance ($F=1$). |
| **Per-Distance Fano Aggregates** | `willow_fano_analysis.py` (lines 235–236) | `step0_and_compute()` (lines 476–481) | **Author-Derived:** Unweighted means for subsets $d=3, 5, 7$. |
| **One-Way ANOVA across Distances** | `willow_fano_analysis.py` (line 242: `sp_stats.f_oneway`) | `step0_and_compute()` (line 484) | **Author-Derived:** ANOVA $F$-statistic and $p$-value across distance groups. |
| **Premise Invalidation Gate ($P_1$–$P_5$)** | Protocol P10 Standard | `pin_preregistration()`, `pin_archive()`, `step0_and_compute()` | **Independently Implemented:** Halts execution if archive cardinality, layout, or tiling fail. |
| **Cryptographic Manifest Pinning** | Protocol P10 Standard | `verify_manifest()`, `build_manifest()` (lines 268–340) | **Independently Implemented:** Bit-for-bit SHA-256 verification of 1,260 archive members. |
| **Automated Decision Engine ($R_1$–$R_{10}$)** | Protocol P10 Standard | `apply_verdict_rules()` (lines 494–555) | **Independently Implemented:** Mechanical threshold comparisons against pre-registered bands. |
| **Determinism & Reproducibility Harness** | Protocol P10 Standard | Automated test suite / CI | **Independently Implemented:** Byte-identical JSON reproduction from clean environment. |

---

## 2. Decoder Equivalence & Activation Condition

The primary execution path utilizes `read_detection_counts_fast` for all 420 experiments. The author-derived decoder `read_detection_counts_author` is maintained inside `reproduce.py` for epistemic validation:

* **Activation Condition:** Triggered if and only if `--verify-popcount <N>` is passed on the command line.
* **Control Flow (`reproduce.py` lines 420–426):**
  ```python
  if verify_popcount and len(equivalence_checks) < verify_popcount:
      ref = read_detection_counts_author(raw, n_det, shots)
      equal = bool(np.array_equal(counts, ref))
      equivalence_checks.append({"member": e["det_path"], "equal": equal})
      if not equal:
          fail(f"popcount implementations disagree on {e['det_path']}; "
               f"the substituted operation is not the author's operation")
  ```
* **Empirical Verification:** 100% of tested members yielded `equal == True`, confirming that vectorized LSB-first bit-unpacking produces identical integer detection event counts per shot without numerical drift.

---

## 3. Deliberate Scope Justification ($W_1$–$W_4$) & Scope Exit Boundaries

1. **Admitted Claims ($W_1$–$W_4$):**
   * $W_1$: Overall Willow Fano factor $F = 2.42 \pm 0.36$ ($N=420$).
   * $W_2$: Distance scaling ($d=3 \to 2.29, d=5 \to 2.59, d=7 \to 2.80$).
   * $W_3$: One-way ANOVA $F = 59.1, p \approx 0$.
   * $W_4$: $t$-statistic against Poisson $t = +80$.
2. **Exclusions (PREREGISTRATION.md §7):**
   * IBM Eagle r3 telemetry ($F=0.856$) — derives from unverified separate dataset (`10.5281/zenodo.17881116`).
   * Regime classifier logical error rate benchmarks.
   * Companion theoretical physics conjectures (fine-structure constant $\alpha_s$, gauge groups, mass gap).
   * Distances $d=9, 11$ (not present in the public 105Q Willow archive `10.5281/zenodo.13273331`).
