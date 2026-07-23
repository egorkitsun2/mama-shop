import subprocess
import os
from flask import Flask, render_template, request, jsonify
import sqlite3
import json
from PIL import Image

try:
    from rembg import remove

    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

app = Flask(__name__)
DB_PATH = "shop.db"
UPLOAD_FOLDER = "static/img"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

current_cart = {}


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                barcode TEXT PRIMARY KEY, 
                name TEXT, 
                price REAL, 
                image TEXT,
                category TEXT,
                subcategory TEXT
            )
        """)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(products)")
        columns = [column[1] for column in cur.fetchall()]
        if "category" not in columns:
            conn.execute(
                "ALTER TABLE products ADD COLUMN category TEXT DEFAULT 'Прочее'"
            )
        if "subcategory" not in columns:
            conn.execute("ALTER TABLE products ADD COLUMN subcategory TEXT DEFAULT ''")


def export_json():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT barcode, name, price, image, category, subcategory FROM products"
        )
        data = [
            {
                "barcode": r[0],
                "name": r[1],
                "price": r[2],
                "image": r[3],
                "category": r[4] or "Прочее",
                "subcategory": r[5] or "",
            }
            for r in cur.fetchall()
        ]
    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    run_git_push()


def run_git_push():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(base_dir, "push_data.sh")
    subprocess.Popen(["bash", script_path])


def get_product_by_barcode(barcode):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT barcode, name, price, image, category, subcategory FROM products WHERE barcode=?",
            (barcode,),
        )
        row = cur.fetchone()
        if row:
            return {
                "barcode": row[0],
                "name": row[1],
                "price": row[2],
                "image": row[3],
                "category": row[4] or "Прочее",
                "subcategory": row[5] or "",
            }
    return None


def add_to_cart(product):
    barcode = product["barcode"]
    if barcode in current_cart:
        current_cart[barcode]["qty"] += 1
    else:
        current_cart[barcode] = {
            "barcode": barcode,
            "name": product["name"],
            "price": product["price"],
            "image": product["image"],
            "category": product["category"],
            "subcategory": product["subcategory"],
            "qty": 1,
        }


@app.route("/scanner")
def scanner():
    return render_template("scanner.html")


@app.route("/display")
def display():
    return render_template("display.html")


@app.route("/scan", methods=["POST"])
def scan_barcode():
    data = request.get_json() or {}
    barcode = data.get("barcode")
    mode = data.get("mode", "sell")

    product = get_product_by_barcode(barcode)

    if product:
        if mode == "sell":
            add_to_cart(product)

        return jsonify(
            {
                "status": "found",
                "name": product["name"],
                "price": product["price"],
                "category": product.get("category", ""),
                "subcategory": product.get("subcategory", ""),
                "barcode": barcode,
            }
        )

    return jsonify({"status": "not_found"})


@app.route("/add", methods=["POST"])
def add():
    barcode = request.form.get("barcode")
    name = request.form.get("name")
    price = float(request.form.get("price"))
    category = request.form.get("category", "Прочее")
    subcategory = request.form.get("subcategory", "")
    file = request.files.get("image")

    filename = ""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT image FROM products WHERE barcode=?", (barcode,))
        old_row = cur.fetchone()
        if old_row and old_row[0]:
            filename = old_row[0]

    if file and file.filename != "":
        input_image = Image.open(file.stream)

        if REMBG_AVAILABLE:
            try:
                output_image = remove(input_image)
            except Exception as e:
                print(f"Ошибка rembg: {e}, сохраняем как есть")
                output_image = input_image
        else:
            output_image = input_image

        filename = f"{barcode}.png"
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        output_image.save(save_path, format="PNG")
        # Ограничиваем максимальный размер картинки и оптимизируем PNG
        output_image.thumbnail((800, 800))
        output_image.save(save_path, format="PNG", optimize=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO products (barcode, name, price, image, category, subcategory) 
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (barcode, name, price, filename, category, subcategory),
        )

    export_json()

    if barcode in current_cart:
        current_cart[barcode]["name"] = name
        current_cart[barcode]["price"] = price
        current_cart[barcode]["image"] = filename
        current_cart[barcode]["category"] = category
        current_cart[barcode]["subcategory"] = subcategory

    return jsonify({"status": "ok"})


@app.route("/api/sync", methods=["POST"])
def manual_sync():
    run_git_push()
    return jsonify({"status": "ok", "message": "Скрипт синхронизации запущен!"})


@app.route("/api/cart", methods=["GET"])
def get_cart():
    cart_items = list(current_cart.values())
    total = sum(item["price"] * item["qty"] for item in cart_items)
    return jsonify({"cart": cart_items, "total": total})


@app.route("/api/cart/remove", methods=["POST"])
def remove_cart_item():
    barcode = request.json.get("barcode")
    if barcode in current_cart:
        current_cart[barcode]["qty"] -= 1
        if current_cart[barcode]["qty"] <= 0:
            del current_cart[barcode]
    return jsonify({"status": "ok"})


@app.route("/api/cart/clear", methods=["POST"])
def clear_cart():
    current_cart.clear()
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, ssl_context="adhoc")
