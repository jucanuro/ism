import os
import pandas as pd
from datetime import date
from dotenv import load_dotenv
from conectar_sql import conectar_tienda_kr

# --- Carga de variables de entorno ---
load_dotenv()
LINKED_SERVER = os.getenv('LINKED_SERVER_S1_NAME')

# ==============================================================================
# SECCIÓN DE CONSULTAS
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. CONSULTAS PARA VENTAS (Modelo: DatosDashboard)
# ------------------------------------------------------------------------------

CONSULTA_VENTAS_ARICA = f"""
    SELECT 
        'CHILE' AS PAIS, 'ARICA' AS CIUDAD, DAY(CDT.FECHA) AS DIA, 
        CASE WHEN MONTH(CDT.FECHA) = 1 THEN 'ENERO' WHEN MONTH(CDT.FECHA) = 2 THEN 'FEBRERO' WHEN MONTH(CDT.FECHA) = 3 THEN 'MARZO' WHEN MONTH(CDT.FECHA) = 4 THEN 'ABRIL' WHEN MONTH(CDT.FECHA) = 5 THEN 'MAYO' WHEN MONTH(CDT.FECHA) = 6 THEN 'JUNIO' WHEN MONTH(CDT.FECHA) = 7 THEN 'JULIO' WHEN MONTH(CDT.FECHA) = 8 THEN 'AGOSTO' WHEN MONTH(CDT.FECHA) = 9 THEN 'SEPTIEMBRE' WHEN MONTH(CDT.FECHA) = 10 THEN 'OCTUBRE' WHEN MONTH(CDT.FECHA) = 11 THEN 'NOVIEMBRE' WHEN MONTH(CDT.FECHA) = 12 THEN 'DICIEMBRE' END AS MES, 
        YEAR(CDT.FECHA) AS AÑO, CDT.[ESTADO DOCUMENTO] AS ESTADO, CDT.[NUMERO DE DOCUMENTO] AS FACTURA, 
        'VENTAS' AS TIPO, 'ENTREGADO' AS MOTIVO, CLD.cod_cliente AS codigo_cliente, C.NOMBRE AS CLIENTE,
        CLD.ITEM AS SUCURSAL, CONCAT(CDT.CODCLIENTE, CLD.item) AS CODIGO_SUCURSAL, C.RUT, CLD.ruta, G.NOMBRE AS GIRO,
        CLD.DIRECCION, V.NOMBRE AS VENDEDOR, D.NOMBRE AS DISTRIBUIDOR, PS.CATEGORIA, PS.MARCA, PS.FORMATO,
        PS.SABOR,
        SUM(DDT.CANTIDAD * CASE WHEN CDT.[LISTA PRECIO] = 1 AND DDT.descuento = 0 THEN PD.[CDIST MIN] WHEN CDT.[LISTA PRECIO] = 1 AND DDT.descuento > 0 THEN PD.[CDIST MAY] WHEN CDT.[LISTA PRECIO] = 2 AND DDT.descuento = 0 THEN PD.[CDIST MIN PROV] WHEN CDT.[LISTA PRECIO] = 2 AND DDT.descuento > 0 THEN PD.[CDIST MAY PROV] ELSE 0 END) AS COM_DISTRIBUIDOR,
        SUM(DDT.CANTIDAD * CASE WHEN CDT.[LISTA PRECIO] = 1 AND DDT.descuento = 0 THEN PD.[CVEND MIN] WHEN CDT.[LISTA PRECIO] = 1 AND DDT.descuento > 0 THEN PD.[CVEND MAY] WHEN CDT.[LISTA PRECIO] = 2 AND DDT.descuento = 0 THEN PD.[CVEND MIN PROV] WHEN CDT.[LISTA PRECIO] = 2 AND DDT.descuento > 0 THEN PD.[CVEND MAY PROV] ELSE 0 END) AS COM_VENDEDOR,
        SUM(DDT.CANTIDAD) AS DISPLAY, SUM(PD.MCUBICO * DDT.CANTIDAD * PD.CXBULTO) AS LITROS,
        SUM(DDT.neto) AS NETO, SUM(DDT.arancel) AS ARANCEL, SUM(DDT.ila13) AS ILA13,
        SUM(DDT.bruto) AS BRUTO, SUM(DDT.CANTIDAD * DDT.[PRECIO LISTA UNITARIO]) AS MONTO
    FROM [{LINKED_SERVER}].[TiendaAR].[dbo].CABECERADOCUMENTO CDT 
    INNER JOIN [{LINKED_SERVER}].[TiendaAR].[dbo].DETALLEDOCUMENTO as DDT ON CDT.[NUMERO DE DOCUMENTO]=DDT.[NUMERO DE DOCUMENTO] 
    INNER JOIN [{LINKED_SERVER}].[TiendaAR].[dbo].CLIENTES AS C ON CDT.CODCLIENTE=C.[CODIGO NUMERICO]
    INNER JOIN [{LINKED_SERVER}].[TiendaAR].[dbo].CLIENTES_DIR AS CLD ON C.[CODIGO NUMERICO] = CLD.cod_cliente AND CDT.[DIR CLIENTE] = cld.item
    INNER JOIN [{LINKED_SERVER}].[TiendaAR].[dbo].VENDEDOR AS V ON CDT.[CODIGO VENDEDOR] = V.CODIGO 
    INNER JOIN [{LINKED_SERVER}].[TiendaAR].[dbo].DISTRIBUIDOR AS D ON CDT.DISTRIBUIDOR = D.CODIGO 
    INNER JOIN [{LINKED_SERVER}].[ZoftNetSAR].[dbo].PRODUCTOSAP AS PS ON DDT.ESPECIFICO = PS.[CODIGO CHILE] 
    INNER JOIN [{LINKED_SERVER}].[TiendaAR].[dbo].PRODUCTO AS PD ON DDT.ESPECIFICO=PD.ESPECIFICO 
    INNER JOIN [{LINKED_SERVER}].[TiendaAR].[dbo].GIRO AS G ON C.GIRO=G.CODIGO 
    WHERE CDT.[TIPO DE DOCUMENTO] ='FA' AND CDT.[ESTADO DOCUMENTO] IN('I','C') AND CDT.FECHA BETWEEN ? AND ?
    GROUP BY cdt.[ESTADO DOCUMENTO], cdt.[NUMERO DE DOCUMENTO],CDT.FECHA,CLD.cod_cliente,C.NOMBRE,CLD.item, CLD.DIRECCION,V.NOMBRE,D.NOMBRE,PS.MARCA, PS.CATEGORIA, PS.FORMATO, PS.SABOR, PD.MCUBICO, PD.CXBULTO, CDT.[LISTA PRECIO], PD.[CDIST MIN], PD.[CDIST MAY], PD.[CDIST MIN PROV], PD.[CDIST MAY PROV], PD.[CVEND MIN], PD.[CVEND MAY], PD.[CVEND MIN PROV], PD.[CVEND MAY PROV], DDT.[PRECIO LISTA UNITARIO], C.RUT, CLD.ruta, G.NOMBRE, DDT.descuento, CDT.CODCLIENTE;
"""

