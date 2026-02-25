#!/usr/bin/env python3
import re
from pathlib import Path


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------
DIR_IN = Path("corpus/02_extracted")
DIR_OUT = Path("corpus/05_human")
INDEX_FILE = Path("file_index.txt")

DIR_OUT.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# Load file_index.txt mapping
# ---------------------------------------------------------
def load_index_map(index_path):
    """
    Reads file_index.txt which has lines like:
        t001.txt 00204690045c0943bbf20e39a31b8f298e0e9529
    Returns dict:
        { "00204690045c0943bbf20e39a31b8f298e0e9529" : "t001" }
    """
    mapping = {}
    for line in index_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        fname, hashval = line.split()
        stem = Path(fname).stem  # t001
        mapping[hashval] = stem
    return mapping


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
def main():
    # Load the hash → tXXX mapping
    mapping = load_index_map(INDEX_FILE)

    # Process each extracted file
    for infile in sorted(DIR_IN.glob("*_extracted.txt")):
        stem = infile.stem.replace("_extracted", "")  # the hash
        if stem not in mapping:
            print(f"[WARN] No mapping for {infile.name}")
            continue

        tname = mapping[stem]  # t001, t002, ...
        outname = f"{tname}_human.txt"
        outfile = DIR_OUT / outname

        text = infile.read_text(encoding="utf-8", errors="ignore")
        answers = text

        outfile.write_text(answers, encoding="utf-8")
        print(f"[OK] {infile.name} → {outfile.name}")


if __name__ == "__main__":
    main()
