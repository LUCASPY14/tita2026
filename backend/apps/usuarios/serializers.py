from rest_framework import serializers
from .models import Empleados, Roles, PerfilesUsuario, UsuariosPortal


class RolesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = '__all__'


class EmpleadosSerializer(serializers.ModelSerializer):
    rol_nombre = serializers.CharField(source='id_rol.nombre_rol', read_only=True)
    
    class Meta:
        model = Empleados
        fields = '__all__'
        extra_kwargs = {
            'contrasena_hash': {'write_only': True}
        }


class PerfilesUsuarioSerializer(serializers.ModelSerializer):
    empleado_nombre = serializers.CharField(source='id_empleado.nombre', read_only=True)
    
    class Meta:
        model = PerfilesUsuario
        fields = '__all__'


class UsuariosPortalSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source='id_cliente.nombre', read_only=True)
    
    class Meta:
        model = UsuariosPortal
        fields = '__all__'
        extra_kwargs = {
            'password_hash': {'write_only': True}
        }
