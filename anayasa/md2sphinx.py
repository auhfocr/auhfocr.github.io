#!/usr/bin/env python3
"""anayasa_hukuku_ders_notlari.md -> Sphinx (reStructuredText) projesi."""
import re
import sys
import unicodedata
from pathlib import Path

from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode

SRC = Path(sys.argv[1])
OUT = Path(sys.argv[2])

# (bölüm, dosya adı, başlık, ayırıcı satır metni [, kaçıncı geçiş])
CHAPTERS = [
    (1, "01-giris-siyasal-iktidar", "Giriş ve Siyasal İktidar", None),
    (1, "02-devlet", "Devlet", '### "DEVLET"'),
    (1, "03-anayasa-kavrami", "Anayasaların Tanımlanması ve Sınıflandırılması", "### ANAYASALARIN TANIMLANMASI"),
    (1, "04-normlar-hiyerarsisi", "Normlar Hiyerarşisi", "### NORMLAR HİYERARŞİSİ"),
    (1, "05-anayasacilik-hareketleri", "Anayasacılık Hareketleri", "### ANAYASACILIK HAREKETLERİ"),
    (1, "06-anayasal-belgeler", "Anayasal Belgeler (İngiltere, ABD, Fransa)", "### ANAYASAL BELGELER"),
    (1, "07-osmanli-turkiye-anayasacilik", "Osmanlı ve Türkiye'de Anayasacılık Hareketleri", "### Osmanlı ve Türkiye'de Anayasacılık Hareketleri"),
    (1, "08-yasama", "Kurucu ve Kurulu İktidar, Yasama Organı (TBMM)", "### İKTİDAR"),
    (1, "09-yurutme-cumhurbaskani", "Yürütme ve Cumhurbaşkanı", "### YÜRÜTME"),
    (1, "10-kanun-yasama-yontemi", "Kanun Kavramı ve Yasama Yöntemleri", "### Kanun Kavramı"),
    (1, "11-yurutmenin-denetlenmesi", "Yürütmenin Denetlenmesi, Cumhurbaşkanı Yardımcıları ve Bakanlar", "### Yürütmenin Denetlenmesi"),
    (1, "12-yurutme-fonksiyonu-kararnameler", "Yürütme Fonksiyonu ve Düzenleyici İşlemler", "### YÜRÜTME FONKSİYONU ve ÖZELLİKLERİ"),
    (1, "13-olaganustu-yonetim", "Olağanüstü Yönetim Usulleri", "### Olağanüstü Yönetim Usulleri"),
    (2, "01-anayasa-yargisi-giris", "Anayasa Yargısı: Giriş ve Temel Kavramlar", "# 2. DÖNEM"),
    (2, "02-hukumet-sistemleri", "Hükümet Sistemleri", "### HÜKÜMET SİSTEMLERİ"),
    (2, "03-devlet-bicimleri", "Devlet Biçimleri", "### DEVLET BİÇİMLERİ"),
    (2, "04-siyasal-sistemler", "Siyasal Sistemler", "### SİYASAL SİSTEMLER"),
    (2, "05-demokrasi", "Demokrasi (Demos - Kratein)", "### DEMOKRASİ (Demos - Kratein)"),
    (2, "06-secim-sistemleri", "Seçim Sistemleri", "### SEÇİM SİSTEMLERİ"),
    (2, "07-aym-kurulusu-gorevleri", "Anayasa Mahkemesinin Kuruluşu ve Görevleri", "### ANAYASA MAHKEMESİNİN KURULUŞU VE ÜYELERİN STATÜSÜ"),
    (2, "08-siyasal-partiler", "Siyasal Partiler", "### SİYASAL PARTİLER"),
    (2, "09-hukuk-devleti", "Hukuk Devleti", "### HUKUK DEVLETİ"),
    (2, "10-hak-ve-ozgurlukler", "1982 Anayasasında Hak ve Özgürlükler", "### 1982 Anayasasında Hak ve Özgürlükler"),
    (2, "11-norm-denetimi-normlar", "Norm Denetimine Tabi Normlar ve Ölçü Normlar", "### Norm Denetimine Tabi Normlar"),
    (2, "12-hak-ozgurluk-sinirlama-koruma", "Temel Hak ve Özgürlüklerin Sınırlandırılması ve Korunması", "### Temel Hak ve Özgürlüklerin Sınırlandırılması"),
    (2, "13-laiklik", "Laiklik", "### LAİKLİK"),
    (2, "14-sosyal-devlet", "Sosyal Devlet", "> **2. Dönem | 12. Hafta | 1/B | ANAYASA HUKUKU | 08/05/2019 (Betacopy 22)**"),
    (2, "15-iptal-davasi", "Anayasa Yargısı: Norm Denetiminin Yolları ve İptal Davası", "### ANAYASA YARGISI", 1),
    (2, "16-sosyal-ekonomik-haklar", "Sosyal Devlet (Devam): Sosyal ve Ekonomik Haklar", "**09.05.2019**"),
    (2, "17-asli-kurucu-iktidar", "Anayasanın Yapılması: Asli Kurucu İktidar", "### ANAYASANIN YAPILMASI VE DEĞİŞTİRİLMESİ"),
    (2, "18-itiraz-yolu", "Anayasa Yargısı: İtiraz Yolu (Somut Norm Denetimi)", "### ANAYASA YARGISI", 2),
    (2, "19-turev-kurucu-iktidar", "Türev Kurucu İktidar ve Anayasanın Değiştirilmesi", "**16.05.2019**"),
    (2, "20-aym-kararlari", "Anayasa Yargısı: AYM Kararları ve Pratik Çalışma", "### ANAYASA YARGISI", 3),
    (2, "21-bireysel-basvuru", "Bireysel Başvuru (Anayasa Şikayeti)", "### BİREYSEL BAŞVURU"),
    (2, "22-anayasa-degisikligi-denetimi", "Anayasa Değişikliklerinin Görüşülmesi, Kabulü ve Denetimi", "**29.05.2019**"),
    (2, "23-kurgusal-pratik-calismalar", "Kurgusal Pratik Çalışmaları", "## Sayfa 553 (Not Sayfa: 559)"),
]