CONSULTA_VENTAS_IQUIQUE = """
    SELECT 
        'CHILE' AS PAIS, 'IQUIQUE' AS CIUDAD, DAY(CDT.FECHA) AS DIA, 
        CASE WHEN MONTH(CDT.FECHA) = 1 THEN 'ENERO' WHEN MONTH(CDT.FECHA) = 2 THEN 'FEBRERO' WHEN MONTH(CDT.FECHA) = 3 THEN 'MARZO' WHEN MONTH(CDT.FECHA) = 4 THEN 'ABRIL' WHEN MONTH(CDT.FECHA) = 5 THEN 'MAYO' WHEN MONTH(CDT.FECHA) = 6 THEN 'JUNIO' WHEN MONTH(CDT.FECHA) = 7 THEN 'JULIO' WHEN MONTH(CDT.FECHA) = 8 THEN 'AGOSTO' WHEN MONTH(CDT.FECHA) = 9 THEN 'SEPTIEMBRE' WHEN MONTH(CDT.FECHA) = 10 THEN 'OCTUBRE' WHEN MONTH(CDT.FECHA) = 11 THEN 'NOVIEMBRE' WHEN MONTH(CDT.FECHA) = 12 THEN 'DICIEMBRE' END AS MES, 
        YEAR(CDT.FECHA) AS AÑO, CDT.[ESTADO DOCUMENTO] AS ESTADO, CDT.[NUMERO DE DOCUMENTO] AS FACTURA, 
        'VENTAS' AS TIPO, 'ENTREGADO' AS MOTIVO, CLD.cod_cliente AS codigo_cliente, C.NOMBRE AS CLIENTE,
        CLD.ITEM AS SUCURSAL, CONCAT(CDT.CODCLIENTE, CLD.item) AS CODIGO_SUCURSAL, C.RUT, CLD.ruta, G.NOMBRE AS GIRO,
        CLD.DIRECCION, V.NOMBRE AS VENDEDOR, D.NOMBRE AS DISTRIBUIDOR, PS.CATEGORIA, PS.MARCA, PS.FORMATO,
        PS.SABOR,
        SUM(DDT.CANTIDAD * CASE WHEN CDT.[LISTA PRECIO] = 1 AND DDT.descuento = 0 THEN PD.[CDIST MIN] WHEN CDT.[LISTA PRECIO] = 1 AND DDT.descuento > 0 THEN PD.[CDIST MAY] WHEN CDT.[LISTA PRECIO] = 2 AND DDT.descuento = 0 THEN PD.[CDIST MIN PROV] WHEN CDT.[LISTA PRECIO] = 2 AND DDT.descuento > 0 THEN PD.[CDIST MAY PROV] ELSE 0 END) AS COM_DISTRIBUIDOR,
        SUM(DDT.CANTIDAD * CASE WHEN CDT.[LISTA PRECIO] = 1 AND DDT.descuento = 0 THEN PD.[CVEND MIN] WHEN CDT.[LISTA PRECIO] = 1 AND DDT.descuento > 0 THEN PD.[CVEND MAY] WHEN CDT.[LISTA PRECIO] = 2 AND DDT.descuento = 0 THEN PD.[CVEND MIN PROV] WHEN CDT.[LISTA PRECIO] = 2 AND DDT.descuento > 0 THEN PD.[CVEND MAY PROV] ELSE 0 END) AS COM_VENDEDOR,
        SUM(DDT.CANTIDAD) AS DISPLAY, SUM(PD.MCUBICO * DDT.CANTIDAD * PD.CXBULTO) AS LITROS,
        SUM(DDT.neto) AS NETO, SUM(DDT.arancel) AS ARANCEL, SUM(DDT.ila13) AS ILA13,
        SUM(DDT.bruto) AS BRUTO, SUM(DDT.CANTIDAD * DDT.[PRECIO LISTA UNITARIO]) AS MONTO
    FROM TiendaKR.dbo.CABECERADOCUMENTO CDT 
    INNER JOIN TiendaKR.dbo.DETALLEDOCUMENTO as DDT ON CDT.[NUMERO DE DOCUMENTO]=DDT.[NUMERO DE DOCUMENTO] 
    INNER JOIN TiendaKR.dbo.CLIENTES AS C ON CDT.CODCLIENTE=C.[CODIGO NUMERICO]
    INNER JOIN TiendaKR.dbo.CLIENTES_DIR AS CLD ON C.[CODIGO NUMERICO] = CLD.cod_cliente AND CDT.[DIR CLIENTE] = cld.item
    INNER JOIN TiendaKR.dbo.VENDEDOR AS V ON CDT.[CODIGO VENDEDOR] = V.CODIGO 
    INNER JOIN TiendaKR.dbo.DISTRIBUIDOR AS D ON CDT.DISTRIBUIDOR = D.CODIGO 
    INNER JOIN ZoftNetSVE.dbo.PRODUCTOSAP AS PS ON DDT.ESPECIFICO = PS.[CODIGO CHILE] 
    INNER JOIN TiendaKR.dbo.PRODUCTO AS PD ON DDT.ESPECIFICO=PD.ESPECIFICO 
    INNER JOIN TiendaKR.dbo.GIRO AS G ON C.GIRO=G.CODIGO 
    WHERE CDT.[TIPO DE DOCUMENTO] ='FA' AND CDT.[ESTADO DOCUMENTO] IN('I','C') AND CDT.FECHA BETWEEN ? AND ?
    GROUP BY cdt.[ESTADO DOCUMENTO], cdt.[NUMERO DE DOCUMENTO],CDT.FECHA,CLD.cod_cliente,C.NOMBRE,CLD.item, CLD.DIRECCION,V.NOMBRE,D.NOMBRE,PS.MARCA, PS.CATEGORIA, PS.FORMATO, PS.SABOR, PD.MCUBICO, PD.CXBULTO, CDT.[LISTA PRECIO], PD.[CDIST MIN], PD.[CDIST MAY], PD.[CDIST MIN PROV], PD.[CDIST MAY PROV], PD.[CVEND MIN], PD.[CVEND MAY], PD.[CVEND MIN PROV], PD.[CVEND MAY PROV], DDT.[PRECIO LISTA UNITARIO], C.RUT, CLD.ruta, G.NOMBRE, DDT.descuento, CDT.CODCLIENTE;
"""

