import os, time, requests

TG_TOKEN = os.environ["TELEGRAM_TOKEN"]
TG_CHAT  = os.environ["TELEGRAM_CHAT_ID"]
SYMBOL   = os.environ.get("SYMBOL", "PEPEUSDT").upper()
PRICE_JUMP_PCT = float(os.environ.get("PRICE_JUMP_PCT", "1.5"))  # نسبة القفزة %
WINDOW_MIN = int(os.environ.get("WINDOW_MIN", "5"))               # عدد الدقائق
NET_BUY_USD_MIN = float(os.environ.get("NET_BUY_USD_MIN", "150000")) # السيولة بالدولار

BAPI = "https://api.binance.com"

def tg(msg):
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                  json={"chat_id": TG_CHAT, "text": msg})

def now_ms():
    return int(time.time()*1000)

def get_price_jump_pct():
    limit = max(WINDOW_MIN, 1)
    r = requests.get(f"{BAPI}/api/v3/klines",
                     params={"symbol": SYMBOL, "interval":"1m", "limit": limit}, timeout=15)
    r.raise_for_status()
    kl = r.json()
    o0 = float(kl[0][1])
    cl = float(kl[-1][4])
    return (cl/o0 - 1.0)*100.0, cl

def get_net_buy_usd():
    start = now_ms() - WINDOW_MIN*60*1000
    r = requests.get(f"{BAPI}/api/v3/aggTrades",
                     params={"symbol": SYMBOL, "startTime": start}, timeout=20)
    r.raise_for_status()
    trades = r.json()
    buy_usd = sum(float(t["p"])*float(t["q"]) for t in trades if not t["m"])
    sell_usd = sum(float(t["p"])*float(t["q"]) for t in trades if t["m"])
    return buy_usd - sell_usd

if __name__ == "__main__":
    try:
        jump_pct, last_price = get_price_jump_pct()
        if jump_pct >= PRICE_JUMP_PCT:
            tg(f"📈 PEPE قفز {jump_pct:.2f}% خلال {WINDOW_MIN} دقيقة\nالسعر: {last_price}\nزوج: {SYMBOL}")
    except Exception as e:
        tg(f"⚠️ خطأ في حساب القفزة: {e}")

    try:
        net_buy = get_net_buy_usd()
        if net_buy >= NET_BUY_USD_MIN:
            tg(f"💸 دخول سيولة شراء صافية خلال {WINDOW_MIN} دقيقة\nالصافي: ${net_buy:,.0f}\nزوج: {SYMBOL}")
    except Exception as e:
        tg(f"⚠️ خطأ في حساب السيولة: {e}")
