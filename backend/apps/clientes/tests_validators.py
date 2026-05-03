"""
Tests para los validadores del módulo Clientes
Coverage completo de todas las reglas de negocio
"""

from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.clientes.validators import (  # Clientes; Tipos de Cliente; Hijos; Grados; Historial de Grados; Restricciones; Autorizaciones; Logs
    validar_anio_escolar,
    validar_apellido_hijo,
    validar_apellidos_cliente,
    validar_cambio_grado,
    validar_descripcion_restriccion,
    validar_direccion_cliente,
    validar_email_cliente,
    validar_fecha_nacimiento,
    validar_foto_perfil,
    validar_grado_hijo,
    validar_ip_origen,
    validar_limite_credito_cliente,
    validar_monto_autorizado,
    validar_motivo_autorizacion,
    validar_motivo_cambio_grado,
    validar_nivel_grado,
    validar_nombre_grado,
    validar_nombre_hijo,
    validar_nombre_tipo_cliente,
    validar_nombres_cliente,
    validar_observaciones_restriccion,
    validar_orden_visualizacion,
    validar_razon_social,
    validar_resultado_log,
    validar_ruc_ci,
    validar_saldos_autorizacion,
    validar_severidad_restriccion,
    validar_telefono_cliente,
    validar_tipo_operacion_log,
    validar_tipo_restriccion,
)

# ============================================================================
# TESTS DE VALIDADORES DE CLIENTES
# ============================================================================


class ValidarNombresClienteTest(TestCase):
    """Tests para validación de nombres de cliente"""

    def test_nombres_validos(self):
        """Nombres válidos deben pasar"""
        nombres_validos = [
            "Juan",
            "María José",
            "O'Connor",
            "María-Elena",
            "José María de los Ángeles",
        ]
        for nombre in nombres_validos:
            try:
                validar_nombres_cliente(nombre)
            except ValidationError:  # pragma: no cover
                self.fail(f"Nombre válido rechazado: {nombre}")

    def test_nombres_muy_cortos(self):
        """Nombres muy cortos deben fallar"""
        with self.assertRaises(ValidationError):
            validar_nombres_cliente("A")

    def test_nombres_muy_largos(self):
        """Nombres muy largos deben fallar"""
        nombre_largo = "A" * 101
        with self.assertRaises(ValidationError):
            validar_nombres_cliente(nombre_largo)

    def test_nombres_con_numeros(self):
        """Nombres con números deben fallar"""
        with self.assertRaises(ValidationError):
            validar_nombres_cliente("Juan123")


class ValidarApellidosClienteTest(TestCase):
    """Tests para validación de apellidos de cliente"""

    def test_apellidos_validos(self):
        """Apellidos válidos deben pasar"""
        apellidos_validos = [
            "Pérez",
            "García López",
            "O'Brien",
            "Saint-Exupéry",
        ]
        for apellido in apellidos_validos:
            try:
                validar_apellidos_cliente(apellido)
            except ValidationError:  # pragma: no cover
                self.fail(f"Apellido válido rechazado: {apellido}")

    def test_apellidos_muy_cortos(self):
        """Apellidos muy cortos deben fallar"""
        with self.assertRaises(ValidationError):
            validar_apellidos_cliente("P")

    def test_apellidos_muy_largos(self):
        """Apellidos muy largos deben fallar"""
        apellido_largo = "P" * 101
        with self.assertRaises(ValidationError):
            validar_apellidos_cliente(apellido_largo)

    def test_apellidos_con_numeros(self):
        """Apellidos con números deben fallar"""
        with self.assertRaises(ValidationError):
            validar_apellidos_cliente("Pérez123")


class ValidarRazonSocialTest(TestCase):
    """Tests para validación de razón social"""

    def test_razon_social_valida(self):
        """Razones sociales válidas deben pasar"""
        razones_validas = [
            "Comercial ABC S.A.",
            "Supermercado El Ahorro",
            "Distribuidora López & Hnos",
            "Empresa XYZ (PY)",
        ]
        for razon in razones_validas:
            try:
                validar_razon_social(razon)
            except ValidationError:  # pragma: no cover
                self.fail(f"Razón social válida rechazada: {razon}")

    def test_razon_social_muy_corta(self):
        """Razón social muy corta debe fallar"""
        with self.assertRaises(ValidationError):
            validar_razon_social("AB")

    def test_razon_social_muy_larga(self):
        """Razón social muy larga debe fallar"""
        razon_larga = "A" * 256
        with self.assertRaises(ValidationError):
            validar_razon_social(razon_larga)

    def test_razon_social_opcional(self):
        """Razón social None o vacía debe pasar (es opcional)"""
        try:
            validar_razon_social(None)
            validar_razon_social("")
        except ValidationError:  # pragma: no cover
            self.fail("Razón social opcional rechazada")


