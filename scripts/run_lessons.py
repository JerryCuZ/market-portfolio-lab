"""Execute lessons sequentially against one verified snapshot, without changing sources."""
from pathlib import Path
import argparse
import os
import sys
import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from market_data import load_snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', default='latest', help='Local snapshot ID, or latest')
    parser.add_argument('--rates-snapshot', help='Lesson 08 local DFF snapshot ID, or latest')
    args = parser.parse_args()
    _, manifest = load_snapshot(None if args.snapshot == 'latest' else args.snapshot)
    snapshot = manifest['snapshot']
    os.environ['MARKET_LAB_SNAPSHOT'] = snapshot
    if args.rates_snapshot:
        os.environ['MARKET_LAB_RATE_SNAPSHOT'] = args.rates_snapshot
    for key, part in [('MPLCONFIGDIR', 'matplotlib'), ('IPYTHONDIR', 'ipython'),
                      ('JUPYTER_CONFIG_DIR', 'jupyter/config'), ('JUPYTER_RUNTIME_DIR', 'jupyter/runtime')]:
        folder = ROOT / '.cache' / part
        folder.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault(key, str(folder))
    output = ROOT / 'reports' / 'runs' / snapshot
    output.mkdir(parents=True, exist_ok=True)
    for source in sorted((ROOT / 'notebooks').glob('[0-9][0-9]_*.ipynb')):
        print(f'Executing {source.name} on {snapshot}', flush=True)
        notebook = nbformat.read(source, as_version=4)
        NotebookClient(notebook, timeout=180, kernel_name='market-portfolio-lab',
                       resources={'metadata': {'path': str(ROOT)}}).execute()
        nbformat.write(notebook, output / source.name)
        exporter = HTMLExporter()
        exporter.exclude_input = True
        html, _ = exporter.from_notebook_node(notebook)
        (output / (source.stem + '.html')).write_text(html, encoding='utf-8')
    print(f'Completed: {output}')


if __name__ == '__main__':
    main()
