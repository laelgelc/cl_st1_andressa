python summarise_posts.py \
    --input corpus/02_extracted \
    --output corpus/03_summary \
    --model grok-4 \
    --workers 6

python build_prompts.py

python generate_gpt.py \
    --input corpus/04_prompt \
    --output corpus/05_gpt \
    --model gpt-5.1 \
    --workers 4

python generate_grok.py \
    --input corpus/04_prompt \
    --output corpus/05_grok \
    --model grok-4 \
    --workers 4

python generate_gemini.py \
    --input corpus/04_prompt \
    --output corpus/05_gemini \
    --model gemini-2.5-pro \
    --workers 4

python clean_answers_human.py
# output: corpus/05_human

python tag.py
# output: corpus/07_tagged

python keylemmas.py \
    --input corpus/07_tagged \
    --output corpus/08_keylemmas \
    --cutoff 3

python select_kws_stratified.py \
    --ceiling 420 \
    --human-weight 2 \
    --max-total 1200
# output: corpus/09_kw_selected
"
=== Keyword Quotas ===
gemini          → 420 keywords (max)
gpt             → 420 keywords (max)
grok            → 420 keywords (max)
human           → 840 keywords (max)
=======================

gemini          → selected 1/420 keywords
gpt             → selected 385/420 keywords
grok            → selected 4/420 keywords
human           → selected 840/840 keywords

Total consolidated keywords (incl. duplicates): 1200
Unique keywords (used downstream): 970
Duplicates removed later: 230

Final unique keywords written: 970
"

rm -rf columns columns_clean
python columns.py
# output: columns, columns_clean, file_ids.txt, index_keywords.txt

python merge_columns.py
# output: sas/counts.txt

python sas_formats.py
# output: sas/word_labels_format.sas, etc

## RUN SAS
## Rogerio Yamada's account

python factor_lists.py
# output: factors

python corpus_size.py
# output: corpus_size/corpus_size.tsv

cd latex_boxplots
# builds boxplots for factor analysis:
python latex_boxplots.py
# output: latex_boxplots/slides
cd ..

python latex_anova_table.py
# output: latex_tables

python examples.py
# output: examples (LaTEX format)

# sanity check on the scores:
python score_details.py
# output: examples/score_details.txt

# interpretation
# build prompts:
python interpretation_prompts.py

# submit prompts:
python generate_interpretation_gpt.py \
    --input interpretation/input \
    --output interpretation/output \
    --model gpt-5.1 \
    --workers 4