PAGE_RE = re.compile(r"^## (Sayfa \d+.*)$")
SECTION_CHARS = ["=", "-", "~", "^", '"', "'"]


def split_chapters(lines):
    starts = []
    for ch in CHAPTERS:
        marker = ch[3]
        if marker is None:
            starts.append((0, False))
            continue
        nth = ch[4] if len(ch) > 4 else 1
        hits = [i for i, l in enumerate(lines) if l.rstrip("\n") == marker]
        if len(hits) < nth:
            raise SystemExit(f"ayırıcı bulunamadı: {marker!r} #{nth}")
        idx = hits[nth - 1]
        is_heading = marker.startswith("#") and not PAGE_RE.match(marker)
        # Bölüm başlığı sayfanın ilk içeriğiyse sayfa işaretini de yeni bölüme al
        j = idx - 1
        while j >= 0 and (not lines[j].strip() or lines[j].strip() == "---"):
            j -= 1
        start = j if j >= 0 and PAGE_RE.match(lines[j].rstrip("\n")) else idx
        starts.append((start, (idx, is_heading)))
    chunks = []
    for k, (start, drop) in enumerate(starts):
        end = starts[k + 1][0] if k + 1 < len(starts) else len(lines)
        body = lines[start:end]
        if drop and drop[1]:
            body = [l for n, l in enumerate(body, start) if n != drop[0]]
        if k == 0:
            body = [l for l in body if not l.startswith("# Anayasa Hukuku Ders Notları")]
        chunks.append(body)
    return chunks


# ---------------------------------------------------------------- inline
BEFORE_OK = set(" \t\n'\"([{<-/:")
AFTER_OK = set(" \t\n-.,:;!?\\/'\")]}>")


def ok_before(c):
    return c == "" or c in BEFORE_OK or unicodedata.category(c) in ("Ps", "Pi", "Pf", "Pd", "Po", "Zs")


def ok_after(c):
    return c == "" or c in AFTER_OK or unicodedata.category(c) in ("Pe", "Pi", "Pf", "Pd", "Po", "Zs")


def esc(text):
    text = text.replace("\\", "\\\\")
    for ch in "*`|_":
        text = text.replace(ch, "\\" + ch)
    return text


def plain(node):
    """Bir düğümün düz metni (iç içe vurgu reST'te desteklenmez)."""
    if node.type in ("text", "code_inline"):
        return node.content
    if node.type in ("softbreak", "hardbreak"):
        return " "
    if node.type == "html_inline":
        return " " if re.match(r"<br\s*/?>", node.content, re.I) else node.content
    return "".join(plain(c) for c in node.children)


