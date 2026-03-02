"""
Servicio de  integración con Bancard (Paraguay)
API de pasarela de pagos para procesamiento de tarjetas de crédito/débito
"""
import hashlib
import hmac
import json
import requests
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional
from django.conf import settings
from django.db import transaction

from apps.api_integrations.models import (
    ProveedoresApi,
    LogsLlamadasApi,
    CredencialesApi
)
from apps.core.models import CargasSaldo, ConfiguracionSistema


class BancardService:
    """
    Servicio para integración con API de Bancard
    
    Documentación: https://www.bancard.com.py/desarrolladores
    
    Flujo:
    1. Iniciar transacción con single_buy
    2. Obtener process_id y redirect_url
    3. Redirigir usuario a Bancard
    4. Recibir confirmación vía webhook
    5. Validar firma HMAC-SHA256
    6. Completar recarga
    """
    
    # URLs de Bancard
    BANCARD_STAGING_URL = "https://vpos.infonet.com.py:8888"
    BANCARD_PRODUCTION_URL = "https://vpos.infonet.com.py"
    
    # Endpoints
    ENDPOINT_SINGLE_BUY = "/vpos/api/0.3/single_buy"
    ENDPOINT_CONFIRM = "/vpos/api/0.3/single_buy/confirmations"
    ENDPOINT_ROLLBACK = "/vpos/api/0.3/single_buy/rollback"
    
    def __init__(self, ambiente: str = None):
        """
        Inicializa el servicio con credenciales de Bancard
        
        Args:
            ambiente: 'staging' o 'production'. Si None, toma de settings.
        """
        self.ambiente = ambiente or getattr(settings, 'BANCARD_AMBIENTE', 'staging')
        
        # Cargar credenciales desde BD o settings
        self.public_key = self._get_config('BANCARD_PUBLIC_KEY')
        self.private_key = self._get_config('BANCARD_PRIVATE_KEY')
        
        # URL base según ambiente
        self.base_url = (
            self.BANCARD_PRODUCTION_URL 
            if self.ambiente == 'production' 
            else self.BANCARD_STAGING_URL
        )
        
        # Configuración de timeouts
        self.timeout = 30  # segundos
    
    def _get_config(self, clave: str, default: str = None) -> str:
        """
        Obtiene configuración desde ConfiguracionSistema o settings
        
        Args:
            clave: Nombre de la configuración
            default: Valor por defecto
            
        Returns:
            Valor de la configuración
        """
        try:
            config = ConfiguracionSistema.objects.filter(clave=clave, activo=True).first()
            if config:
                return config.valor_texto or config.valor_numerico
        except Exception:
            pass
        
        return getattr(settings, clave, default)
    
    def _generar_token(self, process_id: str) -> str:
        """
        Genera el token de seguridad para Bancard
        
        Token = MD5(private_key + process_id + "request_new_single_buy")
        
        Args:
            process_id: ID único de la transacción
            
        Returns:
            Token MD5
        """
        concatenacion = f"{self.private_key}{process_id}request_new_single_buy"
        return hashlib.md5(concatenacion.encode('utf-8')).hexdigest()
    
    def _validar_webhook_signature(
        self, 
        shop_process_id: str, 
        operation: Dict[str, Any],
        signature: str
    ) -> bool:
        """
        Valida la firma HMAC-SHA256 del webhook de Bancard
        
        Firma = HMAC-SHA256(private_key, shop_process_id + operation_json)
        
        Args:
            shop_process_id: ID de la transacción en nuestra BD
            operation: Diccionario con datos de la operación
            signature: Firma recibida en el webhook
            
        Returns:
            True si la firma es válida
        """
        # Convertir operation a JSON sin espacios
        operation_json = json.dumps(operation, separators=(',', ':'), sort_keys=True)
        
        # Concatenar shop_process_id + operation_json
        mensaje = f"{shop_process_id}{operation_json}"
        
        # Calcular HMAC-SHA256
        firma_calculada = hmac.new(
            self.private_key.encode('utf-8'),
            mensaje.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(firma_calculada, signature)
    
    def _log_api_call(
        self,
        metodo: str,
        url: str,
        payload_req: Dict = None,
        status_code: int = None,
        payload_res: Dict = None,
        tiempo_ms: int = None,
        exitoso: bool = True,
        error_msg: str = None,
        contexto: Dict = None
    ) -> None:
        """
        Registra llamada a API en LogsLlamadasApi
        
        Args:
            metodo: GET, POST, etc.
            url: URL completa
            payload_req: Body del request
            status_code: Código HTTP de respuesta
            payload_res: Body de la respuesta
            tiempo_ms: Tiempo de respuesta en milisegundos
            exitoso: Si la llamada fue exitosa
            error_msg: Mensaje de error si falló
            contexto: Contexto adicional (ej: id_recarga)
        """
        try:
            LogsLlamadasApi.objects.create(
                timestamp=datetime.now(),
                metodo=metodo,
                url=url,
                headers_req={},  # Evitar loguear headers con credenciales
                payload_req=json.dumps(payload_req) if payload_req else None,
                status_code=status_code or 0,
                headers_res={},
                payload_res=json.dumps(payload_res) if payload_res else None,
                tiempo_ms=tiempo_ms or 0,
                bytes_sent=len(json.dumps(payload_req)) if payload_req else 0,
                bytes_received=len(json.dumps(payload_res)) if payload_res else 0,
                exitoso=1 if exitoso else 0,
                error_msg=error_msg,
                intento=1,
                contexto=contexto or {}
            )
        except Exception as e:
            # No fallar si falla el logging
            print(f"Error logging API call: {e}")
    
    def iniciar_transaccion(
        self,
        recarga_id: int,
        monto: Decimal,
        descripcion: str,
        return_url: str,
        cancel_url: str,
        buyer_info: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Inicia una transacción de pago con Bancard (single_buy)
        
        Args:
            recarga_id: ID de la recarga en nuestra BD
            monto: Monto a cobrar (incluye comisión)
            descripcion: Descripción del pago
            return_url: URL de retorno después del pago
            cancel_url: URL si el usuario cancela
            buyer_info: Información del comprador (opcional)
                {
                    "ci": "12345678",
                    "nombre": "Juan Pérez",
                    "email": "juan@example.com",
                    "telefono": "0981234567"
                }
        
        Returns:
            {
                "success": bool,
                "process_id": str,  # ID de Bancard
                "payment_url": str,  # URL para redirigir al usuario
                "error": str  # Si hay error
            }
        """
        start_time = datetime.now()
        
        # Generar shop_process_id único (nuestro ID interno)
        shop_process_id = f"REC-{recarga_id}-{int(datetime.now().timestamp())}"
        
        # Generar token de seguridad
        token = self._generar_token(shop_process_id)
        
        # Formatear monto (Bancard espera formato "100.00")
        monto_str = f"{monto:.2f}"
        
        # Construir payload
        payload = {
            "public_key": self.public_key,
            "operation": {
                "token": token,
                "shop_process_id": shop_process_id,
                "currency": "PYG",
                "amount": monto_str,
                "additional_data": "",
                "description": descripcion,
                "return_url": return_url,
                "cancel_url": cancel_url
            }
        }
        
        # Agregar información del comprador si está disponible
        if buyer_info:
            payload["operation"]["buyer_preload"] = {
                "ci": buyer_info.get("ci", ""),
                "name": buyer_info.get("nombre", ""),
                "email": buyer_info.get("email", ""),
                "phone": buyer_info.get("telefono", ""),
                "address": buyer_info.get("direccion", "")
            }
        
        # URL completa
        url = f"{self.base_url}{self.ENDPOINT_SINGLE_BUY}"
        
        try:
            # Hacer request POST a Bancard
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )
            
            # Calcular tiempo de respuesta
            tiempo_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            response_data = response.json()
            
            # Loguear llamada
            self._log_api_call(
                metodo="POST",
                url=url,
                payload_req=payload,
                status_code=response.status_code,
                payload_res=response_data,
                tiempo_ms=tiempo_ms,
                exitoso=response.status_code == 200 and response_data.get("status") == "success",
                contexto={"recarga_id": recarga_id, "shop_process_id": shop_process_id}
            )
            
            # Validar respuesta exitosa
            if response.status_code == 200 and response_data.get("status") == "success":
                process_id = response_data.get("process_id")
                
                # Construir URL de pago
                payment_url = f"{self.base_url}/checkout/new?process_id={process_id}"
                
                return {
                    "success": True,
                    "process_id": process_id,
                    "shop_process_id": shop_process_id,
                    "payment_url": payment_url
                }
            else:
                # Error de Bancard
                error_messages = response_data.get("messages", [])
                error_msg = "; ".join([m.get("dsc", "") for m in error_messages]) if error_messages else "Error desconocido"
                
                return {
                    "success": False,
                    "error": error_msg
                }
                
        except requests.exceptions.Timeout:
            self._log_api_call(
                metodo="POST",
                url=url,
                payload_req=payload,
                exitoso=False,
                error_msg="Timeout al conectar con Bancard",
                contexto={"recarga_id": recarga_id}
            )
            return {
                "success": False,
                "error": "Timeout al conectar con Bancard. Intente nuevamente."
            }
            
        except requests.exceptions.RequestException as e:
            self._log_api_call(
                metodo="POST",
                url=url,
                payload_req=payload,
                exitoso=False,
                error_msg=str(e),
                contexto={"recarga_id": recarga_id}
            )
            return {
                "success": False,
                "error": f"Error de conexión: {str(e)}"
            }
            
        except Exception as e:
            self._log_api_call(
                metodo="POST",
                url=url,
                payload_req=payload,
                exitoso=False,
                error_msg=str(e),
                contexto={"recarga_id": recarga_id}
            )
            return {
                "success": False,
                "error": f"Error inesperado: {str(e)}"
            }
    
    def procesar_webhook(
        self,
        shop_process_id: str,
        operation: Dict[str, Any],
        signature: str
    ) -> Dict[str, Any]:
        """
        Procesa webhook de confirmación de Bancard
        
        Args:
            shop_process_id: ID de nuestra transacción (REC-{id}-{timestamp})
            operation: Datos de la operación
                {
                    "response": "S" o "N",  # S=Aprobada, N=Rechazada
                    "response_details": "Descripción",
                    "amount": "100.00",
                    "currency": "PYG",
                    "authorization_number": "123456",
                    "ticket_number": "789012",
                    "response_code": "00",
                    "response_description": "Transacción aprobada",
                    "security_information": {...}
                }
            signature: Firma HMAC-SHA256 del webhook
            
        Returns:
            {
                "success": bool,
                "recarga_id": int,
                "estado": str,  # 'completada' o 'rechazada'
                "error": str
            }
        """
        try:
            # 1. Validar firma
            if not self._validar_webhook_signature(shop_process_id, operation, signature):
                return {
                    "success": False,
                    "error": "Firma inválida. Posible intento de fraude."
                }
            
            # 2. Extraer recarga_id del shop_process_id (REC-{id}-{timestamp})
            try:
                parts = shop_process_id.split("-")
                recarga_id = int(parts[1])
            except (IndexError, ValueError):
                return {
                    "success": False,
                    "error": f"shop_process_id inválido: {shop_process_id}"
                }
            
            # 3. Obtener recarga
            try:
                recarga = CargasSaldo.objects.select_for_update().get(id_carga=recarga_id)
            except CargasSaldo.DoesNotExist:
                return {
                    "success": False,
                    "error": f"Recarga {recarga_id} no encontrada"
                }
            
            # 4. Validar idempotencia (evitar procesar dos veces el mismo webhook)
            if recarga.estado in ['completada', 'rechazada']:
                return {
                    "success": True,
                    "message": f"Recarga ya procesada con estado: {recarga.estado}",
                    "recarga_id": recarga_id,
                    "estado": recarga.estado
                }
            
            # 5. Procesar según respuesta de Bancard
            response_code = operation.get("response")
            
            with transaction.atomic():
                if response_code == "S":
                    # Transacción aprobada
                    from apps.core.services import RecargaService
                    service = RecargaService()
                    
                    # Actualizar recarga con datos de Bancard
                    recarga.referencia_externa = operation.get("authorization_number")
                    recarga.webhook_payload = json.dumps(operation)
                    recarga.save()
                    
                    # Acreditar saldo y generar factura
                    resultado_acreditacion = service.acreditar_saldo(recarga)
                    resultado_factura = service.generar_factura(recarga)
                    
                    if resultado_acreditacion['success'] and resultado_factura['success']:
                        recarga.estado = 'completada'
                        recarga.fecha_confirmacion = datetime.now()
                        recarga.save()
                        
                        return {
                            "success": True,
                            "recarga_id": recarga_id,
                            "estado": "completada",
                            "saldo_nuevo": resultado_acreditacion['saldo_nuevo'],
                            "id_factura": resultado_factura['id_factura']
                        }
                    else:
                        # Error al acreditar o facturar (muy raro)
                        recarga.estado = 'rechazada'
                        recarga.motivo_rechazo = "Error al procesar acreditación o factura"
                        recarga.save()
                        
                        return {
                            "success": False,
                            "error": "Error al procesar recarga internamente",
                            "recarga_id": recarga_id
                        }
                
                else:
                    # Transacción rechazada
                    recarga.estado = 'rechazada'
                    recarga.motivo_rechazo = operation.get("response_description", "Pago rechazado por Bancard")
                    recarga.webhook_payload = json.dumps(operation)
                    recarga.save()
                    
                    return {
                        "success": True,
                        "recarga_id": recarga_id,
                        "estado": "rechazada",
                        "motivo": recarga.motivo_rechazo
                    }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error al procesar webhook: {str(e)}"
            }
    
    def confirmar_transaccion(self, shop_process_id: str) -> Dict[str, Any]:
        """
        Confirma manualmente el estado de una transacción con Bancard
        (útil si no llegó el webhook)
        
        Args:
            shop_process_id: ID de nuestra transacción
            
        Returns:
            Datos de la transacción según Bancard
        """
        url = f"{self.base_url}{self.ENDPOINT_CONFIRM}"
        
        payload = {
            "public_key": self.public_key,
            "operation": {
                "shop_process_id": shop_process_id
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response_data = response.json()
            
            self._log_api_call(
                metodo="POST",
                url=url,
                payload_req=payload,
                status_code=response.status_code,
                payload_res=response_data,
                exitoso=response.status_code == 200,
                contexto={"shop_process_id": shop_process_id}
            )
            
            return response_data
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def rollback_transaccion(self, shop_process_id: str) -> Dict[str, Any]:
        """
        Reversa una transacción en Bancard
        
        Args:
            shop_process_id: ID de nuestra transacción
            
        Returns:
            Resultado del rollback
        """
        url = f"{self.base_url}{self.ENDPOINT_ROLLBACK}"
        
        payload = {
            "public_key": self.public_key,
            "operation": {
                "shop_process_id": shop_process_id
            }
        }
        
        try:
            response = requests.delete(url, json=payload, timeout=self.timeout)
            response_data = response.json()
            
            self._log_api_call(
                metodo="DELETE",
                url=url,
                payload_req=payload,
                status_code=response.status_code,
                payload_res=response_data,
                exitoso=response.status_code == 200,
                contexto={"shop_process_id": shop_process_id}
            )
            
            return response_data
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
