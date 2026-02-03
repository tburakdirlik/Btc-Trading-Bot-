#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Günlük Bot Kurulum Test Scripti
Bu script günlük botun düzgün çalışıp çalışmadığını test eder
"""

import sys

def test_imports():
    """Gerekli paketlerin kurulu olup olmadığını kontrol et"""
    print("\n" + "="*60)
    print("1. PAKET KONTROLÜ")
    print("="*60)
    
    packages = {
        'ccxt': 'Binance API bağlantısı için',
        'pandas': 'Veri analizi için',
        'numpy': 'Matematiksel hesaplamalar için',
        'requests': 'Telegram API için',
        'ta': 'Teknik indikatörler için'
    }
    
    all_ok = True
    for package, purpose in packages.items():
        try:
            __import__(package)
            print(f"✓ {package:15} - Kurulu ({purpose})")
        except ImportError:
            print(f"✗ {package:15} - KURULU DEĞİL! ({purpose})")
            all_ok = False
    
    return all_ok

def test_binance_connection():
    """Binance bağlantısını test et"""
    print("\n" + "="*60)
    print("2. BİNANCE BAĞLANTISI")
    print("="*60)
    
    try:
        import ccxt
        exchange = ccxt.binance({'enableRateLimit': True})
        
        # BTC/USDT fiyatını çek
        ticker = exchange.fetch_ticker('BTC/USDT')
        price = ticker['last']
        
        print(f"✓ Binance bağlantısı başarılı!")
        print(f"✓ BTC/USDT fiyatı: ${price:,.2f}")
        return True
        
    except Exception as e:
        print(f"✗ Binance bağlantı hatası: {e}")
        return False

def test_data_fetch_15m():
    """15 dakikalık veri çekme ve indikatör testi"""
    print("\n" + "="*60)
    print("3. 15 DAKİKALIK VERİ VE İNDİKATÖR TESTİ")
    print("="*60)
    
    try:
        import ccxt
        import pandas as pd
        from ta.momentum import RSIIndicator, StochasticOscillator
        from ta.trend import MACD, EMAIndicator
        from ta.volatility import BollingerBands, AverageTrueRange
        from datetime import datetime
        
        # 15 dakikalık veri çek
        exchange = ccxt.binance({'enableRateLimit': True})
        ohlcv = exchange.fetch_ohlcv('BTC/USDT', '15m', limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        print(f"✓ {len(df)} adet 15 dakikalık mum verisi çekildi")
        
        # GÜNLÜK BOT İNDİKATÖRLERİNİ HESAPLA
        
        # RSI (9 period)
        rsi = RSIIndicator(close=df['close'], window=9)
        df['rsi'] = rsi.rsi()
        
        # EMA (3 katman: 9, 21, 50)
        ema_9 = EMAIndicator(close=df['close'], window=9)
        ema_21 = EMAIndicator(close=df['close'], window=21)
        ema_50 = EMAIndicator(close=df['close'], window=50)
        df['ema_9'] = ema_9.ema_indicator()
        df['ema_21'] = ema_21.ema_indicator()
        df['ema_50'] = ema_50.ema_indicator()
        
        # MACD (8, 17, 9)
        macd = MACD(close=df['close'], window_slow=17, window_fast=8, window_sign=9)
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        
        # Bollinger Bands
        bb = BollingerBands(close=df['close'], window=20)
        df['bb_high'] = bb.bollinger_hband()
        df['bb_low'] = bb.bollinger_lband()
        
        # Stochastic
        stoch = StochasticOscillator(high=df['high'], low=df['low'], close=df['close'], 
                                     window=14, smooth_window=3)
        df['stoch_k'] = stoch.stoch()
        df['stoch_d'] = stoch.stoch_signal()
        
        # ATR
        atr = AverageTrueRange(high=df['high'], low=df['low'], close=df['close'])
        df['atr'] = atr.average_true_range()
        
        # Volume
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        
        # VWAP (günlük)
        today = datetime.now().date()
        df_today = df[df['timestamp'].dt.date == today].copy()
        if len(df_today) > 0:
            df_today['typical_price'] = (df_today['high'] + df_today['low'] + df_today['close']) / 3
            df_today['vwap_num'] = df_today['typical_price'] * df_today['volume']
            vwap = df_today['vwap_num'].sum() / df_today['volume'].sum()
        else:
            vwap = None
        
        # Son değerleri göster
        latest = df.iloc[-1]
        print(f"✓ Günlük bot indikatörleri hesaplandı:")
        print(f"\n  TEMEL DEĞERLER:")
        print(f"  • Fiyat: ${latest['close']:,.2f}")
        print(f"  • Hacim: {latest['volume']:,.0f}")
        
        print(f"\n  MOMENTUM İNDİKATÖRLERİ:")
        print(f"  • RSI(9): {latest['rsi']:.2f}")
        print(f"  • Stoch K: {latest['stoch_k']:.2f}")
        print(f"  • Stoch D: {latest['stoch_d']:.2f}")
        
        print(f"\n  TREND İNDİKATÖRLERİ:")
        print(f"  • EMA 9: ${latest['ema_9']:,.2f}")
        print(f"  • EMA 21: ${latest['ema_21']:,.2f}")
        print(f"  • EMA 50: ${latest['ema_50']:,.2f}")
        print(f"  • MACD: {latest['macd']:.2f}")
        print(f"  • MACD Signal: {latest['macd_signal']:.2f}")
        
        print(f"\n  VOLATİLİTE:")
        print(f"  • BB Üst: ${latest['bb_high']:,.2f}")
        print(f"  • BB Alt: ${latest['bb_low']:,.2f}")
        print(f"  • ATR: {latest['atr']:.2f}")
        
        print(f"\n  HACİM ANALİZİ:")
        print(f"  • Güncel: {latest['volume']:,.0f}")
        print(f"  • Ortalama: {latest['volume_ma']:,.0f}")
        print(f"  • Oran: {latest['volume']/latest['volume_ma']:.2f}x")
        
        if vwap:
            print(f"\n  VWAP:")
            print(f"  • VWAP: ${vwap:,.2f}")
            print(f"  • Fiyat/VWAP: {(latest['close']/vwap - 1)*100:+.2f}%")
        
        # Trend kontrolü
        if latest['ema_9'] > latest['ema_21'] > latest['ema_50']:
            print(f"\n  📈 TREND: GÜÇLÜ YUKARI (EMA 9 > 21 > 50)")
        elif latest['ema_9'] < latest['ema_21'] < latest['ema_50']:
            print(f"\n  📉 TREND: GÜÇLÜ AŞAĞI (EMA 9 < 21 < 50)")
        else:
            print(f"\n  ↔️  TREND: KARARSIZ/YATAY")
        
        # RSI durumu
        if latest['rsi'] < 25:
            print(f"  ⚠️  RSI: AŞIRI SATIM BÖLGESİNDE (<25)")
        elif latest['rsi'] > 75:
            print(f"  ⚠️  RSI: AŞIRI ALIM BÖLGESİNDE (>75)")
        else:
            print(f"  ✓ RSI: NORMAL BÖLGEDE (25-75)")
        
        return True
        
    except Exception as e:
        print(f"✗ Veri/İndikatör hatası: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_telegram_config():
    """Telegram ayarlarını kontrol et"""
    print("\n" + "="*60)
    print("4. TELEGRAM AYARLARI")
    print("="*60)
    
    try:
        # Bot dosyasını oku
        with open('bitcoin_daily_bot_fixed.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Token ve Chat ID kontrol et
        if 'BURAYA_BOT_TOKEN_YAZIN' in content:
            print("✗ TELEGRAM_BOT_TOKEN henüz ayarlanmamış!")
            print("  → bitcoin_daily_bot_fixed.py dosyasını düzenle")
            print("  → TELEGRAM_BOT_TOKEN = 'BURAYA...' satırını doldur")
            return False
        
        if 'BURAYA_CHAT_ID_YAZIN' in content:
            print("✗ TELEGRAM_CHAT_ID henüz ayarlanmamış!")
            print("  → bitcoin_daily_bot_fixed.py dosyasını düzenle")
            print("  → TELEGRAM_CHAT_ID = 'BURAYA...' satırını doldur")
            return False
        
        print("✓ Telegram ayarları yapılmış görünüyor")
        print("  ⚠  Mesaj gönderimi test edilemedi (bot çalıştırılmalı)")
        return True
        
    except FileNotFoundError:
        print("✗ bitcoin_daily_bot_fixed.py dosyası bulunamadı!")
        print("  → Dosyanın aynı dizinde olduğundan emin olun")
        return False
    except Exception as e:
        print(f"✗ Dosya okuma hatası: {e}")
        return False

def test_signal_system():
    """Sinyal üretim sistemini test et"""
    print("\n" + "="*60)
    print("5. SİNYAL ÜRETİM SİSTEMİ TESTİ")
    print("="*60)
    
    try:
        import ccxt
        import pandas as pd
        from ta.momentum import RSIIndicator, StochasticOscillator
        from ta.trend import MACD, EMAIndicator
        from ta.volatility import BollingerBands
        from datetime import datetime
        
        exchange = ccxt.binance({'enableRateLimit': True})
        ohlcv = exchange.fetch_ohlcv('BTC/USDT', '15m', limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # İndikatörler
        rsi = RSIIndicator(close=df['close'], window=9)
        df['rsi'] = rsi.rsi()
        
        ema_9 = EMAIndicator(close=df['close'], window=9)
        ema_21 = EMAIndicator(close=df['close'], window=21)
        df['ema_9'] = ema_9.ema_indicator()
        df['ema_21'] = ema_21.ema_indicator()
        
        macd = MACD(close=df['close'], window_slow=17, window_fast=8, window_sign=9)
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        
        bb = BollingerBands(close=df['close'], window=20)
        df['bb_high'] = bb.bollinger_hband()
        df['bb_low'] = bb.bollinger_lband()
        
        stoch = StochasticOscillator(high=df['high'], low=df['low'], close=df['close'],
                                     window=14, smooth_window=3)
        df['stoch_k'] = stoch.stoch()
        
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        # VWAP
        today = datetime.now().date()
        df_today = df[df['timestamp'].dt.date == today].copy()
        if len(df_today) > 0:
            df_today['typical_price'] = (df_today['high'] + df_today['low'] + df_today['close']) / 3
            df_today['vwap_num'] = df_today['typical_price'] * df_today['volume']
            vwap = df_today['vwap_num'].sum() / df_today['volume'].sum()
        else:
            vwap = None
        
        latest = df.iloc[-1]
        current_price = latest['close']
        
        # BUY Sinyal Skoru
        buy_score = 0
        if latest['rsi'] < 25: buy_score += 1
        
        bb_position = (current_price - latest['bb_low']) / (latest['bb_high'] - latest['bb_low'])
        if bb_position < 0.2: buy_score += 1
        
        if latest['macd'] > latest['macd_signal']: buy_score += 1
        if latest['ema_9'] > latest['ema_21']: buy_score += 1
        if latest['stoch_k'] < 20: buy_score += 1
        if latest['volume_ratio'] > 1.3: buy_score += 1
        if vwap and current_price < vwap: buy_score += 1
        
        # SELL Sinyal Skoru
        sell_score = 0
        if latest['rsi'] > 75: sell_score += 1
        if bb_position > 0.8: sell_score += 1
        if latest['macd'] < latest['macd_signal']: sell_score += 1
        if latest['ema_9'] < latest['ema_21']: sell_score += 1
        if latest['stoch_k'] > 80: sell_score += 1
        if latest['volume_ratio'] > 1.3: sell_score += 1
        if vwap and current_price > vwap: sell_score += 1
        
        print(f"✓ Sinyal sistemi test edildi:")
        print(f"\n  📊 BUY Skor: {buy_score}/7")
        print(f"  📊 SELL Skor: {sell_score}/7")
        print(f"  📌 Minimum Skor: 5/7")
        
        if buy_score >= 5:
            print(f"\n  🟢 BUY SİNYALİ AKTİF!")
        elif sell_score >= 5:
            print(f"\n  🔴 SELL SİNYALİ AKTİF!")
        else:
            print(f"\n  ⚪ Sinyal yok (skorlar düşük)")
        
        return True
        
    except Exception as e:
        print(f"✗ Sinyal test hatası: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_daily_bot_info():
    """Günlük bot hakkında bilgi göster"""
    print("\n" + "="*60)
    print("6. GÜNLÜK BOT BİLGİLERİ")
    print("="*60)
    
    print("""
