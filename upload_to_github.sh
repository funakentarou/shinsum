#!/bin/bash

# shinsum_complete.htmlをindex.htmlとしてコピー
cp /Users/suginotooru/Desktop/boatrace-scraper/shinsum_complete.html /Users/suginotooru/Desktop/shinsum/index.html

# GitHubリポジトリに移動
cd /Users/suginotooru/Desktop/shinsum

# 変更をコミット
git add index.html
git commit -m "Update shinsum data $(date '+%Y-%m-%d %H:%M')"

# GitHubにプッシュ
git push origin main

echo "✅ GitHubに自動アップロード完了"