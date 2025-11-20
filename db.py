# db.py
import pymysql
import os


UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_connection():
    return pymysql.connect(
        host='127.127.126.6',
        user='root',
        password='',  # ← подставьте свой пароль
        database='repair_db',
        charset='utf8mb4',
        autocommit=True
    )
