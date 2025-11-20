# client_window.py
from PyQt6.QtWidgets import *
from PyQt6.QtWidgets import QHeaderView
from create_request_dialog import CreateRequestDialog
from db import get_connection

class ClientWindow(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("Заказчик")
        self.resize(1200, 600)
        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        btn_new = QPushButton("Создать заявку")
        btn_new.clicked.connect(self.create_request)

        layout.addWidget(QLabel("Мои заявки:"))
        layout.addWidget(self.table)
        layout.addWidget(btn_new)

        # Поле для переписки
        self.comment_input = QTextEdit()
        self.comment_input.setPlaceholderText("Напишите сообщение по выбранной заявке...")
        btn_send_msg = QPushButton("Отправить сообщение")
        btn_send_msg.clicked.connect(self.send_comment)

        layout.addWidget(QLabel("Сообщение по заявке:"))
        layout.addWidget(self.comment_input)
        layout.addWidget(btn_send_msg)

        self.setLayout(layout)
        self.load_requests()

    def load_requests(self):
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    r.requestID, 
                    r.orgTechType, 
                    r.orgTechModel, 
                    r.requestStatus,
                    IFNULL(r.priority, '—'),
                    GROUP_CONCAT(c.message SEPARATOR '; '),
                    IFNULL(u.fio, 'Не назначен')
                FROM Requests r
                LEFT JOIN Comments c ON c.requestID = r.requestID
                LEFT JOIN Users u ON u.userID = r.masterID
                WHERE r.clientID = %s
                GROUP BY r.requestID
                ORDER BY r.requestID DESC
            """, (self.user_id,))
            rows = cur.fetchall()
        self.table.setRowCount(len(rows))
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Тип", "Модель", "Статус", "Приоритет", "Переписка", "Мастер"])
        for i, r in enumerate(rows):
            for j, v in enumerate(r):
                self.table.setItem(i, j, QTableWidgetItem(str(v) if v is not None else ""))
        conn.close()

    def create_request(self):
        dlg = CreateRequestDialog(self.user_id)
        if dlg.exec():
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
