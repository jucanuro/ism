from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('exportar-excel/', views.export_excel_view, name='export_excel'),
    path('rechazos/', views.reporte_rechazos_view, name='reporte_rechazos_view'),
    path('rechazos/exportar-excel/', views.export_rechazos_excel_view, name='exportar_rechazos_excel'),
    path('actualizar-datos/', views.actualizar_datos_view, name='actualizar_datos'),
]