from django.db import models

class DatosDashboard(models.Model):
    pais = models.CharField(max_length=50, null=True, blank=True)
    ciudad = models.CharField(max_length=100, null=True, blank=True)
    dia = models.IntegerField(null=True, blank=True)
    mes = models.CharField(max_length=20, null=True, blank=True)
    año = models.IntegerField(null=True, blank=True)
    estado = models.CharField(max_length=50, null=True, blank=True)
    factura = models.CharField(max_length=100, null=True, blank=True)
    tipo = models.CharField(max_length=50, null=True, blank=True)
    motivo = models.CharField(max_length=100, null=True, blank=True)
    codigo_cliente = models.CharField(max_length=100, null=True, blank=True)
    cliente = models.CharField(max_length=255, null=True, blank=True)
    sucursal = models.CharField(max_length=100, null=True, blank=True)
    codigo_sucursal = models.CharField(max_length=200, null=True, blank=True)
    rut = models.CharField(max_length=20, null=True, blank=True)
    giro = models.CharField(max_length=100, null=True, blank=True)
    direccion = models.CharField(max_length=255, null=True, blank=True)
    ruta = models.CharField(max_length=100, null=True, blank=True)
    vendedor = models.CharField(max_length=100, null=True, blank=True)
    distribuidor = models.CharField(max_length=100, null=True, blank=True)
    categoria = models.CharField(max_length=100, null=True, blank=True)
    marca = models.CharField(max_length=100, null=True, blank=True)
    formato = models.CharField(max_length=100, null=True, blank=True)
    sabor = models.CharField(max_length=100, null=True, blank=True)
    com_distribuidor = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    com_vendedor = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    display = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    litros = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    neto = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    arancel = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    ila13 = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    bruto = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    monto = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    fecha_carga = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"Venta: {self.cliente} - {self.factura} ({self.año}-{self.mes}-{self.dia})"

    class Meta:
        verbose_name = "Dato de Venta"
        verbose_name_plural = "Datos de Ventas"
        ordering = ['-año', '-mes', '-dia']


class DatosRechazos(models.Model):
    pais = models.CharField(max_length=50, null=True, blank=True)
    ciudad = models.CharField(max_length=100, null=True, blank=True)
    dia = models.IntegerField(null=True, blank=True)
    mes = models.CharField(max_length=20, null=True, blank=True)
    año = models.IntegerField(null=True, blank=True)
    estado = models.CharField(max_length=50, null=True, blank=True)
    factura = models.CharField(max_length=100, null=True, blank=True)
    tipo = models.CharField(max_length=50, null=True, blank=True)
    motivo = models.CharField(max_length=100, null=True, blank=True)
    codigo_cliente = models.CharField(max_length=100, null=True, blank=True)
    cliente = models.CharField(max_length=255, null=True, blank=True)
    sucursal = models.CharField(max_length=100, null=True, blank=True)
    codigo_sucursal = models.CharField(max_length=200, null=True, blank=True)
    rut = models.CharField(max_length=20, null=True, blank=True)
    giro = models.CharField(max_length=100, null=True, blank=True)
    direccion = models.CharField(max_length=255, null=True, blank=True)
    ruta = models.CharField(max_length=100, null=True, blank=True)
    vendedor = models.CharField(max_length=100, null=True, blank=True)
    distribuidor = models.CharField(max_length=100, null=True, blank=True)
    categoria = models.CharField(max_length=100, null=True, blank=True)
    marca = models.CharField(max_length=100, null=True, blank=True)
    formato = models.CharField(max_length=100, null=True, blank=True)
    sabor = models.CharField(max_length=100, null=True, blank=True)
    com_distribuidor = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    com_vendedor = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    display = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    litros = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    neto = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    arancel = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    ila13 = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    bruto = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    monto = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    fecha_carga = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"Rechazo: {self.cliente} - {self.factura} ({self.año}-{self.mes}-{self.dia})"

    class Meta:
        verbose_name = "Dato de Rechazo"
        verbose_name_plural = "Datos de Rechazos"
        ordering = ['-año', '-mes', '-dia']