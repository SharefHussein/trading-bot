import ccxt
import time
import os
import sys
import json
from datetime import datetime
import numpy as np

# ============ إعدادات القناص السريع (معدل لـ 1.3$) ============
class Config:
    LEVERAGE = 50                     
    MAX_OPEN_POSITIONS = 1            # مركز واحد في المرة لتركيز الرصيد
    
    # 🎯 أهداف سريعة (سكالبينج)
    STOP_LOSS_PERCENT = 0.6          # وقف خسارة قريب
    TAKE_PROFIT_PERCENT = 1.0        # هدف ربح 1% (يعادل 50% مع الرافعة)
    
    # 📊 شروط الدخول "السريعة"
    RSI_BUY_THRESHOLD = 42           # دخول جريء
    MIN_SCORE_FOR_TRADE = 65         # تقييم متوسط للسرعة
    
    # 📈 فلترة السيولة
    MIN_VOLUME_USDT = 1000000        # مليون دولار سيولة كافية
    CHECK_INTERVAL = 15              # فحص كل 15 ثانية

class Logger:
    def log(self, level, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        sys.stdout.flush()

logger = Logger()

# ============ المحرك الفني الذكي ============
class SmartAnalyzer:
    @staticmethod
    def calculate_rsi(prices, period=14):
        if len(prices) < period + 1: return 50
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        if avg_loss == 0: return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def check_trend(highs, lows, closes):
        # حساب مبسط للسوبر تريند
        if len(closes) < 10: return "NEUTRAL"
        mid = (highs[-1] + lows[-1]) / 2
        return "BULLISH" if closes[-1] > mid else "BEARISH"

# ============ البوت التنفيذي ============
def run_fast_smart_bot():
    BK = os.getenv("BINGX_APIKEY")
    BS = os.getenv("BINGX_SECRETKEY")
    
    try:
        ex = ccxt.bingx({'apiKey': BK, 'secret': BS, 'options': {'defaultType': 'swap'}})
        logger.log("INFO", "🚀 تم تشغيل القناص الذكي (نسخة الـ 1.3$)")
    except: return

    analyzer = SmartAnalyzer()

    while True:
        try:
            # 1. فحص الرصيد والصفقات
            balance = ex.fetch_balance()
            avail = balance['free'].get('USDT', 0)
            
            positions = ex.fetch_positions()
            has_pos = any(float(p['info'].get('positionAmt', 0)) != 0 for p in positions)

            if has_pos:
                logger.log("WAIT", "📦 توجد صفقة مفتوحة.. ننتظر الإغلاق")
                time.sleep(30)
                continue

            if avail < 1.0:
                logger.log("LOW_BALANCE", f"💰 الرصيد {avail}$ قليل جداً")
                time.sleep(60)
                continue

            # 2. البحث عن عملة مناسبة (أفضل 30 عملة سيولة)
            tickers = ex.fetch_tickers()
            symbols = [s for s, t in tickers.items() if s.endswith('/USDT') and t.get('quoteVolume', 0) > Config.MIN_VOLUME_USDT]
            symbols = sorted(symbols, key=lambda x: tickers[x]['quoteVolume'], reverse=True)[:30]

            for symbol in symbols:
                try:
                    ohlcv = ex.fetch_ohlcv(symbol, timeframe='5m', limit=20)
                    closes = [x[4] for x in ohlcv]
                    highs = [x[2] for x in ohlcv]
                    lows = [x[3] for x in ohlcv]
                    
                    rsi = analyzer.calculate_rsi(closes)
                    trend = analyzer.check_trend(highs, lows, closes)

                    # 🎯 شرط الدخول: RSI منخفض + سعر فوق المنتصف (بداية ارتداد)
                    if rsi < Config.RSI_BUY_THRESHOLD and trend == "BULLISH":
                        price = tickers[symbol]['last']
                        # حساب الحجم ليتناسب مع 1.3$ والرافعة 50
                        amount = (avail * 45) / price 
                        
                        logger.log("ACTION", f"🎯 صيد ثمين في {symbol} | RSI: {rsi:.1f}")
                        
                        # تنفيذ الدخول
                        ex.set_leverage(Config.LEVERAGE, symbol)
                        ex.create_market_order(symbol, 'buy', amount)
                        
                        # وضع الأهداف
                        tp = price * (1 + Config.TAKE_PROFIT_PERCENT / 100)
                        sl = price * (1 - Config.STOP_LOSS_PERCENT / 100)
                        
                        ex.create_order(symbol, 'limit', 'sell', amount, tp, {'reduceOnly': True})
                        ex.create_order(symbol, 'stop', 'sell', amount, None, {'stopPrice': sl, 'reduceOnly': True})
                        
                        logger.log("SUCCESS", f"✅ دخلنا الصفقة.. الربح المستهدف: {tp:.4f}")
                        break
                except: continue
            
            time.sleep(Config.CHECK_INTERVAL)

        except Exception as e:
            logger.log("ERROR", f"حدث خطأ: {str(e)}")
            time.sleep(20)

if __name__ == "__main__":
    run_fast_smart_bot()

