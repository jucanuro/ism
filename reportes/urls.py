# En tu archivo urls.py de tu aplicación (ej. reportes/urls.py)
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('rechazos/', views.reporte_rechazos_view, name='reporte_rechazos_view'),
    path('actualizar-datos/', views.actualizar_datos_view, name='actualizar_datos'),
    # Nueva ruta consolidada para exportar Excel
    path('exportar-excel-consolidado/', views.export_excel_consolidado_view, name='exportar_excel_consolidado'),

    # ¡AÑADE ESTA LÍNEA!
    path('enviar-reporte-email/', views.export_report_email_view, name='export_report_email'),
    # Asegúrate de que 'export_report_email_view' sea el nombre de tu función de vista
    # que procesará la solicitud de envío de email en tu views.py
]