#!/usr/bin/env python3
"""OCR sidecar metnini (ocrmypdf --sidecar) haftalık Sphinx RST sayfalarına dönüştürür.

Kullanım:  python3 tools/ocr2rst.py ocr/borclar_ocr.txt docs/source
"""
import re
import sys
from pathlib import Path

AYLAR = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
         "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

DATE_RE = re.compile(r"(\d{1,2})[./](\d{1,2})[./]((?:20)?2[23])\b")
JUNK_RE = re.compile(r"betac|tel\s*:|ankara|dönem|donem|hafta\s|info", re.I)
BULLET_RE = re.compile(r"^(?:[eo]\s+(?=[A-ZÇĞİÖŞÜ])|[»«•]\s+|[*•]\s*|-\s*)(?=\S)")
TITLE_ENUM_RE = re.compile(r"^(?:\(?[0-9]{1,2}|[a-zA-Z]{1,2}|[IVX]{1,4})(?:\.[0-9a-z])?[.)-]+\)?\s*")
ENUM_RE = re.compile(r"^(\(?[0-9A-Za-zÇĞİÖŞÜçğıöşü]{1,3}(?:\.[0-9a-z]{1,2})*)([.)])(\)?)(\s)")

# Haftalık sayfa başlıkları (konu özetleri)
KONULAR = {
    ("guz", 1): "Giriş, borçlar hukukunun temel ilkeleri",
    ("guz", 2): "Borç ilişkisinin içerdiği haklar, sorumluluk",
    ("guz", 3): "Edim türleri, hukuki işlem ve irade beyanı",
    ("guz", 4): "İrade beyanlarının yorumu, hukuki işlem türleri",
    ("guz", 5): "Hukuki işlem ve sözleşme türleri",
    ("guz", 6): "Sözleşmenin kurulması, öneri (icap)",
    ("guz", 7): "Öneri ve kabul, sözleşmelerde şekil",
    ("guz", 8): "Şekil, sözleşme özgürlüğü",
    ("guz", 9): "Sözleşme özgürlüğünün sınırları, kesin hükümsüzlük",
    ("guz", 10): "Genel işlem şartları, muvazaa, inançlı işlem",
    ("guz", 11): "İnançlı işlem, irade bozuklukları",
    ("guz", 12): "Aşırı yararlanma (gabin), sözleşmenin yorumu",
    ("guz", 13): "Temsil",
    ("guz", 14): "Pratik çalışma",
    ("bahar", 1): "Kusursuz sorumluluk",
    ("bahar", 2): "Tehlike sorumluluğu",
    ("bahar", 3): "Maddi ve manevi zararın tazmini",
    ("bahar", 4): "Manevi tazminat, sebepsiz zenginleşme",
    ("bahar", 5): "Sebepsiz zenginleşmede iade borcu",
    ("bahar", 6): "Borçların ifası: seçimlik borçlar, para borçları, faiz",
    ("bahar", 7): "Alacaklı temerrüdü, kötü ifa, borçlu temerrüdü",
    ("bahar", 8): "İfa edilmemenin müeyyideleri, tazminat",
    ("bahar", 9): "Borçlu temerrüdünün sonuçları",
    ("bahar", 10): "Üçüncü kişilere etki, şarta bağlı borçlar, ceza koşulu",
    ("bahar", 11): "Müteselsil borçluluk, taraf değişiklikleri",
    ("bahar", 12): "Borcun sona ermesi, takas, zamanaşımı",
    ("bahar", 13): "Pratik çalışması",
}


def is_marker(line):
    """Ders başlangıcını gösteren tarih satırı mı?"""
    s = line.strip()
    if len(s) > 45 or "Tel" in s:
        return None
    m = DATE_RE.search(s)
    if not m:
        return None
    rest = re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşü]{3,}", DATE_RE.sub("", s))
    if any(w.lower() not in {"hafta", "borçlar", "hukuku", "ders", "notu"} for w in rest):
        return None
    d, mo, y = int(m.group(1)), int(m.group(2)), m.group(3)
    y = int(y) if len(y) == 4 else 2000 + int(y)
    return (y, mo, d)


def is_noise(line):
    s = line.strip()
    letters = sum(c.isalpha() for c in s)
    return len(s) <= 8 and letters <= 1


def escape(text):
    text = text.replace("\\", "\\\\")
    for ch in "*`|_":
        text = text.replace(ch, "\\" + ch)
    return text


