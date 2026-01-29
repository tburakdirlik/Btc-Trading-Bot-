"""
Bot Kurulum Test Scripti
Bu script botun düzgün çalışıp çalışmadığını test eder
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

def test_data_fetch():
    """Veri çekme ve indikatör hesaplamayı test et"""
    print("\n" + "="*60)
    print("3. VERİ VE İNDİKATÖR TESTİ")
    print("="*60)
    
    try:
        import ccxt
        import pandas as pd
        from ta.momentum import RSIIndicator
        from ta.trend import MACD, EMAIndicator
        from ta.volatility import BollingerBands, AverageTrueRange
        
        # Veri çek
        exchange = ccxt.binance({'enableRateLimit': True})
        ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        print(f"✓ {len(df)} adet mum verisi çekildi")
        
        # İndikatörleri hesapla
        rsi = RSIIndicator(close=df['close'], window=14)
        df['rsi'] = rsi.rsi()
        
        macd = MACD(close=df['close'])
        df['macd'] = macd.macd()
        
        ema_20 = EMAIndicator(close=df['close'], window=20)
        df['ema_20'] = ema_20.ema_indicator()
        
        bb = BollingerBands(close=df['close'], window=20)
        df['bb_high'] = bb.bollinger_hband()
        
        atr = AverageTrueRange(high=df['high'], low=df['low'], close=df['close'])
        df['atr'] = atr.average_true_range()
        
        # Son değerleri göster
        latest = df.iloc[-1]
        print(f"✓ İndikatörler hesaplandı:")
        print(f"  • Fiyat: ${latest['close']:,.2f}")
        print(f"  • RSI: {latest['rsi']:.2f}")
        print(f"  • MACD: {latest['macd']:.2f}")
        print(f"  • EMA 20: ${latest['ema_20']:,.2f}")
        print(f"  • BB Üst: ${latest['bb_high']:,.2f}")
        print(f"  • ATR: {latest['atr']:.2f}")
        
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
        with open('bitcoin_weekly_bot.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Token ve Chat ID kontrol et
        if 'BURAYA_TELEGRAM_BOT_TOKEN_YAZ' in content:
            print("✗ TELEGRAM_BOT_TOKEN henüz ayarlanmamış!")
            print("  → bitcoin_weekly_bot.py dosyasını düzenle")
            print("  → TELEGRAM_BOT_TOKEN = 'BURAYA...' satırını doldur")
            return False
        
        if 'BURAYA_TELEGRAM_CHAT_ID_YAZ' in content:
            print("✗ TELEGRAM_CHAT_ID henüz ayarlanmamış!")
            print("  → bitcoin_weekly_bot.py dosyasını düzenle")
            print("  → TELEGRAM_CHAT_ID = 'BURAYA...' satırını doldur")
            return False
        
        print("✓ Telegram ayarları yapılmış görünüyor")
        print("  ⚠ Mesaj gönderimi test edilemedi (bot çalıştırılmalı)")
        return True
        
    except Exception as e:
        print(f"✗ Dosya okuma hatası: {e}")
        return False

def main():
    """Ana test fonksiyonu"""
    print("\n" + "="*60)
    print("BİTCOİN HAFTALIK BOT - KURULUM TESTİ")
    print("="*60)
    
    results = []
    
    # Testleri çalıştır
    results.append(("Paketler", test_imports()))
    results.append(("Binance Bağlantısı", test_binance_connection()))
    results.append(("Veri ve İndikatörler", test_data_fetch()))
    results.append(("Telegram Ayarları", test_telegram_config()))
    
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
    
    if all_passed:
        print("\n🎉 TÜM TESTLER BAŞARILI!")
        print("\nBotu çalıştırmak için:")
        print("  python bitcoin_weekly_bot.py")
    else:
        print("\n⚠️  BAZI TESTLER BAŞARISIZ!")
        print("\nLütfen yukarıdaki hataları düzeltin.")
        print("Detaylı kurulum için KURULUM.md dosyasını okuyun.")
    
    print("")

if __name__ == "__main__":
    main()
