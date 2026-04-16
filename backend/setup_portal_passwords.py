"""
Script para establecer contraseñas conocidas a usuarios del portal para pruebas.

Uso:
    python manage.py shell < setup_portal_passwords.py
    
O desde Django shell:
    exec(open('setup_portal_passwords.py').read())
"""

from apps.usuarios.models import UsuariosPortal
from apps.core.models import Tarjetas, ConsumosTarjeta

# Contraseña por defecto para todos los usuarios portal de prueba
PASSWORD_DEFAULT = "Portal123!"

print("=" * 60)
print("CONFIGURACIÓN DE CONTRASEÑAS PARA USUARIOS PORTAL")
print("=" * 60)

usuarios = UsuariosPortal.objects.select_related('id_cliente').all()

if not usuarios.exists():
    print("\n❌ No hay usuarios portal registrados.")
    print("Ejecuta primero las fixtures o crea usuarios manualmente.\n")
else:
    print(f"\n✅ Encontrados {usuarios.count()} usuarios portal\n")
    print(f"📝 Estableciendo contraseña: {PASSWORD_DEFAULT}\n")
    
    for usuario in usuarios:
        # Establecer contraseña
        usuario.set_password(PASSWORD_DEFAULT)
        usuario.save(update_fields=['password_hash'])
        
        # Obtener información del cliente
        cliente = usuario.id_cliente
        hijos = cliente.hijos.all()
        
        print(f"✓ {usuario.email}")
        print(f"  Cliente: {cliente.nombre_completo} ({cliente.ruc_ci})")
        print(f"  Estado: {'✓ Activo' if usuario.estado else '✗ Inactivo'}")
        print(f"  Email verificado: {'✓ Sí' if usuario.email_verificado else '✗ No'}")
        print(f"  Crédito disponible: Gs. {cliente.credito_disponible:,.0f}")
        print(f"  Hijos: {hijos.count()}")
        
        for hijo in hijos:
            try:
                tarjeta = Tarjetas.objects.get(id_hijo=hijo)
                consumos_count = ConsumosTarjeta.objects.filter(nro_tarjeta=tarjeta).count()
                print(f"    → {hijo.nombre_completo}")
                print(f"      Tarjeta: {tarjeta.nro_tarjeta} | Saldo: Gs. {tarjeta.saldo_actual:,.0f}")
                print(f"      Consumos: {consumos_count} registros")
            except Tarjetas.DoesNotExist:
                print(f"    → {hijo.nombre_completo} (sin tarjeta)")
        
        print()
    
    print("=" * 60)
    print("RESUMEN DE CREDENCIALES")
    print("=" * 60)
    print(f"\nTodos los usuarios tienen la contraseña: {PASSWORD_DEFAULT}\n")
    print("CREDENCIALES PARA PRUEBAS:")
    print("-" * 60)
    for usuario in usuarios:
        print(f"Email:    {usuario.email}")
        print(f"Password: {PASSWORD_DEFAULT}")
        print(f"Cliente:  {usuario.id_cliente.nombre_completo}")
        print(f"Hijos:    {usuario.id_cliente.hijos.count()}")
        print("-" * 60)
    
    print("\n✅ Configuración completada!")
    print(f"Accede al portal en: http://localhost:3000/portal/login\n")
