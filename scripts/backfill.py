"""一次性回補過去 ~3 個月：類股指數、上市個股收盤與成交金額、三大法人 → 各 history 檔。跑完再跑 daily.py。"""
import time, datetime as dt
from common import *

# 成員（產業別）— 與 daily.py 同邏輯
def pick(row, *keys):
    for k in row:
        if all(x in k for x in keys): return row[k]
    return None
members = {}
for url, market in (("https://openapi.twse.com.tw/v1/opendata/t187ap03_L", "tse"), ("https://www.tpex.org.tw/openapi/v1/t187ap03_O", "otc")):
    try:
        for row in get_json(url):
            code = (pick(row, "公司代號") or "").strip(); sec = SECTORS.get(str(pick(row, "產業別") or "").strip().zfill(2))
            if code and sec and code not in members: members[code] = sec
    except Exception as e: print("基本資料失敗", url, repr(e))
print("成員", len(members))

idx_hist = load("index_history.json", {}); close_hist = load("close_history.json", {})
flow_hist = load("flow_history.json", {}); amt_hist = load("amt_history.json", {})
DAYS = 100  # 日曆天，約 68 個交易日
end = now().date()
for i in range(DAYS, 0, -1):
    d = end - dt.timedelta(days=i)
    if d.weekday() >= 5: continue
    ds = d.strftime("%Y%m%d")
    if ds in idx_hist and ds in close_hist and ds in flow_hist: continue
    try:
        mi = get_json(f"https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={ds}&type=ALL&response=json")
        if mi.get("stat") != "OK": print(ds, "休市"); time.sleep(3); continue
        day_idx, closes, amts = {}, {}, {}
        for t in mi.get("tables", []):
            title = t.get("title") or ""; fields = t.get("fields") or []
            if "價格指數" in title and "臺灣證券交易所" in title:
                for r in t["data"]:
                    name = r[0].strip(); val = num(r[1])
                    if name.startswith("發行量加權"): day_idx["加權"] = val
                    for sec, pre in INDEX_NAME.items():
                        if name.startswith(pre): day_idx[sec] = val
            if "每日收盤行情" in title and "證券代號" in fields:
                ic, ia, ip = fields.index("證券代號"), fields.index("成交金額"), fields.index("收盤價")
                for r in t["data"]:
                    c = r[ic].strip(); p = num(r[ip]); a = num(r[ia])
                    if p: closes[c] = p; amts[c] = a or 0
        if day_idx: idx_hist[ds] = day_idx
        if closes:
            close_hist[ds] = closes
            total = sum(amts.values()) or 1
            for sec in SECTORS.values():
                amt_hist.setdefault(sec, {})[ds] = round(sum(a for c, a in amts.items() if members.get(c) == sec) / total * 100, 3)
        time.sleep(3)
        t86 = get_json(f"https://www.twse.com.tw/rwd/zh/fund/T86?date={ds}&selectType=ALLBUT0999&response=json")
        day_flow = {}
        for r in t86.get("data", []):
            c = r[0].strip(); net = num(r[-1]); sec = members.get(c)
            if sec and net is not None and c in closes: day_flow[sec] = day_flow.get(sec, 0) + net * closes[c]
        if day_flow: flow_hist[ds] = day_flow
        print(ds, "ok", len(closes), "檔", len(day_idx), "指數", len(day_flow), "類股法人")
    except Exception as e:
        print(ds, "失敗", repr(e))
    time.sleep(3)
    # 每天都存一次，中途斷掉也不會全丟
    save("index_history.json", idx_hist); save("close_history.json", close_hist); save("flow_history.json", flow_hist); save("amt_history.json", amt_hist)
print("完成", len(idx_hist), "天")
