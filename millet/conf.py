# Sphinx yapılandırması — Milletlerarası Hukuk
# Ortak tema/HTML/PDF ayarları: _tema/ortak.py · Ders bilgileri: dersler.toml
import pathlib
import sys

_kok = next(p for p in pathlib.Path(__file__).resolve().parents if (p / "dersler.toml").exists())
sys.path.insert(0, str(_kok / "_tema"))
from ortak import yapilandir  # noqa: E402

# Notlar Markdown (MyST) biçiminde
extensions = ["myst_parser"]
source_suffix = {".md": "markdown"}
myst_enable_extensions = ["deflist", "smartquotes"]
myst_heading_anchors = 3
exclude_patterns = [
    "README.md",
    "milletlerarasi_hukuk_ders_notlari.md",  # orijinal tek dosya (kaynak arşivi)
]

yapilandir(globals(), "millet")
