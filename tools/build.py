"""Build the site's index.html from tools/data/*.json.

Usage (from the repo root):  python -I tools/build.py
Optional: python -I tools/build.py --fragment out.html   (no <html>/<head> wrapper, for Claude artifacts)

Inputs (all in tools/):
  data/[ABJY]_*.json   one entry per question (schema in BRIEF.md)
  template.html        page template with /*DATA*/ etc. placeholders
  notes.json           one trend note per unit
  img_manifest.json    "考科|年度|題號" -> [image files in q/]  (written by crop.py)
Outputs: ../index.html (or the --fragment path). Question images live in ../q/, illustrations in ../art/.
"""
import json, glob, os, sys, collections

T = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(T)
fragment = "--fragment" in sys.argv
OUT = sys.argv[sys.argv.index("--fragment") + 1] if fragment else os.path.join(ROOT, "index.html")

UNITS = {
 "U01":"數與式","U02":"多項式函數","U03":"指數與對數","U04":"直線與圓（含線性規劃）","U05":"數列與級數",
 "U06":"排列組合","U07":"機率（含期望值、分布）","U08":"數據分析","U09":"三角","U10":"平面向量",
 "U11":"空間向量與空間幾何","U12":"矩陣與線性方程組","U13":"圓錐曲線","U14":"複數","U15":"極限與函數",
 "U16":"微分","U17":"積分","U18":"數B 專屬應用（經緯、透視、截痕）"}
CN = "零一二三四五六七八九十"

def load(name, default):
    p = os.path.join(T, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default

NOTES = load("notes.json", {})
IMGS = load("img_manifest.json", {})
data = []
for f in sorted(glob.glob(os.path.join(T, "data", "[ABJY]_*.json"))):
    arr = json.load(open(f, encoding="utf-8"))
    print(os.path.basename(f), len(arr)); data += arr

clean = []
for d in data:
    d["year"] = int(d.get("year")); d["no"] = str(d.get("no"))
    try: d["points"] = float(d.get("points") or 0)
    except Exception: d["points"] = 0
    if d["points"] == int(d["points"]): d["points"] = int(d["points"])
    if d.get("unit") not in UNITS: print("SKIP unknown unit", d.get("exam"), d["year"], d["no"], d.get("unit")); continue
    if d.get("difficulty") not in ("易", "中", "難"): d["difficulty"] = "中"
    d["secondary"] = [s for s in (d.get("secondary") or []) if s in UNITS and s != d["unit"]]
    r = d.get("rate")
    d["rate"] = (r / 100 if r > 1 else r) if isinstance(r, (int, float)) else None
    for k in ("topic", "context", "stem", "answer", "solution", "pitfall", "type"): d[k] = str(d.get(k) or "")
    clean.append(d)

missing_img = [f"{d['exam']}|{d['year']}|{int(''.join(c for c in d['no'] if c.isdigit()) or 0)}" for d in clean
               if not IMGS.get(f"{d['exam']}|{d['year']}|{int(''.join(c for c in d['no'] if c.isdigit()) or 0)}")]
years = sorted({d["year"] for d in clean}); papers = len({(d["exam"], d["year"]) for d in clean})
span = years[-1] - years[0] + 1
year_range = f"{years[0]}–{years[-1]}"
span_txt = CN[span] if span <= 10 else str(span)

tot = collections.Counter(); cnt = collections.Counter()
for d in clean: tot[d["unit"]] += d["points"]; cnt[d["unit"]] += 1
print("TOTAL", len(clean), "questions,", papers, "papers,", year_range)
for u, p in tot.most_common(): print(" ", u, UNITS[u], cnt[u], "題", p, "分")
print("unverified:", sum(1 for d in clean if d.get("verified") is False), "| questions without image:", len(missing_img))

art_dir = os.path.join(ROOT, "art")
ART = sorted(os.path.splitext(n)[0] for n in os.listdir(art_dir) if n.startswith("U")) if os.path.isdir(art_dir) else []
js = lambda o: json.dumps(o, ensure_ascii=False).replace("</", "<\\/")
html = open(os.path.join(T, "template.html"), encoding="utf-8").read()
html = (html.replace("/*DATA*/[]", js(clean)).replace("/*UNITS*/{}", js(UNITS)).replace("/*NOTES*/{}", js(NOTES))
            .replace("/*IMGS*/{}", js(IMGS)).replace("/*ART*/[]", js(ART))
            .replace("{{YEAR_RANGE}}", year_range).replace("{{YEAR_SPAN}}", span_txt).replace("{{PAPERS}}", str(papers)))

if not fragment:
    desc = f"看懂命題趨勢，找到備考方向。{year_range} 學測數 A・數 B 與分科數甲・數乙共 {len(clean)} 題，依單元整理出題次數、配分與難度，附原題、答案與解析。"
    head = ('<!doctype html>\n<html lang="zh-Hant-TW">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
            f'<meta name="description" content="{desc}">\n<meta property="og:title" content="數學考點導航">\n'
            f'<meta property="og:description" content="{desc}">\n'
            '<meta property="og:image" content="https://bgjd315-cloud.github.io/gsat-math-map/art/cover.webp">\n'
            '<style>:root{color-scheme:light}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n'
            '</head>\n<body>\n')
    html = head + html + "\n</body>\n</html>\n"
open(OUT, "w", encoding="utf-8").write(html)
print("wrote", OUT, len(html), "bytes")
