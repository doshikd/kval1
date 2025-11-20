# login_window.py
from PyQt6.QtWidgets import *
from db import get_connection
from client_window import ClientWindow
from operator_window import OperatorWindow
from master_window import MasterWindow

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Вход в систему")
        self.resize(300, 150)
        layout = QVBoxLayout()
        self.login = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        btn = QPushButton("Войти")
        btn.clicked.connect(self.login_user)
        layout.addWidget(QLabel("Логин:"))
        layout.addWidget(self.login)
        layout.addWidget(QLabel("Пароль:"))
        layout.addWidget(self.password)
        layout.addWidget(btn)
        self.setLayout(layout)

    def login_user(self):
        login = self.login.text()
        password = self.password.text()
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT userID, fio, type FROM Users WHERE login=%s AND password=%s", (login, password))
            row = cur.fetchone()
        conn.close()

        if row:
            user_id, fio, role = row
            if role == "Заказчик":
                self.w = ClientWindow(user_id)
            elif role == "Оператор":
                self.w = OperatorWindow(user_id)
            elif role == "Мастер":
                self.w = MasterWindow(user_id)
            elif role == "Менеджер":
                self.w = OperatorWindow(user_id)  # временно как оператор
            else:
                QMessageBox.warning(self, "Ошибка", "Роль не поддерживается")
                return
            self.w.show()
            self.close()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")
