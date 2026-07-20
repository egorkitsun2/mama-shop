#!/bin/bash
cd /home/sakura/mama-shop
git add products.json
# Конструкция || true спасает от падения скрипта, если попытались пушить без реальных изменений
git commit -m "Auto-update DB from POS" || true
git push