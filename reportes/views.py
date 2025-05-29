from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.management import call_command
from django.contrib.auth.decorators import login_required
from .models import DatosDashboard, DatosRechazos
from .forms import DashboardFilterForm
from django.db.models import Sum, Exists, OuterRef, Value, Case, When, IntegerField, Q
import pandas as pd
from datetime import date
from django.core.paginator import Paginator
from django.http import HttpResponse
import io
import plotly.express as px

MONTH_TO_NUMBER = {
    'ENERO': 1, 'FEBRERO': 2, 'MARZO': 3, 'ABRIL': 4, 'MAYO': 5, 'JUNIO': 6,
    'JULIO': 7, 'AGOSTO': 8, 'SEPTIEMBRE': 9, 'OCTUBRE': 10, 'NOVIEMBRE': 11, 'DICIEMBRE': 12
}

def dashboard(request):
    form = DashboardFilterForm(request.GET or None)
    
    base_dashboard_qs = DatosDashboard.objects.all()
    base_rechazos_qs = DatosRechazos.objects.all()

    month_whens = [When(mes=name, then=Value(num)) for name, num in MONTH_TO_NUMBER.items()]
    base_dashboard_qs = base_dashboard_qs.annotate(
        mes_numero=Case(*month_whens, default=Value(0), output_field=IntegerField())
    )
    base_rechazos_qs = base_rechazos_qs.annotate(
        mes_numero=Case(*month_whens, default=Value(0), output_field=IntegerField())
    )

    rechazos_factura_subquery = DatosRechazos.objects.filter(factura=OuterRef('factura'))
    base_dashboard_qs = base_dashboard_qs.annotate(es_rechazado=Exists(rechazos_factura_subquery))

    estado_choice = form.initial.get('estado_documento', 'VENTA_OK')
    
    common_filters_q = Q()

    if form.is_valid():
        estado_choice = form.cleaned_data.get('estado_documento', 'VENTA_OK')
        fecha_desde = form.cleaned_data.get('fecha_desde')
        fecha_hasta = form.cleaned_data.get('fecha_hasta')

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
        if form.cleaned_data.get('ciudad'):
            common_filters_q &= Q(ciudad=form.cleaned_data.get('ciudad'))
        if form.cleaned_data.get('vendedor'):
            common_filters_q &= Q(vendedor=form.cleaned_data.get('vendedor'))
        if form.cleaned_data.get('marca'):
            common_filters_q &= Q(marca=form.cleaned_data.get('marca'))
    
    dashboard_data_for_processing = base_dashboard_qs.filter(common_filters_q)
    rechazos_data_for_processing = base_rechazos_qs.filter(common_filters_q)

    table_queryset = None
    dfs_para_graficos = []
    column_names = ['factura', 'ciudad', 'cliente', 'vendedor', 'marca', 'display', 'litros', 'monto']

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
        column_names = ['factura', 'ciudad', 'motivo', 'cliente', 'vendedor', 'marca', 'display', 'litros', 'monto']
    elif estado_choice == '': 
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
             column_names.append('es_rechazado')
    else: 
        table_queryset = base_dashboard_qs.filter(common_filters_q).filter(es_rechazado=False) if form.is_valid() else base_dashboard_qs.filter(es_rechazado=False)
        df_temp = pd.DataFrame(list(table_queryset.values('ciudad', 'marca', 'display')))
        if not df_temp.empty:
            df_temp['tipo'] = 'Ventas Puras'
            dfs_para_graficos.append(df_temp)

    paginator = Paginator(table_queryset.order_by('-año', '-mes_numero', '-dia'), 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    df_final_graficos = pd.DataFrame()
    if dfs_para_graficos:
        df_final_graficos = pd.concat(dfs_para_graficos, ignore_index=True)

    color_map = {
        'Ventas Puras': '#28a745',
        'Rechazos': '#dc3545',
        'Ventas con Rechazo': '#fd7e14' 
    }
    
    font_color_light_bg = "#333333" # Color de fuente para fondos claros
    grid_color_light_bg = "rgba(200, 200, 200, 0.3)" # Color de grid sutil
    plot_bgcolor_light = 'rgba(255,255,255,0)' # Fondo del área de trazado transparente
    paper_bgcolor_light = 'rgba(255,255,255,0)' # Fondo del gráfico transparente (o #FFFFFF)

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
    
    chart_marca_html = ""
    if not df_final_graficos.empty and 'display' in df_final_graficos.columns and 'marca' in df_final_graficos.columns:
        df_chart_marca_data = df_final_graficos.groupby(['marca', 'tipo'], as_index=False)['display'].sum()
        summed_display_by_marca = df_chart_marca_data.groupby('marca')['display'].sum()
        numeric_summed_display = pd.to_numeric(summed_display_by_marca, errors='coerce').fillna(0)
        top_marcas = numeric_summed_display.nlargest(15).index
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
                margin=dict(l=50, r=20, t=60, b=100) 
            )
            fig_marca.update_traces(textfont_size=10, textangle=0, textposition="outside", cliponaxis=False)
            chart_marca_html = fig_marca.to_html(full_html=False, include_plotlyjs='cdn')

    column_headers = [name.replace("_", " ").capitalize() for name in column_names]

    context = {
        'form': form,
        'page_obj': page_obj,
        'total_rows': paginator.count,
        'column_headers': column_headers,
        'column_names_for_loop': column_names,
        'query_params': request.GET.urlencode(),
        'chart_ciudad_html': chart_ciudad_html,
        'chart_marca_html': chart_marca_html,
    }
    return render(request, 'reportes/dashboard.html', context)

