"""
Tests para validadores del módulo common
Verifica validación de RUC/CI para Paraguay
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.common.validators.ruc_validator import validate_ruc


class ValidateRucTest(TestCase):
    """Tests para validador de RUC/CI paraguayo"""

    def test_ci_simple_valido(self):
        """CI simple (solo números) válido"""
        valores_validos = [
            "1234567",  # 7 dígitos
            "123456",  # 6 dígitos
            "12345",  # 5 dígitos
            "1",  # 1 dígito
            "5678901",  # Otro formato válido
        ]

        for valor in valores_validos:
            result = validate_ruc(valor)
            self.assertEqual(result, valor)

    def test_ruc_con_digito_verificador_valido(self):
        """RUC con dígito verificador (XXXXXXX-D) válido"""
        valores_validos = [
            "1234567-8",
            "80012345-6",
            "123-4",
            "12345678-9",
        ]

        for valor in valores_validos:
            result = validate_ruc(valor)
            self.assertEqual(result, valor)

    def test_ruc_con_espacios_valido(self):
        """RUC con espacios se trimea correctamente"""
        ruc_con_espacios = "  1234567-8  "
        result = validate_ruc(ruc_con_espacios)
        self.assertEqual(result, "1234567-8")

    def test_ci_con_espacios_valido(self):
        """CI con espacios se trimea correctamente"""
        ci_con_espacios = "  1234567  "
        result = validate_ruc(ci_con_espacios)
        self.assertEqual(result, "1234567")

    def test_ruc_vacio_invalido(self):
        """RUC/CI vacío es inválido"""
        with self.assertRaises(ValidationError) as context:
            validate_ruc("")

        self.assertIn("requerido", str(context.exception))

    def test_ruc_none_invalido(self):
        """RUC/CI None es inválido"""
        with self.assertRaises(ValidationError) as context:
            validate_ruc(None)

        self.assertIn("requerido", str(context.exception))

    def test_formato_con_letras_invalido(self):
        """Formato con letras es inválido"""
        valores_invalidos = [
            "12345AB",
            "ABC1234",
            "1234567-A",
            "RUC123456",
        ]

        for valor in valores_invalidos:
            with self.assertRaises(ValidationError) as context:
                validate_ruc(valor)

            self.assertIn("Formato inválido", str(context.exception))

    def test_formato_con_multiples_guiones_invalido(self):
        """Formato con múltiples guiones es inválido"""
        valores_invalidos = [
            "123-456-7",
            "12-34-56",
            "1234567--8",
        ]

        for valor in valores_invalidos:
            with self.assertRaises(ValidationError) as context:
                validate_ruc(valor)

            self.assertIn("Formato inválido", str(context.exception))

    def test_formato_con_caracteres_especiales_invalido(self):
        """Formato con caracteres especiales es inválido"""
        valores_invalidos = [
            "1234567@8",
            "123.456-7",
            "1234567/8",
            "1234567 8",  # Espacio en medio
        ]

        for valor in valores_invalidos:
            with self.assertRaises(ValidationError) as context:
                validate_ruc(valor)

            self.assertIn("Formato inválido", str(context.exception))

    def test_ruc_sin_digito_verificador_invalido(self):
        """RUC con guión pero sin dígito verificador es inválido"""
        valores_invalidos = [
            "1234567-",
            "-8",
            "123-",
        ]

        for valor in valores_invalidos:
            with self.assertRaises(ValidationError) as context:
                validate_ruc(valor)

            self.assertIn("Formato inválido", str(context.exception))

    def test_ruc_con_multiples_digitos_verificadores_invalido(self):
        """RUC con múltiples dígitos verificadores es inválido"""
        valores_invalidos = [
            "1234567-89",
            "123-456",
        ]

        for valor in valores_invalidos:
            with self.assertRaises(ValidationError) as context:
                validate_ruc(valor)

            self.assertIn("Formato inválido", str(context.exception))

    def test_ruc_muy_largo_valido(self):
        """RUC de 8 dígitos es válido"""
        ruc_8_digitos = "12345678-9"
        result = validate_ruc(ruc_8_digitos)
        self.assertEqual(result, ruc_8_digitos)

    def test_ci_muy_largo_valido(self):
        """CI de 8 dígitos es válido"""
        ci_8_digitos = "12345678"
        result = validate_ruc(ci_8_digitos)
        self.assertEqual(result, ci_8_digitos)

    def test_ruc_convierte_a_string(self):
        """RUC numérico se convierte a string"""
        ruc_numerico = 1234567
        result = validate_ruc(ruc_numerico)
        self.assertEqual(result, "1234567")

    def test_valores_edge_case(self):
        """Casos edge válidos"""
        valores_edge = [
            "1-2",  # Mínimo RUC con verificador
            "123456789",  # 9 dígitos sin verificador (¿válido?)
            # Nota: El validador permite hasta 8 dígitos + guión + 1 dígito
        ]

        # Verificar cuáles son válidos según la implementación
        result = validate_ruc("1-2")
        self.assertEqual(result, "1-2")
