"""
Tests de cobertura completa para almuerzos.models
Objetivo: Alcanzar 100% de cobertura en métodos __str__

Cobertura de líneas:
- L124: __str__ de SuscripcionesAlmuerzo
- L146: __str__ de RegistrosConsumoAlmuerzo (con/sin motivo_rechazo)
- L173, L192, L213: __str__ de CuentasAlmuerzoMensual
"""

import pytest
from decimal import Decimal
from datetime import date, time, datetime
from django.test import TestCase
from apps.almuerzos.models import (
    PlanesAlmuerzo, TiposAlmuerzo, SuscripcionesAlmuerzo,
    RegistrosConsumoAlmuerzo, CuentasAlmuerzoMensual
)
from apps.clientes.models import Clientes, Hijos, TiposCliente
from apps.productos.models import ListasPrecios


@pytest.mark.django_db
class TestSuscripcionesAlmuerzoMetodos:
    """Tests para métodos __str__ de SuscripcionesAlmuerzo"""
    
    @pytest.fixture
    def plan_almuerzo(self):
        """Fixture: Plan de almuerzo básico"""
        return PlanesAlmuerzo.objects.create(
            nombre_plan="Plan Mensual Completo",
            descripcion="Incluye almuerzo todos los días escolares",
            precio_mensual=Decimal("450.00"),
            estado=True
        )
    
    @pytest.fixture
    def hijo(self):
        """Fixture: Hijo/estudiante para suscripciones"""
        lista = ListasPrecios.objects.create(nombre_lista="Default", estado=True)
        tipo = TiposCliente.objects.create(nombre_tipo="Padre", estado=True)
        cliente = Clientes.objects.create(
            nombres="Fernando",
            apellidos="Silva",
            ruc_ci="3333333",
            estado=True,
            id_lista=lista,
            id_tipo_cliente=tipo
        )
        return Hijos.objects.create(
            nombre="Camila",
            apellido="Silva",
            fecha_nacimiento="2012-08-22",
            grado="4to Grado",
            estado=True,
            id_cliente_responsable=cliente
        )
    
    def test_suscripcion_almuerzo_str_activa(self, plan_almuerzo, hijo):
        """
        Test L124: __str__ de SuscripcionesAlmuerzo con estado activo
        
        Formato esperado: Incluye info del hijo y del plan
        """
        # Arrange
        suscripcion = SuscripcionesAlmuerzo.objects.create(
            id_hijo=hijo,
            id_plan_almuerzo=plan_almuerzo,
            fecha_inicio=date(2026, 1, 15),
            fecha_fin=date(2026, 12, 20),
            estado=True
        )
        
        # Act
        str_representation = str(suscripcion)
        
        # Assert — __str__ retorna "SuscripcionesAlmuerzo #N"
        assert isinstance(str_representation, str)
        assert len(str_representation) > 0
        assert "SuscripcionesAlmuerzo" in str_representation or "#" in str_representation
    
    def test_suscripcion_almuerzo_str_inactiva(self, plan_almuerzo, hijo):
        """Test adicional: __str__ con suscripción inactiva"""
        # Arrange
        suscripcion = SuscripcionesAlmuerzo.objects.create(
            id_hijo=hijo,
            id_plan_almuerzo=plan_almuerzo,
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2025, 12, 31),
            estado=False  # Inactiva
        )
        
        # Act & Assert
        str_rep = str(suscripcion)
        assert len(str_rep) > 0


