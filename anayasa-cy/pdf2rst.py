"""Anayasa Hukuku ders notu PDF'ini Sphinx (reStructuredText) projesine dönüştürür."""
import re
import sys
import unicodedata
from pathlib import Path

import pymupdf

PDF = Path(sys.argv[1])
OUT = Path(sys.argv[2])

PLAIN, BOLD, ITALIC = 0, 1, 2
RIGHT_EDGE = 525  # bu x'ten önce biten satır paragraf sonu sayılır

# (paragraf başlangıcı, klasör/dosya, başlık)
CHAPTERS = [
    ("Yürürlükteki Hukuk:", "donem1/01-temel-kavramlar", "Temel Kavramlar: Anayasa, İktidar, Devlet ve Ulus"),
    ("John Boden:", "donem1/02-egemenlik", "Egemenlik"),
    ("Maddi anlamda anayasa:", "donem1/03-anayasa-turleri", "Anayasa Kavramı ve Anayasa Türleri"),
    ("Anayasanın İşlevi:", "donem1/04-anayasanin-islevleri", "Anayasanın İşlevleri"),
    ("Anayasacılık Hareketleri:", "donem1/05-anayasacilik-hareketleri", "Anayasacılık Hareketleri"),
    ("Sened-i İttifak", "donem1/06-turk-anayasal-gelismesi", "Osmanlı–Türk Anayasal Gelişmesi"),
    ("Devlet Biçimi", "donem1/07-devlet-bicimleri", "Devlet Biçimleri: Üniter, Federal ve Bölgeli Devlet"),
    ("Yasama, yürütme ve yargı işlerinin", "donem1/08-devlet-fonksiyonlari", "Devletin Temel Fonksiyonları ve Yasama İşlemleri"),
    ("Yasama Organının Kurulu", "donem1/09-yasama-organi", "Yasama Organı (TBMM)"),
    ("Yürütme Organı: Tekçi", "donem1/10-yurutme-organi", "Yürütme Organı ve Cumhurbaşkanı"),
    ("Anayasanın Üstünlüğü ve Bağlay", "donem1/11-anayasanin-ustunlugu", "Anayasanın Üstünlüğü, Seçim Süreci ve Olağanüstü Hal"),
    ("Hükümet Sistemleri:", "donem1/12-hukumet-sistemleri", "Hükümet Sistemleri: Meclis Hükümeti ve Parlamenter Sistem"),
    ("II. Dönem 22 Şubat 2023", "donem2/01-22-subat", "22 Şubat 2023 — Yarı Başkanlık ve Başkanlık Sistemleri"),
    ("7 Mart 2023", "donem2/02-07-mart", "7 Mart 2023 — Demokrasi"),
    ("14 Mart 2023", "donem2/03-14-mart", "14 Mart 2023 — Seçimler ve Seçim Sistemleri"),
    ("21 Mart 2023", "donem2/04-21-mart", "21 Mart 2023 — Siyasal Partiler"),
    ("28 Mart 2023", "donem2/05-28-mart", "28 Mart 2023 — Hukuk Devleti"),
    ("29 Mart 2023", "donem2/06-29-mart", "29 Mart 2023 — Yargı Bağımsızlığı ve Eşitlik İlkesi"),
    ("4 Nisan 2023", "donem2/07-04-nisan", "4 Nisan 2023 — İnsan Hakları ve Temel Hakların Sınırlandırılması"),
    ("12 Nisan 2023", "donem2/08-12-nisan", "12 Nisan 2023 — Kötüye Kullanma Yasağı ve Laiklik"),
    ("18 Nisan 2023", "donem2/09-18-nisan", "18 Nisan 2023 — Din ve Vicdan Özgürlüğü, Sosyal Devlet"),
    ("25 Nisan 2023", "donem2/10-25-nisan", "25 Nisan 2023 — Kolektif Haklar ve Anayasaların Yapılması"),
    ("02 Mayıs 2023", "donem2/11-02-mayis", "2 Mayıs 2023 — Asli ve Türev Kurucu İktidar"),
    ("9 Mayıs 2023", "donem2/12-09-mayis", "9 Mayıs 2023 — Anayasanın Değiştirilmesi"),
]

START_OK = set("-:/'\"<([{")
END_OK = set("-.,:;!?\\/'\")]}>")


def is_punct(ch):
    return unicodedata.category(ch).startswith("P")


def ok_before(ch):
    return ch.isspace() or ch in START_OK or (ord(ch) > 127 and is_punct(ch))


def ok_after(ch):
    return ch.isspace() or ch in END_OK or (ord(ch) > 127 and is_punct(ch))


def esc(t):
    return re.sub(r"([\\*`|_])", r"\\\1", t)


