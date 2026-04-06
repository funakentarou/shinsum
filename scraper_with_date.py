#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ボートレース 日付指定データ取得スクリプト

使い方:
  python3 scraper_with_date.py 20260104
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
import sys

# 全24会場
VENUES = {
    1: '桐生', 2: '戸田', 3: '江戸川', 4: '平和島',
    5: '多摩川', 6: '浜名湖', 7: '蒲郡', 8: '常滑',
    9: '津', 10: '三国', 11: 'びわこ', 12: '住之江',
    13: '尼崎', 14: '鳴門', 15: '丸亀', 16: '児島',
    17: '宮島', 18: '徳山', 19: '下関', 20: '若松',
    21: '芦屋', 22: '福岡', 23: '唐津', 24: '大村'
}

class DateScraper:
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
    
    def get_race_data(self, venue_no, race_no, date):
        """1レースのデータを取得"""
        if not self.driver:
            self.setup_driver()
        
        venue_code = str(venue_no).zfill(2)
        url = f'https://race.boatcast.jp/replay?jo={venue_code}&ymd={date}&race={race_no}'
        
        try:
            self.driver.get(url)
            time.sleep(3)
            
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            data_rows = []
            
            script_tag = soup.find('script', string=re.compile('var tenji_data'))
            if not script_tag:
                return None
            
            tenji_match = re.search(r'var tenji_data\s*=\s*({.*?});', script_tag.string, re.DOTALL)
            if not tenji_match:
                return None
            
            tenji_json = tenji_match.group(1)
            
            for i in range(1, 7):
                match = re.search(f'"{i}":\\s*{{[^}}]*"tenji":\\s*"([^"]+)"[^}}]*"ichisyu":\\s*"([^"]+)"[^}}]*"mawari":\\s*"([^"]+)"[^}}]*"chokusen":\\s*"([^"]+)"', tenji_json)
                if match:
                    exhibition = match.group(1).strip()
                    one_lap = match.group(2).strip()
                    turning = match.group(3).strip()
                    straight = match.group(4).strip()
                    
                    data_rows.append({
                        'venue_no': venue_no,
                        'venue_name': VENUES[venue_no],
                        'race_no': race_no,
                        'number': i,
                        'exhibition': exhibition,
                        'one_lap': one_lap,
                        'turning': turning,
                        'straight': straight
                    })
            
            return data_rows
            
        except Exception as e:
            print(f'  ⚠️ {race_no}R: データ取得失敗')
            return None
    
    def scrape_all(self, target_date):
        """指定日付の全会場データを取得"""
        print(f'📅 {target_date[:4]}年{target_date[4:6]}月{target_date[6:8]}日のデータを取得します\n')
        
        all_data = []
        
        # 全24会場を試す
        for venue_no in range(1, 25):
            print(f'🏁 {VENUES[venue_no]}（会場{venue_no}）')
            
            venue_data = []
            
            # 最大12レースまで試す
            for race_no in range(1, 13):
                data = self.get_race_data(venue_no, race_no, target_date)
                
                if data:
                    venue_data.extend(data)
                    print(f'  ✅ {race_no}R')
                else:
                    # 1つ失敗したら次の会場へ
                    if race_no == 1:
                        print(f'  ⚠️ 開催なし')
                    break
                
                time.sleep(1)
            
            if venue_data:
                all_data.extend(venue_data)
            
            print()
        
        if all_data:
            df = pd.DataFrame(all_data)
            output_file = f'all_races_{target_date}.csv'
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f'✅ {output_file} を保存しました')
            print(f'📊 合計 {len(all_data)} レース分のデータ\n')
            return output_file
        else:
            print('❌ データが取得できませんでした')
            return None
    
    def close(self):
        """ブラウザを閉じる"""
        if self.driver:
            self.driver.quit()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('使い方: python3 scraper_with_date.py YYYYMMDD')
        print('例: python3 scraper_with_date.py 20260104')
        sys.exit(1)
    
    target_date = sys.argv[1]
    
    # 日付の検証
    if not re.match(r'^\d{8}$', target_date):
        print('❌ 日付はYYYYMMDD形式で指定してください（例: 20260104）')
        sys.exit(1)
    
    scraper = DateScraper()
    
    try:
        scraper.scrape_all(target_date)
    finally:
        scraper.close()