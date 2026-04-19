"""
Tests de cobertura completa para clientes.models
Objetivo: Alcanzar 100% de cobertura en propiedades y métodos __str__

Cobertura de líneas:
- L106: credito_disponible property con límite
- L128: tiene_credito_disponible property
- L171: nombre_completo property de Hijo
- L195: __str__ method de Hijo  
- L311: __str__ method de Grados
- L348-353: __str__ method de HistorialGradosHijos
- L398: __str__ method de RestriccionesHijos
- L436: Creación de LogsAutorizaciones
"""

import pytest
from decimal import Decimal
from django.test import TestCase
from apps.clientes.models import (
    Clientes, Hijos, Grados, TiposCliente,
    HistorialGradosHijos, RestriccionesHijos, LogsAutorizaciones
)
from apps.productos.models import ListasPrecios
from apps.core.models import TarjetasAutorizacion


@pytest.mark.django_db
class TestClientesPropertiesYMetodos:
    """Tests para propiedades calculadas y métodos especiales de Clientes"""
    
    @pytest.fixture
    def lista_precios(self):
        """Fixture: Lista de precios base"""
        return ListasPrecios.objects.create(
            nombre_lista="Lista Default",

            estado=True
        )
    
    @pytest.fixture
    def tipo_cliente(self):
        """Fixture: Tipo de cliente base"""
        return TiposCliente.objects.create(
            nombre_tipo="Cliente Regular",
            estado=True
        )
    
    @pytest.fixture
    def cliente_con_credito(self, lista_precios, tipo_cliente):
        """Fixture: Cliente con límite de crédito configurado"""
        return Clientes.objects.create(
            nombres="Juan Carlos",
            apellidos="Pérez González",
            ruc_ci="1234567-8",
            telefono="0981123456",
            email="juan.perez@example.com",
            limite_credito=Decimal("5000.00"),
            estado=True,
            id_lista=lista_precios,
            id_tipo_cliente=tipo_cliente
        )
    
    def test_credito_disponible_con_limite_credito(self, cliente_con_credito):
        """
        Test L106: Propiedad credito_disponible cuando cliente tiene límite
        
        Verifica que el cálculo de crédito disponible sea correcto:
        credito_disponible = limite_credito - credito_utilizado
        """
        # Arrange: Crear venta con saldo pendiente para que credito_utilizado se calcule
        from apps.ventas.models import Ventas
        from datetime import datetime
        
        Ventas.objects.create(
            id_cliente=cliente_con_credito,
            fecha_venta=datetime.now().date(),
            total_venta=Decimal("1500.00"),
            saldo_pendiente=Decimal("1500.00"),
            estado="Pendiente"
        )
        
        # Act
        disponible = cliente_con_credito.credito_disponible
        
        # Assert
        assert disponible == Decimal("3500.00")  # 5000 - 1500
        assert isinstance(disponible, Decimal)
    
    def test_tiene_credito_disponible_true(self, cliente_con_credito):
        """
        Test L128: Propiedad tiene_credito_disponible retorna True
        
        Verifica que el cliente con crédito disponible > 0 retorne True
        """
        # Arrange: Crear venta pequeña para tener crédito disponible
        from apps.ventas.models import Ventas
        from datetime import datetime
        
        Ventas.objects.create(
            id_cliente=cliente_con_credito,
            fecha_venta=datetime.now().date(),
            total_venta=Decimal("500.00"),
            saldo_pendiente=Decimal("500.00"),
            estado="Pendiente"
        )
        
        # Act
        tiene_credito = cliente_con_credito.tiene_credito_disponible
        
        # Assert
        assert tiene_credito is True  # Tiene 4500 disponible
    
    def test_tiene_credito_disponible_false(self, lista_precios, tipo_cliente):
        """
        Test L128: Propiedad tiene_credito_disponible retorna False
        
        Verifica que cliente sin crédito disponible retorne False
        """
        # Arrange: Cliente con crédito totalmente utilizado
        from apps.ventas.models import Ventas
        from datetime import datetime
        
        cliente = Clientes.objects.create(
            nombres="María",
            apellidos="López",
            ruc_ci="9876543",
            limite_credito=Decimal("1000.00"),
            estado=True,
            id_lista=lista_precios,
            id_tipo_cliente=tipo_cliente
        )
        
        # Crear venta que use todo el crédito
        Ventas.objects.create(
            id_cliente=cliente,
            fecha_venta=datetime.now().date(),
            total_venta=Decimal("1000.00"),
            saldo_pendiente=Decimal("1000.00"),
            estado="Pendiente"
        )
        
        # Act
        tiene_credito = cliente.tiene_credito_disponible
        
        # Assert
        assert tiene_credito is False


