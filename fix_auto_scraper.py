# このスクリプトを実行すると、auto_scraper.pyの問題部分を自動修正します

with open('/Users/suginotooru/Desktop/boatrace-scraper/auto_scraper.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 175行目から240行目を新しいコードに置き換え
new_code = '''        
        boats.sort(key=lambda x: x['number'])
        return boats
    
    def get_all_races_for_venue(self, venue_no, date, existing_df=None):
        """1会場の全12レースを取得（効率化版）"""
        venue_name = VENUES[venue_no]
        
        print(f'\\n{"="*60}')
        print(f'🏁 {venue_name} ({venue_no}) - レース取得開始')
        print('='*60)
        
        # まず1Rをチェック（開催確認）
        print(f'  📊 1R 取得中...', end=' ')
        boats_1r = self.get_race_data(venue_no, 1, date)
        
        if not boats_1r:
            print('⚠️ データなし（開催していない可能性）')
            return []
        
        # 1Rのデータがある = 開催中
        print(f'✅ 開催確認')
        
        all_data = []
        
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
                
                print(f'  💡 新しいデータを取得したため、この会場は終了します')
                break
            else:
                print('⚠️ データなし（この会場は終了）')
                break
        
        return all_data
    
    def close(self):
        """ブラウザを閉じる"""
        if self.driver:
            self.driver.quit()

'''

# 175-239行目を置き換え（0-indexedなので174-239）
new_lines = lines[:174] + [new_code] + lines[239:]

# ファイルに書き込み
with open('/Users/suginotooru/Desktop/boatrace-scraper/auto_scraper.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('✅ 修正完了！')