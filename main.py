# main.py
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox
from login_window import LoginWindow




app = QApplication(sys.argv)
login = LoginWindow()
login.show()
sys.exit(app.exec())
