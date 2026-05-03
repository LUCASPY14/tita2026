"""
Servicio de integración con SIPAP (Sistema de Pagos del Paraguay)
API de pagos QR nativo regulado por Banco Central del Paraguay

Flujo:
1. Comercio genera QR dinámico con monto y descripción
2. Cliente escanea QR con app bancaria (Zimple, Continental, Atlas, etc.)
3. Red SIPAP procesa pago entre bancos
4. Banco notifica via webhook con firma RSA
5. Sistema valida firma y aplica pago automáticamente

Documentación:
- Banco Central: https://www.bcp.gov.py/sipap
- Estándar EMVCo: https://www.emvco.com/emv-technologies/qrcodes/
"""

import base64
import hashlib
import hmac
import io
import json
from datetime import timedelta
from decimal import Decimal
from typing import Any, Dict

from django.conf import settings
from django.db import transaction
from django.utils import timezone

import qrcode
import requests
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from apps.api_integrations.models import LogsLlamadasApi, ProveedoresApi
from apps.cobros.models import AplicacionPagosClientes, PagosClientes
from apps.ventas.models import Ventas


class SIPAPService:
    """
    Servicio para integración con SIPAP - Sistema de Pagos QR del Paraguay

    Características:
    - QR dinámico con expiración configurable (default 15 min)
    - Validación de firma RSA-2048 en webhooks
    - Aplicación automática de pagos a facturas (FIFO)
    - Soporte multi-banco (Continental, Atlas, Itaú, etc.)
    - Logging completo de transacciones
    """

    def __init__(self, ambiente: str = None, banco_agregador: str = None):
        """
        Inicializa el servicio con credenciales SIPAP

        Args:
            ambiente: 'sandbox' o 'produccion'. Si None, toma de settings.
            banco_agregador: Banco agregador (continental, atlas, itau). Si None, toma de settings.
        """
        self.ambiente = ambiente or settings.SIPAP_AMBIENTE
        self.banco_agregador = banco_agregador or settings.SIPAP_BANCO_AGREGADOR
        self.merchant_id = settings.SIPAP_MERCHANT_ID
        self.api_key = settings.SIPAP_API_KEY
        self.api_secret = settings.SIPAP_API_SECRET
        self.banco_public_key = settings.SIPAP_BANCO_PUBLIC_KEY

        # URL base según ambiente y banco
        api_urls = settings.SIPAP_API_URLS.get(self.ambiente, {})
        self.base_url = api_urls.get(self.banco_agregador, "")

        if not self.base_url:
            raise ValueError(f"URL no configurada para ambiente={self.ambiente}, banco={self.banco_agregador}")

        # Obtener o crear registro de proveedor API
        self.proveedor_api, _ = ProveedoresApi.objects.get_or_create(
            nombre="SIPAP",
            defaults={
                "url_base": self.base_url,
                "tipo_autenticacion": "API_KEY",
                "descripcion": f"Sistema de Pagos QR - {self.banco_agregador.upper()}",
                "activo": True,
            },
        )

    def generar_qr_dinamico(
        self, id_cobro: int, monto: Decimal, descripcion: str, id_cliente: int = None
    ) -> Dict[str, Any]:
        """
        Genera un QR dinámico SIPAP para cobro

        Args:
            id_cobro: ID del registro de cobro
            monto: Monto a cobrar en Guaraníes
            descripcion: Descripción del pago (ej: "Pago cantina - 5 facturas")
            id_cliente: ID del cliente (opcional, para tracking)

        Returns:
            {
                'qr_image': 'data:image/png;base64,...',  # Imagen QR en base64
                'qr_string': '00020126...',  # String EMVCo para apps
                'txn_id': 'COB-123-1713308400',  # ID único de transacción
                'expira_en': 900,  # Segundos hasta expiración
                'expira_at': '2026-04-16T15:30:00Z'  # Timestamp exacto
            }
        """
        # Generar ID de transacción único
        timestamp = int(timezone.now().timestamp())
        txn_id = f"COB-{id_cobro}-{timestamp}"

        # Calcular fecha de expiración
        expira_minutos = settings.SIPAP_QR_EXPIRACION_MINUTOS
        expira_at = timezone.now() + timedelta(minutes=expira_minutos)

        # Payload para API del banco
        payload = {
            "merchant_id": self.merchant_id,
            "txn_id": txn_id,
            "monto": str(monto),  # Guaraníes sin decimales
            "moneda": "PYG",
            "descripcion": descripcion[:50],  # Máximo 50 caracteres
            "expira_at": expira_at.isoformat(),
            "callback_url": self._get_callback_url(),
            "metadata": {"id_cobro": id_cobro, "id_cliente": id_cliente, "generado_en": timezone.now().isoformat()},
        }

        try:
            # Llamar API del banco agregador
            headers = self._generar_headers(payload)

            response = requests.post(f"{self.base_url}/qr/dinamico", json=payload, headers=headers, timeout=30)

            # Log de la llamada
            self._log_llamada_api(
                endpoint="/qr/dinamico",
                metodo="POST",
                payload=payload,
                response_code=response.status_code,
                response_data=response.json() if response.ok else response.text,
            )

            if not response.ok:
                raise Exception(f"Error API SIPAP: {response.status_code} - {response.text}")

            data = response.json()

            # Extraer string QR EMVCo
            qr_string = data.get("qr_code", "")

            if not qr_string:
                raise Exception("API no retornó string QR")

            # Generar imagen QR
            qr_image = self._generar_imagen_qr(qr_string)

            return {
                "qr_image": qr_image,
                "qr_string": qr_string,
                "txn_id": txn_id,
                "expira_en": expira_minutos * 60,  # Convertir a segundos
                "expira_at": expira_at.isoformat(),
                "banco": self.banco_agregador,
                "ambiente": self.ambiente,
            }

        except requests.exceptions.RequestException as e:
            # Error de red/timeout
            self._log_llamada_api(
                endpoint="/qr/dinamico",
                metodo="POST",
                payload=payload,
                response_code=0,
                response_data=str(e),
                error=str(e),
            )
            raise Exception(f"Error al conectar con SIPAP: {str(e)}")

        except Exception as e:
            raise Exception(f"Error al generar QR SIPAP: {str(e)}")

    def procesar_webhook(self, payload: Dict[str, Any], firma: str, ip_origen: str) -> Dict[str, Any]:
        """
        Procesa webhook de confirmación de pago desde SIPAP

        Args:
            payload: Datos del webhook
            firma: Firma RSA del banco (header X-SIPAP-Signature)
            ip_origen: IP de origen del request

        Returns:
            {
                'success': True/False,
                'mensaje': 'Descripción del resultado',
                'id_pago_cliente': 123  # Si se aplicó exitosamente
            }
        """
        try:
            # 1. Validar IP de origen
            if not self._validar_ip_origen(ip_origen):
                raise Exception(f"IP no autorizada: {ip_origen}")

            # 2. Validar firma RSA del banco
            if not self._validar_firma_webhook(payload, firma):
                raise Exception("Firma RSA inválida - webhook rechazado")

            # 3. Extraer datos del webhook
            txn_id = payload.get("txn_id")
            estado = payload.get("estado")  # 'aprobado', 'rechazado', 'expirado'
            monto = Decimal(payload.get("monto", "0"))
            banco_origen = payload.get("banco_origen")
            referencia_bancaria = payload.get("referencia_bancaria")
            fecha_pago = payload.get("fecha_pago")
            metadata = payload.get("metadata", {})

            # Log del webhook
            self._log_llamada_api(
                endpoint="/webhook",
                metodo="POST",
                payload=payload,
                response_code=200,
                response_data={"estado": estado, "validado": True},
            )

            # 4. Verificar estado
            if estado != "aprobado":
                return {"success": False, "mensaje": f"Pago no aprobado - Estado: {estado}", "txn_id": txn_id}

            # 5. Extraer ID de cobro del txn_id
            # Formato: COB-{id_cobro}-{timestamp}
            int(txn_id.split("-")[1])
            id_cliente = metadata.get("id_cliente")

            # 6. Verificar si ya fue procesado (idempotencia)
            if PagosClientes.objects.filter(referencia=txn_id).exists():
                return {"success": True, "mensaje": "Pago ya procesado anteriormente (duplicado)", "txn_id": txn_id}

            # 7. Registrar pago en el sistema
            with transaction.atomic():
                # Obtener medio de pago SIPAP QR
                from apps.core.models import MediosPago

                medio_pago_sipap, _ = MediosPago.objects.get_or_create(
                    descripcion="SIPAP QR", defaults={"activo": True, "requiere_autorizacion": False}
                )

                # Crear registro de pago
                pago = PagosClientes.objects.create(
                    id_cliente_id=id_cliente,
                    monto_total=monto,
                    fecha_pago=fecha_pago or timezone.now(),
                    id_medio_pago=medio_pago_sipap,
                    referencia=txn_id,
                    banco_emisor=banco_origen,
                    observaciones=f"Pago SIPAP QR - Ref: {referencia_bancaria}",
                    estado="aplicado",
                )

                # Obtener facturas pendientes del cliente (FIFO)
                facturas_pendientes = Ventas.objects.filter(id_cliente_id=id_cliente, estado="pendiente").order_by(
                    "fecha_venta"
                )

                # Aplicar pago a facturas (FIFO)
                monto_restante = monto

                for factura in facturas_pendientes:
                    if monto_restante <= 0:
                        break

                    saldo_factura = factura.total - factura.monto_pagado

                    if saldo_factura <= 0:
                        continue

                    # Determinar cuánto aplicar a esta factura
                    monto_a_aplicar = min(monto_restante, saldo_factura)

                    # Crear aplicación
                    AplicacionPagosClientes.objects.create(
                        id_pago_cliente=pago,
                        id_venta=factura,
                        monto_aplicado=monto_a_aplicar,
                        fecha_aplicacion=timezone.now(),
                    )

                    # Actualizar monto pagado de la factura
                    factura.monto_pagado += monto_a_aplicar

                    # Si se pagó completa, marcar como pagada
                    if factura.monto_pagado >= factura.total:
                        factura.estado = "pagada"

                    factura.save()

                    monto_restante -= monto_a_aplicar

                return {
                    "success": True,
                    "mensaje": f"Pago procesado exitosamente - {monto} aplicados",
                    "id_pago_cliente": pago.id_pago_cliente,
                    "txn_id": txn_id,
                    "monto": float(monto),
                    "facturas_aplicadas": facturas_pendientes.count(),
                }

        except Exception as e:
            # Log de error
            self._log_llamada_api(
                endpoint="/webhook",
                metodo="POST",
                payload=payload,
                response_code=500,
                response_data=str(e),
                error=str(e),
            )

            return {
                "success": False,
                "mensaje": f"Error al procesar webhook: {str(e)}",
                "txn_id": payload.get("txn_id"),
            }

    def _validar_firma_webhook(self, payload: Dict[str, Any], firma: str) -> bool:
        """
        Valida la firma RSA del webhook usando la clave pública del banco

        Args:
            payload: Datos del webhook
            firma: Firma RSA en base64

        Returns:
            True si la firma es válida, False caso contrario
        """
        try:
            # Si no hay clave pública configurada, solo en sandbox/desarrollo
            if not self.banco_public_key:
                if self.ambiente == "sandbox":
                    # En sandbox permitir sin validación (para testing)
                    return True
                else:
                    # En producción es obligatorio
                    raise Exception("Clave pública RSA del banco no configurada")

            # Convertir payload a string canónico (ordenado)
            payload_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))
            payload_bytes = payload_str.encode("utf-8")

            # Decodificar firma de base64
            firma_bytes = base64.b64decode(firma)

            # Cargar clave pública RSA del banco
            public_key = serialization.load_pem_public_key(
                self.banco_public_key.encode("utf-8"), backend=default_backend()
            )

            # Verificar firma RSA con SHA-256
            public_key.verify(firma_bytes, payload_bytes, padding.PKCS1v15(), hashes.SHA256())

            return True

        except InvalidSignature:
            return False
        except Exception as e:
            print(f"Error al validar firma: {str(e)}")
            return False

    def _validar_ip_origen(self, ip: str) -> bool:
        """
        Valida que la IP de origen esté en la whitelist

        Args:
            ip: Dirección IP de origen

        Returns:
            True si está permitida, False caso contrario
        """
        whitelist = settings.SIPAP_IP_WHITELIST

        # En desarrollo/sandbox, permitir localhost
        if self.ambiente == "sandbox":
            localhost_ips = ["127.0.0.1", "::1", "localhost"]
            if ip in localhost_ips:
                return True

        return ip in whitelist

    def _generar_imagen_qr(self, qr_string: str) -> str:
        """
        Genera imagen QR PNG y la retorna como base64

        Args:
            qr_string: String EMVCo del QR

        Returns:
            String base64 con formato data:image/png;base64,...
        """
        # Crear objeto QR
        qr = qrcode.QRCode(
            version=None,  # Auto-detectar tamaño
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )

        qr.add_data(qr_string)
        qr.make(fit=True)

        # Generar imagen
        img = qr.make_image(fill_color="black", back_color="white")

        # Convertir a bytes
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_bytes = buffer.getvalue()

        # Codificar en base64
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")

        return f"data:image/png;base64,{img_base64}"

    def _generar_headers(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """
        Genera headers HTTP con autenticación HMAC-SHA256

        Args:
            payload: Datos del request

        Returns:
            Headers HTTP con firma HMAC
        """
        # Convertir payload a string canónico
        payload_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))

        # Generar firma HMAC-SHA256
        signature = hmac.new(self.api_secret.encode("utf-8"), payload_str.encode("utf-8"), hashlib.sha256).hexdigest()

        return {
            "Content-Type": "application/json",
            "X-SIPAP-API-Key": self.api_key,
            "X-SIPAP-Signature": signature,
            "X-SIPAP-Timestamp": str(int(timezone.now().timestamp())),
            "User-Agent": "CantinaTita/1.0",
        }

    def _get_callback_url(self) -> str:
        """
        Retorna la URL del webhook para recibir confirmaciones

        Returns:
            URL completa del webhook
        """
        # En producción usar dominio real
        if self.ambiente == "produccion":
            base_domain = "https://api.cantina.tita"  # Actualizar con dominio real
        else:
            base_domain = "http://127.0.0.1:8000"

        return f"{base_domain}/api/v1/webhooks/sipap/"

    def _log_llamada_api(
        self,
        endpoint: str,
        metodo: str,
        payload: Dict[str, Any],
        response_code: int,
        response_data: Any,
        error: str = None,
    ):
        """
        Registra llamada a la API en base de datos para auditoría

        Args:
            endpoint: Endpoint llamado
            metodo: Método HTTP (GET, POST, etc.)
            payload: Datos enviados
            response_code: Código HTTP de respuesta
            response_data: Datos recibidos
            error: Mensaje de error si hubo
        """
        try:
            LogsLlamadasApi.objects.create(
                id_proveedor_api=self.proveedor_api,
                endpoint=endpoint,
                metodo_http=metodo,
                payload_request=payload,
                response_code=response_code,
                response_data=response_data,
                tiempo_respuesta_ms=0,  # Implementar medición si es necesario
                exitoso=(200 <= response_code < 300) if response_code > 0 else False,
                mensaje_error=error,
            )
        except Exception as e:
            # No fallar si falla el logging
            print(f"Error al guardar log: {str(e)}")