@pytest.mark.django_db
class TestHijosPropertiesYMetodos:
    """Tests para propiedades y métodos de modelo Hijos"""
    
    @pytest.fixture
    def hijo(self):
        """Fixture: Hijo/estudiante completo"""
        lista = ListasPrecios.objects.create(nombre_lista="Default", estado=True)
        tipo = TiposCliente.objects.create(nombre_tipo="Padre", estado=True)
        cliente = Clientes.objects.create(
            nombres="Roberto",
            apellidos="Martínez",
            ruc_ci="5555555",
            estado=True,
            id_lista=lista,
            id_tipo_cliente=tipo
        )
        return Hijos.objects.create(
            nombre="Pedro José",
            apellido="Martínez Sánchez",
            fecha_nacimiento="2010-05-15",
            grado="5to Grado",
            estado=True,
            id_cliente_responsable=cliente
        )
    
    def test_hijo_nombre_completo_property(self, hijo):
        """
        Test L171: Propiedad nombre_completo de Hijo
        
        Verifica que concatene correctamente nombre + apellido
        """
        # Act
        nombre_completo = hijo.nombre_completo
        
        # Assert
        assert nombre_completo == "Pedro José Martínez Sánchez"
        assert isinstance(nombre_completo, str)
    
    def test_hijo_str_method(self, hijo):
        """
        Test L195: Método __str__ de Hijo
        
        Verifica formato: "Apellido, Nombre (Grado)"
        """
        # Act
        str_representation = str(hijo)
        
        # Assert
        assert "Martínez Sánchez" in str_representation
        assert "Pedro José" in str_representation
        assert "5to Grado" in str_representation
        assert str_representation == "Martínez Sánchez, Pedro José (5to Grado)"


@pytest.mark.django_db
class TestGradosMetodos:
    """Tests para métodos de modelo Grados"""
    
    def test_grado_str_method(self):
        """
        Test L311: Método __str__ de Grados
        
        Verifica que retorne el nombre del grado
        """
        # Arrange
        grado = Grados.objects.create(
            nombre_grado="Primer Grado",
            nivel=1,
            orden_visualizacion=1,
            es_ultimo_grado=False,
            estado=True
        )
        
        # Act
        str_representation = str(grado)
        
        # Assert
        assert str_representation == "Primer Grado"
        assert isinstance(str_representation, str)
    
    def test_grado_str_method_ultimo_grado(self):
        """Test adicional: __str__ para último grado"""
        # Arrange
        grado = Grados.objects.create(
            nombre_grado="Sexto Grado",
            nivel=6,
            orden_visualizacion=6,
            es_ultimo_grado=True,
            estado=True
        )
        
        # Act & Assert
        assert str(grado) == "Sexto Grado"


@pytest.mark.django_db
class TestHistorialGradosMetodos:
    """Tests para métodos de HistorialGradosHijos"""
    
    @pytest.fixture
    def hijo_base(self):
        """Fixture: Hijo base para historial"""
        lista = ListasPrecios.objects.create(nombre_lista="Default", estado=True)
        tipo = TiposCliente.objects.create(nombre_tipo="Padre", estado=True)
        cliente = Clientes.objects.create(
            nombres="Ana",
            apellidos="Torres",
            ruc_ci="7777777",
            estado=True,
            id_lista=lista,
            id_tipo_cliente=tipo
        )
        return Hijos.objects.create(
            nombre="Luis",
            apellido="Torres",
            fecha_nacimiento="2012-03-10",
            grado="3ro",
            estado=True,
            id_cliente_responsable=cliente
        )
    
    def test_historial_grados_str_con_grado_anterior(self, hijo_base):
        """
        Test L348-353: Método __str__ de HistorialGradosHijos
        
        Formato: "Hijo - Grado_Anterior → Grado_Nuevo (Año)"
        """
        # Arrange
        historial = HistorialGradosHijos.objects.create(
            grado_anterior="2do Grado",
            grado_nuevo="3er Grado",
            anio_escolar=2025,
            motivo="Promoción Regular",
            id_hijo=hijo_base
        )
        
        # Act
        str_representation = str(historial)
        
        # Assert
        assert "2do Grado" in str_representation
        assert "3er Grado" in str_representation
        assert "2025" in str_representation
        assert "→" in str_representation or "->" in str_representation
    
    def test_historial_grados_str_sin_grado_anterior(self, hijo_base):
        """Test: __str__ cuando no hay grado anterior (ingreso inicial)"""
        # Arrange: Primer ingreso del estudiante
        historial = HistorialGradosHijos.objects.create(
            grado_anterior=None,  # Sin grado anterior
            grado_nuevo="1er Grado",
            anio_escolar=2024,
            motivo="Ingreso Inicial",
            id_hijo=hijo_base
        )
        
        # Act & Assert
        str_hist = str(historial)
        assert "1er Grado" in str_hist
        assert "2024" in str_hist


