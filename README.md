# Provider Evaluation

Analytical pipeline for evaluating data providers: fill rate, freshness, volume coverage, comparison and ranking. Input: zip with provider folders (JSON/CSV/Excel). Output: scored ranking, fill-rate matrix, freshness and volume metrics, HTML/PDF report with AI recommendation.

---

## What it is for

- **Compare several data providers** (e.g. people/contact datasets) on the same criteria.
- **Fill rate**: share of profiles where key fields (email, phone, job title, company, skills, etc.) are present.
- **Freshness**: how recent the data is (e.g. `updated_at` or file dates); stale threshold configurable (default 365 days).
- **Volume**: total counts per query/region from a volume file (Excel/CSV) when available.
- **Single report**: one HTML (and optional PDF) with ranking, fill-rate table, freshness/volume cards, and an LLM-generated recommendation.

---

## Approach and algorithm

1. **Input**: One zip file (e.g. `Archive.zip`). Inside: one folder per provider at top level (`people_context/`, `the_swarm/`, …). Each folder contains sample files (JSON arrays of profiles) and optionally one volume file (Excel/CSV with query/region/total).
2. **Workspace**: Notebook cleans the working directory (keeps `output/`), unzips the archive, removes junk (`__MACOSX`, `._*`).
3. **Discovery**: Scan provider folders for `.json`, `.csv`, `.xlsx`/`.xls`; build a short preview (keys/columns/sample rows) per file.
4. **Structure (LLM or heuristics)**:
   - Which files are **samples** (profile arrays) and which is the **volume** file.
   - For volume file: column roles (`query_col`, `region_col`, `total_col`).
   - How query/region are derived: **from_filename** (e.g. `role_region.json`) or **from_profile** (fields inside each record).
5. **Query/region rule (LLM or heuristics)**: If from_filename, derive mapping (e.g. last token → region, stem → query) using volume file context when available.
6. **Field mapping (LLM or heuristics)**: Map provider-specific field names to a common schema (email, phone, current_job_title, current_company, skills_keywords, work_history, education, location, linkedin_url, etc.). KEY_FIELDS can be suggested by LLM from data preview.
7. **Metrics**:
   - **Fill rate**: per provider and per key field, % of non-empty values in samples (optionally grouped by query/region).
   - **Freshness**: e.g. median/mean days since `updated_at` (or fallback); count of stale profiles (> STALE_DAYS).
   - **Volume**: total records per query/region from volume file; normalized for comparison (e.g. 0–1 by max across providers).
8. **Scoring**: Weighted composite: `FILL_RATE_WEIGHT * fill + FRESHNESS_WEIGHT * freshness_norm + VOLUME_WEIGHT * volume_norm`. Weights and STALE_DAYS are configurable.
9. **Output**: In-memory tables + HTML dashboard (ranking, fill-rate table, freshness/volume cards, comparison, AI recommendation). Report is also saved as standalone HTML and optionally PDF (WeasyPrint). Log is written to a file and can be downloaded in Colab.

Heuristics are used when `OPENROUTER_API_KEY` is not set; with the key, LLM (OpenRouter, default model `anthropic/claude-sonnet-4.6`) is used for structure, query/region rule, volume columns, field mapping, KEY_FIELDS, and final recommendation.

---

## How to use

### Local

1. Clone the repo, create a venv if you want, install: `pandas`, `openpyxl`, `requests`, `json5`. For PDF: `weasyprint`.
2. Put your zip (e.g. `Archive.zip`) in the project root or set env `PROVIDER_ZIP` to its path.
3. Set `OPENROUTER_API_KEY` in the environment for LLM steps (optional; without it, heuristics only).
4. Open `provider_evaluation.ipynb`, run cells in order:
   - Setup → Input (zip path/upload) → Config → Scan → Build structure → Query/region rule → Volume columns → Field mappings → KEY_FIELDS → Load data → Fill rate → Freshness → Volume → Comparison → Score → AI summary → Dashboard → Export report.
5. Reports and log: `output/provider_report.html`, `output/provider_report.pdf` (if WeasyPrint ok), `provider_evaluation_run.log`.

### Google Colab

1. Upload the notebook (or clone from git). Upload `Archive.zip` when the “Input” cell asks for a file (or mount Drive and set path).
2. In Colab Secrets, add `OPENROUTER_API_KEY`.
3. Run all cells. Download the report and log from the last cells.

---

## How to scale to other providers and use cases

- **New provider**: Add a new folder in the zip with the same contract: sample file(s) (JSON arrays of profiles) and optionally one volume file (Excel/CSV). The notebook will pick it up; structure and mapping are inferred by LLM or heuristics. No code change required if the provider fits “samples + optional volume”.
- **Other key fields**: Either set `KEY_FIELDS` in the Config cell or let the LLM suggest them from the data preview (cell “KEY_FIELDS from LLM”).
- **Other weights / staleness**: In Config, change `FILL_RATE_WEIGHT`, `FRESHNESS_WEIGHT`, `VOLUME_WEIGHT` and `STALE_DAYS`.
- **Different LLM**: Change `OPENROUTER_MODEL` in the Setup cell.
- **Caching**: The notebook does not persist structure/mapping to disk by default. To cache, save `structures` and `mappings` (and optionally KEY_FIELDS) after the corresponding cells and load them at the start of the next run to skip LLM calls.
- **Batch / automation**: Run the notebook headlessly (e.g. `jupyter nbconvert --execute provider_evaluation.ipynb`) with `PROVIDER_ZIP` and `OPENROUTER_API_KEY` set; collect reports from `output/`.

---

## Analytical tasks covered

| Task | Where |
|------|--------|
| Fill rate by provider and by key field | Fill rate cell → `fill_key`, dashboard table |
| Freshness (days since update, stale count) | Freshness cell → `fresh_df`, dashboard cards |
| Volume and coverage per query/region | Volume cell → `comp_df`, dashboard |
| Provider comparison (side-by-side) | Comparison cell, dashboard |
| Composite score and ranking | Score cell → `overall_rank`, dashboard |
| AI recommendation | AI summary cell → dashboard block |
| Exportable report | Export cell → HTML + optional PDF |

---

## Project layout

- `provider_evaluation.ipynb` – main pipeline (setup, input, structure, mappings, metrics, report).
- `provider_structures/` – optional cached structure per provider (e.g. `the_swarm.json`, `people_context.json`); can be generated by the notebook or committed as reference.
- `provider_mappings/` – optional cached field mapping per provider; same as above.
- `output/` – generated report and log (gitignored by default).
- `patch_zip_cell.py` – helper script if you need to patch the zip/upload cell (e.g. for automation).

---

## Requirements

- Python 3.10+ (or compatible 3.x).
- `pandas`, `openpyxl`, `requests`, `json5`. Optional: `weasyprint` for PDF.

