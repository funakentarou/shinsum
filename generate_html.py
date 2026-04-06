#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ボートレース HTMLサイト生成スクリプト

CSVデータから見やすいHTMLサイトを生成します。
"""

import pandas as pd
from datetime import datetime
import os

def generate_html(csv_file):
    """CSVからHTMLを生成"""
    
    # CSVを読み込み
    if not os.path.exists(csv_file):
        print(f'❌ {csv_file} が見つかりません')
        return
    
    df = pd.read_csv(csv_file)
    
    if len(df) == 0:
        print('⚠️ データが空です')
        return
    
    print(f'📊 {len(df)}件のデータを読み込みました\n')
    
    # 会場ごとにグループ化
    venues = df.groupby('venue_name')
    
    # HTMLヘッダー
    html = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ボートレース オリジナル展示データ</title>
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
        
        .date {
            color: #666;
            font-size: 1.2em;
        }
        
        .venue-tabs {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }
        
        .tab-button {
            padding: 12px 24px;
            border: none;
            background: #f0f0f0;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            font-weight: bold;
            transition: all 0.3s;
        }
        
        .tab-button:hover {
            background: #667eea;
            color: white;
            transform: translateY(-2px);
        }
        
        .tab-button.active {
            background: #667eea;
            color: white;
        }
        
        .venue-content {
            display: none;
        }
        
        .venue-content.active {
            display: block;
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
            padding: 12px;
            text-align: center;
            border-bottom: 1px solid #eee;
        }
        
        th {
            background: #f8f9fa;
            font-weight: bold;
            color: #333;
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
        
        .stats {
            display: flex;
            gap: 20px;
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }
        
        .stat-box {
            flex: 1;
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        
        .stat-label {
            color: #666;
            margin-top: 5px;
        }
        
        @media (max-width: 768px) {
            h1 {
                font-size: 1.8em;
            }
            
            .venue-tabs {
                justify-content: center;
            }
            
            .tab-button {
                font-size: 0.9em;
                padding: 10px 16px;
            }
            
            table {
                font-size: 0.9em;
            }
            
            th, td {
                padding: 8px 4px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚤 ボートレース オリジナル展示データ</h1>
            <p class="date">""" + datetime.now().strftime('%Y年%m月%d日') + """</p>
        </header>
        
        <div class="stats">
            <div class="stat-box">
                <div class="stat-number">""" + str(len(df['venue_name'].unique())) + """</div>
                <div class="stat-label">会場数</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">""" + str(len(df.groupby(['venue_name', 'race_no']))) + """</div>
                <div class="stat-label">レース数</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">""" + str(len(df)) + """</div>
                <div class="stat-label">総データ数</div>
            </div>
        </div>
        
        <div class="venue-tabs">
"""
    
    # タブボタン生成
    for i, (venue_name, _) in enumerate(venues):
        active = 'active' if i == 0 else ''
        html += f'            <button class="tab-button {active}" onclick="showVenue(\'{venue_name}\')">{venue_name}</button>\n'
    
    html += """        </div>
"""
    
    # 各会場のコンテンツ生成
    for i, (venue_name, venue_data) in enumerate(venues):
        active = 'active' if i == 0 else ''
        html += f'        <div class="venue-content {active}" id="{venue_name}">\n'
        
        # レースごとにカード生成
        races = venue_data.groupby('race_no')
        
        for race_no, race_data in races:
            html += f'            <div class="race-card">\n'
            html += f'                <h2 class="race-title">{race_no}R</h2>\n'
            html += '                <table>\n'
            html += '                    <thead>\n'
            html += '                        <tr>\n'
            html += '                            <th>艇番</th>\n'
            html += '                            <th>展示タイム</th>\n'
            html += '                            <th>一周</th>\n'
            html += '                            <th>まわり足</th>\n'
            html += '                            <th>直線</th>\n'
            html += '                        </tr>\n'
            html += '                    </thead>\n'
            html += '                    <tbody>\n'
            
            for _, boat in race_data.iterrows():
                boat_class = f'boat-{int(boat["number"])}'
                html += f'                        <tr class="{boat_class}">\n'
                html += f'                            <td><strong>{int(boat["number"])}号艇</strong></td>\n'
                html += f'                            <td>{boat["exhibition"]}</td>\n'
                html += f'                            <td>{boat["one_lap"]}</td>\n'
                html += f'                            <td>{boat["turning"]}</td>\n'
                html += f'                            <td>{boat["straight"]}</td>\n'
                html += '                        </tr>\n'
            
            html += '                    </tbody>\n'
            html += '                </table>\n'
            html += '            </div>\n'
        
        html += '        </div>\n'
    
    # JavaScriptとフッター
    html += """    </div>
    
    <script>
        function showVenue(venueName) {
            // すべてのタブとコンテンツを非アクティブに
            document.querySelectorAll('.tab-button').forEach(btn => {
                btn.classList.remove('active');
            });
            document.querySelectorAll('.venue-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // 選択されたタブとコンテンツをアクティブに
            event.target.classList.add('active');
            document.getElementById(venueName).classList.add('active');
            
            // ページトップにスクロール
            window.scrollTo({top: 0, behavior: 'smooth'});
        }
    </script>
</body>
</html>
"""
    
    # HTMLファイルを保存
    output_file = 'boatrace_data.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f'✅ {output_file} を生成しました！')
    print(f'\n💡 ブラウザで開いて確認してください')
    
    return output_file

def main():
    print('🚤 ボートレース HTMLサイト生成\n')
    print('='*60 + '\n')
    
    # 最新のCSVファイルを探す
    import glob
    csv_files = glob.glob('all_races_*.csv')
    
    if not csv_files:
        print('❌ CSVファイルが見つかりません')
        print('💡 先に auto_scraper.py を実行してください')
        return
    
    # 最新のファイルを使用
    csv_file = sorted(csv_files)[-1]
    print(f'📄 使用するCSVファイル: {csv_file}\n')
    
    output_file = generate_html(csv_file)
    
    if output_file:
        print(f'\n{"="*60}')
        print('🎉 完了！')
        print('='*60)
        print(f'\n📂 生成されたファイル: {output_file}')
        print('\n💡 ブラウザで開くには:')
        print(f'   Finderで {output_file} をダブルクリック')
        print(f'   または、ターミナルで: open {output_file}')

if __name__ == '__main__':
    main()