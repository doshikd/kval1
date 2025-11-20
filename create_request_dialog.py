# create_request_dialog.py
import os
from PyQt6.QtWidgets import *
from db import get_connection, UPLOAD_FOLDER

class CreateRequestDialog(QDialog):
    def __init__(self, client_id):
        super().__init__()
        self.client_id = client_id
        self.selected_file = None
        self.setWindowTitle("Новая заявка")
        self.resize(450, 400)
        layout = QVBoxLayout()

        self.tech_type = QLineEdit()
        self.tech_model = QLineEdit()
        self.problem = QTextEdit()
        self.file_label = QLabel("Файл не выбран")

        layout.addWidget(QLabel("Тип оргтехники:"))
        layout.addWidget(self.tech_type)
        layout.addWidget(QLabel("Модель:"))
        layout.addWidget(self.tech_model)
        layout.addWidget(QLabel("Описание проблемы:"))
        layout.addWidget(self.problem)

        btn_file = QPushButton("Прикрепить файл (опционально)")
        btn_file.clicked.connect(self.choose_file)
        layout.addWidget(btn_file)
        layout.addWidget(self.file_label)

        btn_submit = QPushButton("Отправить")
        btn_submit.clicked.connect(self.submit)
        layout.addWidget(btn_submit)
        self.setLayout(layout)

    def choose_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Выбрать файл")
        if fname:
            self.selected_file = fname
            self.file_label.setText("Файл: " + os.path.basename(fname))
        else:
            self.selected_file = None
            self.file_label.setText("Файл не выбран")

    def submit(self):
        tech = self.tech_type.text().strip()
        model = self.tech_model.text().strip()
        desc = self.problem.toPlainText().strip()
        if not (tech and model and desc):
            QMessageBox.warning(self, "Ошибка", "Все поля обязательны")
            return

        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO Requests (startDate, orgTechType, orgTechModel,
                    problemDescryption, requestStatus, clientID)
                    VALUES (CURDATE(), %s, %s, %s, 'Новая заявка', %s)
                """, (tech, model, desc, self.client_id))

                # Получаем ID вставленной записи
                cur.execute("SELECT LAST_INSERT_ID()")
                req_id = cur.fetchone()[0]

                if self.selected_file:
                    safe = "".join(
                        c if c.isalnum() or c in "._- " else "_" for c in os.path.basename(self.selected_file))
                    path = os.path.join(UPLOAD_FOLDER, f"req_{req_id}_{safe}")

                    # Создаем папку, если она не существует
                    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

                    with open(self.selected_file, 'rb') as s, open(path, 'wb') as d:
                        d.write(s.read())
                    cur.execute(
                        "INSERT INTO Attachments (requestID, fileName, filePath, uploadedBy) VALUES (%s, %s, %s, %s)",
                        (req_id, safe, path, self.client_id))

                conn.commit()  # Не забудьте коммит!

            conn.close()
            QMessageBox.information(self, "Успех", "Заявка создана!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
