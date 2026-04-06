#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ボートレース シンsum理論 HTMLサイト生成スクリプト（6会場対応版）

平和島、蒲郡、戸田、住之江、多摩川、鳴門に対応
"""

import pandas as pd
from datetime import datetime
import os

# 会場設定
VENUE_PATTERNS = {
    '平和島': 'B',
    '蒲郡': 'B',
    '戸田': 'B',
    '住之江': 'A',
    '多摩川': 'B',
    '鳴門': 'B',
}

# Excelファイルから基準表を読み込む関数
def load_rate_table_from_excel(filepath):
    """Excelファイルから基準表を読み込み"""
    df = pd.read_excel(filepath)
    
    rate_tables = {}
    
    # 列ごとに処理（1号艇、2号艇...が異なる列にある）
    col_idx = 0
    while col_idx < len(df.columns):
        col_name = str(df.columns[col_idx])
        
        # 「号艇」を含む列を探す
        if '号艇' in col_name or (col_idx == 0 and ('１号艇' in str(df.iloc[0, col_idx]) or '1号艇' in str(df.iloc[0, col_idx]))):
            # 艇番を抽出
            import re
            
            # 列名から抽出を試みる
            match = re.search(r'(\d+)号艇', col_name)
            if not match and col_idx < len(df.columns):
                # 最初のセルから抽出を試みる
                first_cell = str(df.iloc[0, col_idx]) if col_idx == 0 else str(df.columns[col_idx])
                match = re.search(r'(\d+)号艇', first_cell)
            
            if match:
                boat_num = int(match.group(1))
                rate_tables[boat_num] = {}
                
                # この艇のデータを読み込み
                start_row = 0 if col_idx > 0 else 0
                for idx in range(start_row, len(df)):
                    range_text = str(df.iloc[idx, col_idx])
                    
                    if pd.isna(df.iloc[idx, col_idx]) or range_text == 'nan':
                        continue
                    
                    if '未満' in range_text or '以上' in range_text:
                        try:
                            # 着順率を取得（同じ行の次の4列）
                            rate_1 = int(round(float(df.iloc[idx, col_idx + 1]) * 100))
                            rate_2 = int(round(float(df.iloc[idx, col_idx + 2]) * 100))
                            rate_3 = int(round(float(df.iloc[idx, col_idx + 3]) * 100))
                            rate_r = int(round(float(df.iloc[idx, col_idx + 4]) * 100))
                            
                            # 範囲を解析
                            min_val, max_val = parse_range(range_text)
                            
                            if min_val != 0 or max_val != 0 or (min_val == 0 and max_val == 0.2):
                                rate_tables[boat_num][(min_val, max_val)] = {
                                    '1着率': rate_1,
                                    '2着率': rate_2,
                                    '3着率': rate_3,
                                    '3連対率': rate_r
                                }
                        except:
                            continue
        
        col_idx += 1
    
    return rate_tables

def parse_range(range_text):
    """範囲テキストを解析（全角・半角対応）"""
    import re
    
    # 全角を半角に変換
    range_text = range_text.replace('０', '0').replace('１', '1').replace('２', '2').replace('３', '3').replace('４', '4')
    range_text = range_text.replace('５', '5').replace('６', '6').replace('７', '7').replace('８', '8').replace('９', '9')
    range_text = range_text.replace('．', '.')
    
    if '未満' in range_text and '以上' not in range_text:
        # 「-0.4未満」のパターン
        match = re.search(r'([-\d.]+)未満', range_text)
        if match:
            return (-float('inf'), float(match.group(1)))
    
    elif '以上' in range_text and '未満' in range_text:
        # 「-0.4以上-0.2未満」または「0以上0.2未満」のパターン
        match = re.search(r'([-\d.]+)以上([-\d.]+)未満', range_text)
        if match:
            return (float(match.group(1)), float(match.group(2)))
    
    elif '以上' in range_text and '未満' not in range_text:
        # 「0.8以上」や「0.8以上1未満」のパターン
        # まず「以上X未満」パターンをチェック
        match = re.search(r'([-\d.]+)以上([-\d.]+)未満', range_text)
        if match:
            return (float(match.group(1)), float(match.group(2)))
        # 次に「以上」のみのパターン
        match = re.search(r'([-\d.]+)以上', range_text)
        if match:
            return (float(match.group(1)), float('inf'))
    
    return (0, 0)

def get_rate_change(rate_table, boat_number, diff):
    """差分から着順率の変化を取得"""
    if boat_number not in rate_table:
        return {'1着率': 0, '2着率': 0, '3着率': 0, '3連対率': 0}
    
    ranges = rate_table[boat_number]
    
    for (min_val, max_val), rates in ranges.items():
        if min_val <= diff < max_val:
            return rates
    
    return {'1着率': 0, '2着率': 0, '3着率': 0, '3連対率': 0}

def calculate_shinsum(df_race, pattern, rate_table):
    """シンsumを計算"""
    results = []
    
    for _, boat in df_race.iterrows():
        exhibition = float(boat['exhibition'])
        one_lap = float(boat['one_lap'])
        
        if pattern == 'A':
            third_value = float(boat['turning'])
            third_label = '周り足'
        else:
            third_value = float(boat['straight'])
            third_label = '直線'
        
        shinsum = exhibition + one_lap + third_value
        
        results.append({
            'number': int(boat['number']),
            'exhibition': exhibition,
            'one_lap': one_lap,
            'third': third_value,
            'third_label': third_label,
            'shinsum': shinsum
        })
    
    # 平均を計算
    avg = sum(r['shinsum'] for r in results) / len(results)
    
    # 差分と着順率を計算
    for r in results:
        r['diff_raw'] = r['shinsum'] - avg
        r['diff'] = avg - r['shinsum']  # 速い方がプラス
        r['avg'] = avg
        
        rate_change = get_rate_change(rate_table, r['number'], r['diff_raw'])
        r['rate_1'] = rate_change['1着率']
        r['rate_2'] = rate_change['2着率']
        r['rate_3'] = rate_change['3着率']
        r['rate_renntai'] = rate_change['3連対率']
    
    return results

def generate_html_multi_venue(csv_file, formatted_date):
    """複数会場対応のHTMLを生成"""
    
    if not os.path.exists(csv_file):
        print(f'❌ {csv_file} が見つかりません')
        return
    
    df = pd.read_csv(csv_file)
    
    if len(df) == 0:
        print('⚠️ データが空です')
        return
    
    print(f'📊 {len(df)}件のデータを読み込みました\n')
    
    # 基準表を読み込み
    print('📖 基準表を読み込み中...\n')
    rate_tables = {}
    
    excel_files = {
        '平和島': None,  # 手動定義済み
        '蒲郡': '/mnt/user-data/uploads/蒲郡_ハ_ターンB.xlsx',
        '戸田': '/mnt/user-data/uploads/戸田_ハ_ターンB.xlsx',
        '住之江': '/mnt/user-data/uploads/住之江_ハ_ターンA.xlsx',
        '多摩川': '/mnt/user-data/uploads/多摩川_ハ_ターンB.xlsx',
        '鳴門': '/mnt/user-data/uploads/鳴門_ハ_ターンB.xlsx',
    }
    
    # 平和島は手動定義（前のコードと同じ）
    rate_tables['平和島'] = {
        1: {(-float('inf'), -0.2): {'1着率': -13, '2着率': 2, '3着率': 2, '3連対率': -9}, (-0.2, 0): {'1着率': -9, '2着率': 2, '3着率': 0, '3連対率': -7}, (0, 0.2): {'1着率': -6, '2着率': 0, '3着率': 1, '3連対率': -6}, (0.2, 0.4): {'1着率': -3, '2着率': 0, '3着率': 2, '3連対率': -1}, (0.4, 0.6): {'1着率': 3, '2着率': 0, '3着率': -1, '3連対率': 2}, (0.6, 0.8): {'1着率': 11, '2着率': 2, '3着率': -3, '3連対率': 10}, (0.8, 1.0): {'1着率': 13, '2着率': -6, '3着率': -1, '3連対率': 5}, (1.0, float('inf')): {'1着率': 19, '2着率': -3, '3着率': -3, '3連対率': 13}},
        2: {(-float('inf'), -0.6): {'1着率': -15, '2着率': -9, '3着率': 4, '3連対率': -20}, (-0.6, -0.4): {'1着率': -2, '2着率': -9, '3着率': -2, '3連対率': -13}, (-0.4, -0.2): {'1着率': -3, '2着率': -5, '3着率': -4, '3連対率': -12}, (-0.2, 0): {'1着率': -3, '2着率': -2, '3着率': 1, '3連対率': -4}, (0, 0.2): {'1着率': -2, '2着率': 3, '3着率': 2, '3連対率': 3}, (0.2, 0.4): {'1着率': 4, '2着率': 4, '3着率': 2, '3連対率': 9}, (0.4, 0.6): {'1着率': 5, '2着率': 3, '3着率': -2, '3連対率': 7}, (0.6, 0.8): {'1着率': 12, '2着率': 6, '3着率': -2, '3連対率': 16}, (0.8, float('inf')): {'1着率': 19, '2着率': 7, '3着率': -7, '3連対率': 19}},
        3: {(-float('inf'), -0.8): {'1着率': -7, '2着率': -4, '3着率': -2, '3連対率': -13}, (-0.8, -0.6): {'1着率': -6, '2着率': -5, '3着率': -3, '3連対率': -14}, (-0.6, -0.4): {'1着率': -6, '2着率': -4, '3着率': -2, '3連対率': -13}, (-0.4, -0.2): {'1着率': -3, '2着率': -2, '3着率': 2, '3連対率': -3}, (-0.2, 0): {'1着率': -1, '2着率': 0, '3着率': -1, '3連対率': -1}, (0, 0.2): {'1着率': 1, '2着率': 2, '3着率': 0, '3連対率': 4}, (0.2, 0.4): {'1着率': 3, '2着率': 5, '3着率': 2, '3連対率': 9}, (0.4, 0.6): {'1着率': 9, '2着率': 2, '3着率': 2, '3連対率': 14}, (0.6, float('inf')): {'1着率': 16, '2着率': -1, '3着率': -2, '3連対率': 14}},
        4: {(-float('inf'), -0.8): {'1着率': -10, '2着率': -10, '3着率': -10, '3連対率': -30}, (-0.8, -0.6): {'1着率': -1, '2着率': -5, '3着率': -2, '3連対率': -7}, (-0.6, -0.4): {'1着率': -4, '2着率': -4, '3着率': -4, '3連対率': -12}, (-0.4, -0.2): {'1着率': -2, '2着率': -4, '3着率': 0, '3連対率': -5}, (-0.2, 0): {'1着率': -3, '2着率': 2, '3着率': 2, '3連対率': 1}, (0, 0.2): {'1着率': 2, '2着率': 1, '3着率': 1, '3連対率': 4}, (0.2, 0.4): {'1着率': 3, '2着率': 1, '3着率': 2, '3連対率': 5}, (0.4, 0.6): {'1着率': 8, '2着率': 8, '3着率': -1, '3連対率': 14}, (0.6, float('inf')): {'1着率': 18, '2着率': 10, '3着率': -5, '3連対率': 22}},
        5: {(-float('inf'), -0.8): {'1着率': -3, '2着率': -3, '3着率': -1, '3連対率': -7}, (-0.8, -0.6): {'1着率': -5, '2着率': -3, '3着率': -4, '3連対率': -12}, (-0.6, -0.4): {'1着率': -3, '2着率': -6, '3着率': 3, '3連対率': -7}, (-0.4, -0.2): {'1着率': -1, '2着率': -2, '3着率': -1, '3連対率': -4}, (-0.2, 0): {'1着率': -2, '2着率': 0, '3着率': -1, '3連対率': -2}, (0, 0.2): {'1着率': 1, '2着率': 3, '3着率': -1, '3連対率': 3}, (0.2, 0.4): {'1着率': 5, '2着率': 1, '3着率': 1, '3連対率': 8}, (0.4, 0.6): {'1着率': 9, '2着率': 6, '3着率': 3, '3連対率': 17}, (0.6, float('inf')): {'1着率': 3, '2着率': 13, '3着率': 1, '3連対率': 16}},
        6: {(-float('inf'), -0.1): {'1着率': 0, '2着率': -3, '3着率': -6, '3連対率': -9}, (-0.1, -0.08): {'1着率': -3, '2着率': -9, '3着率': -8, '3連対率': -20}, (-0.08, -0.06): {'1着率': -2, '2着率': -5, '3着率': -5, '3連対率': -12}, (-0.06, -0.04): {'1着率': 0, '2着率': -4, '3着率': -3, '3連対率': -7}, (-0.04, -0.02): {'1着率': -1, '2着率': -1, '3着率': -3, '3連対率': -5}, (-0.02, 0): {'1着率': 1, '2着率': 2, '3着率': 2, '3連対率': 4}, (0, 0.2): {'1着率': 1, '2着率': 1, '3着率': -1, '3連対率': 2}, (0.2, 0.4): {'1着率': 1, '2着率': 4, '3着率': 7, '3連対率': 11}, (0.4, 0.6): {'1着率': 1, '2着率': 3, '3着率': 5, '3連対率': 9}, (0.6, float('inf')): {'1着率': -2, '2着率': 8, '3着率': 13, '3連対率': 20}},
    }
    
    # 他の会場のExcelファイルを読み込み
    for venue_name, filepath in excel_files.items():
        if filepath and os.path.exists(filepath):
            print(f'  📖 {venue_name} を読み込み中...')
            rate_tables[venue_name] = load_rate_table_from_excel(filepath)
    
    print(f'\n✅ {len(rate_tables)}会場の基準表を読み込みました\n')
    
    # 対応会場のデータのみ抽出
    df_target = df[df['venue_name'].isin(VENUE_PATTERNS.keys())]
    
    if len(df_target) == 0:
        print('⚠️ 対応会場のデータがありません')
        return
    
    # HTMLヘッダー
    html = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>シンsum理論</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Hiragino Sans', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        header { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); margin-bottom: 30px; text-align: center; }
        h1 { color: #333; font-size: 2.5em; margin-bottom: 10px; }
        .venue-tabs { display: flex; flex-wrap: wrap; gap: 10px; background: white; padding: 20px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); margin-bottom: 30px; }
        .tab-button { padding: 12px 24px; border: none; background: #f0f0f0; border-radius: 8px; cursor: pointer; font-size: 1em; font-weight: bold; transition: all 0.3s; }
        .tab-button:hover { background: #667eea; color: white; transform: translateY(-2px); }
        .tab-button.active { background: #667eea; color: white; }
        .venue-content { display: none; }
        .venue-content.active { display: block; }
        .race-card { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); margin-bottom: 20px; }
        .race-title { font-size: 1.5em; color: #667eea; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 3px solid #667eea; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 12px 8px; text-align: center; border-bottom: 1px solid #eee; font-size: 0.95em; }
        th { background: #f8f9fa; font-weight: bold; color: #333; }
        tr:hover { background: #f8f9fa; }
        .boat-1, .boat-2 { border-left: 4px solid #000; }
        .boat-3 { border-left: 4px solid #ff0000; }
        .boat-4 { border-left: 4px solid #0000ff; }
        .boat-5 { border-left: 4px solid #ffff00; }
        .boat-6 { border-left: 4px solid #00ff00; }
        .positive { color: #28a745; font-weight: bold; }
        .negative { color: #dc3545; font-weight: bold; }
        .rate-box { display: inline-block; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
        .rate-positive { background: #d4edda; color: #155724; }
        .rate-negative { background: #f8d7da; color: #721c24; }
        .rate-neutral { background: #e2e3e5; color: #383d41; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚤 シンsum理論</h1>
            <p class="date">""" + formatted_date + """</p>
        </header>
        <div class="venue-tabs">
"""
    
    # タブボタン生成
    venues_with_data = df_target['venue_name'].unique()
    for i, venue_name in enumerate(venues_with_data):
        active = 'active' if i == 0 else ''
        pattern_label = 'パターンA（展示+1周+周り足）' if VENUE_PATTERNS[venue_name] == 'A' else 'パターンB（展示+1周+直線）'
        html += f'            <button class="tab-button {active}" onclick="showVenue(\'{venue_name}\')" title="{pattern_label}">{venue_name}</button>\n'
    
    html += """        </div>
"""
    
    # 各会場のコンテンツ生成
    for i, venue_name in enumerate(venues_with_data):
        active = 'active' if i == 0 else ''
        pattern = VENUE_PATTERNS[venue_name]
        rate_table = rate_tables.get(venue_name, {})
        
        venue_data = df_target[df_target['venue_name'] == venue_name]
        
        html += f'        <div class="venue-content {active}" id="{venue_name}">\n'
        
        races = venue_data.groupby('race_no')
        
        for race_no, race_data in races:
            shinsum_results = calculate_shinsum(race_data, pattern, rate_table)
            
            third_label = shinsum_results[0]['third_label']
            
            html += f'            <div class="race-card">\n'
            html += f'                <h2 class="race-title">{race_no}R（平均: {shinsum_results[0]["avg"]:.2f}）</h2>\n'
            html += '                <table>\n'
            html += '                    <thead><tr>\n'
            html += '                        <th>艇番</th><th>展示</th><th>1周</th><th>' + third_label + '</th>\n'
            html += '                        <th>シンsum</th><th>平均との差</th>\n'
            html += '                        <th>1着率</th><th>2着率</th><th>3着率</th><th>3連対率</th>\n'
            html += '                    </tr></thead>\n'
            html += '                    <tbody>\n'
            
            for result in shinsum_results:
                boat_class = f'boat-{result["number"]}'
                diff_class = 'positive' if result['diff'] > 0 else 'negative' if result['diff'] < 0 else ''
                diff_sign = '+' if result['diff'] > 0 else ''
                
                def rate_class(val):
                    return 'rate-positive' if val > 0 else 'rate-negative' if val < 0 else 'rate-neutral'
                
                def rate_sign(val):
                    return f'+{val}' if val > 0 else str(val)
                
                html += f'                        <tr class="{boat_class}">\n'
                html += f'                            <td><strong>{result["number"]}号艇</strong></td>\n'
                html += f'                            <td>{result["exhibition"]:.2f}</td>\n'
                html += f'                            <td>{result["one_lap"]:.2f}</td>\n'
                html += f'                            <td>{result["third"]:.2f}</td>\n'
                html += f'                            <td><strong>{result["shinsum"]:.2f}</strong></td>\n'
                html += f'                            <td class="{diff_class}"><strong>{diff_sign}{result["diff"]:.2f}</strong></td>\n'
                html += f'                            <td><span class="rate-box {rate_class(result["rate_1"])}">{rate_sign(result["rate_1"])}%</span></td>\n'
                html += f'                            <td><span class="rate-box {rate_class(result["rate_2"])}">{rate_sign(result["rate_2"])}%</span></td>\n'
                html += f'                            <td><span class="rate-box {rate_class(result["rate_3"])}">{rate_sign(result["rate_3"])}%</span></td>\n'
                html += f'                            <td><span class="rate-box {rate_class(result["rate_renntai"])}">{rate_sign(result["rate_renntai"])}%</span></td>\n'
                html += '                        </tr>\n'
            
            html += '                    </tbody>\n'
            html += '                </table>\n'
            html += '            </div>\n'
        
        html += '        </div>\n'
    
    html += """    </div>
    <script>
        function showVenue(venueName) {
            document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.venue-content').forEach(content => content.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById(venueName).classList.add('active');
            window.scrollTo({top: 0, behavior: 'smooth'});
        }
    </script>
</body>
</html>
"""
    
    output_file = 'shinsum_multi_venue.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f'✅ {output_file} を生成しました！')
    return output_file

def main():
    print('🚤 シンsum理論 HTMLサイト生成（6会場対応）\n')
    print('='*60 + '\n')
    
    import glob
    csv_files = glob.glob('all_races_*.csv')
    
    if not csv_files:
        print('❌ CSVファイルが見つかりません')
        return
    
    csv_file = sorted(csv_files)[-1]
    print(f'📄 使用するCSVファイル: {csv_file}\n')
    
    # CSVファイル名から日付を抽出
    import re
    date_match = re.search(r'(\d{8})', csv_file)
    if date_match:
        date_str = date_match.group(1)
        # YYYYMMDD → YYYY年MM月DD日
        formatted_date = f'{date_str[0:4]}年{date_str[4:6]}月{date_str[6:8]}日'
    else:
        formatted_date = datetime.now().strftime('%Y年%m月%d日')
    
    output_file = generate_html_multi_venue(csv_file, formatted_date)
    
    if output_file:
        print(f'\n{"="*60}')
        print('🎉 完了！')
        print('='*60)
        print(f'\n📂 生成されたファイル: {output_file}')
        print('\n💡 ブラウザで開くには:')
        print(f'   open {output_file}')

if __name__ == '__main__':
    main()