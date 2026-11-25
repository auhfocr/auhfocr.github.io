# Sphinx yapılandırması — İdare Hukuku
# Ortak tema/HTML/PDF ayarları: _tema/ortak.py · Ders bilgileri: dersler.toml
import pathlib
import sys

_kok = next(p for p in pathlib.Path(__file__).resolve().parents if (p / "dersler.toml").exists())
sys.path.insert(0, str(_kok / "_tema"))
from ortak import yapilandir  # noqa: E402

yapilandir(globals(), "idare")
