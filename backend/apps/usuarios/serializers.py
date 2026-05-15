"""
Serializers para la app usuarios
"""

from rest_framework import serializers

from .models import (
    Usuario,
    Empleado,
    Rol,
    Permiso,
    RolPermiso,
    PerfilUsuario,
)


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = [
            "id",
            "email",
            "nombre",
            "apellido",
            "rol",
            "nombre_completo",
            "is_active",
            "ultimo_acceso",
        ]
        read_only_fields = ["fecha_creacion", "ultimo_acceso"]


class UsuarioCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = Usuario
        fields = ["email", "nombre", "apellido", "rol", "password", "is_active"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = Usuario(**validated_data)
        user.set_password(password)
        user.save()
        return user


class EmpleadoSerializer(serializers.ModelSerializer):
    rol_nombre = serializers.CharField(source="id_rol.nombre_rol", read_only=True)

    class Meta:
        model = Empleado
        fields = "__all__"


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = "__all__"


class PermisoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permiso
        fields = "__all__"
        read_only_fields = ["fecha_creacion"]


class RolPermisoSerializer(serializers.ModelSerializer):
    rol_nombre = serializers.CharField(source="id_rol.nombre_rol", read_only=True)
    permiso_codigo = serializers.CharField(source="id_permiso.codigo_permiso", read_only=True)

    class Meta:
        model = RolPermiso
        fields = "__all__"
        read_only_fields = ["fecha_asignacion"]


class PerfilUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilUsuario
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]