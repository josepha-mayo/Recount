"""Apply the checked integration, then account for its one new reported asset."""
from pathlib import Path
import runpy
root=Path(__file__).resolve().parents[1]
runpy.run_path(str(root/'scripts/apply_bundled_voice.py'))
p=root/'tests/browser_readback_barrier.py'
s=p.read_text()
old="len(r['asset_sha256'])==9"
assert old in s,'Expected inherited asset-count assertion missing'
s=s.replace(old,"len(r['asset_sha256'])==10 and 'audio-readback.mjs' in r['asset_sha256']")
p.write_text(s)
print('Report assertion includes the new playback module; credential/privacy checks unchanged.')
