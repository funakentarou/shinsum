#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ボートレース 全レースデータ完全自動取得スクリプト

開催会場を自動取得し、全レースのオリジナル展示データを取得します。
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

class FullAutoScraper:
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
    
    def get_todays_venues(self):
        """開催会場を自動取得"""
        if not self.driver:
            self.setup_driver()
        
        url = 'https://boatcast.jp/index.html'
        
        print('🔍 開催会場を自動取得中...\n')
        
        try:
            self.driver.get(url)
            time.sleep(10)
            
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # 会場名から会場番号への逆引き
            venue_name_to_no = {name: no for no, name in VENUES.items()}
            
            venues = []
            elements = soup.find_all(['div', 'span', 'a', 'p'])
            
            full_text = soup.get_text()
            for name, no in venue_name_to_no.items():
                if name in full_text:
                    if no not in venues:
                        venues.append(no)
            
            venues.sort()
            
            if venues:
                print(f'✅ {len(venues)}会場を検出\n')
            
            return venues
            
        except Exception as e:
            print(f'❌ 会場取得エラー: {e}')
            # エラー時は全24会場を返す
            return list(range(1, 25))
    
    def get_race_data(self, venue_no, race_no, date):
        """1レースのデータを取得"""
        if not self.driver:
            self.setup_driver()
        
        venue_code = str(venue_no).zfill(2)
        url = f'https://race.boatcast.jp/replay?jo={venue_code}&ymd={date}&race={race_no}'
        
        try:
            self.driver.get(url)
            time.sleep(5)
            
            # 「直前情報」タブをクリック
            try:
                chokuzen_tab = self.driver.find_element(By.XPATH, "//button[contains(text(), '直前情報')] | //a[contains(text(), '直前情報')]")
                self.driver.execute_script("arguments[0].click();", chokuzen_tab)
                time.sleep(3)
            except:
                pass
            
            # 「オリジナル展示データ」タブをクリック
            try:
                original_tab = self.driver.find_element(By.XPATH, "//button[contains(text(), 'オリジナル展示データ')] | //a[contains(text(), 'オリジナル展示データ')]")
                self.driver.execute_script("arguments[0].click();", original_tab)
                time.sleep(3)
            except:
                pass
            
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            boats = self.extract_original_data(soup)
            return boats
            
        except Exception as e:
            return []
    
    def extract_original_data(self, soup):
        """オリジナル展示データを抽出"""
        boats = []
        tables = soup.find_all('table')
        
        for table in tables:
            table_text = table.get_text()
            
            if '展示タイム' not in table_text:
                continue
            
            # ヘッダー行から列インデックスを特定
            headers = []
            header_row = table.find('tr')
            if header_row:
                headers = [th.get_text(strip=True) for th in header_row.find_all(['th','td'])]
            
            # 列インデックスを特定
            exhibition_idx = None
            one_lap_idx = None
            turning_idx = None
            straight_idx = None
            
            for i, h in enumerate(headers):
                if '展示タイム' in h or '展示' in h:
                    exhibition_idx = i
                elif '一' in h and '周' in h or '一周' in h:
                    one_lap_idx = i
                elif 'まわり足' in h or '周り足' in h:
                    turning_idx = i
                elif '直線' in h or '直　線' in h:
                    straight_idx = i
            
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td','th'])
                if len(cells) < 3:
                    continue
                
                cell_texts = [c.get_text(strip=True) for c in cells]
                
                # 艇番を取得
                boat_number = None
                if cell_texts and cell_texts[0] in ['1','2','3','4','5','6']:
                    boat_number = int(cell_texts[0])
                
                if not boat_number:
                    continue
                
                if any(b['number'] == boat_number for b in boats):
                    continue
                
                # タイムを取得
                def get_val(idx):
                    if idx is not None and idx < len(cell_texts):
                        return cell_texts[idx]
                    return None
                
                exhibition = get_val(exhibition_idx)
                one_lap = get_val(one_lap_idx)
                turning = get_val(turning_idx)
                straight = get_val(straight_idx)
                
                if exhibition and one_lap:
                    boats.append({
                        'number': boat_number,
                        'exhibition': exhibition,
                        'one_lap': one_lap,
                        'turning': turning,
                        'straight': straight
                    })
        
        boats.sort(key=lambda x: x['number'])
        return boats
    
    def get_all_races_for_venue(self, venue_no, date, existing_df=None):
        """1会場の全12レースを取得（効率化版）"""
        venue_name = VENUES[venue_no]
        
        print(f'\n{"="*60}')
        print(f'🏁 {venue_name} ({venue_no}) - レース取得開始')
        print('='*60)
        
        # まず1Rをチェック（開催確認）
        all_data = []
        
        # 1Rが既に取得済みかチェック
        if existing_df is not None:
            r1_exists = ((existing_df['venue_no'] == venue_no) & 
                        (existing_df['race_no'] == 1)).any()
            if r1_exists:
                print(f'  📊 1R 取得中... ⏭️ スキップ（取得済み）')
            else:
                print(f'  📊 1R 取得中...', end=' ')
                boats_1r = self.get_race_data(venue_no, 1, date)
                if not boats_1r:
                    print('⚠️ データなし（開催していない可能性）')
                    return []
                print(f'✅ 開催確認')
                for boat in boats_1r:
                    boat['venue_no'] = venue_no
                    boat['venue_name'] = venue_name
                    boat['race_no'] = 1
                    all_data.append(boat)
        else:
            print(f'  📊 1R 取得中...', end=' ')
            boats_1r = self.get_race_data(venue_no, 1, date)
            if not boats_1r:
                print('⚠️ データなし（開催していない可能性）')
                return []
            print(f'✅ 開催確認')
            for boat in boats_1r:
                boat['venue_no'] = venue_no
                boat['venue_name'] = venue_name
                boat['race_no'] = 1
                all_data.append(boat)
        
        # 2Rから順番にチェック
        for race_no in range(2, 13):
            # 既に取得済みかチェック
            if existing_df is not None:
                already_exists = ((existing_df['venue_no'] == venue_no) & 
                                (existing_df['race_no'] == race_no)).any()
                if already_exists:
                    print(f'  📊 {race_no}R 取得中... ⏭️ スキップ（取得済み）')
                    continue
            
            print(f'  📊 {race_no}R 取得中...', end=' ')
            
            boats = self.get_race_data(venue_no, race_no, date)
            
            if boats:
                print(f'✅ {len(boats)}艇')
                
                for boat in boats:
                    boat['venue_no'] = venue_no
                    boat['venue_name'] = venue_name
                    boat['race_no'] = race_no
                    all_data.append(boat)
                
                pass
            else:
                print('⚠️ データなし（この会場は終了）')
                break
        
        return all_data
    
    def close(self):
        """ブラウザを閉じる"""
        if self.driver:
            self.driver.quit()


