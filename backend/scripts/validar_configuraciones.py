"""
Script de validación de configuraciones BooleanField
Verifica que todos los valores por defecto sean correctos
"""
import os
import sys
import django

# Agregar el directorio backend al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.development')
django.setup()

from apps.core.models import Tarjetas, TarjetasAutorizacion, MediosPago, ConfiguracionSistema, CacheConfiguracion
from apps.almuerzos.models import TiposAlmuerzo, RegistrosConsumoAlmuerzo, ProductosAlergenos


def validar_configuraciones():
    """Valida que todos los BooleanFields tengan los defaults correctos"""
    
    print("=" * 70)
    print("VALIDACIÓN DE CONFIGURACIONES BOOLEANFIELD")
    print("=" * 70)
    print()
    
    errores = []
    ok = []
    
    # Tarjetas
    print("📋 MÓDULO CORE - TARJETAS")
    print("-" * 70)
    
    field = Tarjetas._meta.get_field('permite_saldo_negativo')
    expected = False
    if field.default == expected:
        ok.append(f"✅ Tarjetas.permite_saldo_negativo = {expected}")
    else:
        errores.append(f"❌ Tarjetas.permite_saldo_negativo debe ser {expected}, es {field.default}")
    
    field = Tarjetas._meta.get_field('notificar_saldo_bajo')
    expected = True
    if field.default == expected:
        ok.append(f"✅ Tarjetas.notificar_saldo_bajo = {expected}")
    else:
        errores.append(f"❌ Tarjetas.notificar_saldo_bajo debe ser {expected}, es {field.default}")
    
    # TarjetasAutorizacion
    print("📋 MÓDULO CORE - TARJETAS AUTORIZACIÓN")
    print("-" * 70)
    
    permisos = [
        'puede_anular_almuerzos',
        'puede_anular_ventas',
        'puede_anular_recargas',
        'puede_modificar_precios'
    ]
    
    for permiso in permisos:
        field = TarjetasAutorizacion._meta.get_field(permiso)
        expected = False
        if field.default == expected:
            ok.append(f"✅ TarjetasAutorizacion.{permiso} = {expected}")
        else:
            errores.append(f"❌ TarjetasAutorizacion.{permiso} debe ser {expected}, es {field.default}")
    
    # MediosPago
    print("📋 MÓDULO CORE - MEDIOS DE PAGO")
    print("-" * 70)
    
    field = MediosPago._meta.get_field('genera_comision')
    expected = False
    if field.default == expected:
        ok.append(f"✅ MediosPago.genera_comision = {expected}")
    else:
        errores.append(f"❌ MediosPago.genera_comision debe ser {expected}, es {field.default}")
    
    field = MediosPago._meta.get_field('requiere_validacion')
    expected = False
    if field.default == expected:
        ok.append(f"✅ MediosPago.requiere_validacion = {expected}")
    else:
        errores.append(f"❌ MediosPago.requiere_validacion debe ser {expected}, es {field.default}")
    
    # ConfiguracionSistema
    print("📋 MÓDULO CORE - CONFIGURACIÓN SISTEMA")
    print("-" * 70)
    
    configs = [
        ('requerido', False),
        ('requiere_reinicio', False),
        ('solo_superuser', False)
    ]
    
    for nombre, expected in configs:
        field = ConfiguracionSistema._meta.get_field(nombre)
        if field.default == expected:
            ok.append(f"✅ ConfiguracionSistema.{nombre} = {expected}")
        else:
            errores.append(f"❌ ConfiguracionSistema.{nombre} debe ser {expected}, es {field.default}")
    
    # CacheConfiguracion
    print("📋 MÓDULO CORE - CACHE")
    print("-" * 70)
    
    field = CacheConfiguracion._meta.get_field('auto_invalidate')
    expected = True
    if field.default == expected:
        ok.append(f"✅ CacheConfiguracion.auto_invalidate = {expected}")
    else:
        errores.append(f"❌ CacheConfiguracion.auto_invalidate debe ser {expected}, es {field.default}")
    
    # TiposAlmuerzo
    print("📋 MÓDULO ALMUERZOS - TIPOS")
    print("-" * 70)
    
    tipos_configs = [
        ('incluye_plato_principal', True),
        ('incluye_postre', False),
        ('incluye_bebida', False)
    ]
    
    for nombre, expected in tipos_configs:
        field = TiposAlmuerzo._meta.get_field(nombre)
        if field.default == expected:
            ok.append(f"✅ TiposAlmuerzo.{nombre} = {expected}")
        else:
            errores.append(f"❌ TiposAlmuerzo.{nombre} debe ser {expected}, es {field.default}")
    
    # RegistrosConsumoAlmuerzo
    print("📋 MÓDULO ALMUERZOS - REGISTROS")
    print("-" * 70)
    
    field = RegistrosConsumoAlmuerzo._meta.get_field('marcado_en_cuenta')
    expected = False
    if field.default == expected:
        ok.append(f"✅ RegistrosConsumoAlmuerzo.marcado_en_cuenta = {expected}")
    else:
        errores.append(f"❌ RegistrosConsumoAlmuerzo.marcado_en_cuenta debe ser {expected}, es {field.default}")
    
    # ProductosAlergenos
    print("📋 MÓDULO ALMUERZOS - ALÉRGENOS")
    print("-" * 70)
    
    field = ProductosAlergenos._meta.get_field('contiene')
    expected = True
    if field.default == expected:
        ok.append(f"✅ ProductosAlergenos.contiene = {expected}")
    else:
        errores.append(f"❌ ProductosAlergenos.contiene debe ser {expected}, es {field.default}")
    
    # Resumen
    print()
    print("=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print()
    
    for msg in ok:
        print(msg)
    
    if errores:
        print()
        print("⚠️  ERRORES ENCONTRADOS:")
        for error in errores:
            print(error)
        print()
        print(f"Total: {len(ok)} OK, {len(errores)} errores")
        return False
    else:
        print()
        print(f"✅ TODAS LAS CONFIGURACIONES SON CORRECTAS ({len(ok)} validaciones)")
        return True


# Ejecutar validación
validar_configuraciones()
