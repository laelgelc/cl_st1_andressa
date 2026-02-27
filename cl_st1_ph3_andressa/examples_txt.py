#!/usr/bin/env python3
"""
Generate plaintext example files for each factor pole.

ALIGNMENT NOTE
--------------
This script is intentionally aligned with `examples.py` for selection logic:
    - reads the same scores table (scores_only)
    - uses the same `group` values from SAS output (no re-inference)
    - ranks groups using means_group_f<n>.tsv
    - selects: top group → 20, others → 10 each, skipping score==0

It differs only in *rendering/output* (plaintext + full transcript).
"""

import re
import pandas as pd
from pathlib import Path

# ============================================================
# PATHS (match examples.py for selection inputs)
# ============================================================
SCORES_FILE = Path("sas/output_cl_st1_ph3_andressa/cl_st1_ph3_andressa_scores_only.tsv")
MEANS_PATTERN = "sas/output_cl_st1_ph3_andressa/means_group_f{dim}.tsv"

FILE_IDS_PATH = Path("file_ids.txt")          # tid -> relative path-ish (often includes subfolder)
SCORE_DETAILS = Path("examples/score_details.txt")

TAGGED_BASE = Path("corpus/07_tagged")        # used for consistent existence/selection behavior
FULLTEXT_ROOT = Path("corpus")               # transcripts live under corpus/05_*
OUT_ROOT = Path("examples_txt")
OUT_ROOT.mkdir(exist_ok=True, parents=True)