def main():
    """メイン処理"""
    
    DATE = datetime.now().strftime('%Y%m%d')
    
    print('🚤 ボートレース 全レースデータ完全自動取得\n')
    print('='*60)
    print(f'日付: {DATE} ({datetime.now().strftime("%Y年%m月%d日")})')
    print('='*60 + '\n')
    
    scraper = FullAutoScraper()
    
    try:
        # 開催会場を自動取得
        venues = scraper.get_todays_venues()
        
        print('📋 対象会場:')
        for venue_no in venues:
            print(f'  - {VENUES[venue_no]}')
        print(f'\n合計: {len(venues)}会場')
        
        # 全会場のデータを取得
        # 既存データを読み込み（スキップ判定用）
        filename = f'all_races_{DATE}.csv'
        existing_df = None
        if os.path.exists(filename):
            existing_df = pd.read_csv(filename)
        
        # 全会場のデータを取得
        all_data = []
        
        for venue_no in venues:
            venue_data = scraper.get_all_races_for_venue(venue_no, DATE, existing_df)
            all_data.extend(venue_data)
        # DataFrameに変換
        if all_data:
            df = pd.DataFrame(all_data)
            
            # 列の順番を整理
            df = df[['venue_no', 'venue_name', 'race_no', 'number', 'exhibition', 'one_lap', 'turning', 'straight']]
            # CSV保存（追加モード）
            filename = f'all_races_{DATE}.csv'

            # 既存データを読み込み
            if os.path.exists(filename):
                df_old = pd.read_csv(filename)
                # 重複を削除して結合
                df_combined = pd.concat([df_old, df], ignore_index=True)
                df_combined = df_combined.drop_duplicates(subset=['venue_no', 'race_no', 'number'], keep='last')
                df_combined.to_csv(filename, index=False, encoding='utf-8-sig')
                added_count = len(df_combined) - len(df_old)
            else:
                df_combined = df
                df_combined.to_csv(filename, index=False, encoding='utf-8-sig')
                added_count = len(df)
            
            print(f'\n{"="*60}')
            print('📊 取得結果')
            print('='*60)
            print(f'対象会場数: {len(venues)}会場')
            print(f'データ取得会場数: {len(df_combined["venue_no"].unique())}会場')
            print(f'総レース数: {len(df_combined.groupby(["venue_no", "race_no"]))}レース')
            print(f'総データ数: {len(df_combined)}艇 (追加: {added_count}艇)')
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