# ------------------------------------------------------------------------------
# 2. CONSULTAS PARA RECHAZOS (Modelo: DatosRechazos)
# ------------------------------------------------------------------------------

CONSULTA_RECHAZOS_ARICA = f"""
    SELECT 
        'CHILE' AS PAIS, 'ARICA' AS CIUDAD, DAY(CDT.FECHA) AS DIA, 
        CASE WHEN MONTH(CDT.FECHA) = 1 THEN 'ENERO' WHEN MONTH(CDT.FECHA) = 2 THEN 'FEBRERO' WHEN MONTH(CDT.FECHA) = 3 THEN 'MARZO' WHEN MONTH(CDT.FECHA) = 4 THEN 'ABRIL' WHEN MONTH(CDT.FECHA) = 5 THEN 'MAYO' WHEN MONTH(CDT.FECHA) = 6 THEN 'JUNIO' WHEN MONTH(CDT.FECHA) = 7 THEN 'JULIO' WHEN MONTH(CDT.FECHA) = 8 THEN 'AGOSTO' WHEN MONTH(CDT.FECHA) = 9 THEN 'SEPTIEMBRE' WHEN MONTH(CDT.FECHA) = 10 THEN 'OCTUBRE' WHEN MONTH(CDT.FECHA) = 11 THEN 'NOVIEMBRE' WHEN MONTH(CDT.FECHA) = 12 THEN 'DICIEMBRE' END AS MES, 
        YEAR(CDT.FECHA) AS AÑO, CDT.[ESTADO DOCUMENTO] AS ESTADO, CDT.[NUMERO DE DOCUMENTO] AS FACTURA, 
        'RECHAZOS' AS TIPO, M.DESCRIPCION AS MOTIVO, CLD.cod_cliente AS codigo_cliente, C.NOMBRE AS CLIENTE,
        CLD.ITEM AS SUCURSAL, CONCAT(CDT.CODCLIENTE, CLD.item) AS CODIGO_SUCURSAL, C.RUT, CLD.ruta, G.NOMBRE AS GIRO,
        CLD.DIRECCION, V.NOMBRE AS VENDEDOR, D.NOMBRE AS DISTRIBUIDOR, PS.CATEGORIA, PS.MARCA, PS.FORMATO,
        PS.SABOR,
        SUM(DDT.CANTIDAD * CASE WHEN CDT.[LISTA PRECIO] = 1 AND DDT.descuento = 0 THEN PD.[CDIST MIN] WHEN CDT.[LISTA PRECIO] = 1 AND DDT.descuento > 0 THEN PD.[CDIST MAY] WHEN CDT.[LISTA PRECIO] = 2 AND DDT.descuento = 0 THEN PD.[CDIST MIN PROV] WHEN CDT.[LISTA PRECIO] = 2 AND DDT.descuento > 0 THEN PD.[CDIST MAY PROV] ELSE 0 END) AS COM_DISTRIBUIDOR,
        SUM(DDT.CANTIDAD * CASE WHEN CDT.[LISTA PRECIO] = 1 AND DDT.descuento = 0 THEN PD.[CVEND MIN] WHEN CDT.[LISTA PRECIO] = 1 AND DDT.descuento > 0 THEN PD.[CVEND MAY] WHEN CDT.[LISTA PRECIO] = 2 AND DDT.descuento = 0 THEN PD.[CVEND MIN PROV] WHEN CDT.[LISTA PRECIO] = 2 AND DDT.descuento > 0 THEN PD.[CVEND MAY PROV] ELSE 0 END) AS COM_VENDEDOR,
        SUM(DDT.CANTIDAD) AS DISPLAY, SUM(PD.MCUBICO * DDT.CANTIDAD * PD.CXBULTO) AS LITROS,
        SUM(DDT.neto) AS NETO, SUM(DDT.arancel) AS ARANCEL, SUM(DDT.ila13) AS ILA13,
        SUM(DDT.bruto) AS BRUTO, SUM(DDT.CANTIDAD * DDT.[PRECIO LISTA UNITARIO]) AS MONTO
    FROM [{LINKED_SERVER}].[TiendaAR].[dbo].CABECERADOCUMENTO CDT 
    INNER JOIN [{LINKED_SERVER}].[TiendaAR].[dbo].DETALLE_LOG as DDT ON CDT.[NUMERO DE DOCUMENTO]=DDT.[NUMERO DE DOCUMENTO] 
    INNER JOIN [{LINKED_SERVER}].[TiendaAR].[dbo].MOTIVO AS M ON CDT.MOTIVO=M.CODIGO 
    INNER JOIN [{LINKED_SERVER}].[TiendaAR].[dbo].CLIENTES AS C ON CDT.CODCLIENTE=C.[CODIGO NUMERICO]
    INNER JOIN [{LINKED_SERVER}].[TiendaAR].[dbo].CLIENTES_DIR AS CLD ON C.[CODIGO NUMERICO] = CLD.cod_cliente AND CDT.[DIR CLIENTE] = cld.item
    INNER JOIN [{LINKED_SERVER}].[TiendaAR].[dbo].VENDEDOR AS V ON CDT.[CODIGO VENDEDOR] = V.CODIGO 
    INNER JOIN [{LINKED_SERVER}].[TiendaAR].[dbo].DISTRIBUIDOR AS D ON CDT.DISTRIBUIDOR = D.CODIGO 
    INNER JOIN [{LINKED_SERVER}].[ZoftNetSAR].[dbo].PRODUCTOSAP AS PS ON DDT.ESPECIFICO = PS.[CODIGO CHILE] 
    INNER JOIN [{LINKED_SERVER}].[TiendaAR].[dbo].PRODUCTO AS PD ON DDT.ESPECIFICO=PD.ESPECIFICO 
    INNER JOIN [{LINKED_SERVER}].[TiendaAR].[dbo].GIRO AS G ON C.GIRO=G.CODIGO 
    WHERE CDT.[TIPO DE DOCUMENTO] ='FA' AND CDT.[ESTADO DOCUMENTO]='N' AND CDT.FECHA BETWEEN ? AND ?
    GROUP BY cdt.[ESTADO DOCUMENTO], cdt.[NUMERO DE DOCUMENTO],CDT.FECHA,M.DESCRIPCION,CLD.cod_cliente,C.NOMBRE,CLD.item, CLD.DIRECCION,V.NOMBRE,D.NOMBRE,PS.MARCA, PS.CATEGORIA, PS.FORMATO, PS.SABOR, PD.MCUBICO, PD.CXBULTO, CDT.[LISTA PRECIO], PD.[CDIST MIN], PD.[CDIST MAY], PD.[CDIST MIN PROV], PD.[CDIST MAY PROV], PD.[CVEND MIN], PD.[CVEND MAY], PD.[CVEND MIN PROV], PD.[CVEND MAY PROV], DDT.[PRECIO LISTA UNITARIO], C.RUT, CLD.ruta, G.NOMBRE, DDT.descuento, CDT.CODCLIENTE;
"""

