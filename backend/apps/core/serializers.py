from rest_framework import serializers
from .models import Tarjetas, CargasSaldo, ConsumosTarjeta, MediosPago, ConfiguracionSistema


class TarjetasSerializer(serializers.ModelSerializer):
    hijo_nombre = serializers.CharField(source='id_hijo.nombre', read_only=True)
    hijo_apellido = serializers.CharField(source='id_hijo.apellido', read_only=True)
    saldo_disponible = serializers.SerializerMethodField()
    
    class Meta:
        model = Tarjetas
        fields = '__all__'
    
    def get_saldo_disponible(self, obj):
        """Calcula el saldo disponible considerando límite de crédito"""
        if obj.permite_saldo_negativo:
            return obj.saldo_actual + obj.limite_credito
        return obj.saldo_actual


class CargasSaldoSerializer(serializers.ModelSerializer):
    tarjeta_numero = serializers.CharField(source='nro_tarjeta.nro_tarjeta', read_only=True)
    hijo_nombre = serializers.SerializerMethodField(read_only=True)
    cliente_nombre = serializers.CharField(source='id_cliente_origen.nombres', read_only=True)
    cajero_nombre = serializers.SerializerMethodField(read_only=True)
    supervisor_nombre = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = CargasSaldo
        fields = '__all__'
        read_only_fields = [
            'id_carga',
            'fecha_carga',
            'fecha_confirmacion',
            'fecha_aprobacion',
            'id_factura'
        ]
    
    def get_hijo_nombre(self, obj):
        """Retorna nombre completo del hijo"""
        try:
            return f"{obj.nro_tarjeta.id_hijo.nombre} {obj.nro_tarjeta.id_hijo.apellido}"
        except:
            return None
    
    def get_cajero_nombre(self, obj):
        """Retorna nombre del cajero responsable"""
        try:
            return obj.usuario_responsable.nombre
        except AttributeError:
            return None
    
    def get_supervisor_nombre(self, obj):
        """Retorna nombre del supervisor aprobador"""
        try:
            return obj.supervisor_aprobador.nombre
        except AttributeError:
            return None


class ConsumosTarjetaSerializer(serializers.ModelSerializer):
    tarjeta_numero = serializers.CharField(source='nro_tarjeta.nro_tarjeta', read_only=True)
    
    class Meta:
        model = ConsumosTarjeta
        fields = '__all__'


class MediosPagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediosPago
        fields = '__all__'


class ConfiguracionSistemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfiguracionSistema
        fields = '__all__'
