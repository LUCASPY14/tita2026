"""
Script de configuración para POS Bancard
Ejecuta desde Django ORM
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.development')
django.setup()

from apps.core.models import MediosPago
from apps.contabilidad.models import TarifasComision
from django.utils import timezone
from decimal import Decimal

def configurar_bancard():
    """Configura medios de pago y tarifas Bancard"""
    
    print("="*70)
    print("CONFIGURACIÓN POS BANCARD - Comisiones")
    print("="*70)
    
    # 1. Crear Tarjeta Débito Bancard
    print("\n1. Creando medio de pago: Tarjeta Débito Bancard...")
    debito, created = MediosPago.objects.get_or_create(
        descripcion='Tarjeta Débito Bancard',
        defaults={
            'genera_comision': True,
            'requiere_validacion': True,
            'activo': True
        }
    )
    if created:
        print(f"   ✅ Creado: {debito.descripcion} (ID: {debito.id_medio_pago})")
    else:
        print(f"   ℹ️  Ya existe: {debito.descripcion} (ID: {debito.id_medio_pago})")
    
    # 2. Crear Tarjeta Crédito Bancard
    print("\n2. Creando medio de pago: Tarjeta Crédito Bancard...")
    credito, created = MediosPago.objects.get_or_create(
        descripcion='Tarjeta Crédito Bancard',
        defaults={
            'genera_comision': True,
            'requiere_validacion': True,
            'activo': True
        }
    )
    if created:
        print(f"   ✅ Creado: {credito.descripcion} (ID: {credito.id_medio_pago})")
    else:
        print(f"   ℹ️  Ya existe: {credito.descripcion} (ID: {credito.id_medio_pago})")
    
    # 3. Configurar tarifa Débito: 3.4%
    print("\n3. Configurando tarifa Débito: 3.4%...")
    tarifa_debito, created = TarifasComision.objects.get_or_create(
        id_medio_pago=debito,
        activo=True,
        fecha_fin_vigencia__isnull=True,
        defaults={
            'fecha_inicio_vigencia': timezone.now(),
            'porcentaje_comision': Decimal('0.0340'),
            'monto_fijo_comision': None
        }
    )
    if created:
        print(f"   ✅ Tarifa creada: {tarifa_debito.porcentaje_comision * 100}% (ID: {tarifa_debito.id_tarifa})")
    else:
        print(f"   ℹ️  Tarifa existente: {tarifa_debito.porcentaje_comision * 100}% (ID: {tarifa_debito.id_tarifa})")
    
    # 4. Configurar tarifa Crédito: 5.3%
    print("\n4. Configurando tarifa Crédito: 5.3%...")
    tarifa_credito, created = TarifasComision.objects.get_or_create(
        id_medio_pago=credito,
        activo=True,
        fecha_fin_vigencia__isnull=True,
        defaults={
            'fecha_inicio_vigencia': timezone.now(),
            'porcentaje_comision': Decimal('0.0530'),
            'monto_fijo_comision': None
        }
    )
    if created:
        print(f"   ✅ Tarifa creada: {tarifa_credito.porcentaje_comision * 100}% (ID: {tarifa_credito.id_tarifa})")
    else:
        print(f"   ℹ️  Tarifa existente: {tarifa_credito.porcentaje_comision * 100}% (ID: {tarifa_credito.id_tarifa})")
    
    # 5. Prueba de cálculo
    print("\n" + "="*70)
    print("PRUEBAS DE CÁLCULO")
    print("="*70)
    
    monto_prueba = Decimal('10000')
    
    print(f"\n📊 Venta de prueba: Gs. {monto_prueba:,.0f}")
    print(f"\n   DÉBITO ({tarifa_debito.porcentaje_comision * 100}%):")
    comision_debito = monto_prueba * tarifa_debito.porcentaje_comision
    print(f"   • Comisión: Gs. {comision_debito:,.0f}")
    print(f"   • Total cobrar cliente: Gs. {monto_prueba + comision_debito:,.0f}")
    print(f"   • Factura emitida: Gs. {monto_prueba:,.0f} (solo productos)")
    print(f"   • Recargo POS: Gs. {comision_debito:,.0f} (no facturado)")
    
    print(f"\n   CRÉDITO ({tarifa_credito.porcentaje_comision * 100}%):")
    comision_credito = monto_prueba * tarifa_credito.porcentaje_comision
    print(f"   • Comisión: Gs. {comision_credito:,.0f}")
    print(f"   • Total cobrar cliente: Gs. {monto_prueba + comision_credito:,.0f}")
    print(f"   • Factura emitida: Gs. {monto_prueba:,.0f} (solo productos)")
    print(f"   • Recargo POS: Gs. {comision_credito:,.0f} (no facturado)")
    
    print("\n" + "="*70)
    print("✅ CONFIGURACIÓN COMPLETADA EXITOSAMENTE")
    print("="*70)
    
    return {
        'debito': debito,
        'credito': credito,
        'tarifa_debito': tarifa_debito,
        'tarifa_credito': tarifa_credito
    }

if __name__ == '__main__':
    configurar_bancard()
