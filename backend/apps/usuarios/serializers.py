"""
Serializers para la app usuarios
"""

from rest_framework import serializers

from apps.clientes.models import Cliente

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
            "cliente_id",
            "is_active",
            "ultimo_acceso",
        ]
        read_only_fields = ["fecha_creacion", "ultimo_acceso"]


class UsuarioCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    cliente = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Usuario
        fields = ["email", "nombre", "apellido", "rol", "password", "cliente", "is_active"]

    def validate(self, data):
        rol = data.get("rol")
        cliente = data.get("cliente")
        if rol == Usuario.Rol.CLIENTE_WEB and not cliente:
            raise serializers.ValidationError(
                {"cliente": "Se requiere un cliente para usuarios con rol CLIENTE_WEB."}
            )
        if rol != Usuario.Rol.CLIENTE_WEB and cliente:
            raise serializers.ValidationError(
                {"cliente": "Solo usuarios CLIENTE_WEB pueden tener un cliente asociado."}
            )
        return data

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = Usuario(**validated_data)
        user.set_password(password)
        user.save()
        return user


class CambiarPasswordSerializer(serializers.Serializer):
    password_actual = serializers.CharField(write_only=True)
    password_nuevo = serializers.CharField(write_only=True, min_length=6)

    def validate_password_actual(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("La contraseña actual es incorrecta.")
        return value

    def validate(self, data):
        if data.get("password_nuevo") == data.get("password_actual"):
            raise serializers.ValidationError(
                {"password_nuevo": "La nueva contraseña debe ser diferente a la actual."}
            )
        return data


class RecuperarPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ConfirmarPasswordSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password_nuevo = serializers.CharField(write_only=True, min_length=6)


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