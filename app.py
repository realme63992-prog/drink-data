import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from supabase import create_client, Client
from dotenv import load_dotenv

# โหลดค่าความลับจากไฟล์ .env
load_dotenv()

app = Flask(__name__)
app.secret_key = "cafe_secret_key_change_me"

# กำหนด Supabase Connection โดยดึงจาก Environment Variable
SUPABASE_URL = "https://ostercntusxvfvhwbhlf.supabase.co" 
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------------------------------------------
# 1. ระบบ Login หน้าบ้าน (เข้าเลือกซื้อน้ำ)
# -------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def store_login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == "1111":  # รหัสผ่านสำหรับลูกค้า/หน้าร้าน
            session["store_access"] = True
            return redirect(url_for("index"))
        else:
            return render_template("store_login.html", error="รหัสผ่านหน้าร้านไม่ถูกต้อง!")
    return render_template("store_login.html")

# หน้าร้านค้า (เลือกซื้อน้ำ)
@app.route("/")
def index():
    if not session.get("store_access"):
        return redirect(url_for("store_login"))

    try:
        drinks_response = supabase.table("drinks").select("*").execute()
        drinks = drinks_response.data

        order_items_res = supabase.table("order_items").select("drink_id, quantity").execute()
        
        sales_count = {}
        for item in order_items_res.data:
            d_id = item["drink_id"]
            qty = item["quantity"]
            sales_count[d_id] = sales_count.get(d_id, 0) + qty

        sorted_drinks = sorted(sales_count.items(), key=lambda x: x[1], reverse=True)
        top3_ids = [item[0] for item in sorted_drinks[:3]]

        for drink in drinks:
            drink["is_bestseller"] = drink["id"] in top3_ids

        return render_template("index.html", drinks=drinks)
    except Exception as e:
        return f"เกิดข้อผิดพลาดในการดึงข้อมูล: {str(e)}"

# -------------------------------------------------------------
# 2. ระบบ Login หลังบ้าน (ดูรายงานขายดี Admin)
# -------------------------------------------------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == "9999":  # รหัสผ่านสำหรับหลังบ้าน
            session["admin_access"] = True
            return redirect(url_for("bestsellers"))
        else:
            return render_template("admin_login.html", error="รหัสผ่านหลังบ้านไม่ถูกต้อง!")
    return render_template("admin_login.html")

# หน้ารายงานขายดี (Admin)
@app.route("/bestsellers")
def bestsellers():
    if not session.get("admin_access"):
        return redirect(url_for("admin_login"))

    try:
        response = supabase.table("order_items").select("quantity, price, drinks(name)").execute()
        sales_summary = {}
        for item in response.data:
            drink_name = item["drinks"]["name"] if item.get("drinks") else "ไม่ระบุชื่อ"
            qty = item.get("quantity", 0)
            price = item.get("price", 0)
            
            if drink_name not in sales_summary:
                sales_summary[drink_name] = {"total_qty": 0, "total_revenue": 0}
            
            sales_summary[drink_name]["total_qty"] += qty
            sales_summary[drink_name]["total_revenue"] += qty * price

        sorted_bestsellers = sorted(
            [{"name": k, **v} for k, v in sales_summary.items()],
            key=lambda x: x["total_qty"],
            reverse=True
        )

        return render_template("bestsellers.html", items=sorted_bestsellers)
    except Exception as e:
        return f"เกิดข้อผิดพลาดในการดึงข้อมูลรายงาน: {str(e)}"

# -------------------------------------------------------------
# 3. ฟังก์ชันอื่นๆ (สั่งซื้อ / Logout)
# -------------------------------------------------------------
@app.route("/order", methods=["POST"])
def create_order():
    try:
        data = request.json
        cart = data.get("cart", [])
        total_price = data.get("total_price", 0)

        if not cart:
            return jsonify({"status": "error", "message": "ไม่มีสินค้าในตะกร้า"}), 400

        order_res = supabase.table("orders").insert({"total_price": total_price}).execute()
        order_id = order_res.data[0]["id"]

        order_items = []
        for item in cart:
            order_items.append({
                "order_id": order_id,
                "drink_id": item["drink_id"],
                "quantity": item["quantity"],
                "price": item["price"],
                "sweetness": item.get("sweetness", "100%")
            })

        supabase.table("order_items").insert(order_items).execute()
        return jsonify({"status": "success", "message": "สั่งซื้อสำเร็จเรียบร้อยแล้ว!", "order_id": order_id})

    except Exception as e:
        return jsonify({"status": "error", "message": f"เกิดข้อผิดพลาด: {str(e)}"}), 500

@app.route("/logout")
def logout():
    session.pop("store_access", None)
    return redirect(url_for("store_login"))

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_access", None)
    return redirect(url_for("admin_login"))

if __name__ == "__main__":
    app.run(debug=True)