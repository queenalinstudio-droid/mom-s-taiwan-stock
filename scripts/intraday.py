"""盤中每 10 分鐘：抓類股前三名＋所有類股成員的即時報價（分批）→ data/quotes.json"""
import time
from common import *
sec = load("sectors.json", None)
if not sec: raise SystemExit("還沒有 sectors.json，先跑 daily.py")
codes = {}
for s in sec["sectors"]:
    for st in s["stocks"]: codes[st["code"]] = st["market"]
extra = load("watch.json", [])  # 可自行加碼要盯的代號
for c in extra: codes.setdefault(c, "tse")
quotes = {}
items = list(codes.items())
for i in range(0, len(items), 80):
    batch = "|".join(f"{m}_{c}.tw" for c, m in items[i:i + 80])
    try:
        js = get_json(f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={batch}&json=1&delay=0")
        for r in js.get("msgArray", []):
            z, y = num(r.get("z")), num(r.get("y"))  # z 成交價, y 昨收
            if not z or z <= 0:  # 沒成交用買賣中價
                b, a = (r.get("b") or "").split("_")[0], (r.get("a") or "").split("_")[0]
                b, a = num(b), num(a); z = (b + a) / 2 if b and a else None
            if z and y: quotes[r["c"]] = {"px": z, "chg": round((z / y - 1) * 100, 2), "t": r.get("t")}
    except Exception as e: print("報價失敗", e)
    time.sleep(1.5)
# 加權指數
try:
    js = get_json("https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_t00.tw&json=1&delay=0")
    r = js["msgArray"][0]; z, y = num(r.get("z")), num(r.get("y"))
    if z and y: quotes["_TAIEX"] = {"px": z, "chg": round((z / y - 1) * 100, 2)}
except Exception as e: print("加權失敗", e)
save("quotes.json", {"asof": now().strftime("%Y-%m-%d %H:%M"), "q": quotes})
print("ok", len(quotes), "檔報價")
