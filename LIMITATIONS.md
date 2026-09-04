# Limitations & Scope Analysis — `rotation-gap-fano-s1`

> **Document Status:** SPREMNO ZA GEJT (Draft — not ratified)  
> **Instance:** `rotation-gap-fano-s1`  
> **Source Target:** Stenberg (2026), arXiv:2604.11963v1, Section II F & Table III  

---

## 1. Scope Test & Archive Composition Analysis (R9 / R10)

Under pre-registered rule `R9`/`R10`, we evaluated whether the aggregate overall Fano factor $F = 2.42$ denotes an intrinsic hardware physical constant or an empirical statistic of the archive's specific subgrid distance composition.

### Empirical Findings:
1. **Archive Subgrid Distribution:**
   - Code distance $d = 3$: 270 experiments (**64.3%** of archive) $\to F_{d=3} = 2.2942$
   - Code distance $d = 5$: 120 experiments (**28.6%** of archive) $\to F_{d=5} = 2.5935$
   - Code distance $d = 7$: 30 experiments (**7.1%** of archive) $\to F_{d=7} = 2.7978$
2. **Reweighted Aggregate Comparison:**
   - **Native Unweighted Mean ($F_{\text{native}}$):** $2.4157 \approx 2.42$
   - **Uniformly Reweighted across Distance ($F_{\text{uniform, distance}}$):** $\frac{2.2942 + 2.5935 + 2.7978}{3} = \mathbf{2.5618}$
   - **Composition Delta:** $|\Delta| = 0.1461$
3. **Threshold Sensitivity Limitation:**
   - The pre-registered threshold ($0.36$) was chosen based on the published sample population standard deviation rather than the reweighting sensitivity scale. Because $0.1461 \le 0.36$, rule `R9` fired formally.
   - However, the mathematical calculation proves that $F = 2.42$ is heavily weighted toward $d=3$ (9 patches vs 1 patch at $d=7$). An equal-distance representation shifts the mean to $2.56$.

---

## 2. Estimator and Dependency Lineage Boundaries

1. **ddof=1 Sample Variance:** The author's script uses `var_c = np.var(counts, ddof=1)` (line 58). This is sample variance per shot count vector.
2. **scipy.stats ANOVA:** Claim `W3` relies on `scipy.stats.f_oneway` (line 242) yielding $F = 59.13$ ($p = 2.46 \times 10^{-23}$), which was recomputed identically with zero external discrepancies.
3. **Strict Epistemic Isolation:** This verification applies strictly to the numerical reproducibility of Table III / Section II F of arXiv:2604.11963v1 from raw Google Willow telemetry. As pre-registered in Section 7 of `PREREGISTRATION.md`, zero endorsement or evaluation is implied or transferred to any companion theoretical physics claims (e.g. Standard Model gauge groups, $\alpha_s$, mass gaps, or IBM Eagle datasets).
