#!/usr/bin/env python3
"""
Generate TikZ boxplots in LaTeX for dimensions 1–3 comparing:
 - by source
 - by model
 - by prompt
 - by group

Reads:
    ../sas/output_cl_st1_ph3_andressa/cl_st1_ph3_andressa_scores_only.tsv
    ../sas/output_cl_st1_ph3_andressa/params_f<n>.tsv
    ../sas/output_cl_st1_ph3_andressa/params_model_f<n>.tsv
    ../sas/output_cl_st1_ph3_andressa/params_prompt_f<n>.tsv
    ../sas/output_cl_st1_ph3_andressa/params_source_f<n>.tsv
    ../sas/output_cl_st1_ph3_andressa/params_group_f<n>.tsv

Writes:
    slides/boxplot_f<dim>_by_source.tex
    slides/boxplot_f<dim>_by_model.tex
    slides/boxplot_f<dim>_by_prompt.tex
    slides/boxplot_f<dim>_by_group.tex
    slides/mosaic_by_source.tex
    slides/mosaic_by_model.tex
    slides/mosaic_by_prompt.tex
    slides/mosaic_by_group.tex
"""
import csv
import pandas as pd
from pathlib import Path
from tqdm import tqdm

INPUT_FILE = Path("../sas/output_cl_st1_ph3_andressa/cl_st1_ph3_andressa_scores_only.tsv")
OUTPUT_DIR = Path("slides")
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

def read_rsquare(param_file: str) -> float:
    with open(param_file, newline='') as f:
        reader = csv.DictReader(f, delimiter='\t')
        rows = list(reader)
    return float(rows[0]['RSquare']) * 100.0 if rows else 0.0

def latex_escape(text: str) -> str:
    reps = {
        '\\':r'\textbackslash{}','_':r'\_','%':r'\%','&':r'\&','#':r'\#',
        '{':r'\{','}':r'\}','^':r'\textasciicircum{}','~':r'\textasciitilde{}'
    }
    for o,e in reps.items():
        text = text.replace(o,e)
    return text

def compute_boxplot_stats(s: pd.Series):
    q1, med, q3 = s.quantile([.25, .5, .75])
    iqr = q3 - q1
    return (
        max(s.min(), q1-1.5*iqr),
        q1, med, q3,
        min(s.max(), q3+1.5*iqr)
    )

def generate_boxplot(df: pd.DataFrame, dim: int, group_var: str,
                     suffix: str, caption: str):
    col = f"fac{dim}"
    means = df.groupby(group_var)[col].mean().sort_values(ascending=False)
    groups = means.index.tolist()
    labels = [latex_escape(str(g)) for g in groups]
    total = len(groups)

    tex = [
        r"\begin{figure}[H]",
        r"\centering",
        r"\hspace*{-.25in}",
        r"\begin{tikzpicture}",
        r"\begin{axis}[",
        r"  boxplot/draw direction=y,",
        r"  enlarge x limits=0.01,",
        r"  every boxplot/.style={draw=black, fill=blue!25},",
        f"  ylabel={{Mean Dim. {dim} Score}},",
        r"  ylabel style={font=\scriptsize},",
        r"  height=0.45\textheight, width=\textwidth,",
        r"  yticklabel style={font=\footnotesize},",
        r"  x tick label style={rotate=60, anchor=east, font=\scriptsize},",
        r"  x=7.5,",
        f"  xtick={{1,...,{total}}},",
        r"  xticklabels={",
        ",\n  ".join(labels),
        r"},",
        r"]",
        f"\\addplot[red, densely dashed] coordinates {{(0.5,0) ({total+0.5},0)}};"
    ]

    for i, grp in enumerate(groups, start=1):
        vals = df[df[group_var] == grp][col]
        lw, q1, med, q3, uw = compute_boxplot_stats(vals)

        # outliers
        iqr = q3 - q1
        out = vals[(vals < q1-1.5*iqr) | (vals > q3+1.5*iqr)]
        if not out.empty:
            coords = " ".join(f"({i},{v})" for v in sorted(out))
            tex.append(
                rf"\addplot+[only marks, mark=*, mark options={{fill=black, mark size=.8pt}}] coordinates {{{coords}}};"
            )

        # box
        tex += [
            r"\addplot+[solid, draw=black, fill=blue!25, boxplot prepared={",
            f"  lower whisker={lw},",
            f"  lower quartile={q1},",
            f"  median={med},",
            f"  upper quartile={q3},",
            f"  upper whisker={uw}",
            r"}] coordinates {};",
        ]

        # mean point
        tex.append(
            f"\\addplot[only marks, mark=*, draw=red, fill=red, mark size=1.2pt] coordinates {{({i},{vals.mean()})}};"
        )

    tex += [
        r"\end{axis}",
        r"\end{tikzpicture}",
        f"\\caption{{{caption}}}",
        f"\\label{{fig:means_f{dim}_{suffix}}}",
        r"\end{figure}"
    ]

    (OUTPUT_DIR / f"boxplot_f{dim}_{suffix}.tex")\
        .write_text("\n".join(tex), encoding="utf-8")