@pytest.mark.django_db
class TestRestriccionesHijosMetodos:
    """Tests para métodos de RestriccionesHijos"""
    
    @pytest.fixture
    def hijo_base(self):
        """Fixture: Hijo base para restricciones"""
        lista = ListasPrecios.objects.create(nombre_lista="Default", estado=True)
        tipo = TiposCliente.objects.create(nombre_tipo="Padre", estado=True)
        cliente = Clientes.objects.create(
            nombres="Carlos",
            apellidos="Ramírez",
            ruc_ci="8888888",
            estado=True,
            id_lista=lista,
            id_tipo_cliente=tipo
        )
        return Hijos.objects.create(
            nombre="Sofia",
            apellido="Ramírez",
            fecha_nacimiento="2011-07-20",
            grado="4to",
            estado=True,
            id_cliente_responsable=cliente
        )
    
    def test_restriccion_str_method(self, hijo_base):
        """
        Test L398: Método __str__ de RestriccionesHijos
        
        Formato: "Tipo - Hijo (Severidad)"
        """
        # Arrange
        restriccion = RestriccionesHijos.objects.create(
            tipo_restriccion="Alergia Alimentaria",
            descripcion="Alergia severa al maní y frutos secos",
            severidad="Alta",
            requiere_autorizacion=True,
            estado=True,
            id_hijo=hijo_base
        )
        
        # Act
        str_representation = str(restriccion)
        
        # Assert
        assert "Alergia Alimentaria" in str_representation
        assert "Alta" in str_representation
        # Puede incluir información del hijo
        assert len(str_representation) > 0
    
    def test_restriccion_str_severidad_baja(self, hijo_base):
        """Test adicional: __str__ con severidad baja"""
        # Arrange
        restriccion = RestriccionesHijos.objects.create(
            tipo_restriccion="Intolerancia",
            descripcion="Intolerancia leve a lactosa",
            severidad="Baja",
            requiere_autorizacion=False,
            estado=True,
            id_hijo=hijo_base
        )
        
        # Act & Assert
        str_rest = str(restriccion)
        assert "Intolerancia" in str_rest
        assert "Baja" in str_rest


@pytest.mark.django_db
class TestLogsAutorizaciones:
    """Tests para modelo LogsAutorizaciones"""
    
    @pytest.fixture
    def tarjeta_autorizacion(self):
        """Fixture: Tarjeta de autorización"""
        lista = ListasPrecios.objects.create(nombre_lista="Default", estado=True)
        tipo = TiposCliente.objects.create(nombre_tipo="Padre", estado=True)
        cliente = Clientes.objects.create(
            nombres="Diego",
            apellidos="Fernández",
            ruc_ci="9999999",
            estado=True,
            id_lista=lista,
            id_tipo_cliente=tipo
        )
        hijo = Hijos.objects.create(
            nombre="Valentina",
            apellido="Fernández",
            fecha_nacimiento="2013-11-05",
            grado="2do",
            estado=True,
            id_cliente_responsable=cliente
        )
        from datetime import datetime
        return TarjetasAutorizacion.objects.create(
            codigo_barra="AUTH-2026-001",
            tipo_autorizacion="temporal",
            estado=True,
            fecha_creacion=datetime.now()
        )
    
    def test_log_autorizacion_creacion(self, tarjeta_autorizacion):
        """
        Test L436: Creación de LogsAutorizaciones
        
        Verifica que se puede crear un log de autorización correctamente
        """
        # Arrange & Act
        log = LogsAutorizaciones.objects.create(
            tipo_operacion="Validación",
            descripcion="Validación de acceso a área restringida",
            id_usuario=1,
            ip_origen="192.168.1.100",
            resultado="Exitoso",
            id_tarjeta_autorizacion=tarjeta_autorizacion
        )
        
        # Assert
        assert log.id_log is not None
        assert log.tipo_operacion == "Validación"
        assert log.resultado == "Exitoso"
        assert log.id_tarjeta_autorizacion == tarjeta_autorizacion
        assert log.ip_origen == "192.168.1.100"
    
    def test_log_autorizacion_fallida(self, tarjeta_autorizacion):
        """Test adicional: Log de autorización fallida"""
        # Arrange & Act
        log = LogsAutorizaciones.objects.create(
            tipo_operacion="Lectura",
            descripcion="Intento de lectura de tarjeta inválida",
            resultado="Fallido",
            id_tarjeta_autorizacion=tarjeta_autorizacion
        )
        
        # Assert
        assert log.resultado == "Fallido"
        assert log.fecha_hora is not None  # Auto-generado
