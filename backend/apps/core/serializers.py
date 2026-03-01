from rest_framework import serializers
from .models import Tarjetas, CargasSaldo, ConsumosTarjeta, MediosPago, ConfiguracionSistema


class TarjetasSerializer(serializers.ModelSerializer):
    hijo_nombre = serializers.CharField(source='id_hijo.nombres', read_only=True)
    hijo_apellido = serializers.CharField(source='id_hijo.apellidos', read_only=True)
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
    cliente_nombre = serializers.CharField(source='id_cliente_origen.nombre', read_only=True)
    
    class Meta:
        model = CargasSaldo
        fields = '__all__'


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
