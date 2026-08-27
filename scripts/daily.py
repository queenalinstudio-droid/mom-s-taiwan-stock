"""收盤後跑一次：類股成員、市值排名、類股指數多期報酬、法人買賣超、成交比重、廣度 → data/sectors.json"""
import datetime as dt
from common import *

today = now().strftime("%Y%m%d")

# ---------- 1. 公司基本資料：產業別 + 發行股數 ----------
members = {}  # code -> {name, sector, shares, market}
def pick(row, *keys):
    for k in row:
        if all(x in k for x in keys): return row[k]
    return None
for url, market in (("https://openapi.twse.com.tw/v1/opendata/t187ap03_L", "tse"),
                    ("https://www.tpex.org.tw/openapi/v1/t187ap03_O", "otc"),
                    ("https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O", "otc")):
    try:
        rows = get_json(url)
        if not isinstance(rows, list) or not rows: print("空回應", url); continue
        print("欄位", url, list(rows[0].keys())[:12])
        got = 0
        for row in rows:
            code = (pick(row, "公司代號") or pick(row, "代號") or "").strip()
            ind = str(pick(row, "產業別") or "").strip().zfill(2)
            shares = num(pick(row, "已發行普通股數") or pick(row, "發行股數") or pick(row, "股數"))
            name = pick(row, "公司簡稱") or pick(row, "簡稱") or pick(row, "公司名稱")
            sec = SECTORS.get(ind)
            if code and sec and shares and code not in members:
                members[code] = {"name": name, "sector": sec, "shares": shares, "market": market}; got += 1
        print("基本資料", url, "取得", got, "檔")
    except Exception as e:
        print("基本資料失敗", url, repr(e))
print("成員總數", len(members))

# ---------- 2. 全市場收盤價 / 漲跌 ----------
closes = {}
try:
    for row in get_json("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"):
        c = num(row.get("ClosingPrice")); ch = num(row.get("Change"))
        if row.get("Code") and c: closes[row["Code"]] = {"close": c, "chg": ch or 0, "amt": num(row.get("TradeValue")) or 0}
except Exception as e: print("上市收盤失敗", e)
try:
    for row in get_json("https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes"):
        c = num(row.get("Close")); ch = num(row.get("Change"))
        if row.get("SecuritiesCompanyCode") and c:
            closes[row["SecuritiesCompanyCode"]] = {"close": c, "chg": ch or 0, "amt": num(row.get("TransactionAmount")) or 0}
except Exception as e: print("上櫃收盤失敗", e)

# 收盤價歷史（保留 70 天）供廣度計算
hist = load("close_history.json", {})
hist[today] = {k: v["close"] for k, v in closes.items()}
for d in sorted(hist)[:-70]: hist.pop(d)
save("close_history.json", hist)

# ---------- 3. 類股指數 + 加權指數 ----------
idx_hist = load("index_history.json", {})
try:
    mi = get_json(f"https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={today}&type=ALL&response=json")
    rows = []
    for t in mi.get("tables", []):
        if "價格指數" in (t.get("title") or "") and "臺灣證券交易所" in (t.get("title") or ""): rows = t["data"]
    day = {}
    for r in rows:
        name = r[0].strip(); val = num(r[1])
        if name.startswith("發行量加權"): day["加權"] = val
        for sec, pre in INDEX_NAME.items():
            if name.startswith(pre): day[sec] = val
    if day: idx_hist[today] = day
except Exception as e: print("類股指數失敗", e)
for d in sorted(idx_hist)[:-130]: idx_hist.pop(d)
save("index_history.json", idx_hist)

# ---------- 4. 三大法人（上市 T86）按類股加總 ----------
flow_hist = load("flow_history.json", {})
try:
    t86 = get_json(f"https://www.twse.com.tw/rwd/zh/fund/T86?date={today}&selectType=ALLBUT0999&response=json")
    print("T86 筆數", len(t86.get("data", [])), "欄位", t86.get("fields", [])[-3:])
    day = {}
    for r in t86.get("data", []):
        code = r[0].strip(); net = num(r[-1])  # 三大法人買賣超股數（最後一欄）
        m = members.get(code)
        if m and net is not None and code in closes:
            day[m["sector"]] = day.get(m["sector"], 0) + net * closes[code]["close"]
    if day: flow_hist[today] = day
except Exception as e: print("法人失敗", e)
for d in sorted(flow_hist)[:-30]: flow_hist.pop(d)
save("flow_history.json", flow_hist)

# ---------- 5. 組合成 sectors.json ----------
dates = sorted(idx_hist)
def ret(sec, n):
    if len(dates) <= n or sec not in idx_hist[dates[-1]] or sec not in idx_hist[dates[-1-n]]: return None
    a, b = idx_hist[dates[-1]][sec], idx_hist[dates[-1-n]][sec]
    return (a / b - 1) * 100 if a and b else None
def rel(sec, n):
    s, m = ret(sec, n), ret("加權", n)
    return round(s - m, 2) if s is not None and m is not None else None

total_amt = sum(v["amt"] for v in closes.values()) or 1
amt_hist = load("amt_history.json", {})
cdates = sorted(hist)
out = {"asof": now().strftime("%Y-%m-%d %H:%M"), "market": {"chg1d": round(ret("加權", 1) or 0, 2)}, "sectors": []}
for sec in SECTORS.values():
    ms = [(c, m) for c, m in members.items() if m["sector"] == sec and c in closes]
    for c, m in ms: m["cap"] = m["shares"] * closes[c]["close"] / 1e8  # 億
    ms.sort(key=lambda x: -x[1]["cap"])
    total_cap = sum(m["cap"] for _, m in ms) or 1
    sec_amt = sum(closes[c]["amt"] for c, _ in ms)
    amt_hist.setdefault(sec, {})[today] = sec_amt / total_amt * 100
    for d in sorted(amt_hist[sec])[:-60]: amt_hist[sec].pop(d)
    avg_share = sum(amt_hist[sec].values()) / len(amt_hist[sec])
    # 廣度：站上 20 日均線的比例
    above = n_b = 0
    if len(cdates) >= 20:
        for c, _ in ms:
            ps = [hist[d].get(c) for d in cdates[-20:]]
            if all(ps):
                n_b += 1; above += closes[c]["close"] > sum(ps) / 20
    stocks = [{"code": c, "name": m["name"], "px": closes[c]["close"], "chg": round(closes[c]["chg"] / (closes[c]["close"] - closes[c]["chg"]) * 100, 2) if closes[c]["close"] != closes[c]["chg"] else 0,
               "rank": i + 1, "cap": round(m["cap"], 1), "share": round(m["cap"] / total_cap * 100, 2), "market": m["market"]} for i, (c, m) in enumerate(ms)]
    fd = sorted(flow_hist)
    flow = lambda n: round(sum(flow_hist[d].get(sec, 0) for d in fd[-n:]) / 1e8, 1) if fd else None
    out["sectors"].append({"name": sec, "n": len(ms), "chg1d": round(ret(sec, 1) or 0, 2),
        "rel": {"1d": rel(sec, 1), "5d": rel(sec, 5), "20d": rel(sec, 20), "60d": rel(sec, 60)},
        "flow5": flow(5), "flow20": flow(20),
        "turnover": {"today": round(sec_amt / total_amt * 100, 2), "avg60": round(avg_share, 2)},
        "breadth": round(above / n_b * 100) if n_b else None,
        "top": stocks[:3], "stocks": stocks})
save("amt_history.json", amt_hist)
save("sectors.json", out)
print("ok", len(members), "檔,", len(closes), "收盤價,", len(dates), "天指數")
