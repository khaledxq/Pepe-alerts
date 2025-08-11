import os, time, requests

BAPI = "https://api.binance.com"

def getenv_float(name, default):
    v = os.environ.get(name, "")
    try: return float(v.strip())
    except: return default

def now_ms(): return int(time.time()*1000)

TG_TOKEN = os.environ["TELEGRAM_TOKEN"]
TG_CHAT  = os.environ["TELEGRAM_CHAT_ID"]

SYMBOLS = [s.strip().upper() for s in (os.environ.get("SYMBOLS") or
           "PEPEUSDT,DOGEUSDT,ETHUSDT,BTCUSDT,XRPUSDT,ADAUSDT,ADXUSDT,NFPUSDT,MDTUSDT,BNBUSDT").split(",") if s.strip()]

WINDOW_MIN       = int(getenv_float("WINDOW_MIN", 5))
NET_BUY_USD_MIN  = getenv_float("NET_BUY_USD_MIN", 150000)
PRICE_DROP_PCT   = getenv_float("PRICE_DROP_PCT", 2.0)   # %
PRICE_JUMP_PCT   = getenv_float("PRICE_JUMP_PCT", 0.0)   # 0 = معطّل

def tg(text):
    try:
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                      json={"chat_id": TG_CHAT, "text": text}, timeout=15)
    except: pass

def get_price_jump_pct(symbol):
    limit = max(WINDOW_MIN, 1)
    r = requests.get(f"{BAPI}/api/v3/klines",
                     params={"symbol": symbol, "interval":"1m", "limit": limit}, timeout=20)
    r.raise_for_status()
    kl = r.json()
    o0 = float(kl[0][1])
    cl = float(kl[-1][4])
    pct = (cl/o0 - 1.0)*100.0
    return pct, cl

def get_net_buy_usd(symbol):
    start = now_ms() - WINDOW_MIN*60*1000
    r = requests.get(f"{BAPI}/api/v3/aggTrades",
                     params={"symbol": symbol, "startTime": start}, timeout=25)
    r.raise_for_status()
    trades = r.json()
    buy_usd  = sum(float(t["p"])*float(t["q"]) for t in trades if not t["m"])
    sell_usd = sum(float(t["p"])*float(t["q"]) for t in trades if t["m"])
    return buy_usd - sell_usd

if __name__ == "__main__":
    for sym in SYMBOLS:
        # لكل عملة نفذ باستقلالية
        try:
            pct, last = get_price_jump_pct(sym)
            # هبوط مفاجئ
            if pct <= -abs(PRICE_DROP_PCT):
                tg(f"⚠️ هبوط مفاجئ {pct:.2f}% خلال {WINDOW_MIN} د\nالسعر: {last}\nزوج: {sym}")
            # صعود مفاجئ اختياري
            if PRICE_JUMP_PCT > 0 and pct >= PRICE_JUMP_PCT:
                tg(f"📈 صعود {pct:.2f}% خلال {WINDOW_MIN} د\nالسعر: {last}\nزوج: {sym}")
        except Exception as e:
            tg(f"خطأ سعر {sym}: {e}")

        try:
            net_buy = get_net_buy_usd(sym)
            if net_buy >= NET_BUY_USD_MIN:
                tg(f"💸 سيولة شراء صافية خلال {WINDOW_MIN} د\nالصافي: ${net_buy:,.0f}\nزوج: {sym}")
        except Exception as e:
            tg(f"خطأ سيولة {sym}: {e}")