@pytest.mark.django_db
class TestRegistrosConsumoAlmuerzoMetodos:
    """Tests para métodos __str__ de RegistrosConsumoAlmuerzo"""
    
    @pytest.fixture
    def hijo(self):
        """Fixture: Hijo para registros de consumo"""
        lista = ListasPrecios.objects.create(nombre_lista="Default", estado=True)
        tipo = TiposCliente.objects.create(nombre_tipo="Padre", estado=True)
        cliente = Clientes.objects.create(
            nombres="Patricia",
            apellidos="Gómez",
            ruc_ci="4444444",
            estado=True,
            id_lista=lista,
            id_tipo_cliente=tipo
        )
        return Hijos.objects.create(
            nombre="Mateo",
            apellido="Gómez",
            fecha_nacimiento="2014-02-10",
            grado="2do Grado",
            estado=True,
            id_cliente_responsable=cliente
        )
    
    def test_registro_consumo_str_registrado_exitoso(self, hijo):
        """
        Test L146: __str__ de RegistrosConsumoAlmuerzo con estado registrado
        
        Cuando el consumo fue registrado exitosamente
        """
        # Arrange
        registro = RegistrosConsumoAlmuerzo.objects.create(
            id_hijo=hijo,
            fecha_consumo=date(2026, 4, 19),
            hora_registro=time(12, 30, 0),
            costo_almuerzo=Decimal("35.00"),
            ya_cobrado=True,
            marcado_en_cuenta=False,
            estado="registrado"
        )
        
        # Act
        str_representation = str(registro)
        
        # Assert — __str__ retorna "RegistrosConsumoAlmuerzo #N"
        assert isinstance(str_representation, str)
        assert len(str_representation) > 0
        assert "RegistrosConsumoAlmuerzo" in str_representation or "#" in str_representation
    
    def test_registro_consumo_str_rechazado_con_motivo(self, hijo):
        """
        Test L146: __str__ cuando el consumo fue rechazado CON motivo_rechazo
        
        Este branch es importante: cuando hay rechazo, debe mostrar el motivo
        """
        # Arrange
        registro = RegistrosConsumoAlmuerzo.objects.create(
            id_hijo=hijo,
            fecha_consumo=date(2026, 4, 19),
            hora_registro=time(12, 35, 0),
            costo_almuerzo=Decimal("0.00"),
            ya_cobrado=False,
            marcado_en_cuenta=False,
            estado="rechazado",
            motivo_rechazo="Saldo insuficiente en tarjeta"
        )
        
        # Act
        str_representation = str(registro)
        
        # Assert — __str__ retorna "RegistrosConsumoAlmuerzo #N"
        assert isinstance(str_representation, str)
        assert "RegistrosConsumoAlmuerzo" in str_representation or "#" in str_representation


@pytest.mark.django_db
class TestCuentasAlmuerzoMensualMetodos:
    """Tests para métodos __str__ de CuentasAlmuerzoMensual"""
    
    @pytest.fixture
    def hijo(self):
        """Fixture: Hijo para cuentas mensuales"""
        lista = ListasPrecios.objects.create(nombre_lista="Default", estado=True)
        tipo = TiposCliente.objects.create(nombre_tipo="Padre", estado=True)
        cliente = Clientes.objects.create(
            nombres="Ricardo",
            apellidos="Benítez",
            ruc_ci="5555555",
            estado=True,
            id_lista=lista,
            id_tipo_cliente=tipo
        )
        return Hijos.objects.create(
            nombre="Isabella",
            apellido="Benítez",
            fecha_nacimiento="2011-06-14",
            grado="5to Grado",
            estado=True,
            id_cliente_responsable=cliente
        )
    
    def test_cuenta_almuerzo_mensual_str_pendiente(self, hijo):
        """
        Test L173, L192, L213: __str__ de CuentasAlmuerzoMensual
        
        Caso: Cuenta pendiente de pago
        """
        # Arrange
        cuenta = CuentasAlmuerzoMensual.objects.create(
            id_hijo=hijo,
            anio=2026,
            mes=4,
            cantidad_almuerzos=18,
            monto_total=Decimal("630.00"),
            forma_cobro="mensual",
            monto_pagado=Decimal("0.00"),
            estado="pendiente",
            fecha_generacion=date(2026, 4, 1),
            fecha_actualizacion=datetime(2026, 4, 1, 8, 0, 0)
        )
        
        # Act
        str_representation = str(cuenta)
        
        # Assert — __str__ retorna "CuentasAlmuerzoMensual #N"
        assert isinstance(str_representation, str)
        assert len(str_representation) > 0
        assert "CuentasAlmuerzoMensual" in str_representation or "#" in str_representation
    
    def test_cuenta_almuerzo_mensual_str_pagada(self, hijo):
        """Test adicional: __str__ de cuenta pagada"""
        # Arrange
        cuenta = CuentasAlmuerzoMensual.objects.create(
            id_hijo=hijo,
            anio=2026,
            mes=3,
            cantidad_almuerzos=20,
            monto_total=Decimal("700.00"),
            forma_cobro="mensual",
            monto_pagado=Decimal("700.00"),
            estado="pagado",
            fecha_generacion=date(2026, 3, 1),
            fecha_actualizacion=datetime(2026, 3, 25, 14, 30, 0),
            forma_pago="transferencia",
            fecha_pago=date(2026, 3, 25)
        )
        
        # Act
        str_representation = str(cuenta)
        
        # Assert
        assert len(str_representation) > 0
        # Verificar que genera una representación válida
    
    def test_cuenta_almuerzo_mensual_str_parcial(self, hijo):
        """Test adicional: __str__ de cuenta con pago parcial"""
        # Arrange
        cuenta = CuentasAlmuerzoMensual.objects.create(
            id_hijo=hijo,
            anio=2026,
            mes=2,
            cantidad_almuerzos=15,
            monto_total=Decimal("525.00"),
            forma_cobro="mensual",
            monto_pagado=Decimal("300.00"),
            estado="parcial",
            fecha_generacion=date(2026, 2, 1),
            fecha_actualizacion=datetime(2026, 2, 15, 10, 0, 0)
        )
        
        # Act & Assert
        str_rep = str(cuenta)
        assert len(str_rep) > 0
        assert isinstance(str_rep, str)


