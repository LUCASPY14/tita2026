"""
Tests para los validadores del módulo Inventario
Aseguran que todas las reglas de validación funcionan correctamente
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone

from apps.inventario.validators import (
    # Stock
    validar_cantidad_positiva,
    validar_cantidad_no_negativa,
    validar_stock_minimo_maximo,
    validar_punto_reorden,
    validar_stock_disponible,
    # Movimientos
    validar_tipo_movimiento,
    validar_motivo_movimiento,
    validar_referencia_movimiento,
    # Ajustes
    validar_tipo_ajuste,
    validar_estado_ajuste,
    validar_cantidad_ajuste,
    validar_merma_aceptable,
    # Lotes
    validar_fecha_vencimiento,
    validar_numero_lote,
    validar_cantidad_lote,
    # ML Forecasting
    validar_dias_historico,
    validar_umbral_confianza,
    validar_lead_time,
    validar_dias_cobertura,
    # Costos
    validar_costo_unitario,
    validar_variacion_costo,
    # Alertas
    validar_nivel_alerta,
    validar_umbral_alerta,
)
from apps.productos.models import Productos, Categorias, UnidadesMedida, ListasPrecios
from apps.contabilidad.models import Impuestos
from apps.inventario.models import StockUnico


class ValidadoresCantidadTestCase(TestCase):
    """Tests para validadores de cantidades"""
    
    def test_cantidad_positiva_valida(self):
        """Cantidad positiva debe pasar validación"""
        try:
            validar_cantidad_positiva(10)
            validar_cantidad_positiva(Decimal('100.50'))
            validar_cantidad_positiva(0.01)
        except ValidationError:
            self.fail("Esta cantidad debería ser válida")
    
    def test_cantidad_positiva_cero_invalida(self):
        """Cantidad cero debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_cantidad_positiva(0)
        self.assertIn("mayor a cero", str(context.exception))
    
    def test_cantidad_positiva_negativa_invalida(self):
        """Cantidad negativa debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_cantidad_positiva(-5)
        self.assertIn("mayor a cero", str(context.exception))
    
    def test_cantidad_positiva_nula_invalida(self):
        """Cantidad None debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_cantidad_positiva(None)
        self.assertIn("no puede ser nula", str(context.exception))
    
    def test_cantidad_positiva_texto_invalido(self):
        """Texto no numérico debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_cantidad_positiva("abc")
        self.assertIn("número válido", str(context.exception))
    
    def test_cantidad_no_negativa_valida(self):
        """Cero y positivos deben pasar"""
        try:
            validar_cantidad_no_negativa(0)
            validar_cantidad_no_negativa(10)
            validar_cantidad_no_negativa(Decimal('100.50'))
        except ValidationError:
            self.fail("Estas cantidades deberían ser válidas")
    
    def test_cantidad_no_negativa_negativa_invalida(self):
        """Cantidad negativa debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_cantidad_no_negativa(-1)
        self.assertIn("no puede ser negativa", str(context.exception))
    
    def test_cantidad_no_negativa_permite_none(self):
        """None debe permitirse (validación opcional)"""
        try:
            validar_cantidad_no_negativa(None)
        except ValidationError:
            self.fail("None debería ser permitido")


