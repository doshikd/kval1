# operator_window.py
from PyQt6.QtWidgets import *
from PyQt6.QtWidgets import QHeaderView
from db import get_connection

class OperatorWindow(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("Оператор")
        self.resize(1200, 650)
        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Элементы управления
        self.master_combo = QComboBox()
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Низкий", "Средний", "Высокий"])
        btn_assign = QPushButton("Назначить мастера и приоритет")
        btn_assign.clicked.connect(self.assign)
        btn_delete = QPushButton("Удалить заявку (дубликат)")
        btn_delete.clicked.connect(self.delete_request)


        self.load_masters()
        self.load_requests()

        layout.addWidget(QLabel("Все заявки:"))
        layout.addWidget(self.table)
        layout.addWidget(QLabel("Мастер:"))
        layout.addWidget(self.master_combo)
        layout.addWidget(QLabel("Приоритет:"))
        layout.addWidget(self.priority_combo)
        layout.addWidget(btn_assign)
        layout.addWidget(btn_delete)
        self.setLayout(layout)


    def load_masters(self):
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT userID, fio FROM Users WHERE type = 'Мастер'")
            for uid, fio in cur.fetchall():
                self.master_combo.addItem(fio, uid)
        conn.close()


    def load_requests(self):
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    r.requestID, 
                    r.orgTechType, 
                    r.orgTechModel, 
                    r.clientID, 
                    r.requestStatus, 
                    IFNULL(r.priority, '—'),
                    IFNULL(u.fio, '—')
                FROM Requests r
                LEFT JOIN Users u ON u.userID = r.masterID
                ORDER BY r.requestID DESC
            """)
            rows = cur.fetchall()
        self.table.setRowCount(len(rows))
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Тип", "Модель", "Клиент ID", "Статус", "Приоритет", "Мастер"])
        for i, r in enumerate(rows):
            for j, v in enumerate(r):
                self.table.setItem(i, j, QTableWidgetItem(str(v) if v is not None else ""))
        conn.close()


    def assign(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите заявку")
            return
        req_id = int(self.table.item(row, 0).text())
        master_id = self.master_combo.currentData()
        priority = self.priority_combo.currentText()


        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE Requests
                SET masterID = %s, priority = %s, requestStatus = 'В процессе ремонта'
                WHERE requestID = %s
            """, (master_id, priority, req_id))
        conn.close()
        QMessageBox.information(self, "Успех", "Мастер и приоритет назначены")
        self.load_requests()


    def delete_request(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите заявку")
            return
        req_id = int(self.table.item(row, 0).text())
        reply = QMessageBox.question(self, "Подтверждение", f"Удалить заявку №{req_id}? Это действие нельзя отменить.")
        if reply == QMessageBox.StandardButton.Yes:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("DELETE FROM Requests WHERE requestID = %s", (req_id,))
            conn.close()
            QMessageBox.information(self, "Успех", "Заявка удалена")
            self.load_requests()
