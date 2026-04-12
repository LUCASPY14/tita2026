import pyodbc

conn = pyodbc.connect(
    r"DRIVER={ODBC Driver 18 for SQL Server};"
    r"SERVER=np:localhost;"
    r"DATABASE=master;"
    r"Trusted_Connection=yes;"
    r"TrustServerCertificate=yes;"
    r"MARS_Connection=yes",
    autocommit=True,
)

cursor = conn.cursor()
cursor.execute(
    """
    IF DB_ID('test_titadb') IS NOT NULL
    BEGIN
        ALTER DATABASE [test_titadb] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
        DROP DATABASE [test_titadb];
    END
    """
)
print("test_titadb dropped if existed")
