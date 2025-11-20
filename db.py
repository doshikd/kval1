# db.py
import os
import pymysql
from PyQt6.QtWidgets import QMessageBox, QApplication






UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)





def get_connection():
    try:
        return pymysql.connect(
            host='127.0.0.1',      # ← исправлено на стандартный localhost
            user='root',
            password='',           # ← укажите свой пароль, если есть
            database='repair_db',
            charset='utf8mb4',
            autocommit=True
        )
    except Exception:
        QMessageBox.critical(None, "Ошибка БД", 
            "Не удалось подключиться к базе данных.")
        exit()  # закрываем программу
