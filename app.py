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

# Корзина теперь словарь: { "4600171107483": { "barcode": ..., "name": ..., "price": ..., "image": ..., "qty": 1 } }
current_cart = {}

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS products (
                barcode TEXT PRIMARY KEY, 
                name TEXT, 
                price REAL, 
                image TEXT,
                category TEXT,
                subcategory TEXT
            )
        ''')
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(products)")
        columns = [column[1] for column in cur.fetchall()]
        if 'category' not in columns:
            conn.execute("ALTER TABLE products ADD COLUMN category TEXT DEFAULT 'Прочее'")
        if 'subcategory' not in columns:
            conn.execute("ALTER TABLE products ADD COLUMN subcategory TEXT DEFAULT ''")

def export_json():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT barcode, name, price, image, category, subcategory FROM products")
        data = [{
            "barcode": r[0], 
            "name": r[1], 
            "price": r[2], 
            "image": r[3],
            "category": r[4] or "Прочее",
            "subcategory": r[5] or ""
        } for r in cur.fetchall()]
    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    subprocess.Popen(['bash', '/home/sakura/mama-shop/push_data.sh'])

@app.route('/scanner')
def scanner():
    return render_template('scanner.html')

@app.route('/display')
def display():
    return render_template('display.html')

@app.route('/scan', methods=['POST'])
def scan():
    barcode = request.json.get('barcode')
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT name, price, image, category, subcategory FROM products WHERE barcode=?", (barcode,))
        prod = cur.fetchone()
    
    if prod:
        if barcode in current_cart:
            current_cart[barcode]['qty'] += 1
        else:
            current_cart[barcode] = {
                "barcode": barcode,
                "name": prod[0], 
                "price": prod[1], 
                "image": prod[2],
                "category": prod[3],
                "subcategory": prod[4],
                "qty": 1
            }
        return jsonify({
            "status": "found", 
            "name": prod[0], 
            "price": prod[1], 
            "image": prod[2],
            "qty": current_cart[barcode]['qty']
        })
    return jsonify({"status": "new", "barcode": barcode})

@app.route('/add', methods=['POST'])
def add():
    barcode = request.form.get('barcode')
    name = request.form.get('name')
    price = float(request.form.get('price'))
    category = request.form.get('category', 'Прочее')
    subcategory = request.form.get('subcategory', '')
    file = request.files.get('image')
    
    filename = ""
    if file and file.filename != '':
        filename = secure_filename(f"{barcode}_{file.filename}")
        file.save(os.path.join(UPLOAD_FOLDER, filename))

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT OR REPLACE INTO products (barcode, name, price, image, category, subcategory) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (barcode, name, price, filename, category, subcategory))
    
    export_json()

    if barcode in current_cart:
        current_cart[barcode]['qty'] += 1
    else:
        current_cart[barcode] = {
            "barcode": barcode,
            "name": name, 
            "price": price, 
            "image": filename,
            "category": category,
            "subcategory": subcategory,
            "qty": 1
        }

    return jsonify({"status": "ok"})

# Возвращает сгруппированный чек и общую сумму
@app.route('/api/cart', methods=['GET'])
def get_cart():
    cart_items = list(current_cart.values())
    total = sum(item['price'] * item['qty'] for item in cart_items)
    return jsonify({"cart": cart_items, "total": total})

# Списание товара из чека (по одному за запрос)
@app.route('/api/cart/remove', methods=['POST'])
def remove_cart_item():
    barcode = request.json.get('barcode')
    if barcode in current_cart:
        current_cart[barcode]['qty'] -= 1
        if current_cart[barcode]['qty'] <= 0:
            del current_cart[barcode]
    return jsonify({"status": "ok"})

@app.route('/api/cart/clear', methods=['POST'])
def clear_cart():
    current_cart.clear()
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, ssl_context='adhoc')