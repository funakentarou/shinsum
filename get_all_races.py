#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ボートレース 全レースデータ一括取得スクリプト

指定した会場の全12レースのオリジナル展示データを取得します。
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
import re

# 全24会場
VENUES = {
    1: '桐生', 2: '戸田', 3: '江戸川', 4: '平和島',
    5: '多摩川', 6: '浜名湖', 7: '蒲郡', 8: '常滑',
    9: '津', 10: '三国', 11: 'びわこ', 12: '住之江',
    13: '尼崎', 14: '鳴門', 15: '丸亀', 16: '児島',
    17: '宮島', 18: '徳山', 19: '下関', 20: '若松',
    21: '芦屋', 22: '福岡', 23: '唐津', 24: '大村'
}

class AllRacesScraper:
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
    
    def get_race_data(self, venue_no, race_no, date):
        """1レースのデータを取得"""
        if not self.driver:
            self.setup_driver()
        
        venue_code = str(venue_no).zfill(2)
        url = f'https://race.boatcast.jp/replay?jo={venue_code}&ymd={date}&race={race_no}'
        
        try:
            # ページを開く
            self.driver.get(url)
            time.sleep(3)
            
            # 「直前情報」タブをクリック
            try:
                chokuzen_tab = self.driver.find_element(By.XPATH, "//button[contains(text(), '直前情報')] | //a[contains(text(), '直前情報')]")
                self.driver.execute_script("arguments[0].click();", chokuzen_tab)
                time.sleep(2)
            except:
                pass
            
            # 「オリジナル展示データ」タブをクリック
            try:
                original_tab = self.driver.find_element(By.XPATH, "//button[contains(text(), 'オリジナル展示データ')] | //a[contains(text(), 'オリジナル展示データ')]")
                self.driver.execute_script("arguments[0].click();", original_tab)
                time.sleep(2)
            except:
                pass
            
            # HTMLを取得
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # データを抽出
            boats = self.extract_original_data(soup)
            
            return boats
            
        except Exception as e:
            print(f'      ❌ エラー: {e}')
            return []
    
    def extract_original_data(self, soup):
        """オリジナル展示データを抽出"""
        boats = []
        tables = soup.find_all('table')
        
        for table in tables:
            table_text = table.get_text()
            
            if '展示タイム' in table_text or 'まわり足' in table_text or '直　線' in table_text or '一　周' in table_text:
                rows = table.find_all('tr')
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    
                    if len(cells) < 4:
                        continue
                    
                    cell_texts = [c.get_text(strip=True) for c in cells]
                    
                    # 艇番を探す
                    boat_number = None
                    for text in cell_texts:
                        if text in ['1', '2', '3', '4', '5', '6']:
                            boat_number = int(text)
                            break
                    
                    if not boat_number:
                        continue
                    
                    # タイムデータを抽出
                    times = []
                    for text in cell_texts:
                        matches = re.findall(r'\d+\.\d+', text)
                        times.extend(matches)
                    
                    # タイムが5つ以上ある場合（直線なしの会場にも対応）
                    if boat_number and len(times) >= 5:
                        if any(b['number'] == boat_number for b in boats):
                            continue
                        
                        boat = {
                            'number': boat_number,
                            'exhibition': times[2] if len(times) > 2 else None,
                            'one_lap': times[3] if len(times) > 3 else None,
                            'turning': times[4] if len(times) > 4 else None,
                            'straight': times[5] if len(times) > 5 else None
                        }
                        
                        boats.append(boat)
        
        boats.sort(key=lambda x: x['number'])
        return boats
    
    def get_all_races_for_venue(self, venue_no, date):
        """1会場の全12レースを取得"""
        venue_name = VENUES[venue_no]
        
        print(f'\n{"="*60}')
        print(f'🏁 {venue_name} ({venue_no}) - 全12レース取得開始')
        print('='*60)
        
        all_data = []
        
        for race_no in range(1, 13):
            print(f'  📊 {race_no}R 取得中...', end=' ')
            
            boats = self.get_race_data(venue_no, race_no, date)
            
            if boats:
                print(f'✅ {len(boats)}艇')
                
                for boat in boats:
                    boat['venue_no'] = venue_no
                    boat['venue_name'] = venue_name
                    boat['race_no'] = race_no
                    all_data.append(boat)
            else:
                print('⚠️ データなし')
        
        return all_data
    
    def close(self):
        """ブラウザを閉じる"""
        if self.driver:
            self.driver.quit()

def main():
    """メイン処理"""
    
    # ========================================
    # 設定
    # ========================================
    # ============================================================

    # ============================================================
    # 会場番号対応表（全24会場）
    # ============================================================
    # 1: 桐生      2: 戸田      3: 江戸川    4: 平和島
    # 5: 多摩川    6: 浜名湖    7: 蒲郡      8: 常滑
    # 9: 津       10: 三国     11: びわこ   12: 住之江
    # 13: 尼崎    14: 鳴門     15: 丸亀     16: 児島
    # 17: 宮島    18: 徳山     19: 下関     20: 若松
    # 21: 芦屋    22: 福岡     23: 唐津     24: 大村
    # ============================================================

    # 今日開催している会場（会場番号のリスト）

    TODAYS_VENUES = [2, 5, 11, 12, 13, 14, 15, 16, 17, 19, 20,]
    # 桐生、平和島、浜名湖、蒲郡、常滑、びわこ、尼崎、児島、宮島、徳山、若松、芦屋、唐津
    
    DATE = datetime.now().strftime('%Y%m%d')  # 今日
    
    # ========================================
    
    print('🚤 ボートレース 全レースデータ一括取得\n')
    print('='*60)
    print(f'日付: {DATE}')
    print(f'対象会場: {len(TODAYS_VENUES)}会場')
    print('='*60)
    
    for venue_no in TODAYS_VENUES:
        print(f'  - {VENUES[venue_no]}')
    
    # スクレイパー初期化
    scraper = AllRacesScraper()
    
    all_data = []
    
    try:
        # 各会場のデータを取得
        for venue_no in TODAYS_VENUES:
            venue_data = scraper.get_all_races_for_venue(venue_no, DATE)
            all_data.extend(venue_data)
        
        # DataFrameに変換
        if all_data:
            df = pd.DataFrame(all_data)
            
            # 列の順番を整理
            df = df[['venue_no', 'venue_name', 'race_no', 'number', 'exhibition', 'one_lap', 'turning', 'straight']]
            
            # CSV保存
            filename = f'all_races_{DATE}.csv'
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            print(f'\n{"="*60}')
            print('📊 取得結果')
            print('='*60)
            print(f'総レース数: {len(df["race_no"].unique())}レース')
            print(f'総データ数: {len(df)}艇')
            print(f'💾 {filename} に保存しました')
            
            # サンプル表示
            print('\n📋 データサンプル（最初の10件）:')
            print(df.head(10).to_string())
            
        else:
            print('\n⚠️ データが取得できませんでした')
    
    finally:
        scraper.close()
    
    print('\n✅ 完了！')

if __name__ == '__main__':
    main()