class ValidarRucCiTest(TestCase):
    """Tests para validación de RUC/CI paraguayo"""

    def test_ruc_valido_formato_corto(self):
        """RUC formato corto (XXXXX-Y) debe pasar"""
        try:
            validar_ruc_ci("12345-6")
        except ValidationError:  # pragma: no cover
            self.fail("RUC válido formato corto rechazado")

    def test_ruc_valido_formato_largo(self):
        """RUC formato largo (XXXXXXXX-Y) debe pasar"""
        try:
            validar_ruc_ci("12345678-9")
        except ValidationError:  # pragma: no cover
            self.fail("RUC válido formato largo rechazado")

    def test_ci_valida_con_puntos(self):
        """CI con puntos debe pasar"""
        try:
            validar_ruc_ci("1.234.567")
        except ValidationError:  # pragma: no cover
            self.fail("CI válida con puntos rechazada")

    def test_ci_valida_sin_puntos(self):
        """CI sin puntos debe pasar"""
        try:
            validar_ruc_ci("1234567")
        except ValidationError:  # pragma: no cover
            self.fail("CI válida sin puntos rechazada")

    def test_ruc_ci_vacio(self):
        """RUC/CI vacío debe fallar"""
        with self.assertRaises(ValidationError):
            validar_ruc_ci("")

    def test_ruc_formato_incorrecto(self):
        """RUC con formato incorrecto debe fallar"""
        with self.assertRaises(ValidationError):
            validar_ruc_ci("123-45-6")  # Múltiples guiones

    def test_ruc_digitos_incorrectos(self):
        """RUC con cantidad incorrecta de dígitos debe fallar"""
        with self.assertRaises(ValidationError):
            validar_ruc_ci("123-4")  # Muy corto

    def test_ci_muy_corta(self):
        """CI muy corta debe fallar"""
        with self.assertRaises(ValidationError):
            validar_ruc_ci("12345")


class ValidarEmailClienteTest(TestCase):
    """Tests para validación de email de cliente"""

    def test_email_valido(self):
        """Emails válidos deben pasar"""
        emails_validos = [
            "cliente@ejemplo.com",
            "maria.perez@empresa.com.py",
            "usuario+tag@dominio.co",
        ]
        for email in emails_validos:
            try:
                validar_email_cliente(email)
            except ValidationError:  # pragma: no cover
                self.fail(f"Email válido rechazado: {email}")

    def test_email_invalido(self):
        """Emails inválidos deben fallar"""
        with self.assertRaises(ValidationError):
            validar_email_cliente("cliente@")
        with self.assertRaises(ValidationError):
            validar_email_cliente("@ejemplo.com")
        with self.assertRaises(ValidationError):
            validar_email_cliente("cliente.ejemplo.com")

    def test_email_opcional(self):
        """Email None o vacío debe pasar (es opcional)"""
        try:
            validar_email_cliente(None)
            validar_email_cliente("")
        except ValidationError:  # pragma: no cover
            self.fail("Email opcional rechazado")

    def test_email_con_espacios(self):
        """Email con espacios debe fallar"""
        with self.assertRaises(ValidationError):
            validar_email_cliente("cliente @ejemplo.com")


class ValidarTelefonoClienteTest(TestCase):
    """Tests para validación de teléfono paraguayo"""

    def test_telefono_movil_valido(self):
        """Teléfonos móviles válidos deben pasar"""
        moviles_validos = [
            "0981123456",
            "0981-123456",
            "0981 123 456",
        ]
        for movil in moviles_validos:
            try:
                validar_telefono_cliente(movil)
            except ValidationError:  # pragma: no cover
                self.fail(f"Móvil válido rechazado: {movil}")

    def test_telefono_fijo_valido(self):
        """Teléfonos fijos válidos deben pasar"""
        fijos_validos = [
            "021123456",
            "021-123456",
            "021 123 456",
        ]
        for fijo in fijos_validos:
            try:
                validar_telefono_cliente(fijo)
            except ValidationError:  # pragma: no cover
                self.fail(f"Fijo válido rechazado: {fijo}")

    def test_telefono_sin_cero_inicial(self):
        """Teléfono sin 0 inicial debe fallar"""
        with self.assertRaises(ValidationError):
            validar_telefono_cliente("981123456")

    def test_telefono_movil_incompleto(self):
        """Móvil incompleto debe fallar"""
        with self.assertRaises(ValidationError):
            validar_telefono_cliente("09811234")  # Solo 8 dígitos

    def test_telefono_opcional(self):
        """Teléfono None o vacío debe pasar (es opcional)"""
        try:
            validar_telefono_cliente(None)
            validar_telefono_cliente("")
        except ValidationError:  # pragma: no cover
            self.fail("Teléfono opcional rechazado")

    def test_telefono_con_letras(self):
        """Teléfono con letras debe fallar"""
        with self.assertRaises(ValidationError):
            validar_telefono_cliente("0981ABC123")


