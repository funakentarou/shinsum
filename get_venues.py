#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ボートレース 開催会場自動取得スクリプト

その日開催している会場を自動で取得します。
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
from datetime import datetime

# 全24会場
VENUES = {
    1: '桐生', 2: '戸田', 3: '江戸川', 4: '平和島',
    5: '多摩川', 6: '浜名湖', 7: '蒲郡', 8: '常滑',
    9: '津', 10: '三国', 11: 'びわこ', 12: '住之江',
    13: '尼崎', 14: '鳴門', 15: '丸亀', 16: '児島',
    17: '宮島', 18: '徳山', 19: '下関', 20: '若松',
    21: '芦屋', 22: '福岡', 23: '唐津', 24: '大村'
}

class VenueFinder:
    def __init__(self):
        self.driver = None
    
    def setup_driver(self):
        """Chromeドライバーをセットアップ"""
        print('🔧 ブラウザを起動中...')
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # ヘッドレスモード
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print('✅ ブラウザ起動完了\n')
    
    def get_todays_venues(self, date=None):
        """
        その日開催している会場を取得
        
        Args:
            date: 日付（YYYYMMDD形式、Noneで今日）
        
        Returns:
            開催会場のリスト [4, 5, 12, ...] （会場番号）
        """
        if not self.driver:
            self.setup_driver()
        
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        # ボートレースキャストのトップページ
        url = 'https://boatcast.jp/index.html'
        
        print(f'🔍 {date} の開催会場を取得中...')
        print(f'URL: {url}\n')
        
        try:
            # ページを開く
            self.driver.get(url)
            
            # ページ読み込み待機
            print('⏳ ページ読み込み中（15秒待機）...')
            time.sleep(15)
            
            # HTMLを取得
            html = self.driver.page_source
            
            # デバッグ用に保存
            with open(f'debug_venues_boatcast.html', 'w', encoding='utf-8') as f:
                f.write(html)
            
            print(f'📄 HTMLを保存しました: debug_venues_boatcast.html\n')
            
            # BeautifulSoupで解析
            soup = BeautifulSoup(html, 'html.parser')
            
            # 開催会場を抽出
            venues = self.extract_venues(soup, date)
            
            if venues:
                print(f'✅ {len(venues)}会場で開催中\n')
                for venue_no in venues:
                    print(f'  {venue_no:2d}. {VENUES[venue_no]}')
            else:
                print('⚠️ 開催会場が見つかりませんでした')
            
            return venues
            
        except Exception as e:
            print(f'❌ エラー: {e}')
            import traceback
            traceback.print_exc()
            return []
    
    def extract_venues(self, soup, date):
        """HTMLから開催会場を抽出"""
        venues = []
        
        # 会場名から会場番号への逆引き辞書
        venue_name_to_no = {name: no for no, name in VENUES.items()}
        
        # すべての要素を検索
        elements = soup.find_all(['div', 'span', 'a', 'p', 'h1', 'h2', 'h3'])
        
        print(f'🔍 {len(elements)}個の要素を検索中...\n')
        
        for element in elements:
            text = element.get_text(strip=True)
            
            # 会場名と一致するか確認
            if text in venue_name_to_no:
                venue_no = venue_name_to_no[text]
                if venue_no not in venues:
                    venues.append(venue_no)
                    print(f'  ✅ 発見: {text} (会場番号: {venue_no})')
        
        # 会場番号順にソート
        venues.sort()
        
        return venues
    
    def close(self):
        """ブラウザを閉じる"""
        if self.driver:
            self.driver.quit()
            print('\nブラウザを閉じました')

def main():
    """メイン処理"""
    
    print('🚤 ボートレース 開催会場自動取得\n')
    print('='*60)
    
    # 日付指定（Noneで今日）
    DATE = None
    
    if DATE:
        print(f'日付: {DATE}')
    else:
        print(f'日付: 今日（{datetime.now().strftime("%Y年%m月%d日")}）')
    
    print('='*60 + '\n')
    
    # 会場取得
    finder = VenueFinder()
    
    try:
        venues = finder.get_todays_venues(DATE)
        
        if venues:
            print(f'\n{"="*60}')
            print('📊 開催会場一覧')
            print('='*60)
            
            for venue_no in venues:
                print(f'{venue_no:2d}: {VENUES[venue_no]}')
            
            print(f'\n合計: {len(venues)}会場')
            
            # 会場番号リストを出力（コピペ用）
            print(f'\n📋 会場番号リスト（コピペ用）:')
            print(f'TODAYS_VENUES = {venues}')
            
    finally:
        finder.close()
    
    print('\n✅ 完了！')

if __name__ == '__main__':
    main()