def protect_start(text):
    """RST'nin satır başını liste/yorum olarak yorumlamasını engelle."""
    m = ENUM_RE.match(text)
    if m:
        return m.group(1) + "\\" + m.group(2) + text[m.end(1) + 1:]
    if text[:1] in "-+#=~^:>.([":
        return "\\" + text
    return text


def is_caps_heading(text):
    letters = [c for c in text if c.isalpha()]
    if not (4 <= len(text) <= 80) or len(letters) < 4:
        return False
    upper = sum(c.isupper() for c in letters)
    return upper / len(letters) > 0.9 and not text.endswith((",", ";"))


def load_pages(path):
    pages = Path(path).read_text(encoding="utf-8").split("\f")
    out = []
    for no, raw in enumerate(pages, 1):
        lines = [l.rstrip() for l in raw.splitlines()]
        # Sayfa sonundaki sayfa numarası / gürültü satırları
        while lines and (not lines[-1].strip() or is_noise(lines[-1])):
            lines.pop()
        # Fotokopici kapak başlığı: ilk tarih satırından önceki gürültü
        nonblank = [i for i, l in enumerate(lines) if l.strip()]
        for k, i in enumerate(nonblank[:12]):
            if is_marker(lines[i]):
                before = [lines[j] for j in nonblank[:k]]
                if any(JUNK_RE.search(b) for b in before):
                    lines = lines[i:]
                break
        out.append((no, lines))
    return out


def blocks_from_pages(pages):
    """Paragraf blokları üret: (sayfa, [satırlar]). Sayfa geçişlerinde bölünen
    paragrafları birleştirir."""
    blocks = []
    for no, lines in pages:
        cur = []
        first = True
        for l in lines + [""]:
            if l.strip() and is_marker(l):
                # Tarih satırı her zaman kendi bloğu olsun
                if cur:
                    blocks.append((no, cur))
                    first = False
                blocks.append((no, [l.strip()]))
                cur = []
                first = False
                continue
            if l.strip() and not is_noise(l):
                cur.append(l.strip())
                continue
            if not cur:
                continue
            if (first and blocks and blocks[-1][1]
                    and not re.search(r"[.:!?)\"”]$", blocks[-1][1][-1])
                    and cur[0][:1].islower()
                    and not is_marker(cur[0])):
                blocks[-1][1].extend(cur)
            else:
                blocks.append((no, cur))
            cur = []
            first = False
    return blocks


def join_lines(lines):
    text = ""
    for l in lines:
        if not text:
            text = l
        elif re.search(r"[a-zçğıöşü]-$", text) and l[:1].islower():
            text = text[:-1] + l
        else:
            text += " " + l
    return re.sub(r"\s+", " ", text).strip()


def titleish(line):
    words = re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşü']{3,}", TITLE_ENUM_RE.sub("", line))
    if not words:
        return False
    caps = sum(w[0].isupper() for w in words)
    return caps / len(words) >= 0.6


def is_rubric(lines, i):
    """Blok içinde paragraftan önce gelen kısa alt başlık satırı mı?"""
    l = lines[i]
    if len(l) > 90 or BULLET_RE.match(l):
        return False
    nxt = lines[i + 1] if i + 1 < len(lines) else ""
    if l.endswith(":") and (titleish(l) or TITLE_ENUM_RE.match(l)) and len(l) <= 70:
        return True
    return (len(l) <= 60 and titleish(l) and not re.search(r"[.,;!?)]$", l)
            and nxt[:1].isupper() and len(l.split()) >= 2)


def clean_caps(text):
    text = re.sub(r"^[^\wÇĞİÖŞÜ(]+", "", text)
    text = re.sub(r"^([0-9]+[.)-]*\s*)?[a-zçğıöşü]{1,2}\s*(?=[A-ZÇĞİÖŞÜ]{2})", r"\1", text)
    return text.strip()


def render_block(lines):
    """Bir bloğu RST satırlarına çevir; içindeki alt başlıkları ayırır."""
    out = []
    seg = []
    for i, l in enumerate(lines):
        if len(lines) > 1 and is_rubric(lines, i):
            if seg:
                out += render_segment(seg)
                seg = []
            out += render_segment([l])
        else:
            seg.append(l)
    if seg:
        out += render_segment(seg)
    return out