class ValidarLimiteCreditoClienteTest(TestCase):
    """Tests para validación de límite de crédito"""

    def test_limite_credito_valido(self):
        """Límites de crédito válidos deben pasar"""
        limites_validos = [
            Decimal("0"),
            Decimal("1000.00"),
            Decimal("50000.50"),
            Decimal("10000000.00"),
        ]
        for limite in limites_validos:
            try:
                validar_limite_credito_cliente(limite)
            except ValidationError:  # pragma: no cover
                self.fail(f"Límite válido rechazado: {limite}")

    def test_limite_credito_negativo(self):
        """Límite de crédito negativo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_limite_credito_cliente(Decimal("-1000.00"))

    def test_limite_credito_excesivo(self):
        """Límite de crédito excesivo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_limite_credito_cliente(Decimal("51000000.00"))

    def test_limite_credito_muchos_decimales(self):
        """Límite con más de 2 decimales debe fallar"""
        with self.assertRaises(ValidationError):
            validar_limite_credito_cliente(Decimal("1000.123"))

    def test_limite_credito_opcional(self):
        """Límite None debe pasar (es opcional)"""
        try:
            validar_limite_credito_cliente(None)
        except ValidationError:  # pragma: no cover
            self.fail("Límite opcional rechazado")


class ValidarDireccionClienteTest(TestCase):
    """Tests para validación de dirección de cliente"""

    def test_direccion_valida(self):
        """Direcciones válidas deben pasar"""
        direcciones_validas = [
            "Av. Eusebio Ayala 1234",
            "Calle Mayor Bullo c/ Azara",
            "Barrio San Vicente, Manzana 15",
        ]
        for direccion in direcciones_validas:
            try:
                validar_direccion_cliente(direccion)
            except ValidationError:  # pragma: no cover
                self.fail(f"Dirección válida rechazada: {direccion}")

    def test_direccion_muy_corta(self):
        """Dirección muy corta debe fallar"""
        with self.assertRaises(ValidationError):
            validar_direccion_cliente("Av1")

    def test_direccion_muy_larga(self):
        """Dirección muy larga debe fallar"""
        direccion_larga = "A" * 256
        with self.assertRaises(ValidationError):
            validar_direccion_cliente(direccion_larga)

    def test_direccion_opcional(self):
        """Dirección None o vacía debe pasar (es opcional)"""
        try:
            validar_direccion_cliente(None)
            validar_direccion_cliente("")
        except ValidationError:  # pragma: no cover
            self.fail("Dirección opcional rechazada")


# ============================================================================
# TESTS DE VALIDADORES DE TIPOS DE CLIENTE
# ============================================================================


class ValidarNombreTipoClienteTest(TestCase):
    """Tests para validación de nombre de tipo de cliente"""

    def test_nombre_tipo_valido(self):
        """Nombres de tipo válidos deben pasar"""
        nombres_validos = [
            "Mayorista",
            "Minorista",
            "Estudiante",
            "Profesor 2024",
        ]
        for nombre in nombres_validos:
            try:
                validar_nombre_tipo_cliente(nombre)
            except ValidationError:  # pragma: no cover
                self.fail(f"Nombre de tipo válido rechazado: {nombre}")

    def test_nombre_tipo_muy_corto(self):
        """Nombre de tipo muy corto debe fallar"""
        with self.assertRaises(ValidationError):
            validar_nombre_tipo_cliente("AB")

    def test_nombre_tipo_muy_largo(self):
        """Nombre de tipo muy largo debe fallar"""
        nombre_largo = "A" * 51
        with self.assertRaises(ValidationError):
            validar_nombre_tipo_cliente(nombre_largo)

    def test_nombre_tipo_con_caracteres_especiales(self):
        """Nombre de tipo con caracteres especiales debe fallar"""
        with self.assertRaises(ValidationError):
            validar_nombre_tipo_cliente("Cliente@VIP")


# ============================================================================
# TESTS DE VALIDADORES DE HIJOS
# ============================================================================


class ValidarNombreHijoTest(TestCase):
    """Tests para validación de nombre de hijo/estudiante"""

    def test_nombre_hijo_valido(self):
        """Nombres de estudiante válidos deben pasar"""
        nombres_validos = [
            "Juan",
            "María José",
            "O'Connor",
            "Jean-Pierre",
        ]
        for nombre in nombres_validos:
            try:
                validar_nombre_hijo(nombre)
            except ValidationError:  # pragma: no cover
                self.fail(f"Nombre válido rechazado: {nombre}")

    def test_nombre_hijo_muy_corto(self):
        """Nombre muy corto debe fallar"""
        with self.assertRaises(ValidationError):
            validar_nombre_hijo("A")

    def test_nombre_hijo_muy_largo(self):
        """Nombre muy largo debe fallar"""
        nombre_largo = "A" * 101
        with self.assertRaises(ValidationError):
            validar_nombre_hijo(nombre_largo)

    def test_nombre_hijo_con_numeros(self):
        """Nombre con números debe fallar"""
        with self.assertRaises(ValidationError):
            validar_nombre_hijo("Juan123")


