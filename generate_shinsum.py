#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ボートレース シンsum理論 HTMLサイト生成スクリプト

シンsum理論を実装したHTMLサイトを生成します。
"""

import pandas as pd
from datetime import datetime
import os

# 平和島の基準表（パターンB: 展示+1周+直線）
HEIWAJIMA_RATES = {
    # 1号艇
    1: {
        (-float('inf'), -0.2): {'1着率': -13, '2着率': 2, '3着率': 2, '3連対率': -9},
        (-0.2, 0): {'1着率': -9, '2着率': 2, '3着率': 0, '3連対率': -7},
        (0, 0.2): {'1着率': -6, '2着率': 0, '3着率': 1, '3連対率': -6},
        (0.2, 0.4): {'1着率': -3, '2着率': 0, '3着率': 2, '3連対率': -1},
        (0.4, 0.6): {'1着率': 3, '2着率': 0, '3着率': -1, '3連対率': 2},
        (0.6, 0.8): {'1着率': 11, '2着率': 2, '3着率': -3, '3連対率': 10},
        (0.8, 1.0): {'1着率': 13, '2着率': -6, '3着率': -1, '3連対率': 5},
        (1.0, float('inf')): {'1着率': 19, '2着率': -3, '3着率': -3, '3連対率': 13},
    },
    # 2号艇
    2: {
        (-float('inf'), -0.6): {'1着率': -15, '2着率': -9, '3着率': 4, '3連対率': -20},
        (-0.6, -0.4): {'1着率': -2, '2着率': -9, '3着率': -2, '3連対率': -13},
        (-0.4, -0.2): {'1着率': -3, '2着率': -5, '3着率': -4, '3連対率': -12},
        (-0.2, 0): {'1着率': -3, '2着率': -2, '3着率': 1, '3連対率': -4},
        (0, 0.2): {'1着率': -2, '2着率': 3, '3着率': 2, '3連対率': 3},
        (0.2, 0.4): {'1着率': 4, '2着率': 4, '3着率': 2, '3連対率': 9},
        (0.4, 0.6): {'1着率': 5, '2着率': 3, '3着率': -2, '3連対率': 7},
        (0.6, 0.8): {'1着率': 12, '2着率': 6, '3着率': -2, '3連対率': 16},
        (0.8, float('inf')): {'1着率': 19, '2着率': 7, '3着率': -7, '3連対率': 19},
    },
    # 3号艇
    3: {
        (-float('inf'), -0.8): {'1着率': -7, '2着率': -4, '3着率': -2, '3連対率': -13},
        (-0.8, -0.6): {'1着率': -6, '2着率': -5, '3着率': -3, '3連対率': -14},
        (-0.6, -0.4): {'1着率': -6, '2着率': -4, '3着率': -2, '3連対率': -13},
        (-0.4, -0.2): {'1着率': -3, '2着率': -2, '3着率': 2, '3連対率': -3},
        (-0.2, 0): {'1着率': -1, '2着率': 0, '3着率': -1, '3連対率': -1},
        (0, 0.2): {'1着率': 1, '2着率': 2, '3着率': 0, '3連対率': 4},
        (0.2, 0.4): {'1着率': 3, '2着率': 5, '3着率': 2, '3連対率': 9},
        (0.4, 0.6): {'1着率': 9, '2着率': 2, '3着率': 2, '3連対率': 14},
        (0.6, float('inf')): {'1着率': 16, '2着率': -1, '3着率': -2, '3連対率': 14},
    },
    # 4号艇
    4: {
        (-float('inf'), -0.8): {'1着率': -10, '2着率': -10, '3着率': -10, '3連対率': -30},
        (-0.8, -0.6): {'1着率': -1, '2着率': -5, '3着率': -2, '3連対率': -7},
        (-0.6, -0.4): {'1着率': -4, '2着率': -4, '3着率': -4, '3連対率': -12},
        (-0.4, -0.2): {'1着率': -2, '2着率': -4, '3着率': 0, '3連対率': -5},
        (-0.2, 0): {'1着率': -3, '2着率': 2, '3着率': 2, '3連対率': 1},
        (0, 0.2): {'1着率': 2, '2着率': 1, '3着率': 1, '3連対率': 4},
        (0.2, 0.4): {'1着率': 3, '2着率': 1, '3着率': 2, '3連対率': 5},
        (0.4, 0.6): {'1着率': 8, '2着率': 8, '3着率': -1, '3連対率': 14},
        (0.6, float('inf')): {'1着率': 18, '2着率': 10, '3着率': -5, '3連対率': 22},
    },
    # 5号艇
    5: {
        (-float('inf'), -0.8): {'1着率': -3, '2着率': -3, '3着率': -1, '3連対率': -7},
        (-0.8, -0.6): {'1着率': -5, '2着率': -3, '3着率': -4, '3連対率': -12},
        (-0.6, -0.4): {'1着率': -3, '2着率': -6, '3着率': 3, '3連対率': -7},
        (-0.4, -0.2): {'1着率': -1, '2着率': -2, '3着率': -1, '3連対率': -4},
        (-0.2, 0): {'1着率': -2, '2着率': 0, '3着率': -1, '3連対率': -2},
        (0, 0.2): {'1着率': 1, '2着率': 3, '3着率': -1, '3連対率': 3},
        (0.2, 0.4): {'1着率': 5, '2着率': 1, '3着率': 1, '3連対率': 8},
        (0.4, 0.6): {'1着率': 9, '2着率': 6, '3着率': 3, '3連対率': 17},
        (0.6, float('inf')): {'1着率': 3, '2着率': 13, '3着率': 1, '3連対率': 16},
    },
    # 6号艇
    6: {
        (-float('inf'), -0.1): {'1着率': 0, '2着率': -3, '3着率': -6, '3連対率': -9},
        (-0.1, -0.08): {'1着率': -3, '2着率': -9, '3着率': -8, '3連対率': -20},
        (-0.08, -0.06): {'1着率': -2, '2着率': -5, '3着率': -5, '3連対率': -12},
        (-0.06, -0.04): {'1着率': 0, '2着率': -4, '3着率': -3, '3連対率': -7},
        (-0.04, -0.02): {'1着率': -1, '2着率': -1, '3着率': -3, '3連対率': -5},
        (-0.02, 0): {'1着率': 1, '2着率': 2, '3着率': 2, '3連対率': 4},
        (0, 0.2): {'1着率': 1, '2着率': 1, '3着率': -1, '3連対率': 2},
        (0.2, 0.4): {'1着率': 1, '2着率': 4, '3着率': 7, '3連対率': 11},
        (0.4, 0.6): {'1着率': 1, '2着率': 3, '3着率': 5, '3連対率': 9},
        (0.6, float('inf')): {'1着率': -2, '2着率': 8, '3着率': 13, '3連対率': 20},
    },
}

def get_rate_change(boat_number, diff):
    """差分から着順率の変化を取得"""
    if boat_number not in HEIWAJIMA_RATES:
        return {'1着率': 0, '2着率': 0, '3着率': 0, '3連対率': 0}
    
    ranges = HEIWAJIMA_RATES[boat_number]
    
    for (min_val, max_val), rates in ranges.items():
        if min_val <= diff < max_val:
            return rates
    
    return {'1着率': 0, '2着率': 0, '3着率': 0, '3連対率': 0}

def calculate_shinsum(df_race, pattern='B'):
    """シンsumを計算"""
    results = []
    
    for _, boat in df_race.iterrows():
        exhibition = float(boat['exhibition'])
        one_lap = float(boat['one_lap'])
        
        if pattern == 'A':
            # パターンA: 展示+1周+周り足
            third_value = float(boat['turning'])
        else:
            # パターンB: 展示+1周+直線
            third_value = float(boat['straight'])
        
        shinsum = exhibition + one_lap + third_value
        
        results.append({
            'number': int(boat['number']),
            'exhibition': exhibition,
            'one_lap': one_lap,
            'third': third_value,
            'shinsum': shinsum
        })
    
    # 平均を計算
    avg = sum(r['shinsum'] for r in results) / len(results)
    
    # 差分と着順率を計算
    for r in results:
        # 平均より速い（小さい）方をプラスにするため符号を逆転
        r['diff_raw'] = r['shinsum'] - avg  # 基準表用（元の差分）
        r['diff'] = avg - r['shinsum']  # 表示用（速い方がプラス）
        r['avg'] = avg
        
        # 着順率の変化を取得（基準表用の元の差分を使用）
        rate_change = get_rate_change(r['number'], r['diff_raw'])
        r['rate_1'] = rate_change['1着率']
        r['rate_2'] = rate_change['2着率']
        r['rate_3'] = rate_change['3着率']
        r['rate_renntai'] = rate_change['3連対率']
    
    return results

def generate_html_with_shinsum(csv_file):
    """シンsum理論を実装したHTMLを生成"""
    
    if not os.path.exists(csv_file):
        print(f'❌ {csv_file} が見つかりません')
        return
    
    df = pd.read_csv(csv_file)
    
    if len(df) == 0:
        print('⚠️ データが空です')
        return
    
    print(f'📊 {len(df)}件のデータを読み込みました\n')
    
    # 平和島のデータのみ抽出
    df_heiwajima = df[df['venue_name'] == '平和島']
    
    if len(df_heiwajima) == 0:
        print('⚠️ 平和島のデータがありません')
        return
    
    # HTMLヘッダー
    html = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>シンsum理論 - 平和島</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Hiragino Sans', 'Hiragino Kaku Gothic ProN', 'Yu Gothic', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            text-align: center;
        }
        
        h1 {
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #667eea;
            font-size: 1.3em;
            font-weight: bold;
            margin-top: 10px;
        }
        
        .date {
            color: #666;
            font-size: 1.2em;
        }
        
        .race-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 20px;
        }
        
        .race-title {
            font-size: 1.5em;
            color: #667eea;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        
        th, td {
            padding: 12px 8px;
            text-align: center;
            border-bottom: 1px solid #eee;
            font-size: 0.95em;
        }
        
        th {
            background: #f8f9fa;
            font-weight: bold;
            color: #333;
            position: sticky;
            top: 0;
        }
        
        tr:hover {
            background: #f8f9fa;
        }
        
        .boat-1 { border-left: 4px solid #000; }
        .boat-2 { border-left: 4px solid #000; }
        .boat-3 { border-left: 4px solid #ff0000; }
        .boat-4 { border-left: 4px solid #0000ff; }
        .boat-5 { border-left: 4px solid #ffff00; }
        .boat-6 { border-left: 4px solid #00ff00; }
        
        .positive {
            color: #28a745;
            font-weight: bold;
        }
        
        .negative {
            color: #dc3545;
            font-weight: bold;
        }
        
        .rate-box {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        .rate-positive {
            background: #d4edda;
            color: #155724;
        }
        
        .rate-negative {
            background: #f8d7da;
            color: #721c24;
        }
        
        .rate-neutral {
            background: #e2e3e5;
            color: #383d41;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚤 シンsum理論</h1>
            <p class="subtitle">平和島（パターンB: 展示+1周+直線）</p>
            <p class="date">""" + datetime.now().strftime('%Y年%m月%d日') + """</p>
        </header>
"""
    
    # レースごとに処理
    races = df_heiwajima.groupby('race_no')
    
    for race_no, race_data in races:
        # シンsumを計算
        shinsum_results = calculate_shinsum(race_data, pattern='B')
        
        html += f'        <div class="race-card">\n'
        html += f'            <h2 class="race-title">{race_no}R（平均: {shinsum_results[0]["avg"]:.2f}）</h2>\n'
        html += '            <table>\n'
        html += '                <thead>\n'
        html += '                    <tr>\n'
        html += '                        <th>艇番</th>\n'
        html += '                        <th>展示</th>\n'
        html += '                        <th>1周</th>\n'
        html += '                        <th>直線</th>\n'
        html += '                        <th>シンsum</th>\n'
        html += '                        <th>平均との差</th>\n'
        html += '                        <th>1着率</th>\n'
        html += '                        <th>2着率</th>\n'
        html += '                        <th>3着率</th>\n'
        html += '                        <th>3連対率</th>\n'
        html += '                    </tr>\n'
        html += '                </thead>\n'
        html += '                <tbody>\n'
        
        for result in shinsum_results:
            boat_class = f'boat-{result["number"]}'
            diff_class = 'positive' if result['diff'] > 0 else 'negative' if result['diff'] < 0 else ''
            diff_sign = '+' if result['diff'] > 0 else ''
            
            # 着順率のクラス
            def rate_class(val):
                if val > 0:
                    return 'rate-positive'
                elif val < 0:
                    return 'rate-negative'
                else:
                    return 'rate-neutral'
            
            def rate_sign(val):
                if val > 0:
                    return f'+{val}'
                else:
                    return str(val)
            
            html += f'                    <tr class="{boat_class}">\n'
            html += f'                        <td><strong>{result["number"]}号艇</strong></td>\n'
            html += f'                        <td>{result["exhibition"]:.2f}</td>\n'
            html += f'                        <td>{result["one_lap"]:.2f}</td>\n'
            html += f'                        <td>{result["third"]:.2f}</td>\n'
            html += f'                        <td><strong>{result["shinsum"]:.2f}</strong></td>\n'
            html += f'                        <td class="{diff_class}"><strong>{diff_sign}{result["diff"]:.2f}</strong></td>\n'
            html += f'                        <td><span class="rate-box {rate_class(result["rate_1"])}">{rate_sign(result["rate_1"])}%</span></td>\n'
            html += f'                        <td><span class="rate-box {rate_class(result["rate_2"])}">{rate_sign(result["rate_2"])}%</span></td>\n'
            html += f'                        <td><span class="rate-box {rate_class(result["rate_3"])}">{rate_sign(result["rate_3"])}%</span></td>\n'
            html += f'                        <td><span class="rate-box {rate_class(result["rate_renntai"])}">{rate_sign(result["rate_renntai"])}%</span></td>\n'
            html += '                    </tr>\n'
        
        html += '                </tbody>\n'
        html += '            </table>\n'
        html += '        </div>\n'
    
    html += """    </div>
</body>
</html>
"""
    
    # HTMLファイルを保存
    output_file = 'shinsum_heiwajima.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f'✅ {output_file} を生成しました！')
    
    return output_file

def main():
    print('🚤 シンsum理論 HTMLサイト生成\n')
    print('='*60 + '\n')
    
    # 最新のCSVファイルを探す
    import glob
    csv_files = glob.glob('all_races_*.csv')
    
    if not csv_files:
        print('❌ CSVファイルが見つかりません')
        print('💡 先に auto_scraper.py を実行してください')
        return
    
    csv_file = sorted(csv_files)[-1]
    print(f'📄 使用するCSVファイル: {csv_file}\n')
    
    output_file = generate_html_with_shinsum(csv_file)
    
    if output_file:
        print(f'\n{"="*60}')
        print('🎉 完了！')
        print('='*60)
        print(f'\n📂 生成されたファイル: {output_file}')
        print('\n💡 ブラウザで開くには:')
        print(f'   open {output_file}')

if __name__ == '__main__':
    main()