# ============================================================
# LOAD FILE-ID → RELATIVE PATH MAP (same approach as examples.py)
# ============================================================
id_map: dict[str, str] = {}
with open(FILE_IDS_PATH, encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue
        file_id, rel = line.strip().split(maxsplit=1)
        id_map[file_id] = rel

# ============================================================
# LOAD SCORES (same source + same group semantics as examples.py)
# ============================================================
scores_df = pd.read_csv(SCORES_FILE, sep="\t")

scores_df["group"] = scores_df["group"].astype(str).str.strip()
scores_df["source"] = scores_df["source"].astype(str).str.strip()
scores_df["model"] = scores_df["model"].astype(str).str.strip()

# ============================================================
# FACTOR COUNT
# ============================================================
factor_cols = [c for c in scores_df.columns if c.startswith("fac")]
num_factors = len(factor_cols)
print(f"Detected {num_factors} factors.\n")

# ============================================================
# LOAD loading words from examples/score_details.txt
# ============================================================
def parse_score_details(path: Path, *, num_factors: int) -> dict[str, dict[str, list[str]]]:
    out: dict[str, dict[str, list[str]]] = {}
    txt = path.read_text(encoding="utf-8")
    blocks = txt.split("=============================================")

    for b in blocks:
        m = re.search(r"text ID:\s*(t\d+)", b)
        if not m:
            continue

        tid = m.group(1)
        out[tid] = {}

        for f in range(1, num_factors + 1):
            mp = re.search(rf"f{f} pos words \(N=\d+\):\s*(.*)", b)
            mn = re.search(rf"f{f} neg words \(N=\d+\):\s*(.*)", b)

            pos = mp.group(1).split(",") if mp else []
            neg = mn.group(1).split(",") if mn else []

            out[tid][f"f{f}_pos"] = [w.strip() for w in pos if w.strip()]
            out[tid][f"f{f}_neg"] = [w.strip() for w in neg if w.strip()]

    return out

loading_words = parse_score_details(SCORE_DETAILS, num_factors=num_factors)

# ============================================================
# PATH RESOLUTION
#   - Use tagged path for existence checks (align with examples.py behavior)
#   - Use fulltext path for output (corpus/05_*)
# ============================================================
def locate_tagged_text(row) -> Path | None:
    tid = row["filename"]
    rel = id_map.get(tid)
    if not rel:
        return None

    p = TAGGED_BASE / rel
    if p.exists():
        return p

    # fallback: old behavior if mapping is only a filename
    return TAGGED_BASE / row["group"] / rel


def locate_fulltext(row) -> Path | None:
    """
    Try to locate the 'full transcript' corresponding to the same tid.

    We derive the 05_* folder primarily from file_ids.txt mapping:
      - if rel looks like "<subdir>/<fname>", use corpus/05_<subdir>/<fname>
      - special-case: <subdir> == "human" -> corpus/05_human/<fname>

    Fallback if mapping is only a filename:
      - group == "human" -> corpus/05_human/<fname>
      - else -> corpus/05_<group>/<fname>
    """
    tid = row["filename"]
    rel = id_map.get(tid)
    if not rel:
        return None

    rel_path = Path(rel)
    fname = rel_path.name

    if len(rel_path.parts) >= 2:
        subdir = rel_path.parts[0]
        folder = FULLTEXT_ROOT / ("05_human" if subdir == "human" else f"05_{subdir}")
        return folder / fname

    # mapping did not include a subfolder
    grp = str(row["group"]).strip()
    folder = FULLTEXT_ROOT / ("05_human" if grp == "human" else f"05_{grp}")
    return folder / fname


def write_plaintext_example(
        *,
        outfile: Path,
        tid: str,
        group: str,
        model: str,
        fulltext_path: Path,
        label: str,
        score_value,
        lw: list[str],
) -> None:
    header: list[str] = []
    header.append(f"Text ID: {tid}")
    header.append(f"Group: {group}")
    header.append(f"Model: {model}")
    header.append(f"File:   {fulltext_path}")
    header.append("")
    header.append(f"Score ({label}): {score_value}")
    header.append(f"Loading words ({label}), N={len(lw)}: {', '.join(lw)}")
    header.append("")

    body = fulltext_path.read_text(encoding="utf-8", errors="ignore")
    outfile.write_text("\n".join(header) + body, encoding="utf-8")

# ============================================================
# MAIN (selection logic mirrors examples.py)
# ============================================================
missing_files: set[str] = set()

for fac_num in range(1, num_factors + 1):
    col = f"fac{fac_num}"

    means_df = pd.read_csv(MEANS_PATTERN.format(dim=fac_num), sep="\t")
    group_means = dict(zip(means_df["group"], means_df[f"Mean fac{fac_num}"]))

    for pole, ascending in (("pos", False), ("neg", True)):
        label = f"f{fac_num}_{pole}"
        print(f"→ {label}: selecting by group means (col={col}, ascending={ascending})")

        ranked_groups = sorted(
            group_means.keys(),
            key=lambda g: group_means[g],
            reverse=not ascending,
        )
        top_group = ranked_groups[0]
        other_groups = ranked_groups[1:]

        sorted_df = scores_df.sort_values(by=col, ascending=ascending)

        out_dir = OUT_ROOT / label
        out_dir.mkdir(parents=True, exist_ok=True)

        ex_id = 1

        # ---------------------------------------
        # TOP GROUP — 20 EXAMPLES
        # ---------------------------------------
        tg_df = sorted_df[sorted_df["group"] == top_group]
        for _, row in tg_df.iterrows():
            if row[col] == 0:
                continue
            if ex_id > 20:
                break

            # align missing/skip behavior with examples.py: ensure tagged exists
            tagged_path = locate_tagged_text(row)
            if not tagged_path or not tagged_path.exists():
                missing_files.add(row["filename"])
                continue

            fulltext_path = locate_fulltext(row)
            if not fulltext_path or not fulltext_path.exists():
                missing_files.add(row["filename"])
                continue

            tid = row["filename"]
            lw = loading_words.get(tid, {}).get(label, [])

            outfile = out_dir / f"{label}_{ex_id:03d}.txt"
            write_plaintext_example(
                outfile=outfile,
                tid=tid,
                group=str(row["group"]).strip(),
                model=str(row["model"]).strip(),
                fulltext_path=fulltext_path,
                label=label,
                score_value=row[col],
                lw=lw,
            )
            ex_id += 1

        # ---------------------------------------
        # OTHER GROUPS — 10 EACH
        # ---------------------------------------
        for grp in other_groups:
            grp_df = sorted_df[sorted_df["group"] == grp]

            count = 0
            for _, row in grp_df.iterrows():
                if row[col] == 0:
                    continue
                if count >= 10:
                    break

                tagged_path = locate_tagged_text(row)
                if not tagged_path or not tagged_path.exists():
                    missing_files.add(row["filename"])
                    continue

                fulltext_path = locate_fulltext(row)
                if not fulltext_path or not fulltext_path.exists():
                    missing_files.add(row["filename"])
                    continue

                tid = row["filename"]
                lw = loading_words.get(tid, {}).get(label, [])

                outfile = out_dir / f"{label}_{ex_id:03d}.txt"
                write_plaintext_example(
                    outfile=outfile,
                    tid=tid,
                    group=str(row["group"]).strip(),
                    model=str(row["model"]).strip(),
                    fulltext_path=fulltext_path,
                    label=label,
                    score_value=row[col],
                    lw=lw,
                )

                count += 1
                ex_id += 1

        print(f"  ✓ Wrote {ex_id - 1} examples for {label}\n")

# ============================================================
# MISSING FILE REPORT (match examples.py behavior)
# ============================================================
if missing_files:
    Path("missing_files.txt").write_text("\n".join(sorted(missing_files)), encoding="utf-8")
    print("⚠ Missing files written to missing_files.txt")

print("\n✓ Done! All plaintext examples written to examples_txt/")