class ValidarApellidoHijoTest(TestCase):
    """Tests para validación de apellido de hijo/estudiante"""

    def test_apellido_hijo_valido(self):
        """Apellidos de estudiante válidos deben pasar"""
        apellidos_validos = [
            "Pérez",
            "García López",
            "O'Brien",
        ]
        for apellido in apellidos_validos:
            try:
                validar_apellido_hijo(apellido)
            except ValidationError:  # pragma: no cover
                self.fail(f"Apellido válido rechazado: {apellido}")

    def test_apellido_hijo_muy_corto(self):
        """Apellido muy corto debe fallar"""
        with self.assertRaises(ValidationError):
            validar_apellido_hijo("P")

    def test_apellido_hijo_muy_largo(self):
        """Apellido muy largo debe fallar"""
        apellido_largo = "P" * 101
        with self.assertRaises(ValidationError):
            validar_apellido_hijo(apellido_largo)

    def test_apellido_hijo_con_numeros(self):
        """Apellido con números debe fallar"""
        with self.assertRaises(ValidationError):
            validar_apellido_hijo("Pérez123")


class ValidarFechaNacimientoTest(TestCase):
    """Tests para validación de fecha de nacimiento"""

    def test_fecha_nacimiento_valida(self):
        """Fechas de nacimiento válidas deben pasar"""
        fechas_validas = [
            date.today() - timedelta(days=365 * 5),  # 5 años
            date.today() - timedelta(days=365 * 10),  # 10 años
            date.today() - timedelta(days=365 * 18),  # 18 años
        ]
        for fecha in fechas_validas:
            try:
                validar_fecha_nacimiento(fecha)
            except ValidationError:  # pragma: no cover
                self.fail(f"Fecha válida rechazada: {fecha}")

    def test_fecha_nacimiento_futura(self):
        """Fecha de nacimiento futura debe fallar"""
        fecha_futura = date.today() + timedelta(days=1)
        with self.assertRaises(ValidationError):
            validar_fecha_nacimiento(fecha_futura)

    def test_fecha_nacimiento_muy_antigua(self):
        """Fecha de nacimiento muy antigua debe fallar"""
        fecha_antigua = date(1949, 1, 1)
        with self.assertRaises(ValidationError):
            validar_fecha_nacimiento(fecha_antigua)

    def test_fecha_nacimiento_muy_reciente(self):
        """Fecha muy reciente (menor de 3 años) debe fallar"""
        fecha_reciente = date.today() - timedelta(days=365 * 2)  # 2 años
        with self.assertRaises(ValidationError):
            validar_fecha_nacimiento(fecha_reciente)

    def test_fecha_nacimiento_muy_vieja(self):
        """Fecha muy vieja (mayor de 25 años) debe fallar"""
        fecha_vieja = date.today() - timedelta(days=365 * 26)  # 26 años
        with self.assertRaises(ValidationError):
            validar_fecha_nacimiento(fecha_vieja)

    def test_fecha_nacimiento_opcional(self):
        """Fecha None debe pasar (es opcional)"""
        try:
            validar_fecha_nacimiento(None)
        except ValidationError:  # pragma: no cover
            self.fail("Fecha opcional rechazada")


class ValidarGradoHijoTest(TestCase):
    """Tests para validación de grado de hijo"""

    def test_grado_valido(self):
        """Grados válidos deben pasar"""
        grados_validos = [
            "1° Grado",
            "Preescolar",
            "6to Grado",
        ]
        for grado in grados_validos:
            try:
                validar_grado_hijo(grado)
            except ValidationError:  # pragma: no cover
                self.fail(f"Grado válido rechazado: {grado}")

    def test_grado_muy_corto(self):
        """Grado muy corto debe fallar"""
        with self.assertRaises(ValidationError):
            validar_grado_hijo("1")

    def test_grado_muy_largo(self):
        """Grado muy largo debe fallar"""
        grado_largo = "G" * 51
        with self.assertRaises(ValidationError):
            validar_grado_hijo(grado_largo)

    def test_grado_opcional(self):
        """Grado None o vacío debe pasar (es opcional)"""
        try:
            validar_grado_hijo(None)
            validar_grado_hijo("")
        except ValidationError:  # pragma: no cover
            self.fail("Grado opcional rechazado")