class ValidadoresStockTestCase(TestCase):
    """Tests para validadores de stock"""
    
    def test_stock_minimo_maximo_valido(self):
        """Stock mínimo < máximo debe pasar"""
        try:
            validar_stock_minimo_maximo(10, 100)
            validar_stock_minimo_maximo(Decimal('5'), Decimal('50'))
        except ValidationError:
            self.fail("Este rango debería ser válido")
    
    def test_stock_minimo_mayor_que_maximo_invalido(self):
        """Mínimo >= máximo debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_stock_minimo_maximo(100, 50)
        self.assertIn("debe ser menor que el máximo", str(context.exception))
    
    def test_stock_minimo_igual_que_maximo_invalido(self):
        """Mínimo == máximo debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_stock_minimo_maximo(50, 50)
        self.assertIn("debe ser menor que el máximo", str(context.exception))
    
    def test_stock_minimo_negativo_invalido(self):
        """Stock mínimo negativo debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_stock_minimo_maximo(-5, 100)
        self.assertIn("no puede ser negativo", str(context.exception))
    
    def test_stock_maximo_cero_invalido(self):
        """Stock máximo cero o negativo debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_stock_minimo_maximo(0, 0)
        self.assertIn("debe ser mayor a cero", str(context.exception))
    
    def test_stock_permite_none(self):
        """None en stock debe permitirse (validación opcional)"""
        try:
            validar_stock_minimo_maximo(None, None)
            validar_stock_minimo_maximo(10, None)
        except ValidationError:
            self.fail("None debería ser permitido")