def render_segment(lines):
    out = []
    # Blok içindeki madde işaretli satırları ayrı öğe yap
    items, cur = [], []
    for l in lines:
        if BULLET_RE.match(l) and cur:
            items.append(cur)
            cur = []
        cur.append(l)
    items.append(cur)

    for it in items:
        text = join_lines(it)
        if re.fullmatch(r"[\W_]{3,}", text):
            continue
        if BULLET_RE.match(text):
            body = text
            while BULLET_RE.match(body):
                body = BULLET_RE.sub("", body, count=1)
            out.append("- " + protect_start(escape(body)))
            out.append("")
            continue
        if len(it) == 1 and is_caps_heading(text) and "BAŞARILAR" not in text:
            text = clean_caps(text)
            if text.endswith(":"):
                out += ["**" + escape(text) + "**", ""]
            else:
                out.append(("H", text))
            continue
        body = protect_start(escape(text))
        if body.endswith("::"):
            body = body[:-1] + "\\:"
        if len(it) == 1 and len(text) <= 90 and (text.endswith(":") or titleish(text)) \
                and not re.search(r"[.?!]$", text):
            out.append("**" + body + "**")
        else:
            out.append(body)
        out.append("")
    return out


def heading(text, ch):
    return [text, ch * len(text), ""]


def tarih(t):
    y, mo, d = t
    return f"{d} {AYLAR[mo]} {y}"


def main(src, dst):
    dst = Path(dst)
    pages = load_pages(src)
    blocks = blocks_from_pages(pages)

    # Dersleri (tarih işaretlerine göre) ayır
    lessons = []
    for no, lines in blocks:
        t = is_marker(lines[0]) if len(lines) == 1 else None
        if t:
            lessons.append({"date": t, "pages": [no], "blocks": []})
        elif lessons:
            lessons[-1]["blocks"].append(lines)
            lessons[-1]["pages"].append(no)

    # Haftalara grupla (Salı–Çarşamba dersleri aynı hafta)
    import datetime as dt
    weeks = []
    for les in lessons:
        d = dt.date(*les["date"])
        donem = "guz" if d.year == 2022 else "bahar"
        iso = d.isocalendar()[:2]
        if weeks and weeks[-1]["iso"] == iso:
            weeks[-1]["lessons"].append(les)
        else:
            weeks.append({"donem": donem, "iso": iso, "lessons": [les]})

    counters = {"guz": 0, "bahar": 0}
    toc = {"guz": [], "bahar": []}
    for w in weeks:
        counters[w["donem"]] += 1
        n = counters[w["donem"]]
        w["no"] = n
        konu = KONULAR.get((w["donem"], n), "")
        tarihler = " / ".join(tarih(l["date"]) for l in w["lessons"])
        title = f"{n}. Hafta — {konu}" if konu else f"{n}. Hafta"
        p0 = min(min(l["pages"]) for l in w["lessons"])
        p1 = max(max(l["pages"]) for l in w["lessons"])

        rst = heading(title, "=")
        rst += [f":Ders tarihi: {tarihler}",
                f":Taranmış PDF: s. {p0}–{p1}", ""]
        multi = len(w["lessons"]) > 1
        for les in w["lessons"]:
            if multi:
                rst += heading(f"{tarih(les['date'])} dersi", "-")
            for b in les["blocks"]:
                for item in render_block(b):
                    if isinstance(item, tuple):
                        rst += heading(item[1],
                                       "~" if multi else "-")
                    else:
                        rst.append(item)
        name = f"{w['donem']}/hafta-{n:02d}"
        path = dst / f"{name}.rst"
        path.parent.mkdir(parents=True, exist_ok=True)
        text = "\n".join(rst)
        text = re.sub(r"\n{3,}", "\n\n", text).rstrip() + "\n"
        path.write_text(text, encoding="utf-8")
        toc[w["donem"]].append(f"hafta-{n:02d}")

    for donem, baslik in (("guz", "I. Dönem (Güz 2022)"),
                          ("bahar", "II. Dönem (Bahar 2023)")):
        idx = heading(baslik, "#") + [
            ".. toctree::", "   :maxdepth: 1", ""] + [
            f"   {t}" for t in toc[donem]] + [""]
        (dst / donem / "index.rst").write_text("\n".join(idx), encoding="utf-8")
    print({k: v for k, v in counters.items()}, "hafta yazıldı")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