class ValidarFotoPerfilTest(TestCase):
    """Tests para validación de URL de foto de perfil"""

    def test_foto_url_valida(self):
        """URLs de foto válidas deben pasar"""
        urls_validas = [
            "https://example.com/foto.jpg",
            "http://cdn.ejemplo.com/perfil/123.png",
        ]
        for url in urls_validas:
            try:
                validar_foto_perfil(url)
            except ValidationError:  # pragma: no cover
                self.fail(f"URL válida rechazada: {url}")

    def test_foto_path_valido(self):
        """Paths de foto válidos deben pasar"""
        paths_validos = [
            "/media/fotos/perfil123.jpg",
            "fotos/estudiantes/2024/juan.png",
        ]
        for path in paths_validos:
            try:
                validar_foto_perfil(path)
            except ValidationError:  # pragma: no cover
                self.fail(f"Path válido rechazado: {path}")

    def test_foto_url_invalida(self):
        """URL de foto inválida debe fallar"""
        with self.assertRaises(ValidationError):
            validar_foto_perfil("http://")

    def test_foto_muy_larga(self):
        """URL muy larga debe fallar"""
        url_larga = "https://example.com/" + "a" * 250
        with self.assertRaises(ValidationError):
            validar_foto_perfil(url_larga)

    def test_foto_opcional(self):
        """Foto None o vacía debe pasar (es opcional)"""
        try:
            validar_foto_perfil(None)
            validar_foto_perfil("")
        except ValidationError:  # pragma: no cover
            self.fail("Foto opcional rechazada")


# ============================================================================
# TESTS DE VALIDADORES DE GRADOS
# ============================================================================


class ValidarNombreGradoTest(TestCase):
    """Tests para validación de nombre de grado"""

    def test_nombre_grado_valido(self):
        """Nombres de grado válidos deben pasar"""
        nombres_validos = [
            "1° Grado",
            "Preescolar",
            "6to Grado",
            "Bachillerato Científico",
        ]
        for nombre in nombres_validos:
            try:
                validar_nombre_grado(nombre)
            except ValidationError:  # pragma: no cover
                self.fail(f"Nombre de grado válido rechazado: {nombre}")

    def test_nombre_grado_muy_corto(self):
        """Nombre muy corto debe fallar"""
        with self.assertRaises(ValidationError):
            validar_nombre_grado("1")

    def test_nombre_grado_muy_largo(self):
        """Nombre muy largo debe fallar"""
        nombre_largo = "G" * 51
        with self.assertRaises(ValidationError):
            validar_nombre_grado(nombre_largo)

    def test_nombre_grado_con_caracteres_especiales(self):
        """Nombre con caracteres no permitidos debe fallar"""
        with self.assertRaises(ValidationError):
            validar_nombre_grado("Grado@2024")


class ValidarNivelGradoTest(TestCase):
    """Tests para validación de nivel de grado"""

    def test_nivel_grado_valido(self):
        """Niveles válidos (1-12) deben pasar"""
        for nivel in range(1, 13):
            try:
                validar_nivel_grado(nivel)
            except ValidationError:  # pragma: no cover
                self.fail(f"Nivel válido rechazado: {nivel}")

    def test_nivel_grado_cero(self):
        """Nivel 0 debe fallar"""
        with self.assertRaises(ValidationError):
            validar_nivel_grado(0)

    def test_nivel_grado_negativo(self):
        """Nivel negativo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_nivel_grado(-1)

    def test_nivel_grado_excesivo(self):
        """Nivel > 12 debe fallar"""
        with self.assertRaises(ValidationError):
            validar_nivel_grado(13)

    def test_nivel_grado_none(self):
        """Nivel None debe fallar (es obligatorio)"""
        with self.assertRaises(ValidationError):
            validar_nivel_grado(None)


class ValidarOrdenVisualizacionTest(TestCase):
    """Tests para validación de orden de visualización"""

    def test_orden_valido(self):
        """Órdenes válidos (1-100) deben pasar"""
        ordenes_validos = [1, 10, 50, 100]
        for orden in ordenes_validos:
            try:
                validar_orden_visualizacion(orden)
            except ValidationError:  # pragma: no cover
                self.fail(f"Orden válido rechazado: {orden}")

    def test_orden_cero(self):
        """Orden 0 debe fallar"""
        with self.assertRaises(ValidationError):
            validar_orden_visualizacion(0)

    def test_orden_negativo(self):
        """Orden negativo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_orden_visualizacion(-1)

    def test_orden_excesivo(self):
        """Orden > 100 debe fallar"""
        with self.assertRaises(ValidationError):
            validar_orden_visualizacion(101)

    def test_orden_none(self):
        """Orden None debe fallar (es obligatorio)"""
        with self.assertRaises(ValidationError):
            validar_orden_visualizacion(None)


# ============================================================================
# TESTS DE VALIDADORES DE HISTORIAL DE GRADOS
# ============================================================================