CONSULTA_RECHAZOS_IQUIQUE = """
    SELECT 
        'CHILE' AS PAIS, 'IQUIQUE' AS CIUDAD, DAY(CDT.FECHA) AS DIA, 
        CASE WHEN MONTH(CDT.FECHA) = 1 THEN 'ENERO' WHEN MONTH(CDT.FECHA) = 2 THEN 'FEBRERO' WHEN MONTH(CDT.FECHA) = 3 THEN 'MARZO' WHEN MONTH(CDT.FECHA) = 4 THEN 'ABRIL' WHEN MONTH(CDT.FECHA) = 5 THEN 'MAYO' WHEN MONTH(CDT.FECHA) = 6 THEN 'JUNIO' WHEN MONTH(CDT.FECHA) = 7 THEN 'JULIO' WHEN MONTH(CDT.FECHA) = 8 THEN 'AGOSTO' WHEN MONTH(CDT.FECHA) = 9 THEN 'SEPTIEMBRE' WHEN MONTH(CDT.FECHA) = 10 THEN 'OCTUBRE' WHEN MONTH(CDT.FECHA) = 11 THEN 'NOVIEMBRE' WHEN MONTH(CDT.FECHA) = 12 THEN 'DICIEMBRE' END AS MES, 
        YEAR(CDT.FECHA) AS AÑO, CDT.[ESTADO DOCUMENTO] AS ESTADO, CDT.[NUMERO DE DOCUMENTO] AS FACTURA, 
        'RECHAZOS' AS TIPO, M.DESCRIPCION AS MOTIVO, CLD.cod_cliente AS codigo_cliente, C.NOMBRE AS CLIENTE,
        CLD.ITEM AS SUCURSAL, CONCAT(CDT.CODCLIENTE, CLD.item) AS CODIGO_SUCURSAL, C.RUT, CLD.ruta, G.NOMBRE AS GIRO,
        CLD.DIRECCION, V.NOMBRE AS VENDEDOR, D.NOMBRE AS DISTRIBUIDOR, PS.CATEGORIA, PS.MARCA, PS.FORMATO,
        PS.SABOR,
        SUM(DDT.CANTIDAD * CASE WHEN CDT.[LISTA PRECIO] = 1 AND DDT.descuento = 0 THEN PD.[CDIST MIN] WHEN CDT.[LISTA PRECIO] = 1 AND DDT.descuento > 0 THEN PD.[CDIST MAY] WHEN CDT.[LISTA PRECIO] = 2 AND DDT.descuento = 0 THEN PD.[CDIST MIN PROV] WHEN CDT.[LISTA PRECIO] = 2 AND DDT.descuento > 0 THEN PD.[CDIST MAY PROV] ELSE 0 END) AS COM_DISTRIBUIDOR,
        SUM(DDT.CANTIDAD * CASE WHEN CDT.[LISTA PRECIO] = 1 AND DDT.descuento = 0 THEN PD.[CVEND MIN] WHEN CDT.[LISTA PRECIO] = 1 AND DDT.descuento > 0 THEN PD.[CVEND MAY] WHEN CDT.[LISTA PRECIO] = 2 AND DDT.descuento = 0 THEN PD.[CVEND MIN PROV] WHEN CDT.[LISTA PRECIO] = 2 AND DDT.descuento > 0 THEN PD.[CVEND MAY PROV] ELSE 0 END) AS COM_VENDEDOR,
        SUM(DDT.CANTIDAD) AS DISPLAY, SUM(PD.MCUBICO * DDT.CANTIDAD * PD.CXBULTO) AS LITROS,
        SUM(DDT.neto) AS NETO, SUM(DDT.arancel) AS ARANCEL, SUM(DDT.ila13) AS ILA13,
        SUM(DDT.bruto) AS BRUTO, SUM(DDT.CANTIDAD * DDT.[PRECIO LISTA UNITARIO]) AS MONTO
    FROM TiendaKR.dbo.CABECERADOCUMENTO CDT 
    INNER JOIN TiendaKR.dbo.DETALLE_LOG as DDT ON CDT.[NUMERO DE DOCUMENTO]=DDT.[NUMERO DE DOCUMENTO] 
    INNER JOIN TiendaKR.dbo.MOTIVO AS M ON CDT.MOTIVO=M.CODIGO 
    INNER JOIN TiendaKR.dbo.CLIENTES AS C ON CDT.CODCLIENTE=C.[CODIGO NUMERICO]
    INNER JOIN TiendaKR.dbo.CLIENTES_DIR AS CLD ON C.[CODIGO NUMERICO] = CLD.cod_cliente AND CDT.[DIR CLIENTE] = cld.item
    INNER JOIN TiendaKR.dbo.VENDEDOR AS V ON CDT.[CODIGO VENDEDOR] = V.CODIGO 
    INNER JOIN TiendaKR.dbo.DISTRIBUIDOR AS D ON CDT.DISTRIBUIDOR = D.CODIGO 
    INNER JOIN ZoftNetSVE.dbo.PRODUCTOSAP AS PS ON DDT.ESPECIFICO = PS.[CODIGO CHILE] 
    INNER JOIN TiendaKR.dbo.PRODUCTO AS PD ON DDT.ESPECIFICO=PD.ESPECIFICO 
    INNER JOIN TiendaKR.dbo.GIRO AS G ON C.GIRO=G.CODIGO 
    WHERE CDT.[TIPO DE DOCUMENTO] ='FA' AND CDT.[ESTADO DOCUMENTO]='N' AND CDT.FECHA BETWEEN ? AND ?
    GROUP BY cdt.[ESTADO DOCUMENTO], cdt.[NUMERO DE DOCUMENTO],CDT.FECHA,M.DESCRIPCION,CLD.cod_cliente,C.NOMBRE,CLD.item, CLD.DIRECCION,V.NOMBRE,D.NOMBRE,PS.MARCA, PS.CATEGORIA, PS.FORMATO, PS.SABOR, PD.MCUBICO, PD.CXBULTO, CDT.[LISTA PRECIO], PD.[CDIST MIN], PD.[CDIST MAY], PD.[CDIST MIN PROV], PD.[CDIST MAY PROV], PD.[CVEND MIN], PD.[CVEND MAY], PD.[CVEND MIN PROV], PD.[CVEND MAY PROV], DDT.[PRECIO LISTA UNITARIO], C.RUT, CLD.ruta, G.NOMBRE, DDT.descuento, CDT.CODCLIENTE;
"""