📊 GÜNLÜK TRADING BOT ÖZELLİKLERİ:

TEMEL AYARLAR:
• Timeframe: 15 dakika (Haftalık: 1 saat)
• Kar Hedefi: %0.8/gün (Haftalık: %1.5/hafta)
• Stop Loss: %2.5 sabit (Haftalık: ATR bazlı)
• Kontrol: 5 dakikada bir (Haftalık: 30 dakika)
• Sinyal Aralığı: Min 15 dakika
• Commission: %0.1 per trade (dahil edildi)

İNDİKATÖRLER (7/7 SİSTEM):
1. RSI(9) - Oversold: <25, Overbought: >75
2. Bollinger Bands (20, 2)
3. MACD (8, 17, 9)
4. EMA (9, 21, 50) - 3 katmanlı
5. Stochastic (14, 3)
6. Volume Ratio (>1.3x)
7. VWAP (Günlük referans) - Otomatik sıfırlanır

MİNİMUM SKOR: 5/7 (Haftalık: 4/5)

✅ DÜZELTİLEN HATALAR:
• VWAP günlük sıfırlama eklendi
• Sinyal aralığı kontrolü (15 dk minimum)
• Commission hesaplaması eklendi
• Pozisyon takip sistemi düzeltildi
• Encoding sorunları giderildi