class ValidarAnioEscolarTest(TestCase):
    """Tests para validación de año escolar"""

    def test_anio_escolar_valido(self):
        """Años escolares válidos deben pasar"""
        anio_actual = date.today().year
        anios_validos = [anio_actual - 1, anio_actual, anio_actual + 1]
        for anio in anios_validos:
            try:
                validar_anio_escolar(anio)
            except ValidationError:  # pragma: no cover
                self.fail(f"Año válido rechazado: {anio}")

    def test_anio_escolar_muy_antiguo(self):
        """Año muy antiguo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_anio_escolar(1989)

    def test_anio_escolar_muy_futuro(self):
        """Año muy futuro debe fallar"""
        anio_futuro = date.today().year + 2
        with self.assertRaises(ValidationError):
            validar_anio_escolar(anio_futuro)

    def test_anio_escolar_none(self):
        """Año None debe fallar (es obligatorio)"""
        with self.assertRaises(ValidationError):
            validar_anio_escolar(None)


class ValidarMotivoCambioGradoTest(TestCase):
    """Tests para validación de motivo de cambio de grado"""

    def test_motivos_validos(self):
        """Motivos válidos deben pasar"""
        motivos_validos = [
            "Promoción",
            "Repetición",
            "Transferencia",
            "Corrección",
            "Otro",
        ]
        for motivo in motivos_validos:
            try:
                validar_motivo_cambio_grado(motivo)
            except ValidationError:  # pragma: no cover
                self.fail(f"Motivo válido rechazado: {motivo}")

    def test_motivo_invalido(self):
        """Motivo inválido debe fallar"""
        with self.assertRaises(ValidationError):
            validar_motivo_cambio_grado("Expulsión")

    def test_motivo_vacio(self):
        """Motivo vacío debe fallar"""
        with self.assertRaises(ValidationError):
            validar_motivo_cambio_grado("")

    def test_motivo_none(self):
        """Motivo None debe fallar (es obligatorio)"""
        with self.assertRaises(ValidationError):
            validar_motivo_cambio_grado(None)


class ValidarCambioGradoTest(TestCase):
    """Tests para validación de cambio de grado"""

    def test_cambio_grado_valido(self):
        """Cambio de grado válido debe pasar"""
        try:
            validar_cambio_grado("1° Grado", "2° Grado")
        except ValidationError:  # pragma: no cover
            self.fail("Cambio válido rechazado")

    def test_cambio_grado_sin_anterior(self):
        """Cambio sin grado anterior (inscripción nueva) debe pasar"""
        try:
            validar_cambio_grado(None, "1° Grado")
        except ValidationError:  # pragma: no cover
            self.fail("Inscripción nueva rechazada")

    def test_cambio_grado_mismo(self):
        """Cambio al mismo grado debe fallar"""
        with self.assertRaises(ValidationError):
            validar_cambio_grado("1° Grado", "1° Grado")

    def test_cambio_grado_sin_nuevo(self):
        """Cambio sin grado nuevo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_cambio_grado("1° Grado", None)

    def test_cambio_a_sin_grado(self):
        """Cambio a 'Sin grado' debe fallar"""
        with self.assertRaises(ValidationError):
            validar_cambio_grado("1° Grado", "Sin grado")


# ============================================================================
# TESTS DE VALIDADORES DE RESTRICCIONES
# ============================================================================


class ValidarTipoRestriccionTest(TestCase):
    """Tests para validación de tipo de restricción"""

    def test_tipo_restriccion_valido(self):
        """Tipos de restricción válidos deben pasar"""
        tipos_validos = [
            "Alergia",
            "Intolerancia alimentaria",
            "Restricción médica",
        ]
        for tipo in tipos_validos:
            try:
                validar_tipo_restriccion(tipo)
            except ValidationError:  # pragma: no cover
                self.fail(f"Tipo válido rechazado: {tipo}")

    def test_tipo_restriccion_muy_corto(self):
        """Tipo muy corto debe fallar"""
        with self.assertRaises(ValidationError):
            validar_tipo_restriccion("Al")

    def test_tipo_restriccion_muy_largo(self):
        """Tipo muy largo debe fallar"""
        tipo_largo = "A" * 101
        with self.assertRaises(ValidationError):
            validar_tipo_restriccion(tipo_largo)

    def test_tipo_restriccion_con_caracteres_especiales(self):
        """Tipo con caracteres no permitidos debe fallar"""
        with self.assertRaises(ValidationError):
            validar_tipo_restriccion("Alergia@Especial")


class ValidarDescripcionRestriccionTest(TestCase):
    """Tests para validación de descripción de restricción"""

    def test_descripcion_valida(self):
        """Descripciones válidas deben pasar"""
        descripcion = "El estudiante presenta alergia severa al maní y derivados"
        try:
            validar_descripcion_restriccion(descripcion)
        except ValidationError:  # pragma: no cover
            self.fail("Descripción válida rechazada")

    def test_descripcion_muy_corta(self):
        """Descripción muy corta debe fallar"""
        with self.assertRaises(ValidationError):
            validar_descripcion_restriccion("Alergia")

    def test_descripcion_muy_larga(self):
        """Descripción muy larga debe fallar"""
        descripcion_larga = "A" * 501
        with self.assertRaises(ValidationError):
            validar_descripcion_restriccion(descripcion_larga)

    def test_descripcion_opcional(self):
        """Descripción None o vacía debe pasar (es opcional)"""
        try:
            validar_descripcion_restriccion(None)
            validar_descripcion_restriccion("")
        except ValidationError:  # pragma: no cover
            self.fail("Descripción opcional rechazada")