# ==============================================================================
# SECCIÓN DE FUNCIONES PARA OBTENER Y PROCESAR DATOS
# ==============================================================================

def obtener_datos(nombre_reporte, consulta_sql, conexion, fecha_inicio, fecha_fin):
    """Función genérica para ejecutar una consulta SQL y devolver un DataFrame."""
    print(f" Ejecutando consulta para {nombre_reporte} (Rango: {fecha_inicio} a {fecha_fin})...")
    try:
        df = pd.read_sql(consulta_sql, conexion, params=[fecha_inicio, fecha_fin])
        print(f"✅ ¡Consulta de {nombre_reporte} exitosa! Se encontraron {len(df)} filas.")
        return df
    except Exception as e:
        print(f"💥 Ocurrió un error en la consulta de {nombre_reporte}: {e}")
        return None

def fetch_dashboard_data(fecha_inicio_param, fecha_fin_param):
    """Obtiene los datos de VENTAS de Arica e Iquique."""
    print(f"\nObteniendo datos de Ventas DESDE {fecha_inicio_param.strftime('%Y-%m-%d')} HASTA {fecha_fin_param.strftime('%Y-%m-%d')}...")
    if not LINKED_SERVER:
        print("❌ ERROR: No se encontró LINKED_SERVER_S1_NAME en .env")
        return pd.DataFrame()

    conexion = conectar_tienda_kr()
    if not conexion:
        return pd.DataFrame()

    try:
        df_arica = obtener_datos("Ventas Arica", CONSULTA_VENTAS_ARICA, conexion, fecha_inicio_param, fecha_fin_param)
        df_iquique = obtener_datos("Ventas Iquique", CONSULTA_VENTAS_IQUIQUE, conexion, fecha_inicio_param, fecha_fin_param)

        dataframes_a_unir = [df for df in [df_arica, df_iquique] if df is not None and not df.empty]
        
        if not dataframes_a_unir:
            print("No se encontraron datos de ventas para unir.")
            return pd.DataFrame() 

        df_consolidado = pd.concat(dataframes_a_unir, ignore_index=True)
        print(f"Total de filas de Ventas consolidadas para el rango: {len(df_consolidado)}")
        return df_consolidado
    finally:
        if conexion:
            conexion.close()
            print("Conexión (fetch_dashboard_data) cerrada.")

