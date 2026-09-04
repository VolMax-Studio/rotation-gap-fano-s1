# Failure Register — `rotation-gap-fano-s1`

| Entry ID | Date (UTC) | Severity | Category | Description | Remediation / Status |
|---|---|---|---|---|---|
| `#001` | 2026-09-04 | High | Pre-Registration Experimental Design Defect | **Zero-Power Scope Test:** Pre-registered scope rule `R9`/`R10` specified testing sensitivity to QEC round counts ($r \in [1, 250]$). Because Google Willow archive has a perfectly balanced experimental design ($N_r = 28$ across all 15 rounds), $F_{\text{native}} \equiv F_{\text{uniform, rounds}}$ identically ($|\Delta| = 0.000000$). The test structurally guaranteed zero and had zero discriminatory power. | Logged in `FAILURES.md`. Clarified in `LIMITATIONS.md` §1 that `R9` fired formally due to balanced design. Distance-composition shift ($F=2.5618, |\Delta|=0.1461$) strictly demoted to `Exploratory (not pre-registered)`. |