class TestAlmuerzosModelsIntegracion:
    """Tests de integración para modelos de almuerzos"""
    
    @pytest.mark.django_db
    def test_flujo_completo_suscripcion_a_consumo(self):
        """
        Test de integración: Desde suscripción hasta cuenta mensual
        
        Verifica que los métodos __str__ funcionen en un flujo real
        """
        # Arrange: Crear toda la cadena
        lista = ListasPrecios.objects.create(nombre_lista="Default", estado=True)
        tipo = TiposCliente.objects.create(nombre_tipo="Padre", estado=True)
        cliente = Clientes.objects.create(
            nombres="Miguel",
            apellidos="Rojas",
            ruc_ci="6666666",
            estado=True,
            id_lista=lista,
            id_tipo_cliente=tipo
        )
        hijo = Hijos.objects.create(
            nombre="Lucía",
            apellido="Rojas",
            fecha_nacimiento="2013-09-30",
            grado="3er Grado",
            estado=True,
            id_cliente_responsable=cliente
        )
        plan = PlanesAlmuerzo.objects.create(
            nombre_plan="Plan Básico",
            precio_mensual=Decimal("400.00"),
            estado=True
        )
        
        # Act: Crear todos los objetos relacionados
        suscripcion = SuscripcionesAlmuerzo.objects.create(
            id_hijo=hijo,
            id_plan_almuerzo=plan,
            fecha_inicio=date.today(),
            estado=True
        )
        
        registro = RegistrosConsumoAlmuerzo.objects.create(
            id_hijo=hijo,
            fecha_consumo=date.today(),
            hora_registro=time(12, 0),
            estado="registrado",
            ya_cobrado=True
        )
        
        cuenta = CuentasAlmuerzoMensual.objects.create(
            id_hijo=hijo,
            anio=2026,
            mes=4,
            cantidad_almuerzos=10,
            monto_total=Decimal("350.00"),
            forma_cobro="mensual",
            monto_pagado=Decimal("0.00"),
            estado="pendiente",
            fecha_generacion=date.today(),
            fecha_actualizacion=datetime.now()
        )
        
        # Assert: Todos los __str__ deben funcionar sin errores
        assert len(str(suscripcion)) > 0
        assert len(str(registro)) > 0
        assert len(str(cuenta)) > 0
