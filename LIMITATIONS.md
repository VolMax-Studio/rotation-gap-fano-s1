# Limitations & Epistemic Analysis — `rotation-gap-fano-s1`

> **Document Status:** SPREMNO ZA GEJT (Draft — not ratified)  
> **Instance:** `rotation-gap-fano-s1`  
> **Source Target:** Stenberg (2026), arXiv:2604.11963v1, Section II F & Table III  

---

## 1. Pre-Registered Scope Test Analysis (R9 / R10 over QEC Rounds)

Under pre-registered rule `R9`/`R10` (PREREG §4, lines 133–135), the harness tested whether reweighting uniformly over the 15 distinct QEC round counts ($r \in [1, 250]$) shifts the overall aggregate $F$.

### Empirical Measurement from `results/results.json`:
```json
"scope": {
  "abs_difference": 0.0,
  "distinct_rounds": [1, 10, 13, 30, 50, 70, 90, 110, 130, 150, 170, 190, 210, 230, 250],
  "f_native": 2.4156874990071255,
  "f_uniform": 2.4156874990071255
}
```

### Pre-Registration Design Defect:
- **Zero-Power Test:** The Google Willow dataset is constructed with a perfectly balanced experimental design across rounds: exactly 28 experiments exist for every single one of the 15 round values ($28 \times 15 = 420$).
- **Mathematical Identity:** Because each round has an identical number of samples ($N_r = 28$), the unweighted mean over experiments is mathematically identical to the unweighted mean over rounds:
  $$F_{\text{native}} \equiv F_{\text{uniform, rounds}} \implies |\Delta| = 0.000000$$
- **Finding:** Rule `R9` fired formally ($0.0 \le 0.36$), but this was a structural zero resulting from the balanced archive design, not an empirical test of round insensitivity.

---

## 2. Exploratory Post-Hoc Analysis: Code Distance Composition (Not Pre-Registered)

> [!NOTE]
> **Exploratory (not pre-registered):** The following calculation is an exploratory mathematical decomposition of the published archive composition. It does NOT carry an `R9`/`R10` verdict.

While the archive is balanced across rounds, it is **heavily unbalanced across code distances**:

1. **Subgrid Population Distribution:**
   - Distance $d = 3$: 270 experiments (**64.29%** of archive, 9 patches $\times$ 2 bases $\times$ 15 rounds) $\to F_{d=3} = 2.2942$
   - Distance $d = 5$: 120 experiments (**28.57%** of archive, 4 patches $\times$ 2 bases $\times$ 15 rounds) $\to F_{d=5} = 2.5935$
   - Distance $d = 7$: 30 experiments (**7.14%** of archive, 1 patch $\times$ 2 bases $\times$ 15 rounds) $\to F_{d=7} = 2.7978$
2. **Exploratory Distance-Uniform Aggregate:**
   - **Native Unweighted Mean:** $F_{\text{native}} = \mathbf{2.4157} \approx 2.42$
   - **Equal-Distance Weighting ($1/3$ per distance):**
     $$F_{\text{uniform, distance}} = \frac{2.294204 + 2.593491 + 2.797827}{3} = \mathbf{2.5618}$$
   - **Exploratory Composition Shift:** $|\Delta_{\text{distance}}| = 0.1461$
3. **Epistemic Conclusion:**
   - The headline number $F = 2.42$ in Table III and the Abstract directly reflects the $d=3$ dominance of Google's public archive. If code distances are weighted equally, the aggregate mean shifts to $2.56$.

---

## 3. Estimator Lineage & Strict Scope Boundary

1. **Estimator Exactness:** The sample variance calculation employs `ddof=1` (`var_c = np.var(counts, ddof=1)`), exactly matching the author's script.
2. **Statistical Reproducibility:** One-way ANOVA ($F = 59.13, p = 2.46 \times 10^{-23}$) and one-sample $t$-test ($t = +80.15$) reproduce to sub-decimal precision.
3. **Strict Epistemic Isolation:** This audit proves the exact arithmetic reproducibility of Table III from raw detector bitstreams. In accordance with Section 7 of `PREREGISTRATION.md`, zero endorsement, validity, or evaluation is transferred to any companion theoretical physics conjectures (such as Standard Model gauge derivations, $\alpha_s$, or IBM Eagle datasets).