def inline_segments(node):
    """Satır listesi döndürür; her satır (tür, metin) parçalarından oluşur."""
    lines = [[]]
    for c in node.children:
        t = c.type
        if t == "text":
            lines[-1].append(("t", c.content))
        elif t in ("softbreak", "hardbreak"):
            lines.append([])
        elif t == "html_inline":
            if re.match(r"<br\s*/?>", c.content, re.I):
                lines.append([])
            else:
                lines[-1].append(("t", c.content))
        elif t == "strong":
            lines[-1].append(("**", plain(c)))
        elif t == "em":
            # em içinde strong varsa strong olarak bas
            kind = "**" if any(g.type == "strong" for g in c.children) else "*"
            lines[-1].append((kind, plain(c)))
        elif t == "code_inline":
            lines[-1].append(("``", c.content))
        elif t == "link":
            href = c.attrs.get("href", "")
            txt = plain(c)
            lines[-1].append(("link", (txt, href)))
        elif t == "image":
            lines[-1].append(("t", plain(c)))
        else:
            lines[-1].append(("t", plain(c)))
    return lines


def render_segments(segs):
    # bitişik düz metinleri birleştir
    merged = []
    for k, v in segs:
        if k == "t" and merged and merged[-1][0] == "t":
            merged[-1] = ("t", merged[-1][1] + v)
        else:
            merged.append((k, v))
    out = []
    for i, (k, v) in enumerate(merged):
        if k == "t":
            out.append(esc(v))
            continue
        if k == "link":
            txt, href = v
            piece = f"`{esc(txt)} <{href}>`__" if txt.strip() else href
            lead, trail = "", ""
        else:
            raw = v if k == "``" else v
            stripped = raw.strip()
            lead = raw[: len(raw) - len(raw.lstrip())]
            trail = raw[len(raw.rstrip()):]
            if not stripped:
                out.append(esc(raw))
                continue
            if k == "``":
                piece = f"``{stripped}``"
            else:
                piece = f"{k}{esc(stripped)}{k}"
        prev = "".join(out)
        prev_c = (lead[-1:] if lead else prev[-1:])
        nxt_raw = merged[i + 1][1] if i + 1 < len(merged) else ""
        if trail:
            nxt_c = trail[:1]
        elif i + 1 < len(merged) and merged[i + 1][0] == "t":
            nxt_c = nxt_raw[:1]
        elif i + 1 < len(merged):
            nxt_c = "*"  # ardışık işaretleme: ayırıcı gerekir
        else:
            nxt_c = ""
        s = lead
        if not ok_before(prev_c) or (prev.endswith("\\") and not lead):
            s += "\\ "
        s += piece
        if not ok_after(nxt_c):
            s += "\\ "
        s += trail
        out.append(s)
    return "".join(out).rstrip()


BLOCKISH = re.compile(
    r"^(?:[-*+•‣⁃](?:\s|$)|\(?(?:\d+|[a-zA-Z]|[ivxlcdmIVXLCDM]+|#)[.)](?:\s|$)|:|\.\.(?:\s|$)|>>>|-{1,2}\w|\[)"
)
PUNCT_LINE = re.compile(r"^([!-/:-@\[-`{-~])\1+\s*$")


def guard_line(s):
    if BLOCKISH.match(s) or PUNCT_LINE.match(s):
        return "\\" + s
    return s


def render_inline(node):
    lines = [render_segments(segs) for segs in inline_segments(node)]
    lines = [l for l in lines]
    while lines and not lines[-1].strip():
        lines.pop()
    while lines and not lines[0].strip():
        lines.pop(0)
    return lines


def paragraph_block(node):
    lines = render_inline(node)
    if not lines:
        return []
    if len(lines) == 1:
        return [guard_line(lines[0].strip())]
    return ["| " + l.strip() if l.strip() else "|" for l in lines]


