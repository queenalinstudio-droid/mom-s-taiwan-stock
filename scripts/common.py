import json, os, datetime as dt, requests
TZ = dt.timezone(dt.timedelta(hours=8))
def now(): return dt.datetime.now(TZ)
DATA = os.path.join(os.path.dirname(__file__), "..", "data")
H = {"User-Agent": "Mozilla/5.0 (mom-stock-board)", "Accept": "application/json"}
def get_json(url, **kw):
    r = requests.get(url, headers=H, timeout=30, **kw); r.raise_for_status(); return r.json()
def load(name, default):
    p = os.path.join(DATA, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default
def save(name, obj):
    os.makedirs(DATA, exist_ok=True)
    json.dump(obj, open(os.path.join(DATA, name), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
def num(x):
    try: return float(str(x).replace(",", "").replace("+", ""))
    except: return None
# TWSE / TPEx 產業別代碼 → 名稱（只列主要類股）
SECTORS = {"24":"半導體","25":"電腦及週邊設備","26":"光電","27":"通信網路","28":"電子零組件","29":"電子通路","31":"其他電子",
           "17":"金融保險","03":"塑膠","10":"鋼鐵","15":"航運","22":"生技醫療","04":"紡織纖維","21":"化學","14":"建材營造","05":"電機機械"}
# 類股指數在 MI_INDEX 表裡的名稱前綴
INDEX_NAME = {"半導體":"半導體類","電腦及週邊設備":"電腦及週邊設備類","光電":"光電類","通信網路":"通信網路類","電子零組件":"電子零組件類",
              "電子通路":"電子通路類","其他電子":"其他電子類","金融保險":"金融保險類","塑膠":"塑膠類","鋼鐵":"鋼鐵類","航運":"航運類",
              "生技醫療":"生技醫療類","紡織纖維":"紡織纖維類","化學":"化學類","建材營造":"建材營造類","電機機械":"電機機械類"}
