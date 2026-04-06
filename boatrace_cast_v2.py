#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ボートレースキャスト オリジナル展示データ取得スクリプト（修正版v2）

使い方:
    python boatrace_cast_v2.py
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

class BoatcastScraperV2:
    def __init__(self):
        self.driver = None
    
    def setup_driver(self):
        """Chromeドライバーをセットアップ"""
        print('🔧 ブラウザを起動中...')
        
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # 画面表示モード
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print('✅ ブラウザ起動完了\n')
    
    def get_race_data(self, venue_no, race_no, date=None):
        """
        ボートレースキャストからオリジナル展示データを取得
        
        Args:
            venue_no: 会場番号（1-24）
            race_no: レース番号（1-12）
            date: 日付（YYYYMMDD形式、Noneで今日）
        """
        if not self.driver:
            self.setup_driver()
        
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        # 会場番号を2桁にゼロ埋め
        venue_code = str(venue_no).zfill(2)
        
        # ボートレースキャストのURL
        url = f'https://race.boatcast.jp/replay?jo={venue_code}&ymd={date}&race={race_no}'
        
        print(f'🔍 {VENUES[venue_no]}({venue_code}) {race_no}R を取得中...')
        print(f'URL: {url}\n')
        
        try:
            # ページを開く
            self.driver.get(url)
            
            # ページ読み込み待機
            print('⏳ ページ読み込み中（5秒待機）...')
            time.sleep(5)
            
            # 「直前情報」タブをクリック
            print('🖱️  「直前情報」タブをクリック...')
            try:
                # JavaScriptでクリック
                chokuzen_tab = self.driver.find_element(By.XPATH, "//button[contains(text(), '直前情報')] | //a[contains(text(), '直前情報')]")
                self.driver.execute_script("arguments[0].click();", chokuzen_tab)
                time.sleep(3)
                print('   ✅ クリック完了')
            except Exception as e:
                print(f'   ⚠️ 直前情報タブが見つかりません: {e}')
            
            # 「オリジナル展示データ」タブをクリック
            print('🖱️  「オリジナル展示データ」タブをクリック...')
            try:
                # JavaScriptでクリック
                original_tab = self.driver.find_element(By.XPATH, "//button[contains(text(), 'オリジナル展示データ')] | //a[contains(text(), 'オリジナル展示データ')]")
                self.driver.execute_script("arguments[0].click();", original_tab)
                time.sleep(3)
                print('   ✅ クリック完了\n')
            except Exception as e:
                print(f'   ⚠️ オリジナル展示データタブが見つかりません: {e}\n')
            
            # ページのHTMLを取得
            html = self.driver.page_source
            
            # HTMLをファイルに保存（デバッグ用）
            with open(f'debug_original_{venue_code}_{race_no}.html', 'w', encoding='utf-8') as f:
                f.write(html)
            
            print(f'📄 HTMLを保存しました: debug_original_{venue_code}_{race_no}.html\n')
            
            # BeautifulSoupで解析
            soup = BeautifulSoup(html, 'html.parser')
            
            # データを抽出
            boats = self.extract_original_data(soup)
            
            if boats:
                print(f'✅ {len(boats)}艇のデータを取得\n')
            else:
                print('⚠️ データが見つかりませんでした\n')
                print('💡 debug_original_xx_x.html を確認してください')
            
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
    
    def extract_original_data(self, soup):
        """オリジナル展示データを抽出"""
        boats = []
        
        # テーブル内の各行を探す
        tables = soup.find_all('table')
        
        for table in tables:
            # テーブルに「展示タイム」「一周」「まわり足」「直線」が含まれているか確認
            table_text = table.get_text()
            
            if '展示タイム' in table_text or 'まわり足' in table_text or '直　線' in table_text:
                print('💡 オリジナル展示データのテーブルを発見\n')
                
                rows = table.find_all('tr')
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    
                    if len(cells) < 5:
                        continue
                    
                    cell_texts = [c.get_text(strip=True) for c in cells]
                    
                    # 艇番を探す（1-6）
                    boat_number = None
                    for i, text in enumerate(cell_texts):
                        if text in ['1', '2', '3', '4', '5', '6']:
                            boat_number = int(text)
                            boat_index = i
                            break
                    
                    if not boat_number:
                        continue
                    
                    # タイムデータを抽出
                    # パターン: X.XX形式の数値を探す
                    times = []
                    for text in cell_texts:
                        # 数字.数字のパターンをすべて抽出
                        matches = re.findall(r'\d+\.\d+', text)
                        times.extend(matches)
                    
                    # タイムが6つ以上ある場合（体重、チルト、展示、一周、まわり足、直線）
                    if boat_number and len(times) >= 6:
                        # 既に登録済みの艇番はスキップ
                        if any(b['number'] == boat_number for b in boats):
                            continue
                        
                        # times[0] = 体重（スキップ）
                        # times[1] = チルト（スキップ）
                        # times[2] = 展示タイム ← これを取得
                        # times[3] = 一周 ← これを取得
                        # times[4] = まわり足 ← これを取得
                        # times[5] = 直線 ← これを取得
                        
                        boat = {
                            'number': boat_number,
                            'exhibition': times[2] if len(times) > 2 else None,  # 展示タイム
                            'one_lap': times[3] if len(times) > 3 else None,      # 一周
                            'turning': times[4] if len(times) > 4 else None,      # まわり足
                            'straight': times[5] if len(times) > 5 else None      # 直線
                        }
                        
                        boats.append(boat)
                        
                        print(f'  {boat_number}号艇: 展示={boat["exhibition"]}, 一周={boat["one_lap"]}, まわり足={boat["turning"]}, 直線={boat["straight"]}')
        
        # 艇番順にソート
        boats.sort(key=lambda x: x['number'])
        
        return boats
    
    def close(self):
        """ブラウザを閉じる"""
        if self.driver:
            self.driver.quit()
            print('\nブラウザを閉じました')

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
        filename = f'{venue_name}_{race_no}R_{date}_オリジナル展示.csv'
    
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
    
    print('🚤 ボートレースキャスト オリジナル展示データ取得\n')
    print('='*60)
    print('設定')
    print('='*60)
    print(f'会場: {VENUES[VENUE]} ({VENUE})')
    print(f'レース: {RACE}R')
    print(f'日付: {DATE or "今日"}')
    print('='*60 + '\n')
    
    # スクレイパー初期化
    scraper = BoatcastScraperV2()
    
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
                print(f'  艇番: {df["number"].tolist()}')
                print(f'  展示タイム: {df["exhibition"].tolist()}')
                print(f'  一周: {df["one_lap"].tolist()}')
                print(f'  まわり足: {df["turning"].tolist()}')
                print(f'  直線: {df["straight"].tolist()}')
    
    finally:
        # ブラウザを閉じる
        scraper.close()
    
    print('\n✅ 完了！')

if __name__ == '__main__':
    main()