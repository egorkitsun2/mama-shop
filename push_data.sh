#!/bin/bash
cd /home/sakura/mama-shop
git add products.json static/img
# Конструкция || true спасает от падения скрипта, если попытались пушить без реальных изменений
git commit -m "Автообновление прайса и фото бд" || true
git push 