import subprocess
import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify
import sqlite3
import json

app = Flask(__name__)
DB_PATH = "shop.db"
UPLOAD_FOLDER = "static/img"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
current_cart = []

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS products (barcode TEXT PRIMARY KEY, name TEXT, price REAL, image TEXT)')

def export_json():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT barcode, name, price, image FROM products")
        data = [{"barcode": r[0], "name": r[1], "price": r[2], "image": r[3]} for r in cur.fetchall()]
    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        # Тот самый фоновый пинок скрипта после записи файла
    subprocess.Popen(['bash', '/home/sakura/mama-shop/push_data.sh'])

# @app.route('/scanner')
# def scanner():
#     return render_template('scanner.html')

# Страница для монитора
@app.route('/display')
def display():
    return render_template('display.html')

# API: сканирование товара
@app.route('/scan', methods=['POST'])
def scan():
    barcode = request.json.get('barcode')
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT name, price, image FROM products WHERE barcode=?", (barcode,))
        prod = cur.fetchone()
    
    if prod:
        # Фикс: добавили image в чек
        current_cart.append({"name": prod[0], "price": prod[1], "image": prod[2]})
        return jsonify({"status": "found", "name": prod[0], "price": prod[1], "image": prod[2]})
    return jsonify({"status": "new", "barcode": barcode})

# API: добавление нового товара в базу
@app.route('/add', methods=['POST'])
def add():
    barcode = request.form.get('barcode')
    name = request.form.get('name')
    price = request.form.get('price')
    file = request.files.get('image')
    
    filename = ""
    if file and file.filename != '':
        filename = secure_filename(f"{barcode}_{file.filename}")
        file.save(os.path.join(UPLOAD_FOLDER, filename))

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT OR REPLACE INTO products (barcode, name, price, image) VALUES (?, ?, ?, ?)", 
                     (barcode, name, float(price), filename))
    export_json()
    # Фикс: добавили image в чек
    current_cart.append({"name": name, "price": float(price), "image": filename})
    return jsonify({"status": "ok"})

@app.route('/api/cart', methods=['GET'])
def get_cart():
    total = sum(item['price'] for item in current_cart)
    return jsonify({"cart": current_cart, "total": total})

@app.route('/api/cart/clear', methods=['POST'])
def clear_cart():
    current_cart.clear()
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, ssl_context='adhoc')