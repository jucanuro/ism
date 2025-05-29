from django import forms
from datetime import date, timedelta
from .models import DatosDashboard, DatosRechazos

class DashboardFilterForm(forms.Form):
    fecha_desde = forms.DateField(
        label='Fecha Desde',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'})
    )
    fecha_hasta = forms.DateField(
        label='Fecha Hasta',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'})
    )
    
    ciudad = forms.ChoiceField(
        label='Ciudad',
        choices=[('', 'Todas las Ciudades'), ('ARICA', 'Arica'), ('IQUIQUE', 'Iquique')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )

    vendedor = forms.ChoiceField(
        label='Vendedor',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    marca = forms.ChoiceField(
        label='Marca',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )

    # Este campo representa la INTENCIÓN del usuario, no un campo de la BD directamente.
    # La lógica de filtrado se aplicará en la vista.
    estado_documento = forms.ChoiceField(
        label='Tipo de Visualización',
        choices=[
            ('VENTA_OK', 'Ventas'), 
            ('SOLO_RECHAZOS', 'Rechazos'), # <--- NUEVA OPCIÓN
            ('', 'Ventas y Rechazos'), 
        ], 
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        initial='VENTA_OK' 
    )
    

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Establecer fechas por defecto si el formulario no se ha enviado
        if not self.is_bound:
            self.initial['fecha_desde'] = date(date.today().year, 1, 1)
            self.initial['fecha_hasta'] = date.today()
        
        # Cargar opciones dinámicas para Vendedores y Marcas desde el modelo principal
        try:
            vendedores_qs = DatosDashboard.objects.order_by('vendedor').values_list('vendedor', flat=True).distinct()
            vendedor_choices = [('', 'Todos los Vendedores')] + [(v, v) for v in vendedores_qs if v]
            self.fields['vendedor'].choices = vendedor_choices

            marcas_qs = DatosDashboard.objects.order_by('marca').values_list('marca', flat=True).distinct()
            marca_choices = [('', 'Todas las Marcas')] + [(m, m) for m in marcas_qs if m]
            self.fields['marca'].choices = marca_choices
        except Exception as e:
            # Esto puede fallar si la BD está vacía. Es importante manejarlo.
            print(f"Advertencia: No se pudieron cargar opciones para el formulario (la BD podría estar vacía): {e}")
            self.fields['vendedor'].choices = [('', 'Todos los Vendedores')]
            self.fields['marca'].choices = [('', 'Todas las Marcas')]