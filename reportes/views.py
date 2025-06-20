from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.management import call_command
from django.contrib.auth.decorators import login_required
from .models import DatosDashboard, DatosRechazos
from .forms import DashboardFilterForm
from django.db.models import Sum, Exists, OuterRef, Value, Case, When, IntegerField, Q
import pandas as pd
from datetime import date, datetime
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
import io
import plotly.express as px


# Importaciones para SQS (Aunque no se usan en las funciones modificadas directamente, las mantengo si son para otro propósito)
import boto3
from django.conf import settings
import json

# Importaciones necesarias para el envío de correo
from django.core.mail import EmailMessage
# Considera importar un módulo para la generación de Excel en memoria si no quieres reusar
# `export_excel_consolidado_view` directamente, o si esta vista requiere un Excel diferente.
# Por ejemplo, si usas openpyxl directamente:
# import openpyxl
# from openpyxl.workbook import Workbook
from django.views.decorators.http import require_POST

# Mapeo de meses a números para facilitar la comparación de fechas
MONTH_TO_NUMBER = {
    'ENERO': 1, 'FEBRERO': 2, 'MARZO': 3, 'ABRIL': 4, 'MAYO': 5, 'JUNIO': 6,
    'JULIO': 7, 'AGOSTO': 8, 'SEPTIEMBRE': 9, 'OCTUBRE': 10, 'NOVIEMBRE': 11, 'DICIEMBRE': 12
}

