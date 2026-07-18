from flask import Flask, render_template, request, jsonify
import sqlite3
import json

app = Flask(__name__)
DB_PATH = "shop.db"
current_cart = []  # Временная память для чека

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS products (barcode TEXT PRIMARY KEY, name TEXT, price REAL)')

def export_json():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT barcode, name, price FROM products")
        data = [{"barcode": r[0], "name": r[1], "price": r[2]} for r in cur.fetchall()]
    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Страница для телефона
@app.route('/scanner')
def scanner():
    return render_template('scanner.html')

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
        cur.execute("SELECT name, price FROM products WHERE barcode=?", (barcode,))
        prod = cur.fetchone()
    
    if prod:
        # Добавляем в текущий чек
        current_cart.append({"name": prod[0], "price": prod[1]})
        return jsonify({"status": "found", "name": prod[0], "price": prod[1]})
    return jsonify({"status": "new", "barcode": barcode})

# API: добавление нового товара в базу
@app.route('/add', methods=['POST'])
def add():
    data = request.json
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT OR REPLACE INTO products (barcode, name, price) VALUES (?, ?, ?)", 
                     (data['barcode'], data['name'], data['price']))
    export_json()
    current_cart.append({"name": data['name'], "price": data['price']})
    return jsonify({"status": "ok"})

# API: отдать чек монитору
@app.route('/api/cart', methods=['GET'])
def get_cart():
    total = sum(item['price'] for item in current_cart)
    return jsonify({"cart": current_cart, "total": total})

# API: очистить чек (для кнопки "Новый покупатель")
@app.route('/api/cart/clear', methods=['POST'])
def clear_cart():
    current_cart.clear()
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, ssl_context='adhoc')