def fetch_rechazos_data(fecha_inicio_param, fecha_fin_param):
    """Obtiene los datos de RECHAZOS de Arica e Iquique."""
    print(f"\nObteniendo datos de Rechazos DESDE {fecha_inicio_param.strftime('%Y-%m-%d')} HASTA {fecha_fin_param.strftime('%Y-%m-%d')}...")
    if not LINKED_SERVER:
        print("❌ ERROR: No se encontró LINKED_SERVER_S1_NAME en .env")
        return pd.DataFrame()

    conexion = conectar_tienda_kr()
    if not conexion:
        return pd.DataFrame()

    try:
        df_arica_rechazos = obtener_datos("Rechazos Arica", CONSULTA_RECHAZOS_ARICA, conexion, fecha_inicio_param, fecha_fin_param)
        df_iquique_rechazos = obtener_datos("Rechazos Iquique", CONSULTA_RECHAZOS_IQUIQUE, conexion, fecha_inicio_param, fecha_fin_param)

        dataframes_a_unir = [df for df in [df_arica_rechazos, df_iquique_rechazos] if df is not None and not df.empty]
        
        if not dataframes_a_unir:
            print("No se encontraron datos de rechazos para unir.")
            return pd.DataFrame() 

        df_consolidado_rechazos = pd.concat(dataframes_a_unir, ignore_index=True)
        print(f"Total de filas de Rechazos consolidadas para el rango: {len(df_consolidado_rechazos)}")
        return df_consolidado_rechazos
    finally:
        if conexion:
            conexion.close()
            print("Conexión (fetch_rechazos_data) cerrada.")