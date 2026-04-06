#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
シンsum理論 増分更新スクリプト

既存のCSVに新しく公開されたレースデータを追加し、
shinsum理論を再計算してHTMLを更新する
"""

import subprocess
from datetime import datetime
import pandas as pd
import os

def main():
    DATE = datetime.now().strftime('%Y%m%d')
    csv_file = f'all_races_{DATE}.csv'
    
    print(f'🔄 シンsum理論 増分更新')
    print(f'📅 日付: {DATE}')
    print('='*60)
    
    # 既存データを読み込み（なければ空）
    if os.path.exists(csv_file):
        df_old = pd.read_csv(csv_file)
        old_count = len(df_old)
        print(f'📂 既存データ: {old_count}艇')
    else:
        df_old = pd.DataFrame()
        old_count = 0
        print(f'📂 既存データ: なし（新規作成）')
    
    # 新しいデータを取得
    print('\n🚤 新規データ取得中...')
    subprocess.run(['python3', 'auto_scraper.py'])
    
    # 新しく取得したデータを読み込み
    if os.path.exists(csv_file):
        df_new = pd.read_csv(csv_file)
        new_count = len(df_new)
        
        # 増分を計算
        added = new_count - old_count
        
        print(f'\n📊 結果:')
        print(f'  - 既存: {old_count}艇')
        print(f'  - 現在: {new_count}艇')
        print(f'  - 追加: {added}艇')
        
        if added > 0:
            # shinsum理論を実行
            print(f'\n📊 shinsum理論を再計算中...')
            subprocess.run(['python3', 'shinsum_fixed.py', csv_file])
            print('\n✅ 更新完了！')
        else:
            print('\n💤 新しいデータなし（スキップ）')
    else:
        print('\n⚠️ データ取得失敗')

if __name__ == '__main__':
    main()