class ValidadoresPuntoReordenTestCase(TestCase):
    """Tests para punto de reorden"""
    
    def test_punto_reorden_valido(self):
        """Punto en rango válido debe pasar"""
        try:
            validar_punto_reorden(50, 10, 100)
            validar_punto_reorden(Decimal('25'), Decimal('10'), Decimal('100'))
        except ValidationError:
            self.fail("Este punto de reorden debería ser válido")
    
    def test_punto_reorden_menor_que_minimo_invalido(self):
        """Punto < mínimo debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_punto_reorden(5, 10, 100)
        self.assertIn("no puede ser menor que el stock mínimo", str(context.exception))
    
    def test_punto_reorden_mayor_que_maximo_invalido(self):
        """Punto > máximo debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_punto_reorden(150, 10, 100)
        self.assertIn("no puede ser mayor que el stock máximo", str(context.exception))
    
    def test_punto_reorden_cero_invalido(self):
        """Punto de reorden cero debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_punto_reorden(0, 10, 100)
        self.assertIn("debe ser positivo", str(context.exception))
    
    def test_punto_reorden_permite_none(self):
        """None debe permitirse"""
        try:
            validar_punto_reorden(None, 10, 100)
        except ValidationError:
            self.fail("None debería ser permitido")


class ValidadoresStockDisponibleTestCase(TestCase):
    """Tests para validar stock disponible"""
    
    def setUp(self):
        """Crear datos de prueba"""
        self.impuesto = Impuestos.objects.create(
            nombre_impuesto='IVA 10%',
            porcentaje=10.00,
            vigente_desde='2024-01-01',
            activo=True
        )
        
        self.categoria = Categorias.objects.create(
            nombre='Bebidas',
            activo=True
        )
        
        self.unidad = UnidadesMedida.objects.create(
            nombre='Unidad',
            abreviatura='u',
            activo=True
        )
        
        self.lista_precio = ListasPrecios.objects.create(
            nombre_lista='Minorista',
            moneda='PYG',
            activo=True
        )
        
        # Producto con stock
        self.producto = Productos.objects.create(
            codigo_barra='7891234567890',
            descripcion='Coca Cola 2L',
            stock_minimo=10,
            permite_stock_negativo=False,
            id_impuesto=self.impuesto,
            id_categoria=self.categoria,
            id_unidad_medida=self.unidad,
            activo=True
        )
        
        StockUnico.objects.create(
            id_producto=self.producto,
            cantidad=Decimal('50')
        )
        
        # Producto que permite stock negativo
        self.producto_negativo = Productos.objects.create(
            codigo_barra='7891234567891',
            descripcion='Servicio',
            stock_minimo=0,
            permite_stock_negativo=True,
            id_impuesto=self.impuesto,
            id_categoria=self.categoria,
            id_unidad_medida=self.unidad,
            activo=True
        )
        
        StockUnico.objects.create(
            id_producto=self.producto_negativo,
            cantidad=Decimal('10')
        )
    
    def test_stock_disponible_suficiente(self):
        """Stock suficiente debe pasar validación"""
        try:
            validar_stock_disponible(self.producto.id_producto, 30)
        except ValidationError:
            self.fail("Debería haber stock suficiente")
    
    def test_stock_insuficiente_debe_fallar(self):
        """Stock insuficiente debe lanzar error"""
        with self.assertRaises(ValidationError) as context:
            validar_stock_disponible(self.producto.id_producto, 100)
        self.assertIn("insuficiente", str(context.exception))
    
    def test_producto_permite_negativo_pasa_validacion(self):
        """Productos que permiten negativo siempre pasan"""
        try:
            validar_stock_disponible(self.producto_negativo.id_producto, 500)
        except ValidationError:
            self.fail("Producto permite stock negativo")
    
    def test_cantidad_cero_invalida(self):
        """Cantidad solicitada cero debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_stock_disponible(self.producto.id_producto, 0)
        self.assertIn("mayor a cero", str(context.exception))
    
    def test_producto_inexistente_invalido(self):
        """Producto que no existe debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_stock_disponible(9999, 10)
        self.assertIn("no existe", str(context.exception))


class ValidadoresMovimientosTestCase(TestCase):
    """Tests para validadores de movimientos"""
    
    def test_tipo_movimiento_valido(self):
        """Tipos válidos deben pasar"""
        try:
            validar_tipo_movimiento('Ingreso')
            validar_tipo_movimiento('Egreso')
        except ValidationError:
            self.fail("Estos tipos deberían ser válidos")
    
    def test_tipo_movimiento_invalido(self):
        """Tipo inválido debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_tipo_movimiento('Traslado')
        self.assertIn("inválido", str(context.exception))
    
    def test_tipo_movimiento_vacio_invalido(self):
        """Tipo vacío debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_tipo_movimiento('')
        self.assertIn("requerido", str(context.exception))
    
    def test_motivo_movimiento_valido(self):
        """Motivo suficientemente largo debe pasar"""
        try:
            validar_motivo_movimiento('Compra de mercadería a proveedor ABC')
        except ValidationError:
            self.fail("Este motivo debería ser válido")
    
    def test_motivo_muy_corto_invalido(self):
        """Motivo < 10 caracteres debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_motivo_movimiento('Compra')
        self.assertIn("al menos 10 caracteres", str(context.exception))
    
    def test_motivo_vacio_invalido(self):
        """Motivo vacío debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_motivo_movimiento('')
        self.assertIn("requerido", str(context.exception))
    
    def test_motivo_solo_espacios_invalido(self):
        """Motivo solo con espacios debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_motivo_movimiento('      ')
        self.assertIn("requerido", str(context.exception))
    
    def test_referencia_movimiento_valida(self):
        """Referencias válidas deben pasar"""
        try:
            validar_referencia_movimiento('Compra', 123)
            validar_referencia_movimiento('Venta', 456)
            validar_referencia_movimiento('Ajuste', 789)
        except ValidationError:
            self.fail("Estas referencias deberían ser válidas")
    
    def test_referencia_tipo_invalido(self):
        """Tipo de referencia inválido debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_referencia_movimiento('Pedido', 123)
        self.assertIn("Tipo de referencia inválido", str(context.exception))
    
    def test_referencia_id_negativo_invalido(self):
        """ID de referencia negativo debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_referencia_movimiento('Compra', -1)
        self.assertIn("debe ser positivo", str(context.exception))
    
    def test_referencia_id_none_valido(self):
        """ID None debe permitirse (algunos movimientos no tienen referencia)"""
        try:
            validar_referencia_movimiento('Inicial', None)
        except ValidationError:
            self.fail("ID None debería ser permitido")


