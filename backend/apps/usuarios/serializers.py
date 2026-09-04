"""
Serializers para la app usuarios
"""

from rest_framework import serializers

from apps.clientes.models import Cliente

from .models import (
    Usuario,
    Empleado,
    Rol,
)


class UsuarioSerializer(serializers.ModelSerializer):
    cliente_ruc_ci = serializers.SerializerMethodField()
    tiene_2fa_activo = serializers.SerializerMethodField()
    tiene_webauthn = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=False, min_length=6)

    def get_cliente_ruc_ci(self, obj):
        return obj.cliente.ruc_ci if obj.cliente_id else None

    def get_tiene_2fa_activo(self, obj):
        try:
            return bool(obj.auth_2fa.habilitado)
        except Exception:
            return False

    def get_tiene_webauthn(self, obj):
        return obj.credenciales_webauthn.exists()

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save(update_fields=["password"])
        return instance

    class Meta:
        model = Usuario
        fields = [
            "id_usuario",
            "email",
            "ci_ruc",
            "nombre",
            "apellido",
            "fecha_nacimiento",
            "rol",
            "nombre_completo",
            "cliente_id",
            "cliente_ruc_ci",
            "is_active",
            "ultimo_acceso",
            "password",
            "tiene_2fa_activo",
            "tiene_webauthn",
        ]
        read_only_fields = ["fecha_creacion", "ultimo_acceso", "cliente_ruc_ci", "tiene_2fa_activo", "tiene_webauthn"]


class UsuarioCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    cliente = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Usuario
        fields = ["email", "ci_ruc", "nombre", "apellido", "fecha_nacimiento", "rol", "password", "cliente", "is_active"]

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
        if rol != Usuario.Rol.CLIENTE_WEB and not data.get("ci_ruc"):
            raise serializers.ValidationError(
                {"ci_ruc": "El CI/RUC es obligatorio para roles internos: es lo que se usa para iniciar sesión."}
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
                {"password_nuevo": "La nueva contraseña debe ser diferente a la actual."}  # nosec B105
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
