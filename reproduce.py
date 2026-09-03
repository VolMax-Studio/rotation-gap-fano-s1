#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
reproduce.py — instance `rotation-gap-fano-s1`

Single entry point. Recomputes W1-W4 of arXiv:2604.11963v1 (Table III, Sec. II F)
from the Google Willow surface-code archive (Zenodo 10.5281/zenodo.13273331)
under the frozen decision rules in PREREGISTRATION.md.

Execution order is fixed and is not a style choice:

    0. pin PREREGISTRATION.md  (thresholds cannot have moved after data was read)
    1. pin the archive          (MD5 + byte size, PREREG Sec.5)
    2. verify data_manifest.json (COMPARE every digest; never write on this path)
    3. Step 0 premises P1/P2/P3/P5 (HALTING -> no verdict, exit 2)
    4. compute (PREREG Sec.2 estimator, taken from the author's own script)
    5. apply R1-R10 mechanically
    6. write results/results.json  (pure function of archive + this file)

Manifest construction is a separate, explicit invocation (--build-manifest).
The default path never writes a digest, only compares one (PREREG Sec.8).

Usage:
    python reproduce.py --archive PATH/TO/google_105Q_surface_code_d3_d5_d7.zip
    python reproduce.py --archive PATH --build-manifest      # once, then commit
    python reproduce.py --archive PATH --verify-popcount 8   # estimator equivalence proof

Exit codes:
    0  completed, verdicts written
    1  integrity failure (pin, manifest, missing input) — no verdict
    2  HALT under the Premise Invalidation Gate — no verdict
"""

import argparse
import hashlib
import json
import os
import platform
import sys
import zipfile
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np
import scipy
from scipy import stats as sp_stats

# ─────────────────────────────────────────────────────────────────────────────
# FROZEN CONSTANTS
# Every value below is transcribed from PREREGISTRATION.md at commit ff84608
# with its section cited. Nothing here may be edited after data has been read;
# PREREG_SHA256 is what makes that statement checkable rather than promised.
# ─────────────────────────────────────────────────────────────────────────────

INSTANCE = "rotation-gap-fano-s1"

# sha256 of PREREGISTRATION.md as committed at ff84608 (git blob ef2b944).
PREREG_SHA256 = "8fa26d609e3c4cbe9b1681ca05c8cfbcadb09a64b83b5546a054e703a098098f"

# PREREG Sec.5 — archive integrity pin carried over from willow-decoder-audit-s1.
ARCHIVE_MD5 = "21fa6ad35b395d838ebcdbc92e364a12"
ARCHIVE_SIZE_BYTES = 5716907033

# PREREG Sec.1 — sub-claims at the precision printed in the source.
W1_REPORTED_F = 2.42
W1_REPORTED_SPREAD = 0.36
W1_REPORTED_N = 420
W2_REPORTED = {3: 2.29, 5: 2.59, 7: 2.80}
W3_REPORTED_ANOVA_F = 59.1
W4_REPORTED_T = 80.0

# PREREG Sec.4 — thresholds.
R1_BAND = 0.005          # |F_rec - 2.42| <  0.005            -> Verified
R3_BAND = 0.36           # |F_rec - 2.42| >  0.36             -> Not Verified
R5_BAND = 0.005          # all three per-distance |d| < 0.005 -> W2 Verified
R6_BAND = 0.05           # any per-distance |d| > 0.05        -> W2 Not Verified
R7_BAND = 0.5            # |ANOVA F - 59.1| <= 0.5            -> W3 Verified
R8_BAND = 2.0            # |t - 80|         <= 2              -> W4 Verified
R9_BAND = 0.36           # |F_uniform - F_native| <= 0.36     -> aggregate stable

# PREREG Sec.3 — P1.
P1_EXPECTED_N = 420
P1_EXPECTED_DISTANCES = {3, 5, 7}

# PREREG Sec.3 — P4 was measured at freeze time against the author's Git
# repository, not against the archive. Its status is carried, not re-measured
# here: re-measuring a Git tree from inside the data harness would let a value
# obtained after the freeze overwrite a value obtained before it.
P4_STATUS_AT_FREEZE = "FALSIFIED-AS-PREDICTED (measured 2026-09-03)"

VERDICT_VOCAB = {
    "Verified",
    "Verified with Limitations",
    "Not Verified",
    "Not Demonstrated",
    "Unfalsifiable-as-Stated",
    "Deferred",
}

# ─────────────────────────────────────────────────────────────────────────────
# ESTIMATOR PROVENANCE
#
# PREREG Sec.2 freezes the estimator by pointing at willow/willow_fano_analysis.py
# in github.com/SelinaAliens/The_Rotation_Gap_Is_Not_An_Error (MIT, 245 lines).
# The lines this harness reimplements are recorded here and echoed into
# results.json, because two of them (W2, W3) lie OUTSIDE the code block quoted
# in Sec.2 and a reader must be able to see that without reading this file.
# ─────────────────────────────────────────────────────────────────────────────

ESTIMATOR_LINES = {
    "per_experiment_fano": {
        "line": 59,
        "code": "fano = var_c / mean_c if mean_c > 0 else np.nan",
        "in_frozen_block": True,
    },
    "per_experiment_variance": {
        "line": 58,
        "code": "var_c = np.var(counts, ddof=1)",
        "in_frozen_block": False,
        "note": "ddof=1 is not stated in the Sec.2 prose restatement; it is the "
                "author's operation and is what makes F_i a sample-variance ratio.",
    },
    "overall_se": {
        "line": 93,
        "code": "se = np.std(all_fanos) / np.sqrt(len(all_fanos))",
        "in_frozen_block": True,
    },
    "t_vs_poisson": {
        "line": 94,
        "code": "t_vs_1 = (np.mean(all_fanos) - 1.0) / se",
        "in_frozen_block": True,
    },
    "overall_fano": {
        "line": 97,
        "code": 'print(f"\\n  OVERALL: F = {np.mean(all_fanos):.4f} +/- '
                '{np.std(all_fanos):.4f}  (N = {len(all_fanos)})")',
        "in_frozen_block": True,
        "note": "PREREG Sec.2 renders line 97 as `F_overall = np.mean(all_fanos)`. "
                "The file at line 97 is the print statement above. The operation "
                "np.mean(all_fanos) is the same; the quotation is not verbatim.",
    },
    "per_distance_fano": {
        "line": 236,
        "code": 'print(f"    d={d}: {np.mean(fanos):.4f}")   # fanos from line 235',
        "in_frozen_block": False,
        "note": "W2 estimator. Not present in the Sec.2 code block.",
    },
    "anova_across_distances": {
        "line": 242,
        "code": "F_stat, p_anova = sp_stats.f_oneway(*groups)   # groups from line 240",
        "in_frozen_block": False,
        "note": "W3 estimator. Not present in the Sec.2 code block; introduces a "
                "scipy dependency that Sec.2 does not name.",
    },
}

RESULTS_FILENAME = "results.json"
MANIFEST_FILENAME = "data_manifest.json"
PREREG_FILENAME = "PREREGISTRATION.md"


# ─────────────────────────────────────────────────────────────────────────────
# Comparison primitives. Nothing prints a pass string that a comparison did not
# produce, and nothing continues past a failed comparison.
# ─────────────────────────────────────────────────────────────────────────────

def fail(msg):
    print(f"[FAIL] {msg}", file=sys.stderr)
    sys.exit(1)


def halt(msg):
    print(f"[HALT] Premise Invalidation Gate: {msg}", file=sys.stderr)
    print("[HALT] No verdict is issued. Revise and re-freeze PREREGISTRATION.md "
          "before reading further data (PREREG Sec.3, R4).", file=sys.stderr)
    sys.exit(2)


def compare(label, actual, expected):
    """Prints only what it has just compared."""
    if actual != expected:
        fail(f"{label}: expected {expected!r}, measured {actual!r}")
    print(f"[MATCH] {label}: {actual!r}")
    return True


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def hash_file(path, algos=("md5", "sha256"), chunk=1 << 22):
    hs = {a: hashlib.new(a) for a in algos}
    size = 0
    with open(path, "rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            size += len(block)
            for h in hs.values():
                h.update(block)
    return {a: h.hexdigest() for a, h in hs.items()}, size


# ─────────────────────────────────────────────────────────────────────────────
# Step 0 pins
# ─────────────────────────────────────────────────────────────────────────────

def pin_preregistration(repo_root):
    """PREREG Sec.8: 'Any adjustment to the thresholds in Sec.4 after data is read'
    falsifies the audit. This makes that falsifiable at run time."""
    path = os.path.join(repo_root, PREREG_FILENAME)
    if not os.path.isfile(path):
        fail(f"{PREREG_FILENAME} not found at {path}. The harness will not run "
             f"without the frozen rules it claims to execute.")
    with open(path, "rb") as fh:
        digest = sha256_bytes(fh.read())
    compare("PREREGISTRATION.md sha256", digest, PREREG_SHA256)
    return digest


def pin_archive(archive_path):
    """PREREG Sec.5. Also settles P5 (same bytes as willow-decoder-audit-s1)."""
    if not os.path.isfile(archive_path):
        fail(f"archive not found: {archive_path}")
    digests, size = hash_file(archive_path)
    compare("archive size_bytes", size, ARCHIVE_SIZE_BYTES)
    compare("archive md5", digests["md5"], ARCHIVE_MD5)
    return {"md5": digests["md5"], "sha256": digests["sha256"], "size_bytes": size}


# ─────────────────────────────────────────────────────────────────────────────
# Experiment enumeration — the author's own path convention
# (willow_fano_analysis.py lines 32, 48-54)
# ─────────────────────────────────────────────────────────────────────────────

def enumerate_experiments(z):
    """Returns a list of dicts in the author's iteration order: sorted(metas)."""
    metas = sorted(n for n in z.namelist() if n.endswith("metadata.json"))
    experiments = []
    for meta_path in metas:
        parts = meta_path.split("/")
        if len(parts) < 5:
            fail(f"unexpected archive layout for {meta_path!r}: the author's "
                 f"script indexes parts[1] and parts[:4]; this path has "
                 f"{len(parts)} components")
        prefix = "/".join(parts[:4])
        experiments.append({
            "meta_path": meta_path,
            "patch": parts[1],
            "stim_path": prefix + "/circuit_ideal.stim",
            "det_path": prefix + "/detection_events.b8",
        })
    return experiments


def consumed_members(experiments):
    members = []
    for e in experiments:
        members.extend([e["meta_path"], e["stim_path"], e["det_path"]])
    return sorted(members)


# ─────────────────────────────────────────────────────────────────────────────
# data_manifest.json — built once by an explicit invocation, compared always
# ─────────────────────────────────────────────────────────────────────────────

def build_manifest(z, experiments, archive_pin, manifest_path, force):
    if os.path.exists(manifest_path) and not force:
        fail(f"{manifest_path} already exists. Rebuilding a committed manifest "
             f"turns a comparison into a transcription. Pass --force only if you "
             f"intend to replace the pinned digests and can say why in the PR.")
    members = consumed_members(experiments)
    entries = {}
    for i, name in enumerate(members, 1):
        try:
            raw = z.read(name)
        except KeyError:
            fail(f"member referenced by the archive layout is absent: {name}")
        entries[name] = {"size": len(raw), "sha256": sha256_bytes(raw)}
        if i % 200 == 0 or i == len(members):
            print(f"  hashed {i}/{len(members)}", flush=True)

    manifest = {
        "manifest_version": "1.0.0",
        "instance": INSTANCE,
        "preregistration_sha256": PREREG_SHA256,
        "archive": archive_pin,
        "member_count": len(entries),
        "members": entries,
    }
    write_json(manifest_path, manifest)
    print(f"[WROTE] {manifest_path} ({len(entries)} digests). "
          f"Commit it before any run that carries a verdict.")


def verify_manifest(z, experiments, archive_pin, manifest_path):
    if not os.path.isfile(manifest_path):
        fail(f"{manifest_path} not found. A run without a committed manifest "
             f"cannot carry a verdict (PREREG Sec.5). Build it once with "
             f"--build-manifest, review it, commit it, then re-run.")
    with open(manifest_path, "rb") as fh:
        raw = fh.read()
    manifest = json.loads(raw.decode("utf-8"))
    manifest_sha = sha256_bytes(raw)

    compare("manifest.preregistration_sha256",
            manifest.get("preregistration_sha256"), PREREG_SHA256)
    compare("manifest.archive.md5",
            (manifest.get("archive") or {}).get("md5"), ARCHIVE_MD5)
    compare("manifest.archive.size_bytes",
            (manifest.get("archive") or {}).get("size_bytes"), ARCHIVE_SIZE_BYTES)
    compare("manifest.archive.sha256",
            (manifest.get("archive") or {}).get("sha256"), archive_pin["sha256"])

    listed = manifest.get("members") or {}
    expected_members = consumed_members(experiments)
    compare("manifest member set", sorted(listed.keys()), expected_members)

    mismatches = []
    for i, name in enumerate(expected_members, 1):
        raw_member = z.read(name)
        got = {"size": len(raw_member), "sha256": sha256_bytes(raw_member)}
        want = listed[name]
        if got["sha256"] != want.get("sha256") or got["size"] != want.get("size"):
            mismatches.append({"member": name, "manifest": want, "measured": got})
        if i % 200 == 0 or i == len(expected_members):
            print(f"  compared {i}/{len(expected_members)}", flush=True)

    if mismatches:
        for m in mismatches[:10]:
            print(f"  MISMATCH {m['member']}: manifest={m['manifest']} "
                  f"measured={m['measured']}", file=sys.stderr)
        fail(f"{len(mismatches)} of {len(expected_members)} member digests "
             f"disagree with the committed manifest")

    print(f"[MATCH] all {len(expected_members)} member digests equal the "
          f"committed manifest")
    return manifest_sha


# ─────────────────────────────────────────────────────────────────────────────
# Detector decoding (willow_fano_analysis.py lines 14-28)
# ─────────────────────────────────────────────────────────────────────────────

def count_detectors(z, stim_path):
    """Author line 28: substring count of 'DETECTOR' in circuit_ideal.stim."""
    return z.read(stim_path).decode().count("DETECTOR")


def read_detection_counts_author(raw, n_detectors, n_shots):
    """Author lines 14-23, unchanged."""
    bytes_per_shot = (n_detectors + 7) // 8
    data = np.frombuffer(raw, dtype=np.uint8).reshape(n_shots, bytes_per_shot)
    counts = np.zeros(n_shots, dtype=np.int32)
    for byte_idx in range(bytes_per_shot):
        byte_col = data[:, byte_idx].astype(np.int32)
        for bit in range(min(8, n_detectors - byte_idx * 8)):
            counts += (byte_col >> bit) & 1
    return counts


def read_detection_counts_fast(raw, n_detectors, n_shots):
    """Vectorised equivalent. This is integer popcount over the same bits in the
    same LSB-first order, so it is exactly equal to the author's loop — not
    approximately equal, and with no floating-point reassociation. --verify-popcount
    proves the equality on real archive members rather than asserting it."""
    bytes_per_shot = (n_detectors + 7) // 8
    data = np.frombuffer(raw, dtype=np.uint8).reshape(n_shots, bytes_per_shot)
    bits = np.unpackbits(data, axis=1, bitorder="little")[:, :n_detectors]
    return bits.sum(axis=1, dtype=np.int32)


# ─────────────────────────────────────────────────────────────────────────────
# Step 0 premises + computation
# ─────────────────────────────────────────────────────────────────────────────

def step0_and_compute(z, experiments, popcount_impl, verify_popcount):
    """P1/P2/P3 are checked here because they are properties of the data being
    read, not of the file system. Any HALTING failure exits before a verdict."""

    # ---- P1 (HALTING) -------------------------------------------------------
    n_experiments = len(experiments)
    if n_experiments != P1_EXPECTED_N:
        halt(f"P1 falsified: archive yields {n_experiments} metadata.json "
             f"experiments, PREREG Sec.3 requires exactly {P1_EXPECTED_N}")
    print(f"[MATCH] P1 experiment count: {n_experiments}")

    records = []
    by_distance = defaultdict(list)
    p2_defects = []
    equivalence_checks = []

    for i, e in enumerate(experiments):
        md = json.loads(z.read(e["meta_path"]))
        for key in ("distance", "rounds", "shots", "basis"):
            if key not in md:
                halt(f"P2 falsified: {e['meta_path']} has no {key!r} field; the "
                     f"author's script reads it at line 44-47")
        d, rounds, shots = md["distance"], md["rounds"], md["shots"]

        n_det = count_detectors(z, e["stim_path"])
        if n_det <= 0:
            halt(f"P2 falsified: {e['stim_path']} yields {n_det} DETECTOR tokens")

        raw = z.read(e["det_path"])
        bytes_per_shot = (n_det + 7) // 8
        # P2 (HALTING): 'no preprocessing beyond decoding the packed detector
        # records' is false the moment the record does not tile exactly.
        if len(raw) != shots * bytes_per_shot:
            p2_defects.append({
                "member": e["det_path"], "bytes": len(raw),
                "expected_bytes": shots * bytes_per_shot,
                "shots": shots, "n_detectors": n_det,
            })
            continue

        counts = popcount_impl(raw, n_det, shots)

        if verify_popcount and len(equivalence_checks) < verify_popcount:
            ref = read_detection_counts_author(raw, n_det, shots)
            equal = bool(np.array_equal(counts, ref))
            equivalence_checks.append({"member": e["det_path"], "equal": equal})
            if not equal:
                fail(f"popcount implementations disagree on {e['det_path']}; "
                     f"the substituted operation is not the author's operation")

        mean_c = np.mean(counts)                 # author line 57
        var_c = np.var(counts, ddof=1)           # author line 58
        fano = var_c / mean_c if mean_c > 0 else np.nan   # author line 59

        rec = {"distance": d, "patch": e["patch"], "basis": md["basis"],
               "rounds": rounds, "shots": shots, "n_det": n_det,
               "mean": mean_c, "var": var_c, "fano": fano}
        records.append(rec)
        by_distance[d].append(rec)

        if (i + 1) % 50 == 0 or i == 0:
            print(f"  processed {i+1}/{n_experiments}", flush=True)

    if p2_defects:
        for defect in p2_defects[:5]:
            print(f"  P2 defect: {defect}", file=sys.stderr)
        halt(f"P2 falsified on {len(p2_defects)} of {n_experiments} experiments: "
             f"detection_events.b8 length is not shots x ceil(n_detectors/8)")
    print(f"[MATCH] P2 packed-record tiling exact on {len(records)} experiments")

    distances = set(by_distance.keys())
    if distances != P1_EXPECTED_DISTANCES:
        halt(f"P1 falsified: code distances present are {sorted(distances)}, "
             f"PREREG Sec.3 requires {sorted(P1_EXPECTED_DISTANCES)}")
    print(f"[MATCH] P1 distance set: {sorted(distances)}")

    n_nan = int(sum(1 for r in records if not np.isfinite(r["fano"])))
    if n_nan:
        halt(f"{n_nan} experiments have a non-finite F_i (author line 59 returns "
             f"np.nan when mean_c <= 0). PREREG Sec.2 admits no handling for this "
             f"case, so no verdict can be issued under the frozen estimator.")

    # ---- estimator, author's reduction order --------------------------------
    all_fanos = []
    per_distance = {}
    for d in sorted(by_distance.keys()):          # author line 84
        fanos = np.array([r["fano"] for r in by_distance[d]])   # line 86
        all_fanos.extend(fanos)                   # line 88
        per_distance[d] = {
            "n": int(len(fanos)),
            "mean_fano": float(np.mean(fanos)),   # line 236 (W2 estimator)
            "std_fano": float(np.std(fanos)),
        }
    all_fanos = np.array(all_fanos)               # line 92

    f_overall = float(np.mean(all_fanos))         # line 97
    std_pop = float(np.std(all_fanos))            # line 97, ddof=0 (PREREG Sec.2.4)
    se = float(np.std(all_fanos) / np.sqrt(len(all_fanos)))     # line 93
    t_vs_1 = float((np.mean(all_fanos) - 1.0) / se)             # line 94

    groups = [np.array([r["fano"] for r in by_distance[d]])
              for d in sorted(by_distance.keys())]              # line 240
    anova_f, anova_p = sp_stats.f_oneway(*groups)               # line 242

    # ---- P3 (HALTING) -------------------------------------------------------
    n_w1 = int(len(all_fanos))
    n_w2 = int(sum(v["n"] for v in per_distance.values()))
    n_w3 = int(sum(len(g) for g in groups))
    n_w4 = n_w1                                    # line 94 consumes all_fanos
    if not (n_w1 == n_w2 == n_w3 == n_w4 == P1_EXPECTED_N):
        halt(f"P3 falsified: W1={n_w1}, W2={n_w2}, W3={n_w3}, W4={n_w4}; the four "
             f"sub-claims do not rest on the same experiment population")
    print(f"[MATCH] P3 shared population N: {n_w1}")

    # ---- scope test, PREREG Sec.4 R9/R10 ------------------------------------
    by_rounds = defaultdict(list)
    for r in records:
        by_rounds[r["rounds"]].append(r["fano"])
    distinct_rounds = sorted(by_rounds.keys())
    round_means = [float(np.mean(by_rounds[rr])) for rr in distinct_rounds]
    f_native = f_overall
    f_uniform = float(np.mean(np.array(round_means)))

    return {
        "n_experiments": n_w1,
        "per_distance": per_distance,
        "f_overall": f_overall,
        "std_population": std_pop,
        "standard_error": se,
        "t_vs_poisson": t_vs_1,
        "anova_f_statistic": float(anova_f),
        "anova_p_value": float(anova_p),
        "scope": {
            "f_native": f_native,
            "f_uniform": f_uniform,
            "abs_difference": abs(f_uniform - f_native),
            "distinct_rounds": distinct_rounds,
            "mean_fano_by_rounds": {str(rr): m
                                    for rr, m in zip(distinct_rounds, round_means)},
        },
        "popcount_equivalence_checks": equivalence_checks,
        "population_by_distance": {str(d): per_distance[d]["n"]
                                   for d in sorted(per_distance)},
    }


# ─────────────────────────────────────────────────────────────────────────────
# Verdicts — R1-R10 applied mechanically, no branch without a rule ID
# ─────────────────────────────────────────────────────────────────────────────

def apply_rules(m):
    v = {}

    d1 = abs(m["f_overall"] - W1_REPORTED_F)
    if d1 < R1_BAND:
        v["W1"] = {"rule": "R1", "verdict": "Verified"}
    elif d1 <= R3_BAND:
        v["W1"] = {"rule": "R2", "verdict": "Verified with Limitations"}
    else:
        v["W1"] = {"rule": "R3", "verdict": "Not Verified"}
    v["W1"].update({"recomputed": m["f_overall"], "reported": W1_REPORTED_F,
                    "abs_difference": d1})

    d2 = {d: abs(m["per_distance"][d]["mean_fano"] - W2_REPORTED[d])
          for d in sorted(W2_REPORTED)}
    if any(x > R6_BAND for x in d2.values()):
        v["W2"] = {"rule": "R6", "verdict": "Not Verified"}
    elif all(x < R5_BAND for x in d2.values()):
        v["W2"] = {"rule": "R5", "verdict": "Verified"}
    else:
        v["W2"] = {"rule": "R5/R6 interval",
                   "verdict": "Verified with Limitations"}
    v["W2"].update({
        "recomputed": {str(d): m["per_distance"][d]["mean_fano"] for d in d2},
        "reported": {str(d): W2_REPORTED[d] for d in d2},
        "abs_difference": {str(d): d2[d] for d in d2},
    })

    d3 = abs(m["anova_f_statistic"] - W3_REPORTED_ANOVA_F)
    v["W3"] = {"rule": "R7",
               "verdict": "Verified" if d3 <= R7_BAND else "Not Verified",
               "recomputed": m["anova_f_statistic"],
               "reported": W3_REPORTED_ANOVA_F, "abs_difference": d3,
               "recomputed_p_value": m["anova_p_value"],
               "note": "R7 tests the F-statistic only. The source's 'p ~ 0' "
                       "carries no pre-registered threshold and no verdict."}

    d4 = abs(m["t_vs_poisson"] - W4_REPORTED_T)
    v["W4"] = {"rule": "R8",
               "verdict": "Verified" if d4 <= R8_BAND else "Not Verified",
               "recomputed": m["t_vs_poisson"],
               "reported": W4_REPORTED_T, "abs_difference": d4}

    ds = m["scope"]["abs_difference"]
    if ds <= R9_BAND:
        v["scope"] = {"rule": "R9",
                      "finding": "Aggregate stable under reweighting; W1 stands "
                                 "as reported",
                      "w1_as_hardware_property": v["W1"]["verdict"]}
    else:
        v["scope"] = {"rule": "R10",
                      "finding": "Aggregate is composition-dependent",
                      "w1_as_hardware_property": "Unfalsifiable-as-Stated"}
    v["scope"].update({"f_native": m["scope"]["f_native"],
                       "f_uniform": m["scope"]["f_uniform"],
                       "abs_difference": ds, "threshold": R9_BAND})

    for k in ("W1", "W2", "W3", "W4"):
        if v[k]["verdict"] not in VERDICT_VOCAB:
            fail(f"{k} verdict {v[k]['verdict']!r} is outside the controlled "
                 f"vocabulary (PREREG Sec.9)")
    return v


# ─────────────────────────────────────────────────────────────────────────────
# Output
# ─────────────────────────────────────────────────────────────────────────────

def write_json(path, obj):
    """Deterministic by construction: sorted keys, fixed indent, LF newlines,
    trailing newline, no locale-dependent formatting."""
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    text = json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def main():
    ap = argparse.ArgumentParser(description=f"{INSTANCE} reproduction harness")
    ap.add_argument("--archive", required=True,
                    help="path to google_105Q_surface_code_d3_d5_d7.zip")
    ap.add_argument("--repo-root", default=os.path.dirname(os.path.abspath(__file__)),
                    help="directory holding PREREGISTRATION.md and data_manifest.json")
    ap.add_argument("--results-dir", default=None,
                    help="output directory (default: <repo-root>/results)")
    ap.add_argument("--build-manifest", action="store_true",
                    help="build data_manifest.json and exit; writes no verdict")
    ap.add_argument("--force", action="store_true",
                    help="allow --build-manifest to overwrite an existing manifest")
    ap.add_argument("--verify-popcount", type=int, default=0, metavar="N",
                    help="also run the author's byte loop on the first N "
                         "experiments and require exact equality")
    ap.add_argument("--author-popcount", action="store_true",
                    help="use the author's byte loop for every experiment (slow)")
    args = ap.parse_args()

    repo_root = os.path.abspath(args.repo_root)
    results_dir = os.path.abspath(args.results_dir or os.path.join(repo_root, "results"))
    manifest_path = os.path.join(repo_root, MANIFEST_FILENAME)

    print(f"=== {INSTANCE} — reproduce.py ===")

    prereg_sha = pin_preregistration(repo_root)
    archive_pin = pin_archive(args.archive)
    print("[MATCH] P5 archive bytes identical to willow-decoder-audit-s1 pin")

    with zipfile.ZipFile(args.archive) as z:
        experiments = enumerate_experiments(z)

        if args.build_manifest:
            build_manifest(z, experiments, archive_pin, manifest_path, args.force)
            return 0

        manifest_sha = verify_manifest(z, experiments, archive_pin, manifest_path)

        impl = (read_detection_counts_author if args.author_popcount
                else read_detection_counts_fast)
        m = step0_and_compute(z, experiments, impl, args.verify_popcount)

    verdicts = apply_rules(m)

    results = {
        "instance": INSTANCE,
        "preregistration_sha256": prereg_sha,
        "data_manifest_sha256": manifest_sha,
        "archive": archive_pin,
        "estimator_provenance": {
            "source": "github.com/SelinaAliens/The_Rotation_Gap_Is_Not_An_Error"
                      " :: willow/willow_fano_analysis.py (MIT, 245 lines)",
            "lines": ESTIMATOR_LINES,
            "popcount_implementation": ("author_loop" if args.author_popcount
                                        else "vectorised_equivalent"),
        },
        "premises": {
            "P1": {"status": "confirmed", "halting": True,
                   "n_experiments": m["n_experiments"],
                   "population_by_distance": m["population_by_distance"]},
            "P2": {"status": "confirmed", "halting": True},
            "P3": {"status": "confirmed", "halting": True},
            "P4": {"status": P4_STATUS_AT_FREEZE, "halting": False,
                   "note": "carried from the freeze; not re-measured by this harness"},
            "P5": {"status": "confirmed", "halting": False,
                   "basis": "archive md5 and size equal the pinned values"},
        },
        "measurements": {k: v for k, v in m.items()
                         if k not in ("population_by_distance",)},
        "verdicts": verdicts,
        "thresholds": {
            "R1": R1_BAND, "R3": R3_BAND, "R5": R5_BAND, "R6": R6_BAND,
            "R7": R7_BAND, "R8": R8_BAND, "R9": R9_BAND,
        },
        "source_reported_values": {
            "W1_F": W1_REPORTED_F, "W1_spread": W1_REPORTED_SPREAD,
            "W1_N": W1_REPORTED_N, "W2": {str(k): v for k, v in W2_REPORTED.items()},
            "W3_anova_F": W3_REPORTED_ANOVA_F, "W4_t": W4_REPORTED_T,
        },
        "status": "SPREMNO ZA GEJT",
    }
    write_json(os.path.join(results_dir, RESULTS_FILENAME), results)

    # Environment goes in a separate file. It is not deterministic and must not
    # be part of the byte-diff required by PREREG Sec.6.
    write_json(os.path.join(results_dir, "run_env.json"), {
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "platform": platform.platform(),
        "archive_path": os.path.abspath(args.archive),
        "note": "Excluded from the Sec.6 determinism diff by design.",
    })

    print(f"\n[WROTE] {os.path.join(results_dir, RESULTS_FILENAME)}")
    for k in ("W1", "W2", "W3", "W4"):
        print(f"  {k}: {verdicts[k]['verdict']}  (rule {verdicts[k]['rule']})")
    print(f"  scope: rule {verdicts['scope']['rule']} — "
          f"{verdicts['scope']['finding']}")
    print("\nStatus: SPREMNO ZA GEJT. Not ratified. Determinism proof "
          "(rename -> rerun -> byte-diff) has not been executed by this run.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