class ValidadoresAjustesTestCase(TestCase):
    """Tests para validadores de ajustes"""
    
    def test_tipo_ajuste_valido(self):
        """Tipos válidos deben pasar"""
        try:
            validar_tipo_ajuste('Merma')
            validar_tipo_ajuste('Sobrante')
            validar_tipo_ajuste('Correccion')
            validar_tipo_ajuste('Vencimiento')
            validar_tipo_ajuste('Deterioro')
        except ValidationError:
            self.fail("Estos tipos deberían ser válidos")
    
    def test_tipo_ajuste_invalido(self):
        """Tipo inválido debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_tipo_ajuste('Robo')
        self.assertIn("inválido", str(context.exception))
    
    def test_estado_ajuste_valido(self):
        """Estados válidos deben pasar"""
        try:
            validar_estado_ajuste('Pendiente')
            validar_estado_ajuste('Aprobado')
            validar_estado_ajuste('Rechazado')
            validar_estado_ajuste('Aplicado')
        except ValidationError:
            self.fail("Estos estados deberían ser válidos")
    
    def test_estado_ajuste_invalido(self):
        """Estado inválido debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_estado_ajuste('Cancelado')
        self.assertIn("inválido", str(context.exception))
    
    def test_cantidad_ajuste_merma_negativa_valida(self):
        """Merma con cantidad negativa debe pasar"""
        try:
            validar_cantidad_ajuste(Decimal('-10'), 'Merma')
            validar_cantidad_ajuste(Decimal('-5'), 'Vencimiento')
            validar_cantidad_ajuste(Decimal('-3'), 'Deterioro')
        except ValidationError:
            self.fail("Merma con cantidad negativa debería ser válida")
    
    def test_cantidad_ajuste_merma_positiva_invalida(self):
        """Merma con cantidad positiva debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_cantidad_ajuste(Decimal('10'), 'Merma')
        self.assertIn("deben tener cantidad negativa", str(context.exception))
    
    def test_cantidad_ajuste_sobrante_positiva_valida(self):
        """Sobrante con cantidad positiva debe pasar"""
        try:
            validar_cantidad_ajuste(Decimal('10'), 'Sobrante')
        except ValidationError:
            self.fail("Sobrante con cantidad positiva debería ser válido")
    
    def test_cantidad_ajuste_sobrante_negativa_invalida(self):
        """Sobrante con cantidad negativa debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_cantidad_ajuste(Decimal('-10'), 'Sobrante')
        self.assertIn("deben tener cantidad positiva", str(context.exception))
    
    def test_cantidad_ajuste_cero_invalida(self):
        """Cantidad cero debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_cantidad_ajuste(Decimal('0'), 'Correccion')
        self.assertIn("no puede ser cero", str(context.exception))
    
    def test_merma_aceptable_valida(self):
        """Merma <= 5% debe pasar"""
        try:
            validar_merma_aceptable(Decimal('3'), Decimal('100'), porcentaje_max=5)
        except ValidationError:
            self.fail("Merma aceptable debería ser válida")
    
    def test_merma_excesiva_invalida(self):
        """Merma > 5% debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_merma_aceptable(Decimal('10'), Decimal('100'), porcentaje_max=5)
        self.assertIn("supera el máximo permitido", str(context.exception))
    
    def test_merma_total_cero_invalido(self):
        """Total cero debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_merma_aceptable(Decimal('5'), Decimal('0'))
        self.assertIn("debe ser mayor a cero", str(context.exception))


class ValidadoresLotesTestCase(TestCase):
    """Tests para validadores de lotes"""
    
    def test_fecha_vencimiento_futura_valida(self):
        """Fecha futura debe pasar"""
        fecha_futura = timezone.now().date() + timedelta(days=30)
        try:
            validar_fecha_vencimiento(fecha_futura)
        except ValidationError:
            self.fail("Fecha futura debería ser válida")
    
    def test_fecha_vencimiento_pasada_invalida(self):
        """Fecha pasada debe fallar"""
        fecha_pasada = timezone.now().date() - timedelta(days=1)
        with self.assertRaises(ValidationError) as context:
            validar_fecha_vencimiento(fecha_pasada)
        self.assertIn("no puede estar en el pasado", str(context.exception))
    
    def test_fecha_vencimiento_permite_none(self):
        """None debe permitirse (productos sin vencimiento)"""
        try:
            validar_fecha_vencimiento(None)
        except ValidationError:
            self.fail("None debería ser permitido")
    
    def test_numero_lote_valido(self):
        """Número de lote válido debe pasar"""
        try:
            validar_numero_lote('LOT-123')
            validar_numero_lote('ABC123')
            validar_numero_lote('2024-01-001')
        except ValidationError:
            self.fail("Estos números de lote deberían ser válidos")
    
    def test_numero_lote_muy_corto_invalido(self):
        """Lote < 3 caracteres debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_numero_lote('AB')
        self.assertIn("al menos 3 caracteres", str(context.exception))
    
    def test_numero_lote_caracteres_especiales_invalido(self):
        """Lote con caracteres especiales debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_numero_lote('LOT#123')
        self.assertIn("solo puede contener", str(context.exception))
    
    def test_numero_lote_vacio_invalido(self):
        """Lote vacío debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_numero_lote('')
        self.assertIn("requerido", str(context.exception))
    
    def test_cantidad_lote_coincide_valida(self):
        """Cantidades coincidentes deben pasar"""
        try:
            validar_cantidad_lote(Decimal('100'), Decimal('100'))
        except ValidationError:
            self.fail("Cantidades coincidentes deberían ser válidas")
    
    def test_cantidad_lote_no_coincide_invalida(self):
        """Cantidades diferentes deben fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_cantidad_lote(Decimal('100'), Decimal('90'))
        self.assertIn("no coincide", str(context.exception))
    
    def test_cantidad_lote_cero_invalida(self):
        """Cantidad lote cero debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_cantidad_lote(Decimal('0'), Decimal('0'))
        self.assertIn("debe ser positiva", str(context.exception))


