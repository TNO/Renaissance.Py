from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
ALLOWED_DIRS = {
    DOCS / 'assets' / 'images' / 'architecture',
    DOCS / 'assets' / 'images' / 'notation',
    DOCS / 'assets' / 'images' / 'logos',
    DOCS / 'user' / 'concepts' / 'matching',
    DOCS / 'user' / 'features' / 'pattern-matching',
    DOCS / 'developer' / 'architecture' / 'images',
}
NAME_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*\.(svg|png|jpg|jpeg|gif)$')

errors = []
for path in DOCS.rglob('*'):
    if path.is_file() and path.suffix.lower() in {'.svg', '.png', '.jpg', '.jpeg', '.gif'}:
        if path.parent not in ALLOWED_DIRS:
            errors.append(f'Unexpected image location: {path.relative_to(ROOT)}')
        if not NAME_RE.fullmatch(path.name):
            errors.append(f'Unexpected image file name: {path.relative_to(ROOT)}')

if errors:
    raise SystemExit('\n'.join(errors))
print('Image policy check passed.')
