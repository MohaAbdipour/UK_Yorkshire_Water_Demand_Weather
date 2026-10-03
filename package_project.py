"""Package an explicit allowlist of source and aggregate results; no raw data."""
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent


def main():
    files = list(ROOT.glob('*.py')) + list(ROOT.glob('*.md'))
    files += [ROOT/n for n in ['.gitignore','pyproject.toml','requirements.txt','requirements-lock.txt']]
    for folder in ['src','tests']:
        files += list((ROOT/folder).glob('*.py'))
    files += list((ROOT/'outputs/final').glob('*.png'))
    for extension in ['*.png','*.svg']:
        files += list((ROOT/'outputs/visual_report').glob(extension))
    for folder,names in {
        'final':['summary.csv','fold_metrics.csv','coverage.csv','provenance.json'],
        'improved':['summary.csv','fold_metrics.csv','selections.csv']}.items():
        files += [ROOT/'outputs'/folder/n for n in names]
    files += [ROOT/'outputs/validation_review/data_quality.png']
    files += list((ROOT/'outputs/validation_review').glob('*.md'))
    files += list((ROOT/'data').rglob('README.md')) + list((ROOT/'data').rglob('.gitkeep'))
    archive = ROOT/'uk-yorkshire-water-demand-weather-final-source.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for file in sorted(set(files)):
            z.write(file,Path(ROOT.name)/file.relative_to(ROOT))
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise RuntimeError('Archive verification failed.')
        print(f'Verified {len(z.namelist())} files: {archive}')


if __name__ == '__main__':
    main()

