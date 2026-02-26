#!/usr/bin/env python3
"""
Generate LaTeX ANOVA tables for:
    source
    model
    prompt
    group

Each table lists F, p, R², and percent R² for dimensions 1–7.

Reads (per dim):
    anova_<cond>_f<n>.tsv
    params_<cond>_f<n>.tsv

Writes:
    latex_tables/anova_<cond>.tex
"""

import csv
import pandas as pd
from pathlib import Path

INPUT_DIR  = Path('sas/output_cl_st1_ph3_andressa')
OUTPUT_DIR = Path('latex_tables')
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

# -------------------------------------------------------------------
# CONDITIONS UPDATED
# -------------------------------------------------------------------
CONDITIONS = [
    ('Source', 'anova_source_f{dim}.tsv', 'params_source_f{dim}.tsv', 'anova_source.tex'),
    ('Model',  'anova_model_f{dim}.tsv',  'params_model_f{dim}.tsv',  'anova_model.tex'),
    ('Prompt', 'anova_prompt_f{dim}.tsv', 'params_prompt_f{dim}.tsv', 'anova_prompt.tex'),
    ('Group',  'anova_group_f{dim}.tsv',  'params_group_f{dim}.tsv',  'anova_group.tex'),
]

# -------------------------------------------------------------------
def read_rsquare(path: Path) -> float:
    """Read RSquare from first row of a TSV file."""
    with path.open(newline='') as f:
        reader = csv.DictReader(f, delimiter='\t')
        rows = list(reader)
    return float(rows[0]['RSquare']) if rows else 0.0

def format_rsquare(rs: float):
    """Return R² without leading zero + percent."""
    actual = f"{rs:.5f}"
    if actual.startswith("0"):
        actual = actual[1:]
    return actual, f"{rs*100:.2f}"

# -------------------------------------------------------------------
def make_table(cond_name, anova_pat, params_pat, out_filename):
    rows = []

    #for dim in range(1, 8):
    for dim in range(1, 4):
        # ------------------------------
        # Load ANOVA TSV
        # ------------------------------
        anova_file = INPUT_DIR / anova_pat.format(dim=dim)
        df = pd.read_csv(anova_file, sep='\t')

        # SAS stores the tested effect under column "Source"
        target = cond_name.lower()
        sel = df[(df["HypothesisType"] == 1) &
                 (df["Source"].str.lower() == target)]

        if sel.empty:
            sel = df[df["HypothesisType"] == 1]

        row = sel.iloc[0]
        F_val = row["FValue"]
        p_val = row["ProbF"]

        # ------------------------------
        # Load R²
        # ------------------------------
        rs = read_rsquare(INPUT_DIR / params_pat.format(dim=dim))
        r2_act, r2_pct = format_rsquare(rs)

        rows.append((dim, F_val, p_val, r2_act, r2_pct))

    # ------------------------------
    # Write LaTeX table
    # ------------------------------
    out_path = OUTPUT_DIR / out_filename
    with out_path.open('w', encoding='utf-8') as f:
        f.write("\\begin{table}[H]\n")
        f.write("  \\centering\n")
        f.write(f"  \\caption{{ANOVA Results for {cond_name}}}\n")
        f.write(f"  \\label{{tab:{out_filename.replace('.tex','')}}}\n")
        f.write("  \\begin{tabular}{l r r r r}\n")
        f.write("    Dim. & F & p & R$^2$ & \\% \\\\\n")
        f.write("    \\hline\n")

        for dim, F_val, p_val, r2_act, r2_pct in rows:
            f.write(f"    {dim} & {F_val:.2f} & {p_val} & {r2_act} & {r2_pct} \\\\\n")

        f.write("  \\end{tabular}\n")
        f.write("\\end{table}\n")

# -------------------------------------------------------------------
def main():
    for cond_name, anova_pat, params_pat, out_fn in CONDITIONS:
        make_table(cond_name, anova_pat, params_pat, out_fn)

if __name__ == "__main__":
    main()