class ValidarSeveridadRestriccionTest(TestCase):
    """Tests para validación de severidad de restricción"""

    def test_severidades_validas(self):
        """Severidades válidas deben pasar"""
        severidades_validas = ["Baja", "Media", "Alta", "Crítica"]
        for severidad in severidades_validas:
            try:
                validar_severidad_restriccion(severidad)
            except ValidationError:  # pragma: no cover
                self.fail(f"Severidad válida rechazada: {severidad}")

    def test_severidad_invalida(self):
        """Severidad inválida debe fallar"""
        with self.assertRaises(ValidationError):
            validar_severidad_restriccion("Moderada")

    def test_severidad_vacia(self):
        """Severidad vacía debe fallar"""
        with self.assertRaises(ValidationError):
            validar_severidad_restriccion("")

    def test_severidad_none(self):
        """Severidad None debe fallar (es obligatorio)"""
        with self.assertRaises(ValidationError):
            validar_severidad_restriccion(None)


class ValidarObservacionesRestriccionTest(TestCase):
    """Tests para validación de observaciones de restricción"""

    def test_observaciones_validas(self):
        """Observaciones válidas deben pasar"""
        observaciones = "Los padres han proporcionado EpiPen para emergencias"
        try:
            validar_observaciones_restriccion(observaciones)
        except ValidationError:  # pragma: no cover
            self.fail("Observaciones válidas rechazadas")

    def test_observaciones_muy_largas(self):
        """Observaciones muy largas deben fallar"""
        observaciones_largas = "A" * 1001
        with self.assertRaises(ValidationError):
            validar_observaciones_restriccion(observaciones_largas)

    def test_observaciones_opcionales(self):
        """Observaciones None o vacías deben pasar (es opcional)"""
        try:
            validar_observaciones_restriccion(None)
            validar_observaciones_restriccion("")
        except ValidationError:  # pragma: no cover
            self.fail("Observaciones opcionales rechazadas")


# ============================================================================
# TESTS DE VALIDADORES DE AUTORIZACIONES
# ============================================================================


