# 媽媽的台股類股看板

手機打開就能看：16 個主要類股今天強弱、資金輪動（1日/1週/1月/3月相對大盤、法人買賣超、成交比重、廣度）、每個類股前三大、媽媽在該類股的持股與各批損益、ETF 對照。

## 怎麼運作
- `scripts/daily.py`：每個交易日 15:10 自動跑，從證交所/櫃買中心抓收盤資料，算類股數字 → `data/sectors.json`
- `scripts/intraday.py`：開盤時間每 10 分鐘抓即時報價 → `data/quotes.json`
- `index.html`：網頁，讀上面兩個檔案。**持股資料不在這裡**，網頁會從媽媽自己的 Google 試算表讀（網址只存在手機裡）。

## 第一次設定（做一次）
1. 把這些檔案全部上傳到這個 repo（GitHub 網頁：Add file → Upload files，整個資料夾拖進去，Commit）。
2. **Settings → Actions → General → Workflow permissions** 選 **Read and write permissions** → Save。
3. **Actions** 分頁 → 左邊點「收盤後更新類股資料」→ 右邊 **Run workflow** → 等 1～2 分鐘變綠勾。（第一次會失敗很正常，把紅字截圖貼給我。）
4. **Settings → Pages → Branch** 選 `main`、資料夾 `/ (root)` → Save。一分鐘後會出現網址，長這樣：`https://queenalinstudio-droid.github.io/mom-s-taiwan-stock/`
5. 媽媽的 Google 試算表：**檔案 → 共用 → 發布到網路** → 選「交易紀錄」工作表、格式 **CSV** → 發布 → 複製網址。
6. 用媽媽手機打開第 4 步的網址 → **設定** 分頁 → 貼上網址 → 儲存。加到主畫面就像 APP。

## 平常
- 不用做任何事。買賣股票時只改 Google 試算表的「交易紀錄」。
- 1 月 / 3 月的數字要累積 20 / 60 個交易日後才會出現，前幾週會顯示「—」。

## 注意
- 這個 repo 是公開的，所以裡面**沒有**任何持股資料，只有公開市場資料。持股網址只在手機裡。
- 證交所偶爾改格式，Actions 會變紅叉；把錯誤訊息貼給我修就好。