class ValidadoresMLForecastingTestCase(TestCase):
    """Tests para validadores de ML forecasting"""
    
    def test_dias_historico_valido(self):
        """Días en rango 7-365 deben pasar"""
        try:
            validar_dias_historico(7)
            validar_dias_historico(30)
            validar_dias_historico(90)
            validar_dias_historico(365)
        except ValidationError:
            self.fail("Estos valores deberían ser válidos")
    
    def test_dias_historico_muy_pocos_invalido(self):
        """Días < 7 deben fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_dias_historico(5)
        self.assertIn("mínimo 7 días", str(context.exception))
    
    def test_dias_historico_muchos_invalido(self):
        """Días > 365 deben fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_dias_historico(400)
        self.assertIn("no puede superar 365 días", str(context.exception))
    
    def test_dias_historico_none_invalido(self):
        """None debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_dias_historico(None)
        self.assertIn("requerido", str(context.exception))
    
    def test_umbral_confianza_valido(self):
        """Umbral 0.50-0.99 debe pasar"""
        try:
            validar_umbral_confianza(0.50)
            validar_umbral_confianza(0.75)
            validar_umbral_confianza(0.95)
            validar_umbral_confianza(0.99)
        except ValidationError:
            self.fail("Estos umbrales deberían ser válidos")
    
    def test_umbral_confianza_muy_bajo_invalido(self):
        """Umbral < 0.50 debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_umbral_confianza(0.3)
        self.assertIn("no puede ser menor a 0.50", str(context.exception))
    
    def test_umbral_confianza_uno_invalido(self):
        """Umbral >= 1.0 debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_umbral_confianza(1.0)
        self.assertIn("debe ser menor a 1.0", str(context.exception))
    
    def test_lead_time_valido(self):
        """Lead time 1-90 días debe pasar"""
        try:
            validar_lead_time(1)
            validar_lead_time(7)
            validar_lead_time(30)
            validar_lead_time(90)
        except ValidationError:
            self.fail("Estos valores deberían ser válidos")
    
    def test_lead_time_cero_invalido(self):
        """Lead time < 1 debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_lead_time(0)
        self.assertIn("al menos 1 día", str(context.exception))
    
    def test_lead_time_excesivo_invalido(self):
        """Lead time > 90 debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_lead_time(100)
        self.assertIn("no puede superar 90 días", str(context.exception))
    
    def test_dias_cobertura_valido(self):
        """Cobertura 7-60 días debe pasar"""
        try:
            validar_dias_cobertura(7)
            validar_dias_cobertura(14)
            validar_dias_cobertura(30)
            validar_dias_cobertura(60)
        except ValidationError:
            self.fail("Estos valores deberían ser válidos")
    
    def test_dias_cobertura_muy_pocos_invalido(self):
        """Cobertura < 7 debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_dias_cobertura(5)
        self.assertIn("mínima es 7 días", str(context.exception))
    
    def test_dias_cobertura_excesiva_invalida(self):
        """Cobertura > 60 debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_dias_cobertura(90)
        self.assertIn("máxima es 60 días", str(context.exception))


class ValidadoresCostosTestCase(TestCase):
    """Tests para validadores de costos"""
    
    def test_costo_unitario_valido(self):
        """Costo positivo debe pasar"""
        try:
            validar_costo_unitario(Decimal('100.50'))
            validar_costo_unitario(0.01)
        except ValidationError:
            self.fail("Estos costos deberían ser válidos")
    
    def test_costo_unitario_cero_invalido(self):
        """Costo cero debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_costo_unitario(Decimal('0'))
        self.assertIn("mayor a cero", str(context.exception))
    
    def test_costo_unitario_negativo_invalido(self):
        """Costo negativo debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_costo_unitario(Decimal('-10'))
        self.assertIn("mayor a cero", str(context.exception))
    
    def test_variacion_costo_aceptable_valida(self):
        """Variación <= 30% debe pasar"""
        try:
            validar_variacion_costo(Decimal('120'), Decimal('100'), porcentaje_max_variacion=30)
        except ValidationError:
            self.fail("Variación aceptable debería ser válida")
    
    def test_variacion_costo_excesiva_invalida(self):
        """Variación > 30% debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_variacion_costo(Decimal('200'), Decimal('100'), porcentaje_max_variacion=30)
        self.assertIn("supera el máximo permitido", str(context.exception))
    
    def test_variacion_costo_sin_anterior_valida(self):
        """Sin costo anterior debe permitirse"""
        try:
            validar_variacion_costo(Decimal('100'), None)
            validar_variacion_costo(Decimal('100'), Decimal('0'))
        except ValidationError:
            self.fail("Sin costo anterior debería ser válido")


