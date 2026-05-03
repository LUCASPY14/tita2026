from rest_framework import serializers

from .models import AuditoriaOperaciones, Empleados, PerfilesUsuario, Roles, UsuariosPortal


class RolesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = "__all__"


class EmpleadosSerializer(serializers.ModelSerializer):
    rol_nombre = serializers.CharField(source="id_rol.nombre_rol", read_only=True)

    class Meta:
        model = Empleados
        fields = "__all__"
        extra_kwargs = {"contrasena_hash": {"write_only": True}}

    def get_fields(self):
        fields = super().get_fields()
        # Make contrasena_hash optional for updates (when instance exists)
        if self.instance is not None:
            fields["contrasena_hash"].required = False
        return fields


class PerfilesUsuarioSerializer(serializers.ModelSerializer):
    empleado_nombre = serializers.CharField(source="id_empleado.nombre", read_only=True)

    class Meta:
        model = PerfilesUsuario
        fields = "__all__"


class UsuariosPortalSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source="id_cliente.nombre", read_only=True)

    class Meta:
        model = UsuariosPortal
        fields = "__all__"
        extra_kwargs = {"password_hash": {"write_only": True}}


class AuditoriaOperacionesSerializer(serializers.ModelSerializer):
    """
    Serializer para logs de auditoría del sistema.
    """

    tipo_operacion_display = serializers.SerializerMethodField()
    resultado_display = serializers.SerializerMethodField()

    class Meta:
        model = AuditoriaOperaciones
        fields = "__all__"
        read_only_fields = ["id_auditoria", "fecha_operacion"]

    def get_tipo_operacion_display(self, obj):
        """Retorna descripción legible de la operación"""
        operaciones = {
            "LOGIN": "Inicio de sesión",
            "LOGOUT": "Cierre de sesión",
            "CREATE": "Creación",
            "UPDATE": "Modificación",
            "DELETE": "Eliminación",
            "VIEW": "Consulta",
            "EXPORT": "Exportación",
            "IMPORT": "Importación",
            "2FA_ENABLE": "Activación 2FA",
            "2FA_DISABLE": "Desactivación 2FA",
            "PASSWORD_CHANGE": "Cambio de contraseña",
            "PASSWORD_RESET": "Recuperación de contraseña",
        }
        return operaciones.get(obj.operacion, obj.operacion)

    def get_resultado_display(self, obj):
        """Retorna descripción legible del resultado"""
        resultados = {
            "EXITO": "Exitoso",
            "ERROR": "Error",
            "BLOQUEADO": "Bloqueado",
            "DENEGADO": "Denegado",
        }
        return resultados.get(obj.resultado, obj.resultado)
