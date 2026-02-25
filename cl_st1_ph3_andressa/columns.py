#!/usr/bin/env python3
import os
from pathlib import Path

# === Configuration ===
KEYWORD_FILE = Path("corpus/09_kw_selected/keywords.txt")
TAGGED_BASE  = Path("corpus/07_tagged")
OUTPUT_DIR   = Path("columns")
CLEAN_DIR    = Path("columns_clean")
INDEX_FILE   = Path("index_keywords.txt")
FILE_IDS     = Path("file_ids.txt")   # <-- renamed

# === Step 1: Load consolidated keywords ===
lemmas = [
    kw.strip()
    for kw in KEYWORD_FILE.read_text(encoding="utf-8").splitlines()
    if kw.strip()
]

# === Step 2: Create index map for unique lemmas (proper numbering) ===
unique_lemmas = sorted(set(lemmas))   # remove duplicates + stable order

lemma_index = {lemma: f"{i+1:06d}" for i, lemma in enumerate(unique_lemmas)}


# === Step 3: Collect all tagged text files ===
text_paths = []
for folder in sorted(TAGGED_BASE.iterdir()):
    if not folder.is_dir():
        continue
    for text_file in sorted(folder.rglob("*.txt")):
        text_paths.append(text_file)

# === Step 4: Assign file IDs ===
file_id_map = {}
with FILE_IDS.open("w", encoding="utf-8") as fidx:
    for i, text_file in enumerate(text_paths, 1):
        fid = f"t{i:06d}"
        file_id_map[text_file] = fid
        fidx.write(f"{fid} {text_file.name}\n")

# === Step 5: Read each text and record lemma presence ===
text_infos = []
for text_file in text_paths:
    fid = file_id_map[text_file]

    # Example folder names:
    #  human
    #  persona_gpt
    #  plain_grok

    folder = text_file.relative_to(TAGGED_BASE).parts[0]

    # ----- SOURCE -----
    if folder == "human":
        source = "human"
    else:
        source = "ai"

    # ----- PROMPT -----
    if folder == "human":
        prompt = "human"
    elif folder.startswith("plain_"):
        prompt = "plain"
    elif folder.startswith("persona_"):
        prompt = "persona"
    else:
        #prompt = "unknown"
        prompt = "persona" # In this project the AI-generated texts are "persona" texts"

    # ----- MODEL -----
    if folder == "human":
        model = "human"
    else:
        ## folder format: persona_gpt or plain_gemini
        #parts = folder.split("_")
        #model = parts[-1].lower() if len(parts) > 1 else "unknown"
        # folder format: gemini, gpt, or grok
        model = folder.lower()

    # Extract lemmas from 3rd column
    present = set()
    with text_file.open(encoding="utf-8") as tf:
        for line in tf:
            parts = line.strip().split()
            if len(parts) >= 3:
                present.add(parts[2])

    text_infos.append({
        "id": fid,
        "name": text_file.name,
        "source": source,
        "prompt": prompt,
        "model": model,
        "lemmas": present
    })

# === Step 6: Write one column file per lemma ===
OUTPUT_DIR.mkdir(exist_ok=True)

for lemma in lemmas:
    lemma_id = lemma_index[lemma]
    outpath = OUTPUT_DIR / f"{lemma_id}.txt"

    with outpath.open("w", encoding="utf-8") as outf:
        for info in text_infos:
            has_kw = 1 if lemma in info["lemmas"] else 0
            outf.write(
                f"{info['id']} {info['prompt']} {info['model']} "
                f"{info['source']} {has_kw}\n"
            )

# === Step 7: Save lemma index ===
# === Fixed: Consecutive numbering based on actual keywords ===
with INDEX_FILE.open("w", encoding="utf-8") as idxf:
    for i, lemma in enumerate(lemmas, start=1):
        lemma_id = f"{i:06d}"
        idxf.write(f"{lemma_id} {lemma}\n")

# === Step 8: Produce clean column files ===
CLEAN_DIR.mkdir(exist_ok=True)

for lemma in lemmas:
    lemma_id = lemma_index[lemma]
    src = OUTPUT_DIR / f"{lemma_id}.txt"
    dst = CLEAN_DIR / f"{lemma_id}.txt"

    lines = src.read_text(encoding="utf-8").splitlines()

    with dst.open("w", encoding="utf-8") as fout:
        fout.write(f"{lemma_id}\n")
        for line in lines:
            parts = line.split()
            if parts:
                fout.write(f"{parts[-1]}\n")

print("Processing complete.")
print("→ Columns in 'columns/'")
print("→ Clean binary columns in 'columns_clean/'")
print("→ File IDs saved to 'file_ids.txt'")