class ValidadoresAlertasTestCase(TestCase):
    """Tests para validadores de alertas"""
    
    def test_nivel_alerta_valido(self):
        """Niveles válidos deben pasar"""
        try:
            validar_nivel_alerta('Bajo')
            validar_nivel_alerta('Medio')
            validar_nivel_alerta('Alto')
            validar_nivel_alerta('Critico')
        except ValidationError:
            self.fail("Estos niveles deberían ser válidos")
    
    def test_nivel_alerta_invalido(self):
        """Nivel inválido debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_nivel_alerta('Urgente')
        self.assertIn("inválido", str(context.exception))
    
    def test_nivel_alerta_vacio_invalido(self):
        """Nivel vacío debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_nivel_alerta('')
        self.assertIn("requerido", str(context.exception))
    
    def test_umbral_alerta_valido(self):
        """Umbral en rango válido debe pasar"""
        try:
            validar_umbral_alerta(Decimal('50'), Decimal('10'), Decimal('100'))
        except ValidationError:
            self.fail("Este umbral debería ser válido")
    
    def test_umbral_alerta_negativo_invalido(self):
        """Umbral negativo debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_umbral_alerta(Decimal('-5'), Decimal('10'), Decimal('100'))
        self.assertIn("no puede ser negativo", str(context.exception))
    
    def test_umbral_alerta_mayor_que_maximo_invalido(self):
        """Umbral > máximo debe fallar"""
        with self.assertRaises(ValidationError) as context:
            validar_umbral_alerta(Decimal('150'), Decimal('10'), Decimal('100'))
        self.assertIn("no puede ser mayor que el stock máximo", str(context.exception))
