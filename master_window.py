# master_window.py
import os
from PyQt6.QtWidgets import *
from PyQt6.QtWidgets import QHeaderView
from db import get_connection, UPLOAD_FOLDER

class MasterWindow(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("Мастер")
        self.resize(1200, 650)
        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        btn_attach = QPushButton("Прикрепить фото к заявке")
        btn_attach.clicked.connect(self.attach_photo)
        btn_complete = QPushButton("Завершить заявку")
        btn_complete.clicked.connect(self.complete)
        btn_order_parts = QPushButton("Запросить недостающие запчасти")
        btn_order_parts.clicked.connect(self.request_parts)

        layout.addWidget(QLabel("Мои заявки (по приоритету):"))
        layout.addWidget(self.table)
        layout.addWidget(btn_attach)
        layout.addWidget(btn_complete)
        layout.addWidget(btn_order_parts)

        self.comment_input = QTextEdit()
        self.comment_input.setPlaceholderText("Введите сообщение...")
        btn_send = QPushButton("Отправить сообщение")
        btn_send.clicked.connect(self.send_comment)

        layout.addWidget(QLabel("Переписка:"))
        layout.addWidget(self.comment_input)
        layout.addWidget(btn_send)

        self.setLayout(layout)
        self.load_requests()

    def load_requests(self):
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT r.requestID, r.orgTechType, r.orgTechModel, r.problemDescryption,
                       r.priority, IFNULL(r.repairParts, '—'), GROUP_CONCAT(c.message SEPARATOR '; ')
                FROM Requests r
                LEFT JOIN Comments c ON c.requestID = r.requestID
                WHERE r.masterID = %s AND r.requestStatus != 'Готова к выдаче'
                GROUP BY r.requestID
                ORDER BY FIELD(r.priority, 'Высокий', 'Средний', 'Низкий')
            """, (self.user_id,))
            rows = cur.fetchall()
        self.table.setRowCount(len(rows))
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Тип", "Модель", "Проблема", "Приоритет", "Запчасти", "Переписка"]
        )
        for i, r in enumerate(rows):
            for j, v in enumerate(r):
                self.table.setItem(i, j, QTableWidgetItem(str(v) if v else ""))
        conn.close()

    def attach_photo(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите заявку")
            return
        req_id = int(self.table.item(row, 0).text())
        fname, _ = QFileDialog.getOpenFileName(self, "Фото")
        if not fname:
            return
        try:
            safe = "".join(c if c.isalnum() or c in "._- " else "_" for c in os.path.basename(fname))
            path = os.path.join(UPLOAD_FOLDER, f"master_req_{req_id}_{safe}")
            with open(fname, 'rb') as s, open(path, 'wb') as d:
                d.write(s.read())
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("INSERT INTO Attachments (requestID, fileName, filePath, uploadedBy) VALUES (%s, %s, %s, %s)",
                            (req_id, safe, path, self.user_id))
            conn.close()
            QMessageBox.information(self, "Успех", "Фото прикреплено")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def complete(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите заявку")
            return
        req_id = int(self.table.item(row, 0).text())
        parts, ok = QInputDialog.getText(self, "Запчасти", "Укажите запчасти (через запятую):")
        if not ok:
            return
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE Requests
                SET requestStatus = 'Готова к выдаче',
                    completionDate = CURDATE(),
                    repairParts = %s
                WHERE requestID = %s
            """, (parts or None, req_id))
        conn.close()
        QMessageBox.information(self, "Готово", "Заявка завершена!")
        self.load_requests()

    def request_parts(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите заявку")
            return
        req_id = int(self.table.item(row, 0).text())
        parts, ok = QInputDialog.getText(self, "Запрос запчастей", "Какие запчасти нужны?")
        if ok and parts.strip():
            # Можно сохранить как комментарий от мастера или специальный статус
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO Comments (message, authorID, requestID)
                    VALUES (%s, %s, %s)
                """, (f"ЗАПРОС ЗАПЧАСТЕЙ: {parts.strip()}", self.user_id, req_id))
                # Опционально: изменить статус
                cur.execute("UPDATE Requests SET requestStatus = 'Ожидает запчасти' WHERE requestID = %s", (req_id,))
            conn.close()
            QMessageBox.information(self, "Отправлено", "Запрос на запчасти зарегистрирован!")
            self.load_requests()

    def send_comment(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите заявку из таблицы!")
            return
        message = self.comment_input.toPlainText().strip()
        if not message:
            QMessageBox.warning(self, "Ошибка", "Сообщение не может быть пустым!")
            return
        req_id = int(self.table.item(row, 0).text())
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO Comments (message, authorID, requestID)
                    VALUES (%s, %s, %s)
                """, (message, self.user_id, req_id))
            conn.close()
            self.comment_input.clear()
            self.load_requests()
            QMessageBox.information(self, "Успех", "Сообщение отправлено!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось отправить сообщение:\n{str(e)}")
