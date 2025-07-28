import pyodbc

try:
    conn = pyodbc.connect(
        r"DRIVER={ODBC Driver 17 for SQL Server};"
        r"SERVER=DESKTOP-SH532AI\SQLEXPRESS;"
        r"DATABASE=Dotsenko;"
        r"Trusted_Connection=yes;"
    )
    print("✅ Подключение успешно")

    # cursor = conn.cursor()
    # cursor.execute("SELECT TOP 2 * FROM Поставщики")
    # for row in cursor.fetchall():
    #     print(row)

    conn.close()

except Exception as e:
    print("Ошибка подключения:", e)
