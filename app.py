import io
import json
import os
import shutil
import sqlite3
import subprocess
import threading
import time
import zlib
from datetime import datetime
from flask import Flask, jsonify, render_template, request
from PIL import Image
from rembg import new_session, remove

app = Flask(__name__)
DB_PATH = "shop.db"
UPLOAD_FOLDER = "static/img"
BACKUP_FOLDER = "backups"


@app.after_request
def add_cache_headers(response):
    if request.path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=31536000"
    return response


os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(BACKUP_FOLDER, exist_ok=True)

current_cart = {}
bg_session = new_session("u2netp")


def auto_sync_scheduler():
    while True:
        now = datetime.now()
        if now.hour == 19 and now.minute == 0:
            print("⏰ [19:00] Запуск авто-синхронизации и бэкапа...")
            create_backup()
            run_git_push()
            time.sleep(60)
        time.sleep(30)


def create_backup():
    if not os.path.exists(DB_PATH):
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"shop_backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_FOLDER, backup_filename)

    shutil.copy2(DB_PATH, backup_path)

    backups = sorted(
        [
            os.path.join(BACKUP_FOLDER, f)
            for f in os.listdir(BACKUP_FOLDER)
            if f.startswith("shop_backup_")
        ]
    )
    if len(backups) > 15:
        for old_b in backups[:-15]:
            try:
                os.remove(old_b)
            except Exception:
                pass

    return backup_filename


