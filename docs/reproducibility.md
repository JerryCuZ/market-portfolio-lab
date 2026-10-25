# Reproducing the lessons

## Read without executing

The eight notebooks contain saved outputs. `docs/reports/` contains curated HTML exports; open locally after cloning. The original market snapshot is not included. Reviewing results is different from independently recomputing them.

## Environment

Python 3.11 is the reference version. The full dependency ranges are in `requirements.txt`; `requirements-lock.txt` records the original macOS x86_64 environment. Prefer the ranges on other platforms; resolve wheel availability separately. `environment.yml` is an optional Conda alternative, not required alongside venv.

For offline unit tests only:

```bash
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
```

For notebooks install `requirements.txt` and register the kernel as described in the README. On macOS, `start_lab.command` expects `.venv/bin/python`.

## Acquire your own snapshot

```bash
python src/market_data.py --start 2010-01-01 --end 2026-10-07
```

The requested end is exclusive. Omitting `--end` excludes the current New York date. The downloader writes a timestamped folder, a manifest and `data/raw/latest.json`; successful new snapshots do not overwrite older ones. Internet access and the provider's availability/terms apply.

## Run all eight lessons on one snapshot

```bash
python src/cash_rates.py --start 2010-01-01 --end 2026-10-06
python scripts/run_lessons.py --snapshot latest --rates-snapshot latest
```

`latest` is resolved once, before execution, so all lessons use the same data. An explicit snapshot directory ID is also accepted. The runner verifies checksums, sets `MARKET_LAB_SNAPSHOT`, executes lessons 01–08 in order, and writes executed notebook/HTML copies under `reports/runs/<snapshot>/`. Lesson-generated ledgers and metrics stay in their normal local `reports/` locations. Tracked teaching notebooks are not overwritten by the runner.

Lesson 04 checks its baseline metrics against lesson 03, so order matters. The original snapshot `20261007T234808781424Z` remains the manual default. If you do not have it, use the runner or set `MARKET_LAB_SNAPSHOT` to your acquired ID before opening Jupyter.

Fresh downloads may differ from the original due to revisions. The published figures are tied to the original data, environment and assumptions; matching the requested interval does not guarantee bit-for-bit identical prices or results. Compare downloaded manifests and software versions before investigating differences.

## Publication hygiene

Runtime files, local paths, raw/processed data and generated detailed ledgers are excluded from version control. Curated reports retain educational results but replace machine-specific paths. Notebook authoring helpers rebuild source notebooks and may remove executed outputs; they are for lesson maintenance, not ordinary reproduction.

Lesson 05 is standalone after snapshot loading and requires enough history for 252 prior returns and a subsequent monthly decision. All five scenarios restart from cash at the common start. It exports target/risk audits, holding drift, ledgers, metrics and a run manifest under `reports/05_<snapshot>/`.

Lesson 06 uses the same common start as lesson 05 and compares a 126-return ERC baseline with a 200-price SMA overlay. The baseline comparison is asserted when lesson 05 outputs exist. It requires the longest shared warm-up despite the signal needing only 200 preceding prices. Signal audit, annual/segment metrics, cost sensitivity, ledgers and manifest are exported under `reports/06_<snapshot>/`. The original snapshot is intentionally retained; no fresh market data or current recommendation is generated. Optional historical 2020 diagnostics require that year to exist for a meaningful chart.

Lesson 07 keeps the lesson 06 start and baseline. It checks both prior results when available, exports all five target schedules and ledgers under `reports/07_<snapshot>/`, and explicitly labels the future-informed mean-target control `matched_mean_POSTHOC`. Do not present this diagnostic as a tradable historical strategy.

## Lesson 08 rate input

The cash-rate downloader requests official FRED DFF CSV data (inclusive dates), validates percentage units and stores a content-addressed snapshot under `data/raw/cash_rates/`. Raw rates are not distributed. The teaching ID is `dff_c7cffd0a8f824826`; a fresh download may have revisions and a different hash. For manual execution set `MARKET_LAB_RATE_SNAPSHOT` to your ID or `latest`. With a newer ETF end date, download rates covering that interval too. `--input path/to/DFF.csv` can ingest the same official CSV format if direct access is unavailable.

Lesson 08 writes 12 scenario ledgers, interest events, rate audits and a manifest under `reports/08_<ETF snapshot>_<rate snapshot>/`. It checks zero-yield results against lesson 07 when available, and independently reconciles a pure-cash compound chain. The model uses a seven-calendar-day artificial lag, not historical publication timestamps; it is not point-in-time data. See [research design](08_research_design.md).
