from datetime import datetime
from glob import glob
from pathlib import Path

import pandas as pd
from loguru import logger
from tqdm import tqdm

from sqldeps.evaluate import evaluate_extraction_performance

# PARAMETERS
OUTPUT_DIR = "outputs"

# Table with model pricings
df_model_metadata = pd.DataFrame(
    [
        ("groq", "gemma2-9b-it", 0.20, 0.20),
        ("groq", "llama-3.3-70b-versatile", 0.59, 0.79),
        ("groq", "llama-3.1-8b-instant", 0.05, 0.08),
        ("groq", "mixtral-8x7b-32768", 0.24, 0.24),
        ("groq", "deepseek-r1-distill-llama-70b", 0.75, 0.99),
        ("openai", "gpt-4o", 2.50, 10),
        ("openai", "gpt-4o-mini", 0.15, 0.60),
        ("deepseek", "deepseek-chat", 0.27, 1.10),
    ],
    columns=["framework", "model", "input_price", "output_price"],
)

sql_files = [f"tests/test_sql/example{i}.sql" for i in range(1, 11)]
json_files = [f"tests/test_sql_outputs/example{i}_expected.json" for i in range(1, 11)]

# [(row.framework, row.model) for row in df_model_metadata.itertuples()]
models = [
    ("groq", "gemma2-9b-it"),
    ("groq", "llama-3.3-70b-versatile"),
    ("groq", "llama-3.1-8b-instant"),
    ("groq", "mixtral-8x7b-32768"),
    ("groq", "deepseek-r1-distill-llama-70b"),
    ("openai", "gpt-4o"),
    ("openai", "gpt-4o-mini"),
    ("deepseek", "deepseek-chat"),
]

prompts = [
    "configs/prompts/default.yml",
    "configs/prompts/custom.yml",
    "configs/prompts/one_shot_default.yml",
    "configs/prompts/one_shot_custom.yml",
]

# Set Paths
today = datetime.now().strftime("%Y%m%d")
output_path = Path(OUTPUT_DIR) / Path(today)
output_raw_path = Path(output_path) / Path("raw")

# Create directories
output_raw_path.mkdir(parents=True, exist_ok=True)

# Run extractions
for framework, model in models:
    for prompt in prompts:
        output_file_path = (
            output_raw_path / f"{framework}_{model}_{Path(prompt).stem}.csv"
        )

        if output_file_path.exists():
            continue

        logger.info(
            f"Running extraction for {framework}={model} and prompt={Path(prompt).stem}"
        )

        results = []
        for sql_file, json_file in tqdm(zip(sql_files, json_files, strict=False)):
            # Compute performance
            result = evaluate_extraction_performance(
                framework=framework,
                model=model,
                sql_file=sql_file,
                expected_json_file=json_file,
                prompt_path=prompt,
            )
            # Store performance
            results.append(result)

        # Save results for specific framework-model-prompt
        df_results = pd.DataFrame(results)
        df_results.to_csv(output_file_path, index=False)
        logger.success(f"Results saved into {output_file_path}\n")

# Agregate results

files = glob(f"{output_raw_path}/*csv")
df_results = pd.concat([pd.read_csv(file) for file in files])

df_summary = (
    df_results.groupby(["framework", "model", "prompt"])
    .agg(
        all_exact_match=("exact_match", "all"),
        exact_match_pct=("exact_match", "mean"),
        all_tbl_in_cols=("all_tables_in_columns", "all"),
        tbl_in_cols_pct=("all_tables_in_columns", "mean"),
        tbl_recall_avg=("tbl_recall", "mean"),
        tbl_precision_avg=("tbl_precision", "mean"),
        tbl_f1_avg=("tbl_f1", "mean"),
        col_recall_avg=("col_recall", "mean"),
        col_precision_avg=("col_precision", "mean"),
        col_f1_avg=("col_f1", "mean"),
        avg_exec_time=("exec_time", "mean"),
    )
    .reset_index()
)

df_summary = df_summary.merge(df_model_metadata)
df_summary["prompt"] = df_summary["prompt"].str[:-4]
df_summary["avg_price"] = df_summary[["input_price", "output_price"]].mean(axis=1)
df_summary["total_price"] = df_summary[["input_price", "output_price"]].sum(axis=1)

# Save aggregated results
df_summary.to_csv(output_path / "summary.csv", index=False)
