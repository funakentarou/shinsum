#!/bin/bash
# boatrace-scraperディレクトリに移動
cd /Users/suginotooru/Desktop/boatrace-scraper
# 仮想環境を有効化
source venv/bin/activate
# 増分更新を実行
python3 update_shinsum.py

# shinsum理論が更新された場合、GitHubに自動アップロード
if [ -f shinsum_complete.html ]; then
    /Users/suginotooru/Desktop/boatrace-scraper/upload_to_github.sh
fi