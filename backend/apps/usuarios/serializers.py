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
    empleado_nombre = serializers.SerializerMethodField()
    tiene_2fa_activo = serializers.SerializerMethodField()
    tiene_webauthn = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=False, min_length=6)

    def get_cliente_ruc_ci(self, obj):
        return obj.cliente.ruc_ci if obj.cliente_id else None

    def get_empleado_nombre(self, obj):
        return f"{obj.empleado.nombre} {obj.empleado.apellido}" if obj.empleado_id else None

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
            "rol",
            "nombre_completo",
            "cliente_id",
            "cliente_ruc_ci",
            "empleado_id",
            "empleado_nombre",
            "is_active",
            "ultimo_acceso",
            "password",
            "tiene_2fa_activo",
            "tiene_webauthn",
        ]
        read_only_fields = [
            "fecha_creacion", "ultimo_acceso", "cliente_ruc_ci",
            "empleado_nombre", "tiene_2fa_activo", "tiene_webauthn",
        ]


class UsuarioCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    cliente = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.all(),
        required=False,
        allow_null=True,
    )
    empleado = serializers.PrimaryKeyRelatedField(
        queryset=Empleado.objects.all(),
        required=False,
        allow_null=True,
    )
    nombre = serializers.CharField(required=False, allow_blank=True)
    apellido = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Usuario
        fields = ["email", "ci_ruc", "nombre", "apellido", "rol", "password", "cliente", "empleado", "is_active"]

    def validate(self, data):
        rol = data.get("rol")
        cliente = data.get("cliente")
        empleado = data.get("empleado")
        if rol == Usuario.Rol.CLIENTE_WEB and not cliente:
            raise serializers.ValidationError(
                {"cliente": "Se requiere un cliente para usuarios con rol CLIENTE_WEB."}
            )
        if rol != Usuario.Rol.CLIENTE_WEB and cliente:
            raise serializers.ValidationError(
                {"cliente": "Solo usuarios CLIENTE_WEB pueden tener un cliente asociado."}
            )
        if rol == Usuario.Rol.CLIENTE_WEB and empleado:
            raise serializers.ValidationError(
                {"empleado": "Un usuario CLIENTE_WEB no puede tener un empleado asociado."}
            )
        if rol != Usuario.Rol.CLIENTE_WEB and not data.get("ci_ruc"):
            raise serializers.ValidationError(
                {"ci_ruc": "El CI/RUC es obligatorio para roles internos: es lo que se usa para iniciar sesión."}
            )
        # El nombre/apellido se toman del Empleado vinculado ("Otorgar acceso al
        # sistema"); si no hay empleado, siguen siendo obligatorios (alta suelta).
        if not empleado:
            errores = {}
            if not data.get("nombre"):
                errores["nombre"] = "Este campo es obligatorio."
            if not data.get("apellido"):
                errores["apellido"] = "Este campo es obligatorio."
            if errores:
                raise serializers.ValidationError(errores)
        return data

    def create(self, validated_data):
        password = validated_data.pop("password")
        empleado = validated_data.get("empleado")
        if empleado:
            if not validated_data.get("nombre"):
                validated_data["nombre"] = empleado.nombre
            if not validated_data.get("apellido"):
                validated_data["apellido"] = empleado.apellido
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
    ciudad_nombre = serializers.CharField(source="ciudad.nombre", read_only=True, allow_null=True)
    usuario_id = serializers.SerializerMethodField()

    class Meta:
        model = Empleado
        fields = "__all__"

    def get_usuario_id(self, obj):
        return obj.usuario.id_usuario if hasattr(obj, "usuario") else None


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = "__all__"
