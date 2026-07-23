import subprocess
import os
from flask import Flask, render_template, request, jsonify
import sqlite3
import json
from PIL import Image

# Импорт rembg с фоллбеком, если библиотека еще не поставлена
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

    # Авто-отправка изменений на GitHub
    run_git_push()


def run_git_push():
    subprocess.Popen(["bash", "/home/sakura/mama-shop/push_data.sh"])


@app.route("/scanner")
def scanner():
    return render_template("scanner.html")


@app.route("/display")
def display():
    return render_template("display.html")


@app.route("/scan", methods=["POST"])
def scan():
    barcode = request.json.get("barcode")
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT name, price, image, category, subcategory FROM products WHERE barcode=?",
            (barcode,),
        )
        prod = cur.fetchone()

    if prod:
        if barcode in current_cart:
            current_cart[barcode]["qty"] += 1
        else:
            current_cart[barcode] = {
                "barcode": barcode,
                "name": prod[0],
                "price": prod[1],
                "image": prod[2],
                "category": prod[3],
                "subcategory": prod[4],
                "qty": 1,
            }
        return jsonify(
            {
                "status": "found",
                "barcode": barcode,
                "name": prod[0],
                "price": prod[1],
                "image": prod[2],
                "category": prod[3] or "Прочее",
                "subcategory": prod[4] or "",
                "qty": current_cart[barcode]["qty"],
            }
        )
    return jsonify({"status": "new", "barcode": barcode})


@app.route("/add", methods=["POST"])
def add():
    barcode = request.form.get("barcode")
    name = request.form.get("name")
    price = float(request.form.get("price"))
    category = request.form.get("category", "Прочее")
    subcategory = request.form.get("subcategory", "")
    file = request.files.get("image")

    # Достаем старое имя файла из БД, чтобы не затереть фото при редактировании цен
    filename = ""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT image FROM products WHERE barcode=?", (barcode,))
        old_row = cur.fetchone()
        if old_row and old_row[0]:
            filename = old_row[0]

    if file and file.filename != "":
        # Читаем фотку
        input_image = Image.open(file.stream)

        # Если rembg установлен — вырезаем фон в прозрачный PNG
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

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO products (barcode, name, price, image, category, subcategory) 
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (barcode, name, price, filename, category, subcategory),
        )

    export_json()

    # Если товар был в чеке — обновляем его данные
    if barcode in current_cart:
        current_cart[barcode]["name"] = name
        current_cart[barcode]["price"] = price
        current_cart[barcode]["image"] = filename
        current_cart[barcode]["category"] = category
        current_cart[barcode]["subcategory"] = subcategory

    return jsonify({"status": "ok"})


# Ручной пинок push_data.sh с кнопки на телефоне
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