# ---------------------------------------------------------------- blocks
class Renderer:
    def __init__(self):
        self.stack = []  # açık başlıkların md seviyeleri

    def blocks(self, nodes):
        out = []
        for n in nodes:
            b = self.block(n)
            if b is None:
                continue
            if out and out[-1] != "":
                out.append("")
            out.extend(b)
        return out

    def block(self, n):
        t = n.type
        if t == "heading":
            return self.heading(n)
        if t == "paragraph":
            return paragraph_block(n.children[0]) or None
        if t in ("bullet_list", "ordered_list"):
            return self.lst(n)
        if t == "blockquote":
            return self.quote(n)
        if t == "table":
            return self.table(n)
        if t == "hr":
            return None
        if t in ("fence", "code_block"):
            body = n.content.rstrip("\n").split("\n")
            return ["::", ""] + ["   " + l for l in body]
        if t == "html_block":
            txt = n.content.strip()
            return [guard_line(esc(txt))] if txt else None
        raise SystemExit(f"bilinmeyen blok: {t}")

    def heading(self, n):
        level = int(n.tag[1])
        title = " ".join(render_inline(n.children[0])).strip()
        raw = plain(n.children[0]).strip()
        m = PAGE_RE.match("## " + raw) if level == 2 else None
        if m:
            return [f".. rubric:: {title}", "   :class: sayfa"]
        if level == 1:
            return [f".. rubric:: {title}"]
        while self.stack and self.stack[-1] >= level:
            self.stack.pop()
        self.stack.append(level)
        depth = len(self.stack)
        ch = SECTION_CHARS[min(depth, len(SECTION_CHARS)) - 1]
        title = guard_line(title)
        width = max(len(title), 4)
        return [title, ch * (width + 2)]

    def lst(self, n):
        ordered = n.type == "ordered_list"
        start = int(n.attrs.get("start", 1)) if ordered else 1
        out = []
        for i, item in enumerate(n.children):
            marker = f"{start + i}." if ordered else "-"
            ind = " " * (len(marker) + 1)
            body = self.blocks(item.children)
            if not body:
                out.append(marker)
                continue
            if body[0].startswith("| ") or body[0] == "|":
                # satır bloğu liste öğesinin ilk satırında olabilir
                pass
            out.append(f"{marker} {body[0]}")
            for l in body[1:]:
                out.append(ind + l if l else "")
        return out

    def quote(self, n):
        children = list(n.children)
        is_note = False
        title = None
        if children and children[0].type == "paragraph":
            inl = children[0].children[0]
            kids = [c for c in inl.children if not (c.type == "text" and not c.content)]
            first = kids[0] if kids else None
            if first is not None and first.type == "strong":
                label = plain(first).strip()
                if re.match(r"^NOT\b", label):
                    is_note = True
                    lbl = label.rstrip(":").strip()
                    if lbl != "NOT":
                        title = "Not" + lbl[3:]
                    # baştaki "NOT:" etiketini kaldır
                    kids = kids[1:]
                    while kids and kids[0].type in ("softbreak", "hardbreak"):
                        kids = kids[1:]
                    if kids and kids[0].type == "text":
                        kids[0].token.content = kids[0].content.lstrip(": ")
                        if not kids[0].content:
                            kids = kids[1:]
                    inl.children = kids
                    if not kids:
                        children = children[1:]
        body = self.blocks(children)
        if is_note:
            head = [f".. admonition:: {esc(title)}", "   :class: note"] if title else [".. note::"]
            if not body:
                return head
            return head + [""] + ["   " + l if l else "" for l in body]
        if not body:
            return None
        # Önceki bloğa bağlanmaması için boş yorum + girintili blok alıntı
        return ["..", ""] + ["   " + l if l else "" for l in body]

    def table(self, n):
        rows = []
        for sect in n.children:  # thead / tbody
            for tr in sect.children:
                cells = []
                for td in tr.children:
                    inl = td.children[0] if td.children else None
                    if inl is None:
                        cells.append([])
                        continue
                    lines = [l.strip() for l in render_inline(inl)]
                    cells.append(self._cell(lines))
                rows.append(cells)
        ncols = max(len(r) for r in rows)
        out = [".. list-table::", "   :header-rows: 1", "   :class: longtable", ""]
        for r in rows:
            r = r + [[]] * (ncols - len(r))
            for ci, cell in enumerate(r):
                prefix = "   * - " if ci == 0 else "     - "
                if not cell:
                    out.append(prefix.rstrip())
                    continue
                out.append(prefix + cell[0])
                for l in cell[1:]:
                    out.append("       " + l if l else "")
        return out

    @staticmethod
    def _cell(lines):
        """<br> ile bölünmüş hücre: satır bloğu; '- ' ile başlayanlar madde."""
        lines = [l for l in lines]
        while lines and not lines[-1]:
            lines.pop()
        if not lines:
            return []
        if len(lines) == 1:
            return [guard_line(lines[0])]
        return ["| " + l if l else "|" for l in lines]


def convert(chunk_lines):
    md = MarkdownIt("commonmark", {"html": True}).enable("table")
    tokens = md.parse("".join(chunk_lines))
    tree = SyntaxTreeNode(tokens)
    r = Renderer()
    return r.blocks(tree.children)


def title_block(title):
    bar = "#" * (len(title) + 2)
    return [bar, " " + title, bar, ""]


def main():
    lines = SRC.read_text(encoding="utf-8").splitlines(keepends=True)
    chunks = split_chapters(lines)
    for d in ("donem1", "donem2"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    for ch, chunk in zip(CHAPTERS, chunks):
        part, fname, title = ch[0], ch[1], ch[2]
        body = convert(chunk)
        text = "\n".join(title_block(title) + body).rstrip() + "\n"
        (OUT / f"donem{part}" / f"{fname}.rst").write_text(text, encoding="utf-8")
        print(f"donem{part}/{fname}.rst  ({len(chunk)} md satırı)")


if __name__ == "__main__":
    main()
