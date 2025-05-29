from django.core.management.base import BaseCommand
from reportes.models import DatosDashboard, DatosRechazos
from reportes import data_manager
import pandas as pd
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Actualiza las tablas DatosDashboard y DatosRechazos con los datos de SQL Server.'

    def _procesar_y_guardar(self, df, model, column_mapping, model_name):
        """
        Función auxiliar para procesar un DataFrame y guardarlo en el modelo especificado.
        """
        if df is None or df.empty:
            self.stdout.write(self.style.WARNING(f'No se obtuvieron datos para {model_name}. No se actualizó la tabla.'))
            return 0

        self.stdout.write(f'Se obtuvieron {len(df)} filas para {model_name}.')
        
        # 1. Renombrar columnas
        df_renamed = df.rename(columns=column_mapping)
        
        # 2. Limpiar datos antiguos
        self.stdout.write(f'Limpiando tabla {model_name}...')
        model.objects.all().delete()
        self.stdout.write(f'Tabla {model_name} limpiada.')

        # 3. Preparar objetos para bulk_create
        registros_para_guardar = df_renamed.to_dict(orient='records')
        lista_objetos = []
        campos_modelo = {f.name for f in model._meta.get_fields()}

        for record in registros_para_guardar:
            # Reemplazar NaN de pandas con None de Python
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
            
            # Filtrar claves que no están en el modelo para evitar errores
            record_filtrado = {k: v for k, v in record.items() if k in campos_modelo}
            
            lista_objetos.append(model(**record_filtrado))

        # 4. Guardar en la base de datos
        self.stdout.write(f'Preparando {len(lista_objetos)} objetos de {model_name} para guardar...')
        model.objects.bulk_create(lista_objetos, batch_size=500)
        self.stdout.write(self.style.SUCCESS(f'¡Actualización de {model_name} completada! Se guardaron {len(lista_objetos)} registros.'))
        return len(lista_objetos)

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- Iniciando actualización de datos ---'))
        fecha_fin_carga = date.today()
        fecha_inicio_carga = date(fecha_fin_carga.year, 1, 1)
        
        self.stdout.write(f"Rango de carga: {fecha_inicio_carga.strftime('%Y-%m-%d')} a {fecha_fin_carga.strftime('%Y-%m-%d')}")

        # --- PROCESAR DATOS DE VENTAS (DASHBOARD) ---
        df_ventas = data_manager.fetch_dashboard_data(fecha_inicio_carga, fecha_fin_carga)
        mapping_ventas = {
            'PAIS': 'pais', 'CIUDAD': 'ciudad', 'DIA': 'dia', 'MES': 'mes', 'AÑO': 'año',
            'ESTADO': 'estado', 'FACTURA': 'factura', 'TIPO': 'tipo', 'MOTIVO': 'motivo',
            'codigo_cliente': 'codigo_cliente', 'CLIENTE': 'cliente', 'SUCURSAL': 'sucursal',
            'CODIGO_SUCURSAL': 'codigo_sucursal', 'RUT': 'rut', 'ruta': 'ruta', 'GIRO': 'giro',
            'DIRECCION': 'direccion', 'VENDEDOR': 'vendedor', 'DISTRIBUIDOR': 'distribuidor',
            'CATEGORIA': 'categoria', 'MARCA': 'marca', 'FORMATO': 'formato', 'SABOR': 'sabor',
            'COM_DISTRIBUIDOR': 'com_distribuidor', 'COM_VENDEDOR': 'com_vendedor',
            'DISPLAY': 'display', 'LITROS': 'litros', 'NETO': 'neto', 'ARANCEL': 'arancel',
            'ILA13': 'ila13', 'BRUTO': 'bruto', 'MONTO': 'monto'
        }
        self._procesar_y_guardar(df_ventas, DatosDashboard, mapping_ventas, "DatosDashboard (Ventas)")

        # --- PROCESAR DATOS DE RECHAZOS ---
        df_rechazos = data_manager.fetch_rechazos_data(fecha_inicio_carga, fecha_fin_carga)
        # El mapping es idéntico porque las consultas SQL devuelven los mismos nombres de columna
        mapping_rechazos = mapping_ventas.copy() 
        self._procesar_y_guardar(df_rechazos, DatosRechazos, mapping_rechazos, "DatosRechazos")

        self.stdout.write(self.style.SUCCESS('--- Proceso de actualización finalizado. ---'))