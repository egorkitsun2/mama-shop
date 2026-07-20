#!/bin/bash
cd /home/sakura/mama-shop

# Добавляем только статику для сайта
git add products.json static/img/*

# Сохраняем слепок
git commit -m "Автообновление прайса и фото" || true

# Железобетонное стягивание твоего кода перед отправкой
git pull --rebase --autostash

# Пуляем в облако
git push