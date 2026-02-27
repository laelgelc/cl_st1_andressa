#!/usr/bin/env python3
"""
Generate plaintext example files for each factor pole.

For each factor:
    - Positive pole: select top 20 texts from group with highest mean
    - Negative pole: select top 20 texts from group with lowest mean
    - All other groups: 10 texts each
    - Skip any file with factor score == 0

For each selected text output:
    1. Metadata header:
         - tid (t000001 etc.)
         - group
         - model
         - folder + filename
    2. Score and loading words
    3. FULL transcript (human or AI)

Output written as:
    examples_txt/f{factor}_{pole}/f{factor}_{pole}_001.txt
"""

import re
import pandas as pd
from pathlib import Path

# ============================================================
# PATHS
# ============================================================
SCORES_FILE = Path("sas/output_cl_st1_ph3_andressa/cl_st1_ph3_andressa_scores.tsv")
MEANS_PATTERN = "sas/output_cl_st1_ph3_andressa/means_group_f{dim}.tsv"

FILE_IDS = Path("file_ids.txt")      # e.g. t000001 -> human/t828_human.txt (project-specific)
SCORE_DETAILS = Path("examples/score_details.txt")

FULLTEXT_ROOT = Path("corpus")       # transcripts live under corpus/05_*
OUT_ROOT = Path("examples_txt")
OUT_ROOT.mkdir(exist_ok=True, parents=True)

# ============================================================
# LOAD SCORES
# ============================================================
scores = pd.read_csv(SCORES_FILE, sep="\t")
scores.columns = scores.columns.str.lower()

def infer_group(row):
    if row["model"] == "human":
        return "human"
    return f"{row['prompt']}_{row['model']}"

scores["group"] = scores.apply(infer_group, axis=1)

# ============================================================
# LOAD file_ids.txt  (tid_long → relative path or filename)
# ============================================================
id_long_to_short = {}
for line in FILE_IDS.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    longid, shortname = line.split(maxsplit=1)
    id_long_to_short[longid.strip()] = shortname.strip()

# ============================================================
# LOAD loading words from examples/score_details.txt
# ============================================================
def parse_score_details(path: Path, *, num_factors: int):
    out = {}
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

# ============================================================
# RESOLVE PATHS (Phase 3: human/generic_gpt/summary_guided_gpt)
# ============================================================
def _tid_to_tshort(tid: str) -> str | None:
    """
    Convert t000001 -> t001
    """
    m = re.fullmatch(r"t0*(\d+)", str(tid).strip())
    if not m:
        return None
    return f"t{int(m.group(1)):03d}"

def resolve_paths(tid, row):
    """
    Current Phase 3 rules:

      HUMAN:
        file_ids maps tid -> path-ish value like "human/t828_human.txt"
        actual file lives under: corpus/05_human/<basename>

      AI (GPT):
        folder: corpus/05_<prompt>_<model>   e.g. corpus/05_generic_gpt
        file:   tNNN_<model>.txt            e.g. t001_gpt.txt
        where tNNN is derived from tid (t000001 -> t001)
    """
    model = str(row["model"]).strip().lower()
    prompt = str(row["prompt"]).strip().lower()

    if model == "human":
        rel = id_long_to_short.get(tid)
        if not rel:
            return None
        basename = Path(rel).name
        folder = FULLTEXT_ROOT / "05_human"
        path = folder / basename
        return {
            "kind": "human",
            "group": "human",
            "folder": folder,
            "filename": basename,
            "path": path,
        }

    # AI
    tshort = _tid_to_tshort(tid)
    if not tshort:
        return None

    folder = FULLTEXT_ROOT / f"05_{prompt}_{model}"
    fname = f"{tshort}_{model}.txt"
    return {
        "kind": "ai",
        "group": f"{prompt}_{model}",
        "folder": folder,
        "filename": fname,
        "path": folder / fname,
    }

# ============================================================
# MAIN SCRIPT
# ============================================================
factor_cols = [c for c in scores.columns if c.startswith("fac")]
num_factors = len(factor_cols)

loading_words = parse_score_details(SCORE_DETAILS, num_factors=num_factors)

for fnum in range(1, num_factors + 1):

    col = f"fac{fnum}"

    means_df = pd.read_csv(MEANS_PATTERN.format(dim=fnum), sep="\t")
    group_means = dict(zip(means_df["group"], means_df[f"Mean fac{fnum}"]))

    for pole, ascending in (("pos", False), ("neg", True)):

        label = f"f{fnum}_{pole}"
        out_dir = OUT_ROOT / label
        out_dir.mkdir(parents=True, exist_ok=True)

        print(f"Processing {label}...")

        ranked = sorted(group_means, key=lambda g: group_means[g], reverse=not ascending)
        top_group = ranked[0]
        others = ranked[1:]

        df_sorted = scores.sort_values(by=col, ascending=ascending)
        ex_id = 1

        # ---------------------------
        # TOP GROUP – 20 examples
        # ---------------------------
        subset = df_sorted[df_sorted["group"] == top_group]

        for _, row in subset.iterrows():
            if row[col] == 0:
                continue
            if ex_id > 20:
                break

            tid = row["filename"]
            resolved = resolve_paths(tid, row)
            if not resolved:
                continue

            path = resolved["path"]
            if not path.exists():
                continue

            header = []
            header.append(f"Text ID: {tid}")
            header.append(f"Group: {resolved['group']}")
            header.append(f"Model: {row['model']}")
            header.append(f"Folder: {resolved['folder']}")
            header.append(f"File:   {resolved['filename']}")
            header.append("")

            lw = loading_words.get(tid, {}).get(label, [])
            header.append(f"Score ({label}): {row[col]}")
            header.append(f"Loading words ({label}), N={len(lw)}: {', '.join(lw)}")
            header.append("")

            body = [path.read_text(encoding="utf-8", errors="ignore")]

            full = "\n".join(header + body)
            outfile = out_dir / f"{label}_{ex_id:03d}.txt"
            outfile.write_text(full, encoding="utf-8")

            ex_id += 1

        # ---------------------------
        # OTHER GROUPS – 10 each
        # ---------------------------
        for grp in others:
            count = 0
            subset = df_sorted[df_sorted["group"] == grp]

            for _, row in subset.iterrows():
                if row[col] == 0 or count >= 10:
                    continue

                tid = row["filename"]
                resolved = resolve_paths(tid, row)
                if not resolved:
                    continue

                path = resolved["path"]
                if not path.exists():
                    continue

                header = []
                header.append(f"Text ID: {tid}")
                header.append(f"Group: {resolved['group']}")
                header.append(f"Model: {row['model']}")
                header.append(f"Folder: {resolved['folder']}")
                header.append(f"File:   {resolved['filename']}")
                header.append("")

                lw = loading_words.get(tid, {}).get(label, [])
                header.append(f"Score ({label}): {row[col]}")
                header.append(f"Loading words ({label}), N={len(lw)}: {', '.join(lw)}")
                header.append("")

                body = [path.read_text(encoding="utf-8", errors="ignore")]

                full = "\n".join(header + body)
                outfile = out_dir / f"{label}_{ex_id:03d}.txt"
                outfile.write_text(full, encoding="utf-8")

                ex_id += 1
                count += 1

print("\n✓ Done! All plaintext examples written to examples_txt/")