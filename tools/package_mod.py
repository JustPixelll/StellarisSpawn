"""Build the installable archive from the tracked mod source."""
from pathlib import Path
import hashlib
import zipfile

root = Path(__file__).resolve().parent.parent
dist = root / "dist"
dist.mkdir(exist_ok=True)
archive = dist / "Starburst-Tail-Start-v0.1.1.zip"
files = [root / p for p in (
    "niki_starburst_tail_start.mod", "README-FIRST.txt", "SOURCES.txt", "VALIDATION.txt"
)]
files += sorted(p for p in (root / "niki_starburst_tail_start").rglob("*") if p.is_file())
for file in files:
    if not file.is_file():
        raise SystemExit(f"Missing required file: {file}")
with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for file in sorted(files):
        info = zipfile.ZipInfo(file.relative_to(root).as_posix(), (2026, 10, 22, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        z.writestr(info, file.read_bytes())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert "niki_starburst_tail_start.mod" in z.namelist()
    assert "niki_starburst_tail_start/descriptor.mod" in z.namelist()
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
(dist / "SHA256SUMS.txt").write_text("".join(
    f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n"
    for p in sorted(dist.glob("Starburst-Tail-Start-v*.zip"))
))
print(f"{archive.name}: {archive.stat().st_size:,} bytes; ZIP integrity verified")
print(f"SHA256 {digest}")