RİSK UYARISI:
⚠️  Günlük trading haftalık trading'den DAHA RİSKLİDİR
⚠️  15 dakikalık timeframe daha fazla gürültü içerir
⚠️  Stop-loss kullanımı ZORUNLU
⚠️  Küçük sermaye ile başlayın
⚠️  Demo hesap ile test edin

AYLIK POTANSİYEL:
• Teorik: %20-24 (25 işlem günü × %0.8)
• Gerçekçi: %5-10 (commission ve kayıplar dahil)
• Haftalık bot: ~%6/ay
    """)

def main():
    """Ana test fonksiyonu"""
    print("\n" + "="*60)
    print("BİTCOİN GÜNLÜK BOT - KURULUM TESTİ")
    print("DÜZELTİLMİŞ VERSİYON")
    print("="*60)
    
    results = []
    
    # Testleri çalıştır
    results.append(("Paketler", test_imports()))
    results.append(("Binance Bağlantısı", test_binance_connection()))
    results.append(("15dk Veri & İndikatörler", test_data_fetch_15m()))
    results.append(("Telegram Ayarları", test_telegram_config()))
    results.append(("Sinyal Üretim Sistemi", test_signal_system()))
    
    # Sonuçları özetle
    print("\n" + "="*60)
    print("TEST SONUÇLARI")
    print("="*60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ BAŞARILI" if passed else "✗ BAŞARISIZ"
        print(f"{test_name:25} : {status}")
        if not passed:
            all_passed = False
    
    print("="*60)
    
    # Bilgi göster
    show_daily_bot_info()
    
    if all_passed:
        print("\n" + "="*60)
        print("🎉 TÜM TESTLER BAŞARILI!")
        print("="*60)
        print("\nGünlük botu çalıştırmak için:")
        print("  python bitcoin_daily_bot_fixed.py")
        print("\n⚠️  DİKKAT:")
        print("  • İlk önce demo hesap ile test edin")
        print("  • Küçük sermaye ile başlayın")
        print("  • Her sinyali manuel kontrol edin")
        print("  • README_DAILY.md dosyasını okuyun")
    else:
        print("\n" + "="*60)
        print("⚠️  BAZI TESTLER BAŞARISIZ!")
        print("="*60)
        print("\nLütfen yukarıdaki hataları düzeltin.")
    
    print("")

if __name__ == "__main__":
    main()
