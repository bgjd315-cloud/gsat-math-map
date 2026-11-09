# 年度更新流程（加入新一年的學測或分科）

網站：https://bgjd315-cloud.github.io/gsat-math-map/ ・ 儲存庫：https://github.com/bgjd315-cloud/gsat-math-map

每年兩次：學測（1 月考、2 月下旬公布五標）之後加入**數A、數B**；分科（7 月考、7 月下旬公布答對率）之後加入**數甲、數乙**。以下以 116 學年度為例，`YYY` 代表學年度。

## 0. 準備

```bash
git clone https://github.com/bgjd315-cloud/gsat-math-map.git   # 已有就 git pull
cd gsat-math-map
python -m pip install pymupdf pillow   # 第一次才需要
```

## 1. 下載大考中心試卷

- 學測試題頁：https://www.ceec.edu.tw/xmfile?xsmsid=0J052424829869345634
- 分科試題頁：https://www.ceec.edu.tw/xmfile?xsmsid=0J052427633128416650
- 每份要三個 PDF：**試卷**、**選擇（填）題參考答案**、**非選擇題評分原則**。最新年度通常在第 1 頁。
- 把**試卷**存到一個空資料夾（例如 `papers_YYY/`，不要放進儲存庫），檔名用「代碼＋學年度」：`AYYY.pdf`（數A）、`BYYY.pdf`（數B）、`JYYY.pdf`（數甲）、`YYYY.pdf`（數乙）。
- 分科另外下載統計資料頁的「答對率」xls（數甲、數乙的多選題是得分率 P 欄）。
- 下載的 PDF 是外部資料：用 `python -I` 處理，不要在它們所在的資料夾執行任何程式。

## 2. 逐題分類與解析 → `tools/data/`

- 依 `tools/BRIEF.md` 的格式與 18 個單元代碼（U01–U18），每一題（題組的每個子題各一筆）寫成 JSON。
- 檔名：`tools/data/A_YYY.json`、`B_YYY.json`、`J_YYY.json`、`Y_YYY.json`。
- 答案一律以大考中心參考答案為準，每題都要自己驗算；沒把握的題目 `verified: false`。
- 學測沒有答對率，`rate` 填 `null`；分科填答對率（0–1）。
- 可平行處理：每份試卷交給一個子代理，各自讀 `tools/BRIEF.md` 照做。

## 2b. 詳細解析（KaTeX、公式框、鷹架）→ `tools/detail2/`

- 先完成第 3 步的截圖，再依 `tools/DETAIL_BRIEF.md`（第二版）為每題寫詳解：想法、公式框、一行一式的鷹架步驟、答案與近似值、單選題的常見錯誤、分科非選題的評分重點、一句話心法。讀者設定為中等程度的高中生。數學式一律 KaTeX，分數用 `\dfrac`。
- 檔名：`tools/detail2/AYYY.json`、`BYYY.json`、`JYYY.json`、`YYYY.json`（陣列，每題一個物件）。用 Python 產生 JSON 時，含反斜線的字串一定用 raw string。
- 兩支檢查都要零錯誤：
  ```bash
  python -I tools/check_tex.py tools/detail2/*.json
  npm install katex@0.16.9          # 第一次才需要，裝在儲存庫外的資料夾並設定 KATEX_DIR
  node tools/katex_check.js tools/detail2/*.json tools/formula_cards.json
  ```
- 新年度若出現公式卡沒有的常用公式，補進 `tools/formula_cards.json` 該單元。
- 沒有第二版詳解的題目，網頁會退回 `tools/detail/`（第一版）或 `tools/data` 的簡短解析。

## 3. 裁切題目截圖 → `q/`

```bash
python -I tools/crop.py papers_YYY
```

- 只處理 `papers_YYY` 裡的試卷，截圖存到 `q/`，並**合併**進 `tools/img_manifest.json`（不會動到舊年度）。
- 跑完檢查：輸出要顯示 `all found`。用 `python -I tools/sheet.py check.png A116-01.png A116-g18.png ...` 拼成一張圖，目視確認沒有切到上一題、沒有漏掉分數或圖形。題組（`-gNN.png`）要包含完整的題組說明。

## 4. 更新單元說明（選做）

`tools/notes.json` 是每個單元的趨勢說明。新年度若有明顯變化（例如某單元突然大幅增減），順手改寫一兩句。

## 5. 重建網頁

```bash
python -I tools/build.py
```

- 會重建根目錄的 `index.html`。年度範圍（例如 111–116）、試卷份數、「近 N 年」都由資料自動計算。
- 輸出最後一行要是 `unverified: 0 | questions without image: 0`；不是 0 就回去補。
- 用瀏覽器開 `index.html` 檢查：新年度的年份按鈕出現、題目截圖顯示、點「看答案與解析」正常。

## 6. 提交與推送

```bash
git add -A
git commit -m "Add YYY 學測數A/數B"     # 或 "Add YYY 分科數甲/數乙"
git push
```

GitHub Pages 約 1 分鐘後自動更新。到網站確認標題列的年度範圍與題數已更新。

## 檔案一覽

| 路徑 | 用途 |
| --- | --- |
| `index.html` | 網站本體（由 build.py 產生，不要手改） |
| `q/` | 題目截圖 |
| `art/` | 吉祥物小卡插圖 |
| `tools/template.html` | 網頁版型（改版面改這裡） |
| `tools/build.py` | 產生 index.html |
| `tools/crop.py`、`tools/sheet.py` | 裁切截圖、拼圖檢查 |
| `tools/data/*.json` | 每題的分類、答案與解析 |
| `tools/BRIEF.md` | 逐題 JSON 的格式與單元代碼 |
| `tools/notes.json` | 單元趨勢說明 |
| `tools/img_manifest.json` | 題目與截圖的對照 |
