#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ボートレースキャスト データ取得スクリプト

使い方:
    python boatrace_cast.py
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

class BoatcastScraper:
    def __init__(self):
        self.driver = None
    
    def setup_driver(self):
        """Chromeドライバーをセットアップ"""
        print('🔧 ブラウザを起動中...')
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print('✅ ブラウザ起動完了\n')
    
    def get_race_data(self, venue_no, race_no, date=None):
        """
        ボートレースキャストからデータを取得
        
        Args:
            venue_no: 会場番号（1-24）※ゼロ埋め2桁に変換されます
            race_no: レース番号（1-12）
            date: 日付（YYYYMMDD形式、Noneで今日）
        """
        if not self.driver:
            self.setup_driver()
        
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        # 会場番号を2桁にゼロ埋め（例：4 → 04）
        venue_code = str(venue_no).zfill(2)
        
        # ボートレースキャストのURL
        url = f'https://race.boatcast.jp/replay?jo={venue_code}&ymd={date}&race={race_no}'
        
        print(f'🔍 {VENUES[venue_no]}({venue_code}) {race_no}R を取得中...')
        print(f'URL: {url}\n')
        
        try:
            # ページを開く
            self.driver.get(url)
            
            # ページ読み込み待機（長めに15秒）
            print('⏳ ページ読み込み中（15秒待機）...')
            time.sleep(15)
            
            # ページのHTMLを取得
            html = self.driver.page_source
            
            # HTMLをファイルに保存（デバッグ用）
            with open(f'debug_boatcast_{venue_code}_{race_no}.html', 'w', encoding='utf-8') as f:
                f.write(html)
            
            print(f'📄 HTMLを保存しました: debug_boatcast_{venue_code}_{race_no}.html\n')
            
            # BeautifulSoupで解析
            soup = BeautifulSoup(html, 'html.parser')
            
            # データを抽出
            boats = self.extract_data_from_html(soup)
            
            if boats:
                print(f'✅ {len(boats)}艇のデータを取得\n')
            else:
                print('⚠️ データが見つかりませんでした\n')
                print('💡 debug_boatcast_xx_x.html を開いて、実際のHTML構造を確認してください')
            
            return {
                'venue_no': venue_no,
                'venue_name': VENUES[venue_no],
                'race_no': race_no,
                'date': date,
                'boats': boats
            }
            
        except Exception as e:
            print(f'❌ エラー: {e}')
            import traceback
            traceback.print_exc()
            return None
    
    def extract_data_from_html(self, soup):
        """HTMLからデータを抽出（ボートレースキャスト用）"""
        boats = []
        
        # 方法1: テーブルから抽出
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                
                if len(cells) < 2:
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
                
                # タイムデータを抽出（すべてのパターン）
                times = []
                for text in cell_texts:
                    # パターン1: 6.82 のような形式
                    # パターン2: .82 のような形式（先頭の数字なし）
                    # パターン3: 36.5 のような形式
                    
                    # 小数点を含む数字を探す
                    if '.' in text:
                        # 数字だけ抽出
                        match = re.search(r'(\d*\.\d+)', text)
                        if match:
                            time_str = match.group(1)
                            try:
                                # 浮動小数点に変換できるかチェック
                                float(time_str)
                                times.append(time_str)
                            except:
                                continue
                
                if boat_number and len(times) >= 1:
                    # 既に同じ艇番がある場合はスキップ（重複防止）
                    if any(b['number'] == boat_number for b in boats):
                        continue
                    
                    boat = {'number': boat_number}
                    
                    # タイムを割り当て
                    time_labels = ['exhibition', 'one_lap', 'turning', 'straight']
                    for i, time_val in enumerate(times[:4]):
                        if i < len(time_labels):
                            boat[time_labels[i]] = time_val
                    
                    boats.append(boat)
                    
                    # デバッグ出力
                    time_display = ', '.join(times[:4])
                    print(f'  {boat_number}号艇: {time_display}')
        
        # 艇番順にソート
        boats.sort(key=lambda x: x['number'])
        
        return boats
    
    def close(self):
        """ブラウザを閉じる"""
        if self.driver:
            self.driver.quit()
            print('ブラウザを閉じました')

def save_to_csv(data, filename=None):
    """データをCSVに保存"""
    if not data or not data.get('boats'):
        print('⚠️ 保存するデータがありません')
        return None
    
    df = pd.DataFrame(data['boats'])
    
    # ファイル名を生成
    if filename is None:
        venue_name = data['venue_name']
        race_no = data['race_no']
        date = data['date']
        filename = f'{venue_name}_{race_no}R_{date}.csv'
    
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f'💾 {filename} に保存しました')
    
    return df

def main():
    """メイン処理"""
    
    # ========================================
    # 設定（ここを変更してください）
    # ========================================
    
    VENUE = 4       # 会場番号（1-24）
    RACE = 1        # レース番号（1-12）
    DATE = None     # 日付（YYYYMMDD形式、Noneで今日）
    
    # ========================================
    
    print('🚤 ボートレースキャスト データ取得\n')
    print('='*60)
    print('設定')
    print('='*60)
    print(f'会場: {VENUES[VENUE]} ({VENUE})')
    print(f'レース: {RACE}R')
    print(f'日付: {DATE or "今日"}')
    print('='*60 + '\n')
    
    # スクレイパー初期化
    scraper = BoatcastScraper()
    
    try:
        # データ取得
        data = scraper.get_race_data(VENUE, RACE, DATE)
        
        # CSV保存
        if data:
            df = save_to_csv(data)
            
            # データを表示
            if df is not None and len(df) > 0:
                print('\n📊 取得データ:')
                print(df.to_string())
                
                # 列名を日本語で表示
                print('\n📋 データ詳細:')
                for col in df.columns:
                    if col == 'number':
                        print(f'  艇番: {df[col].tolist()}')
                    elif col == 'exhibition':
                        print(f'  展示: {df[col].tolist()}')
                    elif col == 'one_lap':
                        print(f'  1周: {df[col].tolist()}')
                    elif col == 'turning':
                        print(f'  周り足: {df[col].tolist()}')
                    elif col == 'straight':
                        print(f'  直線: {df[col].tolist()}')
    
    finally:
        # ブラウザを閉じる
        scraper.close()
    
    print('\n✅ 完了！')
    print('\n💡 ヒント:')
    print('  - データが正しく取得できない場合、debug_boatcast_xx_x.html を確認してください')
    print('  - HTML構造を見て、セレクタを調整する必要があるかもしれません')

if __name__ == '__main__':
    main()