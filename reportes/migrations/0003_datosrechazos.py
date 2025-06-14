# Generated by Django 4.2.21 on 2025-05-27 00:02

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reportes", "0002_alter_datosdashboard_options_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="DatosRechazos",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("pais", models.CharField(blank=True, max_length=50, null=True)),
                ("ciudad", models.CharField(blank=True, max_length=100, null=True)),
                ("fecha_dato", models.DateField(blank=True, db_index=True, null=True)),
                ("dia", models.IntegerField(blank=True, null=True)),
                ("mes", models.CharField(blank=True, max_length=50, null=True)),
                ("año", models.IntegerField(blank=True, null=True)),
                (
                    "estado_documento",
                    models.CharField(
                        blank=True, db_index=True, max_length=50, null=True
                    ),
                ),
                ("cliente", models.CharField(blank=True, max_length=255, null=True)),
                ("direccion", models.CharField(blank=True, max_length=255, null=True)),
                ("sucursal", models.CharField(blank=True, max_length=100, null=True)),
                (
                    "ruta_cliente",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "vendedor",
                    models.CharField(
                        blank=True, db_index=True, max_length=100, null=True
                    ),
                ),
                (
                    "distribuidor",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "marca",
                    models.CharField(
                        blank=True, db_index=True, max_length=100, null=True
                    ),
                ),
                ("categoria", models.CharField(blank=True, max_length=100, null=True)),
                ("formato", models.CharField(blank=True, max_length=100, null=True)),
                ("sabor", models.CharField(blank=True, max_length=100, null=True)),
                (
                    "display_cajas",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=18, null=True
                    ),
                ),
                (
                    "litros",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=18, null=True
                    ),
                ),
                ("ultima_actualizacion_carga", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Dato de Rechazo/Venta Detallada",
                "verbose_name_plural": "Datos de Rechazos/Ventas Detalladas",
                "ordering": ["-fecha_dato", "estado_documento", "ciudad"],
            },
        ),
    ]