def generate_mosaic(suffix: str, caption: str):
    #dims = range(1, 8)
    dims = range(1, 4)
    blocks = []
    for dim in dims:
        fn = OUTPUT_DIR / f"boxplot_f{dim}_{suffix}.tex"
        lines = fn.read_text(encoding="utf-8").splitlines()
        start = next(i for i,l in enumerate(lines) if l.strip().startswith(r"\hspace*"))
        end   = next(i for i,l in enumerate(lines) if l.strip() == r"\end{tikzpicture}")
        blocks.append("\n".join(lines[start:end+1]))

    mos = [r"\begin{figure}[ht]", r"\centering"]

    # top row dims 1–4
    for i in range(4):
        mos += [
            r"\begin{minipage}[t]{0.24\textwidth}",
            r"\centering",
            blocks[i],
            r"\end{minipage}\hfill",
        ]
#    mos.append(r"\bigskip")
#
#    # bottom row dims 5–7
#    for i in range(4,7):
#        spacer = r"\hfill" if i < 6 else ""
#        mos += [
#            r"\begin{minipage}[t]{0.32\textwidth}",
#            r"\centering",
#            blocks[i],
#            r"\end{minipage}" + spacer,
#        ]

    mos += [
        f"\\caption{{{caption}}}",
        rf"\label{{fig:mosaic_{suffix}}}",
        r"\end{figure}"
    ]

    out_path = OUTPUT_DIR / f"mosaic_{suffix}.tex"
    out_path.write_text("\n".join(mos), encoding="utf-8")

def main():
    df = pd.read_csv(INPUT_FILE, sep="\t")

    df['source'] = df['source'].str.strip().str.lower()
    df['model']  = df['model'].str.strip().str.lower()
    df['prompt'] = df['prompt'].str.strip().str.lower()
    df['group']  = df['group'].str.strip().str.lower()

    #dims = range(1, 8)
    dims = range(1, 4)

    # ----- 1) by source -----
    for dim in tqdm(dims, desc="By source"):
        rs = read_rsquare(f"../sas/output_cl_st1_ph3_andressa/params_source_f{dim}.tsv")
        cap = f"Mean Dim. {dim} Scores by Source (R² = {rs:.2f}\\%)"
        generate_boxplot(df, dim, 'source', 'by_source', cap)

    # ----- 2) by model -----
    for dim in tqdm(dims, desc="By model"):
        rs = read_rsquare(f"../sas/output_cl_st1_ph3_andressa/params_model_f{dim}.tsv")
        cap = f"Mean Dim. {dim} Scores by Model (R² = {rs:.2f}\\%)"
        generate_boxplot(df, dim, 'model', 'by_model', cap)

    # ----- 3) by prompt -----
    for dim in tqdm(dims, desc="By prompt"):
        rs = read_rsquare(f"../sas/output_cl_st1_ph3_andressa/params_prompt_f{dim}.tsv")
        cap = f"Mean Dim. {dim} Scores by Prompt (R² = {rs:.2f}\\%)"
        generate_boxplot(df, dim, 'prompt', 'by_prompt', cap)

    ## ----- 4) by group -----
    #for dim in tqdm(dims, desc="By group"):
    #    rs = read_rsquare(f"../sas/output_cl_st1_ph3_andressa/params_group_f{dim}.tsv")
    #    cap = f"Mean Dim. {dim} Scores by Group (R² = {rs:.2f}\\%)"
    #    generate_boxplot(df, dim, 'group', 'by_group', cap)

    # mosaics
    generate_mosaic('by_source', "Mean Dim. Scores by Source")
    generate_mosaic('by_model',  "Mean Dim. Scores by Model")
    generate_mosaic('by_prompt', "Mean Dim. Scores by Prompt")
    generate_mosaic('by_group',  "Mean Dim. Scores by Group")

    print(f"All boxplots & mosaics saved to {OUTPUT_DIR.resolve()}")

if __name__ == "__main__":
    main()
