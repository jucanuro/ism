import os
import sys
import pyodbc
from dotenv import load_dotenv

# Carga las variables de entorno desde el archivo .env
load_dotenv()


def _crear_conexion_base(server, database, user, password):
    """
    Función privada y centralizada para crear la conexión física.
    """
    try:
        connection_string = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={server},{1433};"
            f"DATABASE={database};"
            f"UID={user};"
            f"PWD={password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=yes;"
            f"Connection Timeout=10;"
        )
        cnxn = pyodbc.connect(connection_string)
        return cnxn
    except Exception as e:
        print(f"❌ ERROR al intentar conectar a {server}/{database}.", file=sys.stderr)
        print(f"   Detalles del error: {e}", file=sys.stderr)
        return None


# --- Nuestras ÚNICAS y FUNCIONALES conexiones ---


def conectar_tienda_kr():
    """Se conecta a la base de datos TiendaKR en el Servidor 2."""
    print("[INFO] Conectando a Servidor 2 / TiendaKR...")
    return _crear_conexion_base(
        os.getenv("S2_HOST"),
        os.getenv("S2_DB_TIENDA"),
        os.getenv("SQL_USER"),
        os.getenv("SQL_PASSWORD"),
    )


def conectar_zoftnet_sve():
    """Se conecta a la base de datos ZoftnetSVE en el Servidor 2."""
    print("[INFO] Conectando a Servidor 2 / ZoftnetSVE...")
    return _crear_conexion_base(
        os.getenv("S2_HOST"),
        os.getenv("S2_DB_ZOFNET"),
        os.getenv("SQL_USER"),
        os.getenv("SQL_PASSWORD"),
    )


# --- Bloque de prueba simplificado ---
if __name__ == "__main__":
    print("--- Realizando pruebas de conexión al Servidor 2 ---")

    for func_conexion in [conectar_tienda_kr, conectar_zoftnet_sve]:
        conexion = func_conexion()
        if conexion:
            print("   -> Resultado: ✅ Conexión Exitosa.")
            conexion.close()
        else:
            print("   -> Resultado: ❌ Falló la conexión.")

    print("\n--- Pruebas finalizadas ---")
