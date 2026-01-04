#!/bin/bash
echo "=== Git设置脚本 ==="
git add .
git commit -m "$(date): 更新"
git log --oneline
