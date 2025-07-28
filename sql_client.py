import sys
import pyodbc
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QLabel, QMessageBox, QTableWidget,
    QTableWidgetItem, QComboBox, QInputDialog
)

class SQLClient(QWidget):
    def __init__(self):
        super().__init__()
        self.connection = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("SQL клиент")
        self.setGeometry(100, 100, 900, 700)
        
        layout = QVBoxLayout()

        self.connect_btn = QPushButton("Подключиться к БД")
        self.connect_btn.clicked.connect(self.connect_to_db)
        layout.addWidget(self.connect_btn)

        self.tables_combo = QComboBox()
        layout.addWidget(QLabel("Выберите таблицу:"))
        layout.addWidget(self.tables_combo)

        show_table_btn = QPushButton("Показать таблицу")
        show_table_btn.clicked.connect(self.load_selected_table)
        layout.addWidget(show_table_btn)

        layout.addWidget(QLabel("Выберите один из запросов"))

        # Кнопки запросов
        buttons = [
            ("Упорядочение материалов", self.query_sort_suppliers),
            ("Поиск поставщика", self.query_search_supplier),
            ("Материал по цене", self.query_filter_material_price),
            ("Средняя цена материала", self.query_avg_price_material),
            ("Удаление поставщика", self.query_delete_supplier),
            ("Ограничение целостности", self.query_integrity_check),
            ("Табличный отчёт", self.query_grouped_report),
            ("Картотека поставщиков", self.query_supplier_card),
            ("Хранимая процедура (ЦеныМатериалов)", self.query_stored_procedure)
        ]

        for name, method in buttons:
            btn = QPushButton(name)
            btn.clicked.connect(method)
            layout.addWidget(btn)

        # таблица результатов
        self.result_table = QTableWidget()
        layout.addWidget(QLabel("Результат:"))
        layout.addWidget(self.result_table)

        self.setLayout(layout)

    def connect_to_db(self):
        try:
            server, ok1 = QInputDialog.getText(self, "Сервер", "Введите имя сервера:")
            database, ok2 = QInputDialog.getText(self, "БД", "Введите имя базы данных:")
            if not (ok1 and ok2):
                return

            self.connection = pyodbc.connect(
                f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;"
            )
            QMessageBox.information(self, "Успех", "Соединение установлено!")

            self.load_table_names()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка подключения", str(e))

    def load_table_names(self):
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
            tables = cursor.fetchall()
            self.tables_combo.clear()
            self.tables_combo.addItem("— Выберите таблицу —")

            for t in tables:
                self.tables_combo.addItem(t[0])
        except Exception as e:
            QMessageBox.critical(self, "Ошибка загрузки таблиц", str(e))

    def load_selected_table(self):
        table_name = self.tables_combo.currentText()
        if table_name == "— Выберите таблицу —" or not self.connection:
            return
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            headers = [desc[0] for desc in cursor.description]
            self.display_results(rows, headers)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка таблицы", str(e))

    def display_results(self, rows, headers):
        self.result_table.clear()
        self.result_table.setColumnCount(len(headers))
        self.result_table.setRowCount(len(rows))
        self.result_table.setHorizontalHeaderLabels(headers)
        for row_idx, row_data in enumerate(rows):
            for col_idx, value in enumerate(row_data):
                self.result_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

    # Метод вызова хранимой процедуры
    def query_stored_procedure(self):
        procedureName, ok1 = QInputDialog.getText(self, "Процедура", "Название материала:")
        if not ok1 or not procedureName.strip(): return
        price, ok2 = QInputDialog.getDouble(self, "Цена", "Введите макс. цену:")
        if not ok2: return
        try:
            cursor = self.connection.cursor()
            cursor.execute("EXEC dbo.ЦеныМатериалов @название_материала = ?, @цена_материала = ?", (procedureName, price))
            rows = cursor.fetchall()
            headers = [desc[0] for desc in cursor.description]
            self.display_results(rows, headers)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка процедуры", str(e))

    # Методы вызова запросов

    # упорядочение сведений о поставщике
    def query_sort_suppliers(self):
        query = """
                SELECT P.*, M.Название_материала 
                FROM Поставщики P
                JOIN Предприятие Pr ON P.id_поставщика = Pr.id_поставщика
                JOIN Материалы M ON Pr.id_предприятия = M.id_предприятия
                ORDER BY M.Название_материала, Pr.Имя_предприятия;
        """
        self.run_and_display_query(query)

    # поиск поставщика
    def query_search_supplier(self):
        name, ok = QInputDialog.getText(self, "Поиск поставщика", "Введите имя поставщика:")
        if not ok: return
        
        query = "SELECT * FROM Поставщики WHERE Имя_поставщика = ?"
        self.run_and_display_query(query, [f'{name}'])

    # выборка материала X по цене меньше цены N
    def query_filter_material_price(self):
        material, ok1 = QInputDialog.getText(self, "Запрос выборки", "Введите нужный материал:")
        if not ok1: return
        price, ok2 = QInputDialog.getDouble(self, "Цена", "Введите максимальную цену:")
        if ok2:
            query = "SELECT * FROM Материалы WHERE Название_материала = ? AND Цена <= ?"
            self.run_and_display_query(query, [material, price])

    # средняя цена материала X
    def query_avg_price_material(self):
        name, ok = QInputDialog.getText(self, "Средняя цена", "Введите название материала:")
        if not ok or not name.strip(): return
        query = "SELECT AVG(Цена) AS Средняя_цена FROM Материалы WHERE Название_материала = ?"
        self.run_and_display_query(query, [name])

    # удаление сведений о поставщике
    def query_delete_supplier(self):
        id_, ok = QInputDialog.getInt(self, "Удаление", "Введите id_поставщика:")
        if not ok: return
        try:
            cursor = self.connection.cursor()
            for q in [
                """DELETE FROM Материалы WHERE Номер_склада IN (
                       SELECT Номер_склада FROM Склады WHERE id_поставщика = ?)""",
                """DELETE FROM ПокупателиСклады WHERE Номер_склада IN (
                       SELECT Номер_склада FROM Склады WHERE id_поставщика = ?)""",
                "DELETE FROM Склады WHERE id_поставщика = ?",
                "DELETE FROM Предприятие WHERE id_поставщика = ?",
                "DELETE FROM Поставщики WHERE id_поставщика = ?"
            ]:
                cursor.execute(q, id_)
            self.connection.commit()
            QMessageBox.information(self, "Успех", f"Поставщик с id {id_} удалён.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка удаления", str(e))

    # увеличение цены материала на X процентов в городе Y
    def query_update_material_price(self):
        material, ok1 = QInputDialog.getText(self, "Увеличить цену материала на X%", "Введите нужный материал:")
        if not ok1: return
        percent, ok2 = QInputDialog.getDouble(self, "Процент", "Введите желаемый %:")
        if not ok2: return
        city, ok3 = QInputDialog.getText(self, "Город", "Название города:")
        if ok3:
            update_query = """
                UPDATE Материалы
                SET Цена = Цена * (1 + ? / 100.0)
                WHERE Название_материала = ? AND id_предприятия IN (
                    SELECT id_предприятия FROM Предприятие WHERE id_поставщика IN (
                        SELECT id_поставщика FROM Поставщики WHERE Город = ?
                    )
                );
            """
            self.run_and_display_query(update_query, [percent, material, city])

    # запрос ограничения целостности каждый поставщик имеет хотя бы один материал
    def query_integrity_check(self):
        material_name, ok = QInputDialog.getText(self, "Проверка целостности", "Введите название материала:")
        if not ok or not material_name.strip():
            return
        try:
            cursor = self.connection.cursor()

            # Поставщики, у которых нет заданного материала
            query = """
                SELECT p.id_поставщика, p.Имя_поставщика
                FROM Поставщики p
                WHERE p.id_поставщика NOT IN (
                    SELECT DISTINCT s.id_поставщика
                    FROM Склады s
                    JOIN Материалы m ON s.Номер_склада = m.Номер_склада
                    WHERE m.Название_материала = ?
                )
            """
            cursor.execute(query, [material_name])
            rows = cursor.fetchall()

            if not rows:
                QMessageBox.information(self, "Проверка целостности", 
                    f"Все поставщики имеют хотя бы один материал с названием '{material_name}'.")
            else:
                headers = ["id_поставщика", "Имя_поставщика"]
                self.display_results(rows, headers)
                QMessageBox.warning(self, "Нарушение целостности", 
                    f"Поставщики {headers[1]} не имеют материал с названием '{material_name}'.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка проверки", str(e))

    # табличный отчет
    def query_grouped_report(self):
        query = """
            SELECT P.Имя_поставщика, M.Название_материала, M.Цена
            FROM Поставщики P
            JOIN Предприятие Pr ON P.id_поставщика = Pr.id_поставщика
            JOIN Материалы M ON Pr.id_предприятия = M.id_предприятия
            ORDER BY P.Имя_поставщика
        """
        self.run_and_display_query(query)

    # картотека поставщиков
    def query_supplier_card(self):
        query = """
            SELECT * FROM Поставщики
        """
        self.run_and_display_query(query)

    # метод отображения результата запроса
    def run_and_display_query(self, query, params=None):
        if self.connection is None:
            QMessageBox.critical(self, "Ошибка подключения", "Отсутствует подключение к базе данных")
            return

        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            rows = cursor.fetchall()
            headers = [desc[0] for desc in cursor.description]
            self.display_results(rows, headers)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка запроса", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    client = SQLClient()
    client.show()
    sys.exit(app.exec_())
