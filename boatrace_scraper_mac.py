#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ボートレース展示データ取得スクリプト（Mac版）

使い方:
    python3 boatrace_scraper.py

設定を変更する場合は、下の方の「設定」セクションを編集してください。
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
import os

# 全24会場
VENUES = {
    1: '桐生', 2: '戸田', 3: '江戸川', 4: '平和島',
    5: '多摩川', 6: '浜名湖', 7: '蒲郡', 8: '常滑',
    9: '津', 10: '三国', 11: 'びわこ', 12: '住之江',
    13: '尼崎', 14: '鳴門', 15: '丸亀', 16: '児島',
    17: '宮島', 18: '徳山', 19: '下関', 20: '若松',
    21: '芦屋', 22: '福岡', 23: '唐津', 24: '大村'
}

class BoatraceScraper:
    def __init__(self):
        self.driver = None
    
    def setup_driver(self):
        """Chromeドライバーをセットアップ"""
        print('🔧 ブラウザを起動中...')
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 画面を表示しない
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # 自動的に最新のChromeDriverをダウンロード
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print('✅ ブラウザ起動完了\n')
    
    def get_race_data(self, place_no, race_no, date=None):
        """
        指定したレースの展示データを取得
        
        Args:
            place_no: 会場番号（1-24）
            race_no: レース番号（1-12）
            date: 日付（YYYYMMDD形式、Noneで今日）
        """
        if not self.driver:
            self.setup_driver()
        
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        # ボートレース日和のURL
        url = f'https://kyoteibiyori.com/race_shusso.php?place_no={place_no}&race_no={race_no}&hiduke={date}&slider=4'
        
        print(f'🔍 {VENUES[place_no]}({place_no}) {race_no}R を取得中...')
        print(f'URL: {url}\n')
        
        try:
            # ページを開く
            self.driver.get(url)
            
            # JavaScriptの実行を待つ
            print('⏳ ページ読み込み中（10秒待機）...')
            time.sleep(10)  # JavaScriptの実行を待つ
            
            # ページのHTMLを取得
            html = self.driver.page_source
            
            # BeautifulSoupで解析
            soup = BeautifulSoup(html, 'html.parser')
            
            # データを抽出
            boats = []
            
            # テーブルを探す
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    
                    if len(cells) < 3:
                        continue
                    
                    cell_texts = [c.get_text(strip=True) for c in cells]
                    
                    # 艇番を探す
                    boat_number = None
                    for text in cell_texts:
                        if text in ['1', '2', '3', '4', '5', '6']:
                            boat_number = int(text)
                            break
                    
                    # タイムデータを抽出
                    times = []
                    for text in cell_texts:
                        # X.XX 形式のタイム
                        if '.' in text and len(text) <= 6:
                            try:
                                float(text)
                                times.append(text)
                            except:
                                pass
                    
                    if boat_number and len(times) >= 1:
                        boat = {'number': boat_number}
                        
                        # タイムを割り当て
                        time_labels = ['exhibition', 'one_lap', 'turning', 'straight']
                        for i, time_val in enumerate(times[:4]):
                            if i < len(time_labels):
                                boat[time_labels[i]] = time_val
                        
                        # 重複チェック
                        if not any(b['number'] == boat_number for b in boats):
                            boats.append(boat)
                            print(f'  {boat_number}号艇: {", ".join(times[:4])}')
            
            # 艇番順にソート
            boats.sort(key=lambda x: x['number'])
            
            if boats:
                print(f'\n✅ {len(boats)}艇のデータを取得\n')
            else:
                print('⚠️ データなし（展示前の可能性）\n')
            
            return {
                'place_no': place_no,
                'place_name': VENUES[place_no],
                'race_no': race_no,
                'date': date,
                'boats': boats
            }
            
        except Exception as e:
            print(f'❌ エラー: {e}')
            import traceback
            traceback.print_exc()
            return None
    
    def get_all_races(self, place_no, date=None):
        """指定会場の全12レースを取得"""
        print(f'\n{"="*60}')
        print(f'🏁 {VENUES[place_no]} 全12レース取得開始')
        print('='*60 + '\n')
        
        all_data = []
        
        for race_no in range(1, 13):
            data = self.get_race_data(place_no, race_no, date)
            if data:
                all_data.append(data)
            
            # レート制限対策
            time.sleep(2)
        
        print(f'\n🎉 {len(all_data)}レース取得完了！\n')
        return all_data
    
    def close(self):
        """ブラウザを閉じる"""
        if self.driver:
            self.driver.quit()
            print('ブラウザを閉じました')

def save_to_csv(data, filename):
    """データをCSVに保存"""
    if not data or not data.get('boats'):
        print('⚠️ 保存するデータがありません')
        return
    
    df = pd.DataFrame(data['boats'])
    
    # ファイル名に会場名とレース番号を含める
    venue_name = data['place_name']
    race_no = data['race_no']
    date = data['date']
    
    if filename is None:
        filename = f'{venue_name}_{race_no}R_{date}.csv'
    
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f'💾 {filename} に保存しました')
    
    return df

def main():
    """メイン処理"""
    
    # ========================================
    # 設定（ここを変更してください）
    # ========================================
    
    PLACE = 4       # 会場番号（1-24）
    RACE = 1        # レース番号（1-12）
    DATE = None     # 日付（YYYYMMDD形式、Noneで今日）
    
    # 全レース取得する場合は True に変更
    GET_ALL_RACES = False
    
    # ========================================
    
    print('🚤 ボートレース展示データ取得\n')
    print('='*60)
    print('設定')
    print('='*60)
    print(f'会場: {VENUES[PLACE]} ({PLACE})')
    print(f'レース: {RACE}R')
    print(f'日付: {DATE or "今日"}')
    print(f'全レース取得: {"はい" if GET_ALL_RACES else "いいえ"}')
    print('='*60 + '\n')
    
    # スクレイパー初期化
    scraper = BoatraceScraper()
    
    try:
        if GET_ALL_RACES:
            # 全レース取得
            all_data = scraper.get_all_races(PLACE, DATE)
            
            # 全レースをまとめてCSV保存
            if all_data:
                all_boats = []
                for race_data in all_data:
                    for boat in race_data['boats']:
                        boat['race_no'] = race_data['race_no']
                        all_boats.append(boat)
                
                if all_boats:
                    df = pd.DataFrame(all_boats)
                    filename = f'{VENUES[PLACE]}_全レース_{DATE or datetime.now().strftime("%Y%m%d")}.csv'
                    df.to_csv(filename, index=False, encoding='utf-8-sig')
                    print(f'\n💾 {filename} に保存しました')
                    print(f'📊 合計 {len(all_boats)} 艇のデータ')
        else:
            # 単一レース取得
            data = scraper.get_race_data(PLACE, RACE, DATE)
            
            # CSV保存
            if data:
                df = save_to_csv(data, None)
                
                # データを表示
                if df is not None:
                    print('\n📊 取得データ:')
                    print(df.to_string())
    
    finally:
        # ブラウザを閉じる
        scraper.close()
    
    print('\n✅ 完了！')

if __name__ == '__main__':
    main()


