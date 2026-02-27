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
         - for HUMAN: hash
    2. Score and loading words
    3. Interviewee Background (AI only — human already contains it)
    4. FULL transcript (human or AI)

Output written as:
    examples_txt/f{factor}_{pole}/f{factor}_{pole}_001.txt
"""

import re
import pandas as pd
from pathlib import Path

# ============================================================
# PATHS
# ============================================================
SCORES_FILE   = Path("sas/output_cl_st1_ph3_andressa/cl_st1_ph3_andressa_scores.tsv")
MEANS_PATTERN = "sas/output_cl_st1_ph3_andressa/means_group_f{dim}.tsv"

FILE_IDS      = Path("file_ids.txt")       # t000001 → t001_human.txt / t154_persona_grok.txt etc.
FILE_INDEX    = Path("file_index.txt")     # t001.txt → HASH

SCORE_DETAILS = Path("examples/score_details.txt")

EXTRACTED_DIR = Path("corpus/02_extracted")       # human background + human full text
FULLTEXT_ROOT = Path("corpus")                    # AI transcripts under /05_*

OUT_ROOT      = Path("examples_txt")
OUT_ROOT.mkdir(exist_ok=True)

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
# LOAD file_ids.txt  (tid_long → real short filename)
# ============================================================
id_long_to_short = {}
for line in FILE_IDS.read_text().splitlines():
    longid, shortname = line.split(maxsplit=1)
    id_long_to_short[longid] = shortname

# ============================================================
# LOAD file_index.txt  (tNNN.txt → hash)
# ============================================================
short_to_hash = {}
for line in FILE_INDEX.read_text().splitlines():
    shortfile, hashname = line.split()
    short_to_hash[shortfile] = hashname

# ============================================================
# LOAD loading words from examples/score_details.txt
# ============================================================
def parse_score_details(path=SCORE_DETAILS):
    out = {}
    txt = path.read_text()
    blocks = txt.split("=============================================")

    for b in blocks:
        m = re.search(r"text ID:\s*(t\d+)", b)
        if not m:
            continue

        tid = m.group(1)
        out[tid] = {}

        for f in range(1, 8):
            mp = re.search(rf"f{f} pos words \(N=\d+\):\s*(.*)", b)
            mn = re.search(rf"f{f} neg words \(N=\d+\):\s*(.*)", b)

            pos = mp.group(1).split(",") if mp else []
            neg = mn.group(1).split(",") if mn else []

            out[tid][f"f{f}_pos"] = [w.strip() for w in pos if w.strip()]
            out[tid][f"f{f}_neg"] = [w.strip() for w in neg if w.strip()]

    return out

loading_words = parse_score_details()

# ============================================================
# RESOLVE PATHS (authoritative version)
# ============================================================
def resolve_paths(tid, row):
    """
    Compute the REAL existing filesystem path for:
       - human transcripts
       - plain AI transcripts
       - persona AI transcripts

    Using your REAL rules:

      HUMAN:
        file_ids:     t000001 → t001_human.txt
        file_index:   t001.txt → HASH
        path:         corpus/02_extracted/HASH_extracted.txt

      PLAIN:
        folder:       corpus/05_plain_<model>
        file:         tNNN_<model>.txt

      PERSONA:
        folder:       corpus/05_persona_<model>
        file:         tNNN.txt
    """

    realname = id_long_to_short.get(tid)
    if not realname:
        return None

    model  = row["model"].strip()     # human / gpt / grok / gemini
    prompt = row["prompt"].strip()    # human / plain / persona

    # -----------------------------
    # HUMAN
    # -----------------------------
    if model == "human":
        # realname is like: t001_human.txt
        # but file_index uses: t001.txt
        base = realname.replace("_human", "")
        hashname = short_to_hash.get(base)
        if not hashname:
            return None

        path = EXTRACTED_DIR / f"{hashname}_extracted.txt"
        return {
            "kind": "human",
            "group": "human",
            "folder": EXTRACTED_DIR,
            "filename": f"{hashname}_extracted.txt",
            "hash": hashname,
            "human_hash": hashname,  # for symmetry with AI (not actually needed)
            "path": path,
        }

    # -----------------------------
    # AI (plain or persona)
    # -----------------------------
    # extract the real 3-digit ID from realname (e.g. t154_persona_grok.txt → t154)
    m = re.match(r"(t\d{3})", realname)
    if not m:
        return None
    tshort = m.group(1)

    # This is the HUMAN base used in file_index.txt
    human_short = f"{tshort}.txt"
    human_hash = short_to_hash.get(human_short)  # may be None if no matching human

    # PERSONA: folder = 05_persona_<model>, file = tNNN.txt
    if "persona" in prompt:
        folder = FULLTEXT_ROOT / f"05_persona_{model}"
        fname  = f"{tshort}.txt"
    else:
        # PLAIN: folder = 05_plain_<model>, file = tNNN_<model>.txt
        folder = FULLTEXT_ROOT / f"05_plain_{model}"
        fname  = f"{tshort}_{model}.txt"

    return {
        "kind": "ai",
        "group": f"{prompt}_{model}",
        "folder": folder,
        "filename": fname,
        "hash": None,
        "human_hash": human_hash,
        "path": folder / fname,
    }

# ============================================================
# EXTRACT interviewee background (AI only)
# ============================================================
def extract_background(hashname):
    p = EXTRACTED_DIR / f"{hashname}_extracted.txt"
    if not p.exists():
        return "[Interviewee Background NOT FOUND]\n"

    txt = p.read_text()
    m = re.search(r"Interviewee Background:\s*(.*?)(?=\nQuestion:|\Z)",
                  txt, flags=re.DOTALL)
    if m:
        return "Interviewee Background:\n" + m.group(1).strip() + "\n"
    return "[Interviewee Background NOT FOUND]\n"

# ============================================================
# MAIN SCRIPT
# ============================================================
factor_cols = [c for c in scores.columns if c.startswith("fac")]
num_factors = len(factor_cols)

for fnum in range(1, num_factors + 1):

    col = f"fac{fnum}"

    means_df = pd.read_csv(MEANS_PATTERN.format(dim=fnum), sep="\t")
    group_means = dict(zip(means_df["group"], means_df[f"Mean fac{fnum}"]))

    for pole, ascending in (("pos", False), ("neg", True)):

        label = f"f{fnum}_{pole}"
        out_dir = OUT_ROOT / label
        out_dir.mkdir(parents=True, exist_ok=True)

        print(f"Processing {label}...")

        ranked = sorted(group_means, key=lambda g: group_means[g],
                        reverse=not ascending)

        top_group = ranked[0]
        others    = ranked[1:]

        df_sorted = scores.sort_values(by=col, ascending=ascending)
        ex_id = 1

        # ---------------------------
        # TOP GROUP – 20 examples
        # ---------------------------
        subset = df_sorted[df_sorted["group"] == top_group]

        for _, row in subset.iterrows():
            if row[col] == 0 or ex_id > 20:
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
            if resolved["kind"] == "human" and resolved.get("hash"):
                header.append(f"Hash:   {resolved['hash']}")
            header.append("")

            lw = loading_words.get(tid, {}).get(label, [])
            header.append(f"Score ({label}): {row[col]}")
            header.append(f"Loading words ({label}), N={len(lw)}: {', '.join(lw)}")
            header.append("")

            body = []
            if resolved["kind"] == "ai" and resolved.get("human_hash"):
                body.append(extract_background(resolved["human_hash"]))
                body.append("")

            body.append(path.read_text())

            full = "\n".join(header + body)
            outfile = out_dir / f"{label}_{ex_id:03d}.txt"
            outfile.write_text(full)

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
                if resolved["kind"] == "human" and resolved.get("hash"):
                    header.append(f"Hash:   {resolved['hash']}")
                header.append("")

                lw = loading_words.get(tid, {}).get(label, [])
                header.append(f"Score ({label}): {row[col]}")
                header.append(f"Loading words ({label}), N={len(lw)}: {', '.join(lw)}")
                header.append("")

                body = []
                if resolved["kind"] == "ai" and resolved.get("human_hash"):
                    body.append(extract_background(resolved["human_hash"]))
                    body.append("")

                body.append(path.read_text())

                full = "\n".join(header + body)
                outfile = out_dir / f"{label}_{ex_id:03d}.txt"
                outfile.write_text(full)

                ex_id += 1
                count += 1

print("\n✓ Done! All plaintext examples written to examples_txt/")