def style_of(span):
    f = span["font"]
    if "Bold" in f or span["flags"] & 16:
        return BOLD
    if "Italic" in f or span["flags"] & 2:
        return ITALIC
    return PLAIN


def read_lines(doc):
    """Sayfa altbilgisi (sayfa numarası) hariç tüm satırları (runs, x1) olarak döndürür."""
    for page in doc:
        for b in page.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                runs = [(s["text"], style_of(s)) for s in l["spans"]]
                text = "".join(t for t, _ in runs).strip()
                if not text:
                    continue
                if l["bbox"][1] > 770 and text.isdigit():
                    continue
                yield runs, l["bbox"][2]


def norm_runs(runs):
    out = []
    for t, st in runs:
        if not t:
            continue
        if not t.strip():
            st = PLAIN if not out else out[-1][1]
        if out and out[-1][1] == st:
            out[-1] = (out[-1][0] + t, st)
        else:
            out.append((t, st))
    return out


def paragraphs(doc):
    para, prev_end_short, prev_last_style = [], True, PLAIN
    for runs, x1 in read_lines(doc):
        runs = norm_runs([(re.sub(r"\s+", " ", t), st) for t, st in runs])
        first_style = next(st for t, st in runs if t.strip())
        last_style = [st for t, st in runs if t.strip()][-1]
        new = prev_end_short or (first_style == BOLD and prev_last_style != BOLD)
        if new and para:
            yield norm_runs(para)
            para = []
        if para:
            joint = para[-1][1] if para[-1][1] == first_style else PLAIN
            para.append((" ", joint))
        para.extend(runs)
        prev_end_short = x1 < RIGHT_EDGE
        prev_last_style = last_style
    if para:
        yield norm_runs(para)


def plain(runs):
    return re.sub(r"\s+", " ", "".join(t for t, _ in runs)).strip()


def render(runs):
    out = ""
    for i, (t, st) in enumerate(runs):
        if st == PLAIN or not t.strip():
            out += esc(t)
            continue
        lead = t[: len(t) - len(t.lstrip())]
        trail = t[len(t.rstrip()):]
        core = esc(t.strip())
        mark = "**" if st == BOLD else "*"
        out += esc(lead)
        if out and not ok_before(out[-1]):
            out += "\\ "
        out += mark + core + mark
        out += trail
        if not trail and i + 1 < len(runs):
            nxt = runs[i + 1][0]
            if nxt and not ok_after(nxt[0]):
                out += "\\ "
    out = re.sub(r" {2,}", " ", out).strip()
    # Paragraf başında RST'nin yanlış yorumlayabileceği ".." gibi yapılar
    if out.startswith(".."):
        out = "\\" + out
    # Paragraf başındaki "1.", "md.", "a)" gibi ifadeler liste sanılmasın
    if re.match(r"\(?[0-9A-Za-z]{1,5}[.)] ", out):
        out = "\\" + out
    return out


def heading(text, ch):
    return f"{text}\n{ch * len(text)}\n"


def is_heading(runs, text):
    if len(text) > 110 or not text or text[0].islower() or text.endswith("."):
        return False
    if ":" in text.rstrip(" :"):
        return False
    return all(st == BOLD for t, st in runs if any(c.isalnum() for c in t))


def main():
    doc = pymupdf.open(PDF)
    chapters = {}
    order = []
    current = None
    found = set()
    for runs in paragraphs(doc):
        text = plain(runs)
        if not text:
            continue
        if text.startswith("ANAYASA HUKUKU I. DÖNEM") or text.startswith("Hazırlayan:"):
            continue
        hit = next((c for c in CHAPTERS if text.startswith(c[0]) and c[0] not in found), None)
        if hit:
            found.add(hit[0])
            current = hit
            order.append(hit)
            chapters[hit[1]] = [heading(hit[2], "=")]
            # Tarih satırlarını başlığa taşıdık; paragraf olarak tekrar yazma
            if re.fullmatch(r"(II\. Dönem )?\d{1,2} \w+ +2023", text):
                continue
        if current is None:
            raise SystemExit(f"Bölüm başlamadan paragraf: {text[:60]}")
        body = chapters[current[1]]
        if is_heading(runs, text):
            title = text.rstrip(" :")
            if current[2].startswith(title):
                continue
            body.append(heading(title, "-"))
        else:
            body.append(render(runs) + "\n")
    missing = [c[0] for c in CHAPTERS if c[0] not in found]
    if missing:
        raise SystemExit(f"Bulunamayan bölüm işaretleri: {missing}")
    for c in order:
        p = OUT / (c[1] + ".rst")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("\n".join(chapters[c[1]]), encoding="utf-8")
    print(f"{len(order)} bölüm yazıldı")


main()
