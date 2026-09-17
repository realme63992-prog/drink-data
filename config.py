

import os
from flask import Flask, render_template, jsonify

from supabase import create_client, Client

# โหลดค่าจากไฟล์ .env


app = Flask(__name__)

# เชื่อมต่อ Supabase
SUPABASE_URL = os.getenv("https://ostercntusxvfvhwbhlf.supabase.co")
SUPABASE_KEY = os.getenv("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9zdGVyY250dXN4dmZ2aHdiaGxmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4ODc2MjQ4MywiZXhwIjoyMTA0MzM4NDgzfQ.Ym1nbswLc4-KoMPjPc7-Uvn1I9v4nx3yGrSOkjFqPwo")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route("/")
def index():
    try:
        # ดึงข้อมูลจากตาราง drinks พร้อมดึงชื่อหมวดหมู่จากตาราง categories มาด้วย
        response = supabase.table("drinks").select("*").execute()
        drinks_data = response.data

        # ส่งข้อมูล drinks ไปให้ไฟล์ HTML แสดงผล
        return render_template("index.html", drinks=drinks_data)
    
    except Exception as e:
        return f"เกิดข้อผิดพลาดในการดึงข้อมูล: {str(e)}"

if __name__ == "__main__":
    app.run(debug=True)