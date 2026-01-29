#!/usr/bin/env python3
"""
Hızlı Başlangıç Scripti
Bot'u kolayca başlatmak için
"""

import os
import sys

def check_config():
    """Config dosyasını kontrol et"""
    if not os.path.exists('bitcoin_weekly_bot.py'):
        print("❌ Hata: bitcoin_weekly_bot.py bulunamadı!")
        print("Bu scripti bot dosyasıyla aynı dizinde çalıştırın.")
        return False
    
    with open('bitcoin_weekly_bot.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'BURAYA_TELEGRAM_BOT_TOKEN_YAZ' in content:
        print("\n" + "="*60)
        print("⚠️  TELEGRAM AYARLARI EKSİK!")
        print("="*60)
        print("\n1. Telegram bot oluştur:")
        print("   • @BotFather'ı aç")
        print("   • /newbot komutunu gönder")
        print("   • Bot adı ve kullanıcı adı belirle")
        print("   • Token'ı kaydet")
        print("\n2. Chat ID bul:")
        print("   • @userinfobot'u aç")
        print("   • /start komutunu gönder")
        print("   • ID'ni kaydet")
        print("\n3. bitcoin_weekly_bot.py dosyasını düzenle:")
        print("   • TELEGRAM_BOT_TOKEN = 'token buraya'")
        print("   • TELEGRAM_CHAT_ID = 'chat id buraya'")
        print("\n4. Bu scripti tekrar çalıştır")
        print("="*60)
        return False
    
    return True

def check_dependencies():
    """Gerekli paketleri kontrol et"""
    required = ['ccxt', 'pandas', 'numpy', 'requests', 'ta']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print("\n" + "="*60)
        print("⚠️  EKSİK PAKETLER!")
        print("="*60)
        print("\nŞu paketler kurulu değil:")
        for pkg in missing:
            print(f"  • {pkg}")
        print("\nKurmak için:")
        print("  pip install -r requirements.txt")
        print("="*60)
        return False
    
    return True

def main():
    print("\n" + "="*60)
    print("🚀 BİTCOİN HAFTALIK BOT - HIZLI BAŞLATMA")
    print("="*60)
    
    # Bağımlılıkları kontrol et
    if not check_dependencies():
        sys.exit(1)
    
    # Config kontrol et
    if not check_config():
        sys.exit(1)
    
    # Her şey tamam, botu başlat
    print("\n✓ Tüm kontroller başarılı!")
    print("\nBot başlatılıyor...")
    print("Durdurmak için CTRL+C basın\n")
    print("="*60 + "\n")
    
    # Botu import et ve çalıştır
    try:
        from bitcoin_weekly_bot import BitcoinWeeklyBot
        
        # Dosyadan token ve chat ID'yi oku
        with open('bitcoin_weekly_bot.py', 'r', encoding='utf-8') as f:
            for line in f:
                if 'TELEGRAM_BOT_TOKEN =' in line and 'BURAYA' not in line:
                    token = line.split('=')[1].strip().strip('"').strip("'")
                if 'TELEGRAM_CHAT_ID =' in line and 'BURAYA' not in line:
                    chat_id = line.split('=')[1].strip().strip('"').strip("'")
        
        bot = BitcoinWeeklyBot(
            telegram_token=token,
            telegram_chat_id=chat_id
        )
        
        bot.run()
        
    except KeyboardInterrupt:
        print("\n\n👋 Bot durduruldu. Hoşça kal!")
    except Exception as e:
        print(f"\n❌ Hata oluştu: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
