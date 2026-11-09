"""Crop each question from official CEEC exam PDFs into PNGs.

Usage (from the repo root):  python -I tools/crop.py <papers_dir>
<papers_dir> holds PDFs named <code><year>.pdf: A=數A, B=數B, J=數甲, Y=數乙 (e.g. A116.pdf, J116.pdf).
Only papers in <papers_dir> are processed; images go to q/ and are MERGED into tools/img_manifest.json.
Questions to look for come from tools/data/*.json, so add the year's JSON data first.
"""
import sys, re, os, json, glob, io, pymupdf
from PIL import Image
T = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(T)
PAP = sys.argv[1]; OUT = os.path.join(ROOT, "q")
os.makedirs(OUT, exist_ok=True)
EX = {"A": "數A", "B": "數B", "J": "數甲", "Y": "數乙"}
data = []
for f in sorted(glob.glob(os.path.join(T, "data", "[ABJY]_*.json"))):
    data += json.load(open(f, encoding="utf-8"))
need = {}
for d in data: need.setdefault((d["exam"], int(d["year"])), set()).add(int(re.match(r"\d+", str(d["no"])).group()))
NUM = re.compile(r"^(\d{1,2})\s*[\.．]\s*\S?")
STOP = re.compile(r"^(參考公式|一|二|三|四|第壹|第貳|說明|第\s*\d+.{0,8}題組|\-\s*\d+\s*\-|◎|※|請記得|以下|.*題組)")
MAN = os.path.join(T, 'img_manifest.json')
manifest = json.load(open(MAN, encoding='utf-8')) if os.path.exists(MAN) else {}; log = []
ZOOM = 2.0
for fn in sorted(os.listdir(PAP)):
    code, year = fn[0], int(fn[1:4]); exam = EX[code]
    doc = pymupdf.open(os.path.join(PAP, fn))
    want = need.get((exam, year), set())
    marks = []   # (page, y, kind, num, text)
    ctop = {}
    ltops = {}
    for pi, pg in enumerate(doc):
        H = pg.rect.height
        for b in pg.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                t = "".join(s["text"] for s in l["spans"]).strip()
                x0, y0, x1, y1 = l["bbox"]
                if not t or y0 < 72 or y0 > H - 60: continue
                ctop[pi] = min(ctop.get(pi, 9999), y0)
                ltops.setdefault(pi, []).append((y0, y1, x0))
                if re.search(r"背面還有|請翻頁|試題結束|以下空白", re.sub(r"\s", "", t)):
                    marks.append((pi, y0 - 16, "s", None, t)); continue
                if x0 > 75: continue
                m = NUM.match(t)
                if m and int(m.group(1)) in want:
                    marks.append((pi, y0, "q", int(m.group(1)), t))
                elif re.search(r"(\d+)\s*(?:[-–－~～]|至第?)\s*(\d+)\s*題\s*為\s*題組", t):
                    g = re.search(r"(\d+)\s*(?:[-–－~～]|至第?)\s*(\d+)\s*題\s*為\s*題組", t)
                    marks.append((pi, y0, "g", [int(g.group(1)), int(g.group(2))], t))
                elif STOP.match(t):
                    marks.append((pi, y0, "s", None, t))
    marks.sort(key=lambda m: (m[0], m[1]))
    seen = set(); clean = []
    for m in marks:
        if m[2] == "q":
            if m[3] in seen: continue
            # enforce increasing order
            if seen and m[3] < max(seen): continue
            seen.add(m[3])
        clean.append(m)
    missing = sorted(want - seen)
    if missing: log.append(f"{fn} missing {missing}")
    def crop(pi, ya, yb, name):
        pg = doc[pi]
        W = pg.rect.width
        rect = pymupdf.Rect(48, max(60, ya - 2), W - 40, min(pg.rect.height - 50, yb - 3))
        if rect.height < 12: return None
        pix = pg.get_pixmap(matrix=pymupdf.Matrix(ZOOM, ZOOM), clip=rect)
        im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("L")
        # trim bottom whitespace
        px = im.load(); w, h = im.size
        last = h - 1
        while last > 10 and min(px[x, last] for x in range(0, w, 3)) > 245: last -= 1
        im = im.crop((0, 0, w, min(h, last + 14)))
        im = im.quantize(colors=16)
        path = os.path.join(OUT, name)
        im.save(path, optimize=True)
        return name
    pages_px = {}
    def page_rows(pi):
        if pi not in pages_px:
            pg = doc[pi]
            pix = pg.get_pixmap(matrix=pymupdf.Matrix(2, 2))
            im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("L")
            w, h = im.size; px = im.load()
            x0, x1 = 48 * 2, int((pg.rect.width - 40) * 2)
            pages_px[pi] = [any(px[x, r] < 200 for x in range(x0, x1, 2)) for r in range(h)]
        return pages_px[pi]
    def top_of(pi, y):
        rows = page_rows(pi); r = int(y * 2) - 1; limit = max(0, r - 90); blank = 0
        while r > limit:
            if rows[r]:
                blank = 0
            else:
                blank += 1
                if blank >= 7: return (r + blank) / 2 + 1
            r -= 1
        return y - 4
    def guard(pi, y, top):
        # do not climb past a text line that starts at the left margin (belongs to the previous block)
        for a, b, x in ltops.get(pi, []):
            if x < 100 and top - 1 <= a < y - 3 and b <= y + 1:
                top = max(top, b + 1)
        return top
    def after_group_top(pi, y):
        L = ltops.get(pi, [])
        def left_row(a):
            return any(x2 < 100 and abs(a2 - a) < 10 and abs(a2 - y) > 2 for a2, b2, x2 in L)
        c = [a for a, b, x in L if y - 32 <= a <= y and x > 130 and not left_row(a)]
        return (min(c) if c else y) - 2
    out = []
    for i, m in enumerate(clean):
        if m[2] not in ("q", "g"):
            out.append(m); continue
        prev = clean[i - 1] if i else None
        if m[2] == "q" and prev and prev[2] == "g" and prev[0] == m[0]:
            out.append((m[0], after_group_top(m[0], m[1])) + m[2:])
        else:
            out.append((m[0], guard(m[0], m[1], top_of(m[0], m[1]))) + m[2:])
    clean = out
    groups = {}
    # continuation: content above first marker on a page belongs to previous page's last question
    cont = {}
    for pi in range(1, doc.page_count):
        first = next((m for m in clean if m[0] == pi), None)
        if first is None or pi not in ctop: continue
        if first[1] - ctop[pi] > 60:
            prev = [m for m in clean if m[0] == pi - 1]
            if prev and prev[-1][2] in ("q", "g"):
                cont[(pi - 1, prev[-1][1])] = (pi, ctop[pi], first[1])
    for i, m in enumerate(clean):
        pi, y = m[0], m[1]
        nxt = next((n for n in clean[i+1:] if n[0] == pi), None)
        yb = nxt[1] if nxt else doc[pi].rect.height - 60
        if m[2] == "q":
            name = crop(pi, y, yb, f"{code}{year}-{m[3]:02d}.png")
            manifest[f"{exam}|{year}|{m[3]}"] = [name]
            c = cont.get((pi, y))
            if c:
                n2 = crop(c[0], c[1] + 6, c[2], f"{code}{year}-{m[3]:02d}b.png")
                if n2: manifest[f"{exam}|{year}|{m[3]}"].append(n2); log.append(f"cont {code}{year}-{m[3]}")
        elif m[2] == "g" and len(m[3]) == 2:
            name = crop(pi, y, yb, f"{code}{year}-g{m[3][0]}.png")
            for k in range(m[3][0], m[3][1] + 1): groups[k] = name
    for k, g in groups.items():
        key = f"{exam}|{year}|{k}"
        if key in manifest and g: manifest[key] = [g] + manifest[key]
json.dump(manifest, open(MAN, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("\n".join(log) or "all found"); print(len(manifest), "questions with images")