class ValidarMontoAutorizadoTest(TestCase):
    """Tests para validación de monto autorizado"""

    def test_monto_autorizado_valido(self):
        """Montos autorizados válidos deben pasar"""
        montos_validos = [
            Decimal("100.00"),
            Decimal("5000.50"),
            Decimal("500000.00"),
        ]
        for monto in montos_validos:
            try:
                validar_monto_autorizado(monto)
            except ValidationError:  # pragma: no cover
                self.fail(f"Monto válido rechazado: {monto}")

    def test_monto_autorizado_cero(self):
        """Monto 0 debe fallar"""
        with self.assertRaises(ValidationError):
            validar_monto_autorizado(Decimal("0"))

    def test_monto_autorizado_negativo(self):
        """Monto negativo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_monto_autorizado(Decimal("-1000.00"))

    def test_monto_autorizado_excesivo(self):
        """Monto excesivo debe fallar"""
        with self.assertRaises(ValidationError):
            validar_monto_autorizado(Decimal("6000000.00"))

    def test_monto_autorizado_muchos_decimales(self):
        """Monto con más de 2 decimales debe fallar"""
        with self.assertRaises(ValidationError):
            validar_monto_autorizado(Decimal("1000.123"))


class ValidarSaldosAutorizacionTest(TestCase):
    """Tests para validación de saldos en autorización"""

    def test_saldos_validos(self):
        """Saldos coherentes deben pasar"""
        try:
            validar_saldos_autorizacion(
                saldo_anterior=Decimal("1000.00"),
                saldo_resultante=Decimal("-500.00"),
                monto_autorizado=Decimal("2000.00"),
            )
        except ValidationError:  # pragma: no cover
            self.fail("Saldos válidos rechazados")

    def test_saldo_resultante_mayor(self):
        """Saldo resultante mayor que anterior debe fallar"""
        with self.assertRaises(ValidationError):
            validar_saldos_autorizacion(
                saldo_anterior=Decimal("1000.00"),
                saldo_resultante=Decimal("1500.00"),
                monto_autorizado=Decimal("2000.00"),
            )

    def test_saldo_resultante_excede_autorizacion(self):
        """Saldo resultante que excede autorización debe fallar"""
        with self.assertRaises(ValidationError):
            validar_saldos_autorizacion(
                saldo_anterior=Decimal("0"),
                saldo_resultante=Decimal("-3000.00"),
                monto_autorizado=Decimal("2000.00"),
            )


class ValidarMotivoAutorizacionTest(TestCase):
    """Tests para validación de motivo de autorización"""

    def test_motivo_valido(self):
        """Motivos válidos deben pasar"""
        motivo = "Cliente de confianza, pago pendiente para mañana"
        try:
            validar_motivo_autorizacion(motivo)
        except ValidationError:  # pragma: no cover
            self.fail("Motivo válido rechazado")

    def test_motivo_muy_corto(self):
        """Motivo muy corto debe fallar"""
        with self.assertRaises(ValidationError):
            validar_motivo_autorizacion("Urgente")

    def test_motivo_muy_largo(self):
        """Motivo muy largo debe fallar"""
        motivo_largo = "A" * 501
        with self.assertRaises(ValidationError):
            validar_motivo_autorizacion(motivo_largo)

    def test_motivo_vacio(self):
        """Motivo vacío debe fallar"""
        with self.assertRaises(ValidationError):
            validar_motivo_autorizacion("")


# ============================================================================
# TESTS DE VALIDADORES DE LOGS
# ============================================================================


class ValidarTipoOperacionLogTest(TestCase):
    """Tests para validación de tipo de operación en log"""

    def test_tipos_operacion_validos(self):
        """Tipos de operación válidos deben pasar"""
        tipos_validos = [
            "Lectura",
            "Autorización",
            "Validación",
            "Rechazo",
            "Otro",
        ]
        for tipo in tipos_validos:
            try:
                validar_tipo_operacion_log(tipo)
            except ValidationError:  # pragma: no cover
                self.fail(f"Tipo válido rechazado: {tipo}")

    def test_tipo_operacion_invalido(self):
        """Tipo de operación inválido debe fallar"""
        with self.assertRaises(ValidationError):
            validar_tipo_operacion_log("Eliminación")

    def test_tipo_operacion_vacio(self):
        """Tipo vacío debe fallar"""
        with self.assertRaises(ValidationError):
            validar_tipo_operacion_log("")

    def test_tipo_operacion_none(self):
        """Tipo None debe fallar (es obligatorio)"""
        with self.assertRaises(ValidationError):
            validar_tipo_operacion_log(None)


class ValidarResultadoLogTest(TestCase):
    """Tests para validación de resultado de log"""

    def test_resultados_validos(self):
        """Resultados válidos deben pasar"""
        resultados_validos = ["Exitoso", "Fallido", "Denegado"]
        for resultado in resultados_validos:
            try:
                validar_resultado_log(resultado)
            except ValidationError:  # pragma: no cover
                self.fail(f"Resultado válido rechazado: {resultado}")

    def test_resultado_invalido(self):
        """Resultado inválido debe fallar"""
        with self.assertRaises(ValidationError):
            validar_resultado_log("Pendiente")

    def test_resultado_vacio(self):
        """Resultado vacío debe fallar"""
        with self.assertRaises(ValidationError):
            validar_resultado_log("")

    def test_resultado_none(self):
        """Resultado None debe fallar (es obligatorio)"""
        with self.assertRaises(ValidationError):
            validar_resultado_log(None)


class ValidarIpOrigenTest(TestCase):
    """Tests para validación de IP de origen"""

    def test_ipv4_validas(self):
        """IPs IPv4 válidas deben pasar"""
        ips_validas = [
            "192.168.1.1",
            "10.0.0.1",
            "172.16.0.1",
            "8.8.8.8",
        ]
        for ip in ips_validas:
            try:
                validar_ip_origen(ip)
            except ValidationError:  # pragma: no cover
                self.fail(f"IP válida rechazada: {ip}")

    def test_ipv4_invalidas(self):
        """IPs IPv4 inválidas deben fallar"""
        ips_invalidas = [
            "192.168.1.256",  # Octeto > 255
            "192.168.1",  # Incompleta
            "192.168.1.1.1",  # Demasiados octetos
        ]
        for ip in ips_invalidas:
            with self.assertRaises(ValidationError):
                validar_ip_origen(ip)

    def test_ipv6_validas(self):
        """IPs IPv6 válidas deben pasar"""
        ips_validas = [
            "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
            "fe80::1",
        ]
        for ip in ips_validas:
            try:
                validar_ip_origen(ip)
            except ValidationError:  # pragma: no cover
                self.fail(f"IPv6 válida rechazada: {ip}")

    def test_ip_opcional(self):
        """IP None o vacía debe pasar (es opcional)"""
        try:
            validar_ip_origen(None)
            validar_ip_origen("")
        except ValidationError:  # pragma: no cover
            self.fail("IP opcional rechazada")

    def test_ip_formato_invalido(self):
        """IP con formato inválido debe fallar"""
        with self.assertRaises(ValidationError):
            validar_ip_origen("no-es-una-ip")