def process_image(file_stream):
    input_bytes = file_stream.read()
    try:
        output_bytes = remove(input_bytes, session=bg_session)
        return Image.open(io.BytesIO(output_bytes))
    except Exception as e:
        print(f"Ошибка вырезания фона: {e}, сохраняем как есть")
        return Image.open(io.BytesIO(input_bytes))


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                barcode TEXT PRIMARY KEY, 
                name TEXT, 
                price REAL, 
                image TEXT,
                category TEXT,
                subcategory TEXT,
                volume_weight TEXT,
                images TEXT
            )
        """
        )
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(products)")
        columns = [column[1] for column in cur.fetchall()]

        for col, default_val in [
            ("category", "DEFAULT 'Прочее'"),
            ("subcategory", "DEFAULT ''"),
            ("volume_weight", "DEFAULT ''"),
            ("images", "DEFAULT '[]'"),
        ]:
            if col not in columns:
                conn.execute(
                    f"ALTER TABLE products ADD COLUMN {col} TEXT {default_val}"
                )
        # 1. В init_db() добавляем проверку колонки old_price:
        for col, default_val in [
            ("category", "DEFAULT 'Прочее'"),
            ("subcategory", "DEFAULT ''"),
            ("volume_weight", "DEFAULT ''"),
            ("images", "DEFAULT '[]'"),
            ("old_price", "DEFAULT 0"),  # <-- Добавили
        ]:
            if col not in columns:
                conn.execute(
                    f"ALTER TABLE products ADD COLUMN {col} TEXT {default_val}"
                )


# 2. В export_json() достаем old_price:
def export_json():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT barcode, name, price, image, category, subcategory, volume_weight, images, old_price FROM products"
        )
        data = []
        for r in cur.fetchall():
            try:
                images_list = json.loads(r[7]) if r[7] else []
            except Exception:
                images_list = []

            if not images_list and r[3]:
                images_list = [r[3]]

            data.append(
                {
                    "barcode": r[0],
                    "name": r[1],
                    "price": r[2],
                    "image": r[3] or (images_list[0] if images_list else ""),
                    "category": r[4] or "Прочее",
                    "subcategory": r[5] or "",
                    "volume_weight": r[6] or "",
                    "images": images_list,
                    "old_price": r[8] or 0,  # <-- Добавили
                }
            )

    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def run_git_push():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(base_dir, "push_data.sh")
    if os.path.exists(script_path):
        subprocess.Popen(["bash", script_path])


def get_product_by_barcode(barcode):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT barcode, name, price, image, category, subcategory, volume_weight, images FROM products WHERE barcode=?",
            (barcode,),
        )
        row = cur.fetchone()
        if row:
            try:
                images_list = json.loads(row[7]) if row[7] else []
            except Exception:
                images_list = []

            if not images_list and row[3]:
                images_list = [row[3]]

            return {
                "barcode": row[0],
                "name": row[1],
                "price": row[2],
                "image": row[3] or (images_list[0] if images_list else ""),
                "category": row[4] or "Прочее",
                "subcategory": row[5] or "",
                "volume_weight": row[6] or "",
                "images": images_list,
            }
    return None


def add_to_cart(product, qty=1):
    barcode = product["barcode"]
    if barcode in current_cart:
        current_cart[barcode]["qty"] += qty
    else:
        current_cart[barcode] = {
            "barcode": barcode,
            "name": product["name"],
            "price": product["price"],
            "image": product["image"],
            "category": product["category"],
            "subcategory": product["subcategory"],
            "volume_weight": product.get("volume_weight", ""),
            "qty": qty,
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
    qty = int(data.get("qty", 1))  # Читаем количество с фронта

    product = get_product_by_barcode(barcode)

    if product:
        if mode == "sell":
            add_to_cart(product, qty)

        return jsonify(
            {
                "status": "found",
                "name": product["name"],
                "price": product["price"],
                "category": product.get("category", ""),
                "subcategory": product.get("subcategory", ""),
                "volume_weight": product.get("volume_weight", ""),
                "barcode": barcode,
                "images": product.get("images", []),
            }
        )

    return jsonify({"status": "not_found"})


def generate_barcode_from_name(name: str) -> str:
    clean_text = name.strip().lower().encode("utf-8")
    base_hash = zlib.crc32(clean_text)

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        for offset in range(100):
            candidate = f"{(base_hash + offset) % 10000000000:010d}"
            cur.execute("SELECT name FROM products WHERE barcode=?", (candidate,))
            row = cur.fetchone()

            if not row or row[0].strip().lower() == name.strip().lower():
                return candidate

    return f"{base_hash:010d}"


@app.route("/add", methods=["POST"])
def add():
    barcode = request.form.get("barcode") or ""
    name = request.form.get("name", "").strip()

    raw_price = request.form.get("price", "0").replace(",", ".").strip()
    try:
        price = float(raw_price)
    except ValueError:
        return jsonify({"status": "error", "message": "Некорректная цена!"}), 400
    raw_old_price = request.form.get("old_price", "0").replace(",", ".").strip()
    try:
        old_price = float(raw_old_price) if raw_old_price else 0
    except ValueError:
        old_price = 0

    category = request.form.get("category", "Прочее")
    subcategory = request.form.get("subcategory", "")
    volume_weight = request.form.get("volume_weight", "").strip()

    if not barcode.strip():
        barcode = generate_barcode_from_name(name)

    # Достаем старые картинки на случай, если при редактировании новые фото не загружали
    existing_images = []
    existing_main_image = ""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT image, images FROM products WHERE barcode=?", (barcode,))
        old_row = cur.fetchone()
        if old_row:
            existing_main_image = old_row[0] or ""
            try:
                existing_images = json.loads(old_row[1]) if old_row[1] else []
            except Exception:
                existing_images = []

    # Собираем загруженные файлы (из массива 'images' или единичного 'image')
    uploaded_files = request.files.getlist("images")
    if not uploaded_files or uploaded_files[0].filename == "":
        single_file = request.files.get("image")
        if single_file and single_file.filename != "":
            uploaded_files = [single_file]
        else:
            uploaded_files = []

    # ТУТ ПЕРЕВОД НА WebP
    if uploaded_files:
        saved_filenames = []
        for idx, file_obj in enumerate(uploaded_files):
            output_image = process_image(file_obj.stream)
            filename = f"{barcode}_{idx + 1}.webp"
            save_path = os.path.join(UPLOAD_FOLDER, filename)

            # Ограничиваем размер 600x600 px и сохраняем с кастомным сжатием
            output_image.thumbnail((600, 600))
            if output_image.mode not in ("RGB", "RGBA"):
                output_image = output_image.convert("RGBA")

            output_image.save(save_path, format="WEBP", quality=80, optimize=True)
            saved_filenames.append(filename)

        main_filename = saved_filenames[0]
        images_json = json.dumps(saved_filenames, ensure_ascii=False)
    else:
        main_filename = existing_main_image
        images_json = json.dumps(existing_images, ensure_ascii=False)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO products (barcode, name, price, image, category, subcategory, volume_weight, images, old_price) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                barcode,
                name,
                price,
                main_filename,
                category,
                subcategory,
                volume_weight,
                images_json,
                old_price,
            ),
        )

    export_json()

    if barcode in current_cart:
        current_cart[barcode]["name"] = name
        current_cart[barcode]["price"] = price
        current_cart[barcode]["image"] = main_filename
        current_cart[barcode]["category"] = category
        current_cart[barcode]["subcategory"] = subcategory
        current_cart[barcode]["volume_weight"] = volume_weight
        current_cart[barcode]["old_price"] = old_price

    return jsonify({"status": "ok", "barcode": barcode})


@app.route("/api/backup", methods=["POST"])
def manual_backup_route():
    filename = create_backup()
    if filename:
        return jsonify({"status": "ok", "message": f"Бэкап сохранен: {filename}"})
    return (
        jsonify({"status": "error", "message": "Не удалось создать бэкап"}),
        500,
    )


@app.route("/api/sync", methods=["POST"])
def manual_sync():
    create_backup()
    run_git_push()
    return jsonify({"status": "ok", "message": "Синхронизация и бэкап запущены!"})


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
    threading.Thread(target=auto_sync_scheduler, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, ssl_context="adhoc")
