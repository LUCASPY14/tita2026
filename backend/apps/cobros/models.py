"""
Módulo de cobros

La lógica de pagos está unificada en:
- apps/ventas/models.py → PagoVenta (pagos de clientes)
- apps/compras/models.py → PagoProveedor (pagos a proveedores)

Este módulo contiene servicios, vistas y serializers para operaciones de cobro.
"""

# No se definen modelos aquí.
# Usar PagoVenta de apps.ventas para toda operación de cobro a clientes.