def dashboard(request):
    """
    Vista principal del dashboard. Maneja la visualización de datos de ventas y rechazos,
    filtrado y generación de gráficos.
    """
    form = DashboardFilterForm(request.GET or None)
    
    # Querysets base para DatosDashboard y DatosRechazos
    base_dashboard_qs = DatosDashboard.objects.all()
    base_rechazos_qs = DatosRechazos.objects.all()

    # Anotar el número de mes para ambos querysets, facilitando el filtrado por rango de fechas
    month_whens = [When(mes=name, then=Value(num)) for name, num in MONTH_TO_NUMBER.items()]
    base_dashboard_qs = base_dashboard_qs.annotate(
        mes_numero=Case(*month_whens, default=Value(0), output_field=IntegerField())
    )
    base_rechazos_qs = base_rechazos_qs.annotate(
        mes_numero=Case(*month_whens, default=Value(0), output_field=IntegerField())
    )

    # Anotar si una factura en DatosDashboard tiene un rechazo asociado
    rechazos_factura_subquery = DatosRechazos.objects.filter(factura=OuterRef('factura'))
    base_dashboard_qs = base_dashboard_qs.annotate(es_rechazado=Exists(rechazos_factura_subquery))

    # Determinar el estado del documento seleccionado (por defecto 'VENTA_OK')
    estado_choice = form.initial.get('estado_documento', 'VENTA_OK')
    
    # Q() para construir filtros dinámicamente
    common_filters_q = Q()

    # Aplicar filtros si el formulario es válido
    if form.is_valid():
        estado_choice = form.cleaned_data.get('estado_documento', 'VENTA_OK')
        fecha_desde = form.cleaned_data.get('fecha_desde')
        fecha_hasta = form.cleaned_data.get('fecha_hasta')

        # Filtrado por rango de fechas
        if fecha_desde:
            common_filters_q &= (
                Q(año__gt=fecha_desde.year) |
                (Q(año=fecha_desde.year) & Q(mes_numero__gt=fecha_desde.month)) |
                (Q(año=fecha_desde.year) & Q(mes_numero=fecha_desde.month) & Q(dia__gte=fecha_desde.day))
            )
        if fecha_hasta:
            common_filters_q &= (
                Q(año__lt=fecha_hasta.year) |
                (Q(año=fecha_hasta.year) & Q(mes_numero__lt=fecha_hasta.month)) |
                (Q(año=fecha_hasta.year) & Q(mes_numero=fecha_hasta.month) & Q(dia__lte=fecha_hasta.day))
            )
        # Filtrado por ciudad, vendedor y marca
        if form.cleaned_data.get('ciudad'):
            common_filters_q &= Q(ciudad=form.cleaned_data.get('ciudad'))
        if form.cleaned_data.get('vendedor'):
            common_filters_q &= Q(vendedor=form.cleaned_data.get('vendedor'))
        if form.cleaned_data.get('marca'):
            common_filters_q &= Q(marca=form.cleaned_data.get('marca'))
    
    # Aplicar filtros comunes a los querysets de dashboard y rechazos
    dashboard_data_for_processing = base_dashboard_qs.filter(common_filters_q)
    rechazos_data_for_processing = base_rechazos_qs.filter(common_filters_q)

    table_queryset = None
    dfs_para_graficos = []
    # Columnas por defecto para la tabla de Dashboard
    column_names = ['factura', 'ciudad', 'cliente', 'vendedor', 'marca', 'display', 'litros', 'monto']

    # Lógica para filtrar y preparar datos según el estado del documento
    if estado_choice == 'VENTA_OK':
        table_queryset = dashboard_data_for_processing.filter(es_rechazado=False)
        df_temp = pd.DataFrame(list(table_queryset.values('ciudad', 'marca', 'display')))
        if not df_temp.empty:
            df_temp['tipo'] = 'Ventas Puras'
            dfs_para_graficos.append(df_temp)
    elif estado_choice == 'CON_RECHAZO':
        table_queryset = dashboard_data_for_processing.filter(es_rechazado=True)
        df_temp = pd.DataFrame(list(table_queryset.values('ciudad', 'marca', 'display')))
        if not df_temp.empty:
            df_temp['tipo'] = 'Ventas con Rechazo'
            dfs_para_graficos.append(df_temp)
    elif estado_choice == 'SOLO_RECHAZOS':
        table_queryset = rechazos_data_for_processing
        df_temp = pd.DataFrame(list(table_queryset.values('ciudad', 'marca', 'display')))
        if not df_temp.empty:
            df_temp['tipo'] = 'Rechazos'
            dfs_para_graficos.append(df_temp)
        # Cambiar las columnas para la tabla si se muestran solo rechazos
        column_names = ['factura', 'ciudad', 'motivo', 'cliente', 'vendedor', 'marca', 'display', 'litros', 'monto']
    elif estado_choice == '': # Si no hay estado seleccionado, se muestran todos los datos
        table_queryset = dashboard_data_for_processing
        df_vp = pd.DataFrame(list(dashboard_data_for_processing.filter(es_rechazado=False).values('ciudad', 'marca', 'display')))
        if not df_vp.empty:
            df_vp['tipo'] = 'Ventas Puras'
            dfs_para_graficos.append(df_vp)
        df_r = pd.DataFrame(list(rechazos_data_for_processing.values('ciudad', 'marca', 'display')))
        if not df_r.empty:
            df_r['tipo'] = 'Rechazos'
            dfs_para_graficos.append(df_r)
        if 'es_rechazado' not in column_names:
             column_names.append('es_rechazado') # Añadir 'es_rechazado' si se muestran todos los datos
    else: # Fallback por si acaso el estado_choice no es reconocido
        table_queryset = base_dashboard_qs.filter(common_filters_q).filter(es_rechazado=False) if form.is_valid() else base_dashboard_qs.filter(es_rechazado=False)
        df_temp = pd.DataFrame(list(table_queryset.values('ciudad', 'marca', 'display')))
        if not df_temp.empty:
            df_temp['tipo'] = 'Ventas Puras'
            dfs_para_graficos.append(df_temp)

    # Paginación de la tabla
    paginator = Paginator(table_queryset.order_by('-año', '-mes_numero', '-dia'), 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    # Concatenar DataFrames para gráficos si hay datos
    df_final_graficos = pd.DataFrame()
    if dfs_para_graficos:
        df_final_graficos = pd.concat(dfs_para_graficos, ignore_index=True)

    # Colores para los gráficos
    color_map = {
        'Ventas Puras': '#28a745', # Verde para ventas OK
        'Rechazos': '#dc3545',     # Rojo para rechazos
        'Ventas con Rechazo': '#fd7e14' # Naranja para ventas con rechazo
    }
    
    # Estilos para los gráficos (fondo claro)
    font_color_light_bg = "#333333"
    grid_color_light_bg = "rgba(200, 200, 200, 0.3)"
    plot_bgcolor_light = 'rgba(255,255,255,0)' # Transparente
    paper_bgcolor_light = 'rgba(255,255,255,0)' # Transparente

    # Generación del gráfico de Display por Ciudad
    chart_ciudad_html = ""
    if not df_final_graficos.empty and 'display' in df_final_graficos.columns and 'ciudad' in df_final_graficos.columns:
        df_chart_ciudad_data = df_final_graficos.groupby(['ciudad', 'tipo'], as_index=False)['display'].sum()
        if not df_chart_ciudad_data.empty:
            fig_ciudad = px.bar(df_chart_ciudad_data, x='ciudad', y='display', color='tipo',
                                 title='Display por Ciudad y Tipo', labels={'display': 'Total Display'},
                                 barmode='group', text_auto=True, color_discrete_map=color_map)
            fig_ciudad.update_layout(
                font_color=font_color_light_bg,
                plot_bgcolor=plot_bgcolor_light,
                paper_bgcolor=paper_bgcolor_light,
                xaxis=dict(gridcolor=grid_color_light_bg, linecolor=grid_color_light_bg, zerolinecolor=grid_color_light_bg, title_font_color=font_color_light_bg, tickfont_color=font_color_light_bg),
                yaxis=dict(gridcolor=grid_color_light_bg, linecolor=grid_color_light_bg, zerolinecolor=grid_color_light_bg, title_font_color=font_color_light_bg, tickfont_color=font_color_light_bg),
                legend_title_font_color=font_color_light_bg,
                legend_font_color=font_color_light_bg,
                title_font_color=font_color_light_bg,
                title_x=0.5, # Centrar título
                margin=dict(l=50, r=20, t=60, b=50)
            )
            fig_ciudad.update_traces(textfont_size=10, textangle=0, textposition="outside", cliponaxis=False)
            chart_ciudad_html = fig_ciudad.to_html(full_html=False, include_plotlyjs='cdn')
    
    # Generación del gráfico de Display por Marca (Top 15)
    chart_marca_html = ""
    if not df_final_graficos.empty and 'display' in df_final_graficos.columns and 'marca' in df_final_graficos.columns:
        df_chart_marca_data = df_final_graficos.groupby(['marca', 'tipo'], as_index=False)['display'].sum()
        summed_display_by_marca = df_chart_marca_data.groupby('marca')['display'].sum()
        numeric_summed_display = pd.to_numeric(summed_display_by_marca, errors='coerce').fillna(0)
        top_marcas = numeric_summed_display.nlargest(15).index # Seleccionar las 15 marcas principales
        df_chart_marca_data_top = df_chart_marca_data[df_chart_marca_data['marca'].isin(top_marcas)]
        if not df_chart_marca_data_top.empty:
            fig_marca = px.bar(df_chart_marca_data_top, x='marca', y='display', color='tipo',
                                 title='Display por Marca y Tipo (Top 15)', labels={'display': 'Total Display'},
                                 barmode='group', text_auto=".2s", color_discrete_map=color_map)
            fig_marca.update_layout(
                font_color=font_color_light_bg,
                plot_bgcolor=plot_bgcolor_light,
                paper_bgcolor=paper_bgcolor_light,
                xaxis=dict(gridcolor=grid_color_light_bg, linecolor=grid_color_light_bg, zerolinecolor=grid_color_light_bg, tickangle=-45, title_font_color=font_color_light_bg, tickfont_color=font_color_light_bg),
                yaxis=dict(gridcolor=grid_color_light_bg, linecolor=grid_color_light_bg, zerolinecolor=grid_color_light_bg, title_font_color=font_color_light_bg, tickfont_color=font_color_light_bg),
                legend_title_font_color=font_color_light_bg,
                legend_font_color=font_color_light_bg,
                title_font_color=font_color_light_bg,
                title_x=0.5, # Centrar título
                margin=dict(l=50, r=20, t=60, b=100) # Ajustar margen inferior para etiquetas de eje x
            )
            fig_marca.update_traces(textfont_size=10, textangle=0, textposition="outside", cliponaxis=False)
            chart_marca_html = fig_marca.to_html(full_html=False, include_plotlyjs='cdn')

    # Preparar encabezados de columna para la tabla HTML
    column_headers = [name.replace("_", " ").capitalize() for name in column_names]

    # Contexto para la plantilla
    context = {
        'form': form,
        'page_obj': page_obj,
        'total_rows': paginator.count,
        'column_headers': column_headers,
        'column_names_for_loop': column_names,
        'query_params': request.GET.urlencode(), # Para mantener los filtros al cambiar de página
        'chart_ciudad_html': chart_ciudad_html,
        'chart_marca_html': chart_marca_html,
    }
    return render(request, 'reportes/dashboard.html', context)

def reporte_rechazos_view(request):
    """
    Vista para el reporte específico de rechazos.
    Permite filtrar y paginar los datos de rechazos.
    """
    form = DashboardFilterForm(request.GET or None)
    datos_queryset = DatosRechazos.objects.all()

    # Anotar el número de mes para filtrar por rango de fechas
    month_whens = [When(mes=name, then=Value(num)) for name, num in MONTH_TO_NUMBER.items()]
    datos_queryset = datos_queryset.annotate(
        mes_numero=Case(*month_whens, default=Value(0), output_field=IntegerField())
    )
    
    common_filters_q = Q()
    if form.is_valid():
        fecha_desde = form.cleaned_data.get('fecha_desde')
        fecha_hasta = form.cleaned_data.get('fecha_hasta')

        # Filtrado por rango de fechas
        if fecha_desde:
            common_filters_q &= (
                Q(año__gt=fecha_desde.year) |
                (Q(año=fecha_desde.year) & Q(mes_numero__gt=fecha_desde.month)) |
                (Q(año=fecha_desde.year) & Q(mes_numero=fecha_desde.month) & Q(dia__gte=fecha_desde.day))
            )
        if fecha_hasta:
            common_filters_q &= (
                Q(año__lt=fecha_hasta.year) |
                (Q(año=fecha_hasta.year) & Q(mes_numero__lt=fecha_hasta.month)) |
                (Q(año=fecha_hasta.year) & Q(mes_numero=fecha_hasta.month) & Q(dia__lte=fecha_hasta.day))
            )
        # Filtrado por ciudad, vendedor y marca
        if form.cleaned_data.get('ciudad'):
            common_filters_q &= Q(ciudad=form.cleaned_data.get('ciudad'))
        if form.cleaned_data.get('vendedor'):
            common_filters_q &= Q(vendedor=form.cleaned_data.get('vendedor'))
        if form.cleaned_data.get('marca'):
            common_filters_q &= Q(marca=form.cleaned_data.get('marca'))
        
        datos_queryset = datos_queryset.filter(common_filters_q)

    # Paginación de la tabla de rechazos
    paginator = Paginator(datos_queryset.order_by('-año', '-mes_numero', '-dia'), 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Obtener nombres de columnas de DatosRechazos dinámicamente
    column_names_rechazos = [f.name for f in DatosRechazos._meta.get_fields() if f.name != 'id' and hasattr(DatosRechazos, f.name)]
    column_headers_rechazos = [name.replace("_", " ").capitalize() for name in column_names_rechazos]
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'total_rows': paginator.count,
        'column_headers': column_headers_rechazos,
        'column_names_for_loop': column_names_rechazos,
        'report_title': 'Reporte de Rechazos',
        'query_params': request.GET.urlencode(),
    }
    return render(request, 'reportes/rechazos.html', context)


def export_excel_consolidado_view(request):
    """
    Función para exportar datos a un archivo Excel consolidado.
    Genera dos hojas: 'Reporte de Ventas' y 'Reporte de Rechazos',
    aplicando los filtros del formulario.
    """
    form = DashboardFilterForm(request.GET or None)
    
    ventas_filters_q = Q() # Filtros para el queryset de ventas
    rechazos_filters_q = Q() # Filtros para el queryset de rechazos
    estado_documento_selected = None 

    if form.is_valid():
        fecha_desde = form.cleaned_data.get('fecha_desde')
        fecha_hasta = form.cleaned_data.get('fecha_hasta')
        ciudad = form.cleaned_data.get('ciudad')
        vendedor = form.cleaned_data.get('vendedor')
        marca = form.cleaned_data.get('marca')
        estado_documento_selected = form.cleaned_data.get('estado_documento')

        # Aplicar filtros de fecha a ambos querysets
        if fecha_desde:
            date_filter_q = (
                Q(año__gt=fecha_desde.year) |
                (Q(año=fecha_desde.year) & Q(mes_numero__gt=fecha_desde.month)) |
                (Q(año=fecha_desde.year) & Q(mes_numero=fecha_desde.month) & Q(dia__gte=fecha_desde.day))
            )
            ventas_filters_q &= date_filter_q
            rechazos_filters_q &= date_filter_q 
        if fecha_hasta:
            date_filter_q = (
                Q(año__lt=fecha_hasta.year) |
                (Q(año=fecha_hasta.year) & Q(mes_numero__lt=fecha_hasta.month)) |
                (Q(año=fecha_hasta.year) & Q(mes_numero=fecha_hasta.month) & Q(dia__lte=fecha_hasta.day))
            )
            ventas_filters_q &= date_filter_q
            rechazos_filters_q &= date_filter_q 

        # Aplicar filtros de ciudad, vendedor y marca a ambos querysets
        if ciudad:
            ventas_filters_q &= Q(ciudad=ciudad)
            rechazos_filters_q &= Q(ciudad=ciudad) 
        if vendedor:
            ventas_filters_q &= Q(vendedor=vendedor)
            rechazos_filters_q &= Q(vendedor=vendedor) 
        if marca:
            ventas_filters_q &= Q(marca=marca)
            rechazos_filters_q &= Q(marca=marca) 
    
    # Anotar el número de mes para ambos querysets
    month_whens = [When(mes=name, then=Value(num)) for name, num in MONTH_TO_NUMBER.items()]

    # --- Lógica para la hoja de VENTAS (DatosDashboard) ---
    dashboard_qs = DatosDashboard.objects.annotate(
        mes_numero=Case(*month_whens, default=Value(0), output_field=IntegerField()),
        es_rechazado=Exists(DatosRechazos.objects.filter(factura=OuterRef('factura')))
    ).filter(ventas_filters_q)

    # Aplicar el filtro de estado_documento solo a las VENTAS
    if estado_documento_selected == 'VENTA_OK':
        dashboard_qs = dashboard_qs.filter(es_rechazado=False)
    elif estado_documento_selected == 'CON_RECHAZO':
        dashboard_qs = dashboard_qs.filter(es_rechazado=True)
    elif estado_documento_selected == 'SOLO_RECHAZOS':
        # Si se selecciona 'SOLO_RECHAZOS', la hoja de ventas debe estar vacía
        dashboard_qs = DatosDashboard.objects.none() 

    # Obtener nombres de columnas para DatosDashboard
    dashboard_columns = [f.name for f in DatosDashboard._meta.get_fields() if f.name != 'id']
    if estado_documento_selected != 'SOLO_RECHAZOS':
        # Solo añadir 'es_rechazado' si no estamos en 'SOLO_RECHAZOS'
        dashboard_columns.append('es_rechazado')
    
    # Convertir queryset de dashboard a DataFrame
    df_dashboard = pd.DataFrame(list(dashboard_qs.values(*dashboard_columns)))
    
    # Renombrar la columna 'es_rechazado' si existe
    if 'Tuvo Rechazo Asociado' not in df_dashboard.columns and 'es_rechazado' in df_dashboard.columns:
        df_dashboard.rename(columns={'es_rechazado': 'Tuvo Rechazo Asociado'}, inplace=True)

    # --- Lógica para la hoja de RECHAZOS (DatosRechazos) ---
    rechazos_qs = DatosRechazos.objects.annotate(
        mes_numero=Case(*month_whens, default=Value(0), output_field=IntegerField())
    ).filter(rechazos_filters_q)
    
    # Si estado_documento_selected es 'VENTA_OK' o 'CON_RECHAZO', la hoja de rechazos debe estar vacía
    if estado_documento_selected in ['VENTA_OK', 'CON_RECHAZO']:
        rechazos_qs = DatosRechazos.objects.none()

    # Obtener nombres de columnas para DatosRechazos
    rechazos_columns = [f.name for f in DatosRechazos._meta.get_fields() if f.name != 'id']
    # Convertir queryset de rechazos a DataFrame
    df_rechazos = pd.DataFrame(list(rechazos_qs.values(*rechazos_columns)))
    
    # --- Manejo de fechas para eliminar timezone si existe (aplicado a ambos DataFrames) ---
    # Esto es importante para evitar errores al exportar a Excel con tz-aware datetimes
    for df_temp in [df_dashboard, df_rechazos]: 
        for col in df_temp.columns:
            if pd.api.types.is_datetime64_any_dtype(df_temp[col]):
                if hasattr(df_temp[col].dt, 'tz') and df_temp[col].dt.tz is not None:
                    df_temp[col] = df_temp[col].dt.tz_localize(None)
            elif df_temp[col].dtype == 'object':
                try:
                    converted_col = pd.to_datetime(df_temp[col], errors='coerce')
                    if hasattr(converted_col.dt, 'tz') and converted_col.dt.tz is not None:
                        df_temp[col] = converted_col.dt.tz_localize(None)
                except Exception:
                    pass # Ignorar si la conversión a datetime falla

    # Verificar si hay datos para exportar
    if df_dashboard.empty and df_rechazos.empty:
        messages.warning(request, "No hay datos para exportar con los filtros seleccionados.")
        return redirect('dashboard') 
    
    # Crear el archivo Excel en memoria
    excel_buffer = io.BytesIO()
    try:
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            if not df_dashboard.empty:
                df_dashboard.to_excel(writer, sheet_name='Reporte de Ventas', index=False)
            
            if not df_rechazos.empty:
                df_rechazos.to_excel(writer, sheet_name='Reporte de Rechazos', index=False)
        
    except Exception as e:
        messages.error(request, f"Ocurrió un error al generar el archivo Excel: {e}")
        return redirect('dashboard')
    
    # Preparar la respuesta HTTP para la descarga del archivo
    excel_buffer.seek(0) # Volver al inicio del buffer
    
    response = HttpResponse(excel_buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"reporte_consolidado_{date.today().strftime('%Y%m%d')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@login_required
def actualizar_datos_view(request):
    """
    Vista para iniciar la actualización de los datos del dashboard.
    Requiere que el usuario esté autenticado.
    """
    if request.method == 'POST':
        try:
            # Llama a un comando de Django para actualizar datos
            call_command('actualizar_dashboard_data')
            messages.success(request, '¡La actualización de datos ha comenzado! El proceso se ejecuta en segundo plano y puede tardar unos minutos.')
        except Exception as e:
            messages.error(request, f'Ocurrió un error al iniciar la actualización: {e}')
    return redirect('dashboard')


@require_POST # Asegura que esta vista solo responda a solicitudes POST
def export_report_email_view(request):
    """
    Vista para manejar la solicitud de envío de reporte por email.
    Recibe los filtros y la dirección de correo a través de POST (JSON).
    """
    try:
        # 1. Parsear los datos JSON del cuerpo de la solicitud
        data = json.loads(request.body)
        to_email = data.get('to_email')
        fecha_desde_str = data.get('fecha_desde')
        fecha_hasta_str = data.get('fecha_hasta')
        ciudad = data.get('ciudad')
        vendedor = data.get('vendedor')
        marca = data.get('marca')
        estado_documento = data.get('estado_documento')

        # --- Validación básica de datos ---
        if not to_email or not fecha_desde_str or not fecha_hasta_str:
            return JsonResponse({'status': 'error', 'message': 'Faltan datos requeridos (email, fechas).'}, status=400)

        # Convertir fechas de string a objetos date (asumiendo formato 'YYYY-MM-DD')
        try:
            fecha_desde = datetime.strptime(fecha_desde_str, '%Y-%m-%d').date()
            fecha_hasta = datetime.strptime(fecha_hasta_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Formato de fecha inválido. Usar YYYY-MM-DD.'}, status=400)


        # --- Lógica de Negocio: Preparar y Enviar el Correo ---
        # Reutilizar la lógica de filtrado de export_excel_consolidado_view
        ventas_filters_q = Q()
        rechazos_filters_q = Q()
        
        # Anotar el número de mes para ambos querysets
        month_whens = [When(mes=name, then=Value(num)) for name, num in MONTH_TO_NUMBER.items()]

        # Aplicar filtros de fecha
        date_filter_q = (
            Q(año__gt=fecha_desde.year) |
            (Q(año=fecha_desde.year) & Q(mes_numero__gt=fecha_desde.month)) |
            (Q(año=fecha_desde.year) & Q(mes_numero=fecha_desde.month) & Q(dia__gte=fecha_desde.day))
        )
        ventas_filters_q &= date_filter_q
        rechazos_filters_q &= date_filter_q 

        date_filter_q = (
            Q(año__lt=fecha_hasta.year) |
            (Q(año=fecha_hasta.year) & Q(mes_numero__lt=fecha_hasta.month)) |
            (Q(año=fecha_hasta.year) & Q(mes_numero=fecha_hasta.month) & Q(dia__lte=fecha_hasta.day))
        )
        ventas_filters_q &= date_filter_q
        rechazos_filters_q &= date_filter_q 

        # Aplicar filtros de ciudad, vendedor y marca
        if ciudad:
            ventas_filters_q &= Q(ciudad=ciudad)
            rechazos_filters_q &= Q(ciudad=ciudad) 
        if vendedor:
            ventas_filters_q &= Q(vendedor=vendedor)
            rechazos_filters_q &= Q(vendedor=vendedor) 
        if marca:
            ventas_filters_q &= Q(marca=marca)
            rechazos_filters_q &= Q(marca=marca) 

        # --- Generar DataFrames filtrados ---
        dashboard_qs = DatosDashboard.objects.annotate(
            mes_numero=Case(*month_whens, default=Value(0), output_field=IntegerField()),
            es_rechazado=Exists(DatosRechazos.objects.filter(factura=OuterRef('factura')))
        ).filter(ventas_filters_q)

        if estado_documento == 'VENTA_OK':
            dashboard_qs = dashboard_qs.filter(es_rechazado=False)
        elif estado_documento == 'CON_RECHAZO':
            dashboard_qs = dashboard_qs.filter(es_rechazado=True)
        elif estado_documento == 'SOLO_RECHAZOS':
            dashboard_qs = DatosDashboard.objects.none() 

        dashboard_columns = [f.name for f in DatosDashboard._meta.get_fields() if f.name != 'id']
        if estado_documento != 'SOLO_RECHAZOS':
            dashboard_columns.append('es_rechazado')
        
        df_dashboard = pd.DataFrame(list(dashboard_qs.values(*dashboard_columns)))
        
        if 'Tuvo Rechazo Asociado' not in df_dashboard.columns and 'es_rechazado' in df_dashboard.columns:
            df_dashboard.rename(columns={'es_rechazado': 'Tuvo Rechazo Asociado'}, inplace=True)

        rechazos_qs = DatosRechazos.objects.annotate(
            mes_numero=Case(*month_whens, default=Value(0), output_field=IntegerField())
        ).filter(rechazos_filters_q)
        
        if estado_documento in ['VENTA_OK', 'CON_RECHAZO']:
            rechazos_qs = DatosRechazos.objects.none()

        rechazos_columns = [f.name for f in DatosRechazos._meta.get_fields() if f.name != 'id']
        df_rechazos = pd.DataFrame(list(rechazos_qs.values(*rechazos_columns)))
        
        # --- Manejo de fechas para eliminar timezone si existe ---
        for df_temp in [df_dashboard, df_rechazos]: 
            for col in df_temp.columns:
                if pd.api.types.is_datetime64_any_dtype(df_temp[col]):
                    if hasattr(df_temp[col].dt, 'tz') and df_temp[col].dt.tz is not None:
                        df_temp[col] = df_temp[col].dt.tz_localize(None)
                elif df_temp[col].dtype == 'object':
                    try:
                        converted_col = pd.to_datetime(df_temp[col], errors='coerce')
                        if hasattr(converted_col.dt, 'tz') and converted_col.dt.tz is not None:
                            df_temp[col] = converted_col.dt.tz_localize(None)
                    except Exception:
                        pass # Ignorar si la conversión a datetime falla


        if df_dashboard.empty and df_rechazos.empty:
            return JsonResponse({'status': 'info', 'message': 'No hay datos para enviar por correo con los filtros seleccionados.'})

        # Crear el archivo Excel en memoria
        excel_buffer = io.BytesIO()
        try:
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                if not df_dashboard.empty:
                    df_dashboard.to_excel(writer, sheet_name='Reporte de Ventas', index=False)
                
                if not df_rechazos.empty:
                    df_rechazos.to_excel(writer, sheet_name='Reporte de Rechazos', index=False)
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Ocurrió un error al generar el archivo Excel para el email: {e}'}, status=500)
        
        excel_buffer.seek(0) # Volver al inicio del buffer

        # --- Enviar el correo electrónico ---
        subject = f"Reporte Consolidado ISM ({fecha_desde_str} a {fecha_hasta_str})"
        body = (
            f"Estimado(a) usuario(a),\n\n"
            f"Adjunto encontrará el reporte consolidado de Ventas y Rechazos con los siguientes filtros:\n"
            f"  Fecha Desde: {fecha_desde_str}\n"
            f"  Fecha Hasta: {fecha_hasta_str}\n"
            f"  Ciudad: {ciudad if ciudad else 'Todas'}\n"
            f"  Vendedor: {vendedor if vendedor else 'Todos'}\n"
            f"  Marca: {marca if marca else 'Todas'}\n"
            f"  Estado Documento: {estado_documento if estado_documento else 'Todos'}\n\n"
            f"Saludos cordiales,\n"
            f"Equipo de Reportes ISM"
        )
        
        # Asumiendo que settings.DEFAULT_FROM_EMAIL está configurado en tu settings.py
        email = EmailMessage(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL, # O una dirección de correo específica si lo deseas
            [to_email]
        )

        filename = f"Reporte_Consolidado_ISM_{fecha_desde_str}_{fecha_hasta_str}.xlsx"
        email.attach(filename, excel_buffer.read(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
        email.send()

        # 2. Devolver una respuesta JSON de éxito
        return JsonResponse({'status': 'success', 'message': f'El reporte ha sido enviado exitosamente a {to_email}.'})

    except json.JSONDecodeError:
        # Error si el cuerpo de la solicitud no es un JSON válido
        return JsonResponse({'status': 'error', 'message': 'Solicitud JSON inválida.'}, status=400)
    except Exception as e:
        # Captura cualquier otro error durante el proceso
        print(f"ERROR en export_report_email_view: {e}") # Log del error para depuración
        return JsonResponse({'status': 'error', 'message': f'Ocurrió un error inesperado al enviar el email: {str(e)}'}, status=500)