def reporte_rechazos_view(request):
    form = DashboardFilterForm(request.GET or None)
    datos_queryset = DatosRechazos.objects.all()

    month_whens = [When(mes=name, then=Value(num)) for name, num in MONTH_TO_NUMBER.items()]
    datos_queryset = datos_queryset.annotate(
        mes_numero=Case(*month_whens, default=Value(0), output_field=IntegerField())
    )
    
    common_filters_q = Q()
    if form.is_valid():
        fecha_desde = form.cleaned_data.get('fecha_desde')
        fecha_hasta = form.cleaned_data.get('fecha_hasta')

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
        if form.cleaned_data.get('ciudad'):
            common_filters_q &= Q(ciudad=form.cleaned_data.get('ciudad'))
        if form.cleaned_data.get('vendedor'):
            common_filters_q &= Q(vendedor=form.cleaned_data.get('vendedor'))
        if form.cleaned_data.get('marca'):
            common_filters_q &= Q(marca=form.cleaned_data.get('marca'))
        
        datos_queryset = datos_queryset.filter(common_filters_q)

    paginator = Paginator(datos_queryset.order_by('-año', '-mes_numero', '-dia'), 25)
    page_obj = paginator.get_page(request.GET.get('page'))

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

def export_excel_view(request):
    form = DashboardFilterForm(request.GET or None)
    
    estado_choice = form.initial.get('estado_documento', 'VENTA_OK')
    if form.is_valid():
        estado_choice = form.cleaned_data.get('estado_documento', 'VENTA_OK')

    export_queryset = None
    model_to_export = None
    df_values_columns = []
    filename_prefix = "reporte"

    common_filters_q = Q()
    if form.is_valid():
        fecha_desde = form.cleaned_data.get('fecha_desde')
        fecha_hasta = form.cleaned_data.get('fecha_hasta')
        if fecha_desde:
            common_filters_q &= ( Q(año__gt=fecha_desde.year) | (Q(año=fecha_desde.year) & Q(mes_numero__gt=fecha_desde.month)) | (Q(año=fecha_desde.year) & Q(mes_numero=fecha_desde.month) & Q(dia__gte=fecha_desde.day)) )
        if fecha_hasta:
            common_filters_q &= ( Q(año__lt=fecha_hasta.year) | (Q(año=fecha_hasta.year) & Q(mes_numero__lt=fecha_hasta.month)) | (Q(año=fecha_hasta.year) & Q(mes_numero=fecha_hasta.month) & Q(dia__lte=fecha_hasta.day)) )
        if form.cleaned_data.get('ciudad'):
            common_filters_q &= Q(ciudad=form.cleaned_data.get('ciudad'))
        if form.cleaned_data.get('vendedor'):
            common_filters_q &= Q(vendedor=form.cleaned_data.get('vendedor'))
        if form.cleaned_data.get('marca'):
            common_filters_q &= Q(marca=form.cleaned_data.get('marca'))

    month_whens = [When(mes=name, then=Value(num)) for name, num in MONTH_TO_NUMBER.items()]

    if estado_choice == 'SOLO_RECHAZOS':
        model_to_export = DatosRechazos
        base_qs = DatosRechazos.objects.annotate(mes_numero=Case(*month_whens, default=Value(0), output_field=IntegerField()))
        export_queryset = base_qs.filter(common_filters_q)
        df_values_columns = [f.name for f in DatosRechazos._meta.get_fields() if f.name != 'id']
        filename_prefix = "reporte_rechazos_filtrado"
    else:
        model_to_export = DatosDashboard
        base_qs = DatosDashboard.objects.annotate(
            mes_numero=Case(*month_whens, default=Value(0), output_field=IntegerField()),
            es_rechazado=Exists(DatosRechazos.objects.filter(factura=OuterRef('factura')))
        )
        filtered_dashboard_qs = base_qs.filter(common_filters_q)

        if estado_choice == 'VENTA_OK':
            export_queryset = filtered_dashboard_qs.filter(es_rechazado=False)
            filename_prefix = "reporte_ventas_puras"
        elif estado_choice == 'CON_RECHAZO':
            export_queryset = filtered_dashboard_qs.filter(es_rechazado=True)
            filename_prefix = "reporte_ventas_con_rechazo"
        elif estado_choice == '': 
            export_queryset = filtered_dashboard_qs
            filename_prefix = "reporte_ventas_todas"
        else: 
            export_queryset = filtered_dashboard_qs.filter(es_rechazado=False) if form.is_valid() else base_qs.filter(common_filters_q).filter(es_rechazado=False)
            filename_prefix = "reporte_ventas_puras_default"
        
        df_values_columns = [f.name for f in DatosDashboard._meta.get_fields() if f.name != 'id']
        if estado_choice == '': 
            df_values_columns.append('es_rechazado')

    if export_queryset is None or not export_queryset.exists():
        messages.warning(request, "No hay datos para exportar con los filtros seleccionados.")
        return redirect('dashboard')

    df_export = pd.DataFrame(list(export_queryset.values(*df_values_columns)))

    if estado_choice == '' and 'es_rechazado' in df_export.columns:
        df_export.rename(columns={'es_rechazado': 'Tuvo Rechazo Asociado'}, inplace=True)
    
    for col in df_export.columns:
        if pd.api.types.is_datetime64_any_dtype(df_export[col]):
            if hasattr(df_export[col].dt, 'tz') and df_export[col].dt.tz is not None:
                df_export[col] = df_export[col].dt.tz_localize(None)
        elif df_export[col].dtype == 'object':
            try:
                converted_col = pd.to_datetime(df_export[col], errors='coerce')
                if hasattr(converted_col.dt, 'tz') and converted_col.dt.tz is not None:
                    df_export[col] = converted_col.dt.tz_localize(None)
            except Exception:
                pass

    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df_export.to_excel(writer, sheet_name=filename_prefix.replace("_", " ").title()[:31], index=False)
    excel_buffer.seek(0)

    response = HttpResponse(excel_buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{date.today().strftime("%Y%m%d")}.xlsx"'
    return response

def export_rechazos_excel_view(request):
    form = DashboardFilterForm(request.GET or None)
    datos_queryset = DatosRechazos.objects.all()

    month_whens = [When(mes=name, then=Value(num)) for name, num in MONTH_TO_NUMBER.items()]
    datos_queryset = datos_queryset.annotate(
        mes_numero=Case(*month_whens, default=Value(0), output_field=IntegerField())
    )
    
    common_filters_rechazos = Q()
    if form.is_valid():
        fecha_desde = form.cleaned_data.get('fecha_desde')
        fecha_hasta = form.cleaned_data.get('fecha_hasta')

        if fecha_desde:
            common_filters_rechazos &= (
                Q(año__gt=fecha_desde.year) |
                (Q(año=fecha_desde.year) & Q(mes_numero__gt=fecha_desde.month)) |
                (Q(año=fecha_desde.year) & Q(mes_numero=fecha_desde.month) & Q(dia__gte=fecha_desde.day))
            )
        if fecha_hasta:
            common_filters_rechazos &= (
                Q(año__lt=fecha_hasta.year) |
                (Q(año=fecha_hasta.year) & Q(mes_numero__lt=fecha_hasta.month)) |
                (Q(año=fecha_hasta.year) & Q(mes_numero=fecha_hasta.month) & Q(dia__lte=fecha_hasta.day))
            )
        if form.cleaned_data.get('ciudad'):
            common_filters_rechazos &= Q(ciudad=form.cleaned_data.get('ciudad'))
        if form.cleaned_data.get('vendedor'):
            common_filters_rechazos &= Q(vendedor=form.cleaned_data.get('vendedor'))
        if form.cleaned_data.get('marca'):
            common_filters_rechazos &= Q(marca=form.cleaned_data.get('marca'))
        
        datos_queryset = datos_queryset.filter(common_filters_rechazos)

    columnas_export = [f.name for f in DatosRechazos._meta.get_fields() if f.name != 'id']
    df_export = pd.DataFrame(list(datos_queryset.values(*columnas_export)))

    if df_export.empty:
        messages.warning(request, "No hay datos de rechazos para exportar con los filtros seleccionados.")
        return redirect('reporte_rechazos_view') 
    
    for col in df_export.columns:
        if pd.api.types.is_datetime64_any_dtype(df_export[col]):
            if hasattr(df_export[col].dt, 'tz') and df_export[col].dt.tz is not None:
                df_export[col] = df_export[col].dt.tz_localize(None)
        elif df_export[col].dtype == 'object':
            try:
                converted_col = pd.to_datetime(df_export[col], errors='coerce')
                if hasattr(converted_col.dt, 'tz') and converted_col.dt.tz is not None:
                    df_export[col] = converted_col.dt.tz_localize(None)
            except Exception:
                pass

    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df_export.to_excel(writer, sheet_name='ReporteRechazos', index=False)
    excel_buffer.seek(0)
    
    response = HttpResponse(
        excel_buffer,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    nombre_archivo_descarga = f"reporte_rechazos_{date.today().strftime('%Y%m%d')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo_descarga}"'
    return response

@login_required
def actualizar_datos_view(request):
    if request.method == 'POST':
        try:
            call_command('actualizar_dashboard_data')
            messages.success(request, '¡La actualización de datos ha comenzado! El proceso se ejecuta en segundo plano y puede tardar unos minutos.')
        except Exception as e:
            messages.error(request, f'Ocurrió un error al iniciar la actualización: {e}')
    return redirect('dashboard')