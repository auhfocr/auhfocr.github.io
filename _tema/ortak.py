"""Tüm derslerin ortak Sphinx yapılandırması.

Her dersin conf.py dosyası şunu yapar::

    import pathlib, sys
    _kok = next(p for p in pathlib.Path(__file__).resolve().parents
                if (p / "dersler.toml").exists())
    sys.path.insert(0, str(_kok / "_tema"))
    from ortak import yapilandir
    yapilandir(globals(), "ceza")

Ders bilgileri (ad, hoca, yıl…) ``dersler.toml`` dosyasından okunur; tema,
HTML ve LaTeX/PDF ayarları burada tek yerden verilir.
"""

from __future__ import annotations

import pathlib
import tomllib

TEMA_DIZINI = pathlib.Path(__file__).resolve().parent
KOK = TEMA_DIZINI.parent


def kayit() -> dict:
    with open(KOK / "dersler.toml", "rb") as f:
        return tomllib.load(f)


def ders_bilgisi(kimlik: str) -> dict:
    for ders in kayit()["ders"]:
        if ders["kimlik"] == kimlik:
            return ders
    raise KeyError(f"dersler.toml içinde '{kimlik}' kimlikli ders yok")


def pdf_adi(kimlik: str) -> str:
    return f"{kimlik}-ders-notlari.pdf"


def _latex_kacis(metin: str) -> str:
    for a, b in (("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"),
                 ("$", r"\$"), ("#", r"\#"), ("_", r"\_"), ("{", r"\{"),
                 ("}", r"\}"), ("~", r"\textasciitilde{}"), ("^", r"\^{}")):
        metin = metin.replace(a, b)
    return metin


def _latex_ayarlari(ders: dict, site: dict) -> dict:
    sty = (TEMA_DIZINI / "latex" / "ankarahukuk.sty").read_text(encoding="utf-8")
    k = _latex_kacis
    bilgi = "\n".join([
        rf"\renewcommand{{\AUdersAdi}}{{{k(ders['ad'])}}}",
        rf"\renewcommand{{\AUaltBaslik}}{{{k(ders.get('alt_baslik', ''))}}}",
        rf"\renewcommand{{\AUhoca}}{{{k(ders.get('hoca', ''))}}}",
        rf"\renewcommand{{\AUyil}}{{{k(ders.get('yil', ''))}}}",
        rf"\renewcommand{{\AUsube}}{{{k(ders.get('sube', ''))}}}",
        rf"\renewcommand{{\AUuyari}}{{{k(site.get('pdf_uyari') or site.get('uyari', ''))}}}",
    ])
    return {
        "papersize": "a4paper",
        "pointsize": "11pt",
        # Bölüm başlıklarını kendimiz biçimlendiriyoruz (ankarahukuk.sty).
        "fncychap": "",
        # Yazı tipleri: XeLaTeX + fontspec (Türkçe için Sphinx polyglossia yükler).
        "fontpkg": r"\usepackage{ankarahukuk-fontlar}",
        "sphinxsetup": ",".join([
            "TitleColor={HTML}{14284B}",
            "InnerLinkColor={HTML}{14284B}",
            "OuterLinkColor={HTML}{8A6A1F}",
            "VerbatimColor={HTML}{F7F3EA}",
            "VerbatimBorderColor={HTML}{D9CDB0}",
            "hmargin={2.4cm,2.4cm}",
            "vmargin={2.6cm,2.6cm}",
        ]),
        "preamble": sty + "\n" + bilgi,
        "maketitle": r"\AUkapak",
        # Dizin üretmiyoruz (notlarda dizin girdisi yok).
        "makeindex": "",
        "printindex": "",
        "extraclassoptions": "openany,oneside",
    }


def yapilandir(ns: dict, kimlik: str) -> None:
    """``conf.py`` ad alanına ortak ayarları yazar."""
    site = kayit()["site"]
    ders = ders_bilgisi(kimlik)

    baslik = ders["ad"]
    if ders.get("hoca"):
        yazar = ders["hoca"]
    else:
        yazar = f"{site['alt_baslik']} — {ders['sube']}"

    ns.update(
        project=f"{baslik} Ders Notları",
        author=yazar,
        copyright=ders.get("yil", ""),
        version="",
        release="",
        language="tr",
        root_doc=ns.get("root_doc", "index"),
        # -- HTML ---------------------------------------------------------
        html_theme="ankara_hukuk",
        html_theme_path=[str(TEMA_DIZINI)],
        html_title=baslik,
        html_short_title=baslik,
        html_static_path=[],
        html_css_files=[],
        html_show_sourcelink=False,
        html_copy_source=False,
        html_show_sphinx=False,
        html_search_language="tr",
        html_last_updated_fmt="%d.%m.%Y",
        html_permalinks_icon="#",
        html_context={
            "site": site,
            "ders": ders,
            "pdf_adi": pdf_adi(kimlik),
        },
        # -- LaTeX / PDF --------------------------------------------------
        latex_engine="xelatex",
        latex_use_xindy=False,
        latex_toplevel_sectioning=ders.get("latex_ust", "chapter"),
        latex_documents=[
            ("index", f"{kimlik}.tex", f"{baslik} Ders Notları", yazar, "manual"),
        ],
        latex_additional_files=[
            str(TEMA_DIZINI / "latex" / "ankarahukuk-fontlar.sty"),
        ],
        latex_elements=_latex_ayarlari(ders, site),
        latex_show_urls="no",
        # -- EPUB (isteğe bağlı) -------------------------------------------
        epub_title=f"{baslik} Ders Notları",
        epub_author=yazar,
    )
    ns.setdefault("extensions", [])
    if "ankara_hukuk_ek" not in ns["extensions"]:
        ns["extensions"].append("ankara_hukuk_ek")
    ns.setdefault("exclude_patterns", [])
    for desen in ("_build", "build", ".venv", "Thumbs.db", ".DS_Store"):
        if desen not in ns["exclude_patterns"]:
            ns["exclude_patterns"].append(desen)
