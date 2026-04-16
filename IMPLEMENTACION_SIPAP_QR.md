# 🇵🇾 Implementación Técnica: SIPAP QR (Sistema de Pagos QR Paraguay)

**Fecha:** 16 de Abril, 2026  
**Sistema:** Pagos Móviles Interoperables - Banco Central del Paraguay  
**Estándar:** ISO 20022, EMVCo QR Code Specification

---

## 📖 ¿Qué es SIPAP QR?

### Definición
**SIPAP** (Sistema de Pagos del Paraguay) es la infraestructura nacional de pagos QR desarrollada por el Banco Central del Paraguay. Permite realizar pagos interoperables entre **cualquier banco o billetera móvil** del país escaneando un código QR.

### Características Principales
- ✅ **Interoperabilidad Total**: Un solo QR funciona con todos los bancos
- ✅ **Confirmación Instantánea**: Notificación en tiempo real (< 5 segundos)
- ✅ **Bajo Costo**: Comisiones 1-1.5% (vs 2.5-3.5% Bancard)
- ✅ **Sin Tarjeta Necesaria**: Solo requiere cuenta bancaria + app
- ✅ **Estándar Nacional**: Regulado por BCP (Banco Central)
- ✅ **Seguridad Bancaria**: Transacciones validadas por sistema financiero

### Apps Compatibles (Paraguay 2026)
1. **Zimple** (Bancard)
2. **Pagos Móviles BCP**
3. **Continental App** (Banco Continental)
4. **Atlas Móvil** (Banco Atlas)
5. **Itaú Paraguay**
6. **Visión Banco**
7. **GNB Paraguay**
8. **BASA**
9. **Familiar**
10. **Sudameris**

---

## 🏗️ Arquitectura Técnica

### Flujo de Pago Completo

```
┌──────────────────┐
│  Portal Cliente  │
│  (React)         │
└────────┬─────────┘
         │ 1. POST /cobros/generar_qr_sipap/
         ▼
┌────────────────────────────────────┐
│  Backend Django                    │
│  ┌─────────────────────────────┐  │
│  │ SIPAPService                │  │
│  │  - generar_qr_dinamico()    │  │
│  │  - registrar_transaccion()  │  │
│  │  - validar_webhook()        │  │
│  └──────────┬──────────────────┘  │
└─────────────┼──────────────────────┘
              │
              │ 2. HTTPS POST /api/sipap/generate
              ▼
┌────────────────────────────────────┐
│  Banco Agregador API               │
│  (Continental / Atlas / Itaú)      │
│                                    │
│  Genera QR dinámico:               │
│  - Monto fijo                      │
│  - ID transacción único            │
│  - Expira en 15 minutos            │
│  - Retorna: qr_string + qr_image   │
└────────┬───────────────────────────┘
         │
         │ Cliente escanea QR con app bancaria
         │
         ▼
┌────────────────────────────────────┐
│  App Bancaria Cliente              │
│  (Zimple, Continental, etc.)       │
│                                    │
│  1. Escanea QR                     │
│  2. Muestra: Monto + Comercio      │
│  3. Confirma pago con PIN/biométrico│
│  4. Envía a red SIPAP              │
└────────┬───────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│  Red SIPAP (Banco Central)         │
│                                    │
│  1. Valida fondos                  │
│  2. Ejecuta transferencia          │
│  3. Notifica a banco agregador     │
└────────┬───────────────────────────┘
         │
         │ 3. Webhook POST (RSA signed)
         ▼
┌────────────────────────────────────┐
│  /api/webhooks/sipap/              │
│                                    │
│  1. Valida firma RSA               │
│  2. Verifica transacción           │
│  3. Aplica pago a facturas         │
│  4. Actualiza saldo cliente        │
│  5. Envía email confirmación       │
└────────────────────────────────────┘
```

---

## 💻 Implementación Técnica

### 1. Servicio Backend: `SIPAPService`

**Ubicación:** `backend/apps/api_integrations/services/sipap_service.py`

```python
"""
Servicio de integración con SIPAP QR (Sistema de Pagos del Paraguay)
Estándar EMVCo QR Code - Banco Central del Paraguay
"""

import hashlib
import hmac
import json
import requests
import base64
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from django.conf import settings
from django.db import transaction

from apps.api_integrations.models import ProveedoresApi, LogsLlamadasApi
from apps.core.models import ConfiguracionSistema


class SIPAPService:
    """
    Servicio para integración con SIPAP QR
    
    Flujo:
    1. Generar QR dinámico con monto y referencia
    2. Cliente escanea con app bancaria
    3. Red SIPAP procesa pago
    4. Recibir confirmación vía webhook
    5. Validar firma RSA
    6. Completar cobro
    
    Documentación: https://www.bcp.gov.py/sipap/documentacion
    """
    
    # URLs según banco agregador
    URLS = {
        'continental': {
            'staging': 'https://api-test.bancontinental.com.py/sipap',
            'production': 'https://api.bancontinental.com.py/sipap'
        },
        'atlas': {
            'staging': 'https://sandbox.atlas.com.py/api/sipap',
            'production': 'https://api.atlas.com.py/sipap'
        },
        'itau': {
            'staging': 'https://sandbox.itau.com.py/pix',
            'production': 'https://api.itau.com.py/pix'
        }
    }
    
    # Endpoints
    ENDPOINT_GENERAR_QR = '/v1/qr/dinamico'
    ENDPOINT_CONSULTAR = '/v1/transacciones/{txn_id}'
    ENDPOINT_REVERTIR = '/v1/transacciones/{txn_id}/reversion'
    
    def __init__(self, banco_agregador: str = 'continental', ambiente: str = None):
        """
        Inicializa servicio con credenciales del banco agregador
        
        Args:
            banco_agregador: 'continental', 'atlas', 'itau'
            ambiente: 'staging' o 'production'
        """
        self.banco_agregador = banco_agregador
        self.ambiente = ambiente or getattr(settings, 'SIPAP_AMBIENTE', 'staging')
        
        # Cargar credenciales
        self.merchant_id = self._get_config(f'SIPAP_{banco_agregador.upper()}_MERCHANT_ID')
        self.api_key = self._get_config(f'SIPAP_{banco_agregador.upper()}_API_KEY')
        self.api_secret = self._get_config(f'SIPAP_{banco_agregador.upper()}_API_SECRET')
        
        # Cargar certificado RSA del banco (para validar webhooks)
        self.public_key_pem = self._get_config(f'SIPAP_{banco_agregador.upper()}_PUBLIC_KEY')
        
        # URL base
        self.base_url = self.URLS[banco_agregador][self.ambiente]
        
        # Configuración
        self.timeout = 30
        self.qr_expiration_minutes = 15
    
    def _get_config(self, clave: str, default: str = None) -> str:
        """Obtiene configuración desde BD o settings"""
        try:
            config = ConfiguracionSistema.objects.filter(clave=clave, estado=True).first()
            if config:
                return config.valor
        except Exception:
            pass
        return getattr(settings, clave, default or '')
    
    def _generar_firma_request(self, payload: Dict[str, Any]) -> str:
        """
        Genera firma HMAC-SHA256 para request
        
        Firma = HMAC-SHA256(api_secret, merchant_id + timestamp + json_payload)
        """
        timestamp = str(int(datetime.now().timestamp()))
        payload_json = json.dumps(payload, separators=(',', ':'), sort_keys=True)
        
        mensaje = f"{self.merchant_id}{timestamp}{payload_json}"
        
        firma = hmac.new(
            self.api_secret.encode('utf-8'),
            mensaje.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return firma
    
    def _validar_firma_webhook(self, payload: str, signature: str) -> bool:
        """
        Valida firma RSA del webhook recibido
        
        El banco firma con su clave privada, nosotros validamos con su clave pública
        """
        try:
            # Cargar clave pública del banco
            public_key = serialization.load_pem_public_key(
                self.public_key_pem.encode('utf-8')
            )
            
            # Decodificar firma de base64
            signature_bytes = base64.b64decode(signature)
            
            # Verificar firma
            public_key.verify(
                signature_bytes,
                payload.encode('utf-8'),
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            
            return True
            
        except Exception as e:
            print(f"Error validando firma RSA: {e}")
            return False
    
    def _generar_headers(self, payload: Dict = None) -> Dict[str, str]:
        """Genera headers para requests a SIPAP"""
        timestamp = str(int(datetime.now().timestamp()))
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Merchant-Id': self.merchant_id,
            'X-Api-Key': self.api_key,
            'X-Timestamp': timestamp,
        }
        
        if payload:
            headers['X-Signature'] = self._generar_firma_request(payload)
        
        return headers
    
    def generar_qr_dinamico(
        self,
        id_cobro: int,
        monto: Decimal,
        descripcion: str,
        cliente_info: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Genera QR dinámico SIPAP
        
        Args:
            id_cobro: ID del cobro en nuestra BD
            monto: Monto exacto a cobrar
            descripcion: Descripción del pago
            cliente_info: Info del cliente (opcional)
                {
                    "nombre": "Juan García",
                    "documento": "1234567",
                    "email": "juan@example.com"
                }
        
        Returns:
            {
                "success": bool,
                "txn_id": str,  # ID único de transacción SIPAP
                "qr_string": str,  # String EMVCo (para generar QR)
                "qr_image": str,  # Base64 PNG del QR
                "expira_en": int,  # Segundos hasta expiración
                "error": str
            }
        """
        start_time = datetime.now()
        
        # Generar ID único de transacción
        txn_id = f"COB-{id_cobro}-{int(start_time.timestamp())}"
        
        # Calcular expiración
        expira_at = start_time + timedelta(minutes=self.qr_expiration_minutes)
        
        # Construir payload según especificación SIPAP
        payload = {
            "merchant_id": self.merchant_id,
            "txn_id": txn_id,
            "monto": f"{monto:.2f}",
            "moneda": "PYG",
            "descripcion": descripcion[:100],  # Máximo 100 caracteres
            "expira_en": expira_at.isoformat(),
            "callback_url": f"{settings.BASE_URL}/api/webhooks/sipap/",
            "metadata": {
                "id_cobro": id_cobro,
                "sistema": "cantina_tita",
                "version": "1.0"
            }
        }
        
        # Agregar info del cliente si está disponible
        if cliente_info:
            payload["cliente"] = {
                "nombre": cliente_info.get("nombre", "")[:50],
                "documento": cliente_info.get("documento", ""),
                "email": cliente_info.get("email", "")
            }
        
        # URL completa
        url = f"{self.base_url}{self.ENDPOINT_GENERAR_QR}"
        
        try:
            # Headers con firma
            headers = self._generar_headers(payload)
            
            # Request POST
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            tiempo_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            response_data = response.json()
            
            # Loguear llamada
            self._log_api_call(
                metodo='POST',
                url=url,
                payload_req=payload,
                status_code=response.status_code,
                payload_res=response_data,
                tiempo_ms=tiempo_ms,
                exitoso=response.status_code == 200,
                contexto={'id_cobro': id_cobro, 'txn_id': txn_id}
            )
            
            # Validar respuesta exitosa
            if response.status_code == 200 and response_data.get('success'):
                qr_string = response_data.get('qr_code')  # String EMVCo
                
                # Generar imagen QR con qrcode library
                qr_image = self._generar_imagen_qr(qr_string)
                
                return {
                    'success': True,
                    'txn_id': txn_id,
                    'qr_string': qr_string,
                    'qr_image': qr_image,
                    'expira_en': self.qr_expiration_minutes * 60,  # segundos
                    'monto': str(monto),
                    'descripcion': descripcion
                }
            else:
                error_msg = response_data.get('mensaje', 'Error desconocido')
                return {'success': False, 'error': error_msg}
        
        except requests.exceptions.Timeout:
            self._log_api_call(
                metodo='POST',
                url=url,
                payload_req=payload,
                exitoso=False,
                error_msg='Timeout al conectar con SIPAP',
                contexto={'id_cobro': id_cobro}
            )
            return {'success': False, 'error': 'Timeout al generar QR. Intente nuevamente.'}
        
        except Exception as e:
            return {'success': False, 'error': f'Error inesperado: {str(e)}'}
    
    def _generar_imagen_qr(self, qr_string: str) -> str:
        """
        Genera imagen QR en base64 desde string EMVCo
        
        Args:
            qr_string: String EMVCo del QR
        
        Returns:
            Base64 PNG: "data:image/png;base64,..."
        """
        import qrcode
        from io import BytesIO
        import base64
        
        # Crear QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4
        )
        qr.add_data(qr_string)
        qr.make(fit=True)
        
        # Generar imagen
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir a base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_base64}"
    
    def procesar_webhook(
        self,
        payload_raw: str,
        signature: str,
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Procesa webhook de confirmación SIPAP
        
        Args:
            payload_raw: JSON string del payload
            signature: Firma RSA del banco (header X-Signature)
            headers: Headers completos del request
        
        Returns:
            {
                "success": bool,
                "cobro_id": int,
                "estado": str,
                "error": str
            }
        """
        try:
            # 1. Validar firma RSA
            if not self._validar_firma_webhook(payload_raw, signature):
                return {
                    'success': False,
                    'error': 'Firma RSA inválida. Posible intento de fraude.'
                }
            
            # 2. Parsear payload
            payload = json.loads(payload_raw)
            
            # Extraer datos
            txn_id = payload.get('txn_id')
            estado = payload.get('estado')  # 'aprobado', 'rechazado', 'expirado'
            monto = Decimal(payload.get('monto', '0'))
            banco_cliente = payload.get('banco_origen')
            referencia_banco = payload.get('referencia_bancaria')
            timestamp_pago = payload.get('timestamp')
            
            # 3. Extraer cobro_id del txn_id (COB-{id}-{timestamp})
            try:
                parts = txn_id.split('-')
                cobro_id = int(parts[1])
            except (IndexError, ValueError):
                return {'success': False, 'error': f'txn_id inválido: {txn_id}'}
            
            # 4. Obtener cobro
            from apps.cobros.models import PagosClientes
            
            try:
                pago = PagosClientes.objects.select_for_update().get(id_pago_cliente=cobro_id)
            except PagosClientes.DoesNotExist:
                return {'success': False, 'error': f'Cobro {cobro_id} no encontrado'}
            
            # 5. Validar idempotencia
            if pago.estado in ['Confirmado', 'Rechazado']:
                return {
                    'success': True,
                    'message': f'Cobro ya procesado con estado: {pago.estado}',
                    'cobro_id': cobro_id,
                    'estado': pago.estado
                }
            
            # 6. Procesar según estado
            with transaction.atomic():
                if estado == 'aprobado':
                    # Pago exitoso
                    pago.estado = 'Confirmado'
                    pago.referencia = referencia_banco
                    pago.banco_emisor = banco_cliente
                    pago.observaciones = f"SIPAP - {banco_cliente} - Ref: {referencia_banco}"
                    pago.save()
                    
                    # Aplicar a facturas (ya implementado en PagosClientes.save())
                    
                    return {
                        'success': True,
                        'cobro_id': cobro_id,
                        'estado': 'confirmado',
                        'monto': str(monto),
                        'banco': banco_cliente
                    }
                
                elif estado in ['rechazado', 'expirado']:
                    # Pago rechazado o QR expirado
                    pago.estado = 'Rechazado'
                    pago.observaciones = f"SIPAP - {estado} - {payload.get('motivo', 'Sin motivo')}"
                    pago.save()
                    
                    return {
                        'success': True,
                        'cobro_id': cobro_id,
                        'estado': estado,
                        'motivo': payload.get('motivo')
                    }
                
                else:
                    return {'success': False, 'error': f'Estado desconocido: {estado}'}
        
        except Exception as e:
            return {'success': False, 'error': f'Error procesando webhook: {str(e)}'}
    
    def consultar_estado(self, txn_id: str) -> Dict[str, Any]:
        """
        Consulta estado de una transacción SIPAP
        (útil si no llegó el webhook)
        
        Args:
            txn_id: ID de transacción
        
        Returns:
            Estado actual de la transacción
        """
        url = f"{self.base_url}{self.ENDPOINT_CONSULTAR.format(txn_id=txn_id)}"
        
        try:
            headers = self._generar_headers()
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response_data = response.json()
            
            self._log_api_call(
                metodo='GET',
                url=url,
                status_code=response.status_code,
                payload_res=response_data,
                exitoso=response.status_code == 200,
                contexto={'txn_id': txn_id}
            )
            
            return response_data
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _log_api_call(self, **kwargs):
        """Registra llamada a API en LogsLlamadasApi"""
        try:
            LogsLlamadasApi.objects.create(
                timestamp=datetime.now(),
                metodo=kwargs.get('metodo', 'GET'),
                url=kwargs.get('url', ''),
                headers_req={},
                payload_req=json.dumps(kwargs.get('payload_req')) if kwargs.get('payload_req') else None,
                status_code=kwargs.get('status_code', 0),
                headers_res={},
                payload_res=json.dumps(kwargs.get('payload_res')) if kwargs.get('payload_res') else None,
                tiempo_ms=kwargs.get('tiempo_ms', 0),
                exitoso=1 if kwargs.get('exitoso', False) else 0,
                error_msg=kwargs.get('error_msg'),
                intento=1,
                contexto=kwargs.get('contexto', {})
            )
        except Exception as e:
            print(f"Error logging API call: {e}")
```

---

## 🔌 Endpoint de Webhook

**Ubicación:** `backend/apps/api_integrations/views.py`

```python
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def sipap_webhook(request):
    """
    Webhook para recibir confirmaciones de SIPAP
    
    POST /api/webhooks/sipap/
    
    Headers:
        X-Signature: Firma RSA del banco
        X-Merchant-Id: ID del comercio
        X-Timestamp: Unix timestamp
    
    Body:
        {
            "txn_id": "COB-123-1713308400",
            "estado": "aprobado",  # aprobado/rechazado/expirado
            "monto": "500000.00",
            "moneda": "PYG",
            "banco_origen": "Banco Continental",
            "referencia_bancaria": "TXN-987654321",
            "timestamp": "2026-04-16T19:30:00Z",
            "metadata": {...}
        }
    """
    try:
        # Obtener firma RSA del header
        signature = request.headers.get('X-Signature')
        if not signature:
            return Response(
                {'error': 'Falta header X-Signature'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Payload raw (para validar firma)
        payload_raw = request.body.decode('utf-8')
        
        # Determinar banco agregador desde merchant_id
        merchant_id = request.headers.get('X-Merchant-Id')
        banco_agregador = 'continental'  # Default, o lookup desde BD
        
        # Procesar con SIPAPService
        from apps.api_integrations.services import SIPAPService
        
        sipap_service = SIPAPService(banco_agregador=banco_agregador)
        resultado = sipap_service.procesar_webhook(
            payload_raw=payload_raw,
            signature=signature,
            headers=dict(request.headers)
        )
        
        # Loguear webhook
        from apps.api_integrations.models import LogsWebhooks
        from django.utils import timezone
        
        try:
            LogsWebhooks.objects.create(
                timestamp=timezone.now(),
                evento_tipo='sipap_payment',
                payload=payload_raw,
                headers=dict(request.headers),
                verificacion_ok=1 if resultado.get('success') else 0,
                procesado_ok=1 if resultado.get('success') else 0,
                ip_origen=request.META.get('REMOTE_ADDR', '')
            )
        except Exception:
            pass
        
        # Retornar respuesta
        if resultado.get('success'):
            return Response(
                {
                    'success': True,
                    'message': 'Webhook procesado correctamente',
                    'cobro_id': resultado.get('cobro_id'),
                    'estado': resultado.get('estado')
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'success': False, 'error': resultado.get('error')},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except Exception as e:
        return Response(
            {'success': False, 'error': f'Error interno: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

---

## 🎨 Frontend: Componente React

**Ubicación:** `frontend/src/pages/portal/PagoSIPAP.tsx`

```tsx
import React, { useState, useEffect } from 'react';
import { Card, Button, message, Modal, Spin } from 'antd';
import { QrcodeOutlined, ClockCircleOutlined } from '@ant-design/icons';
import cobrosService from '../../services/cobros.service';

interface SIPAPQRData {
  success: boolean;
  txn_id: string;
  qr_image: string;
  expira_en: number;
  monto: string;
  descripcion: string;
}

const PagoSIPAP: React.FC<{ idCobro: number; monto: number }> = ({ idCobro, monto }) => {
  const [loading, setLoading] = useState(false);
  const [qrData, setQrData] = useState<SIPAPQRData | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [tiempoRestante, setTiempoRestante] = useState(0);

  // Countdown para expiración del QR
  useEffect(() => {
    if (qrData && tiempoRestante > 0) {
      const interval = setInterval(() => {
        setTiempoRestante(prev => {
          if (prev <= 1) {
            clearInterval(interval);
            message.warning('El QR ha expirado. Genere uno nuevo.');
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      return () => clearInterval(interval);
    }
  }, [qrData, tiempoRestante]);

  const generarQR = async () => {
    setLoading(true);
    try {
      const response = await cobrosService.generarQRSIPAP({
        id_cobro: idCobro,
        monto: monto,
        descripcion: `Pago cantina - Cobro #${idCobro}`
      });

      if (response.success) {
        setQrData(response);
        setTiempoRestante(response.expira_en);
        setModalVisible(true);
      } else {
        message.error(response.error || 'Error al generar QR');
      }
    } catch (error) {
      message.error('Error al generar QR SIPAP');
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <>
      <Button
        type="primary"
        icon={<QrcodeOutlined />}
        onClick={generarQR}
        loading={loading}
        size="large"
      >
        Generar QR SIPAP
      </Button>

      <Modal
        title="Pagar con QR SIPAP"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={500}
      >
        {qrData && (
          <div className="text-center">
            {/* QR Code */}
            <div className="mb-4">
              <img
                src={qrData.qr_image}
                alt="QR SIPAP"
                className="mx-auto"
                style={{ maxWidth: '300px' }}
              />
            </div>

            {/* Monto */}
            <div className="mb-4">
              <p className="text-gray-600">Monto a pagar:</p>
              <p className="text-3xl font-bold text-green-600">
                Gs. {Number(qrData.monto).toLocaleString('es-PY')}
              </p>
            </div>

            {/* Countdown */}
            <div className="mb-4 p-3 bg-orange-50 rounded">
              <ClockCircleOutlined className="mr-2" />
              <span className="font-semibold">
                Expira en: {formatTime(tiempoRestante)}
              </span>
            </div>

            {/* Instrucciones */}
            <div className="text-left mb-4 p-4 bg-blue-50 rounded">
              <h4 className="font-semibold mb-2">📱 Cómo pagar:</h4>
              <ol className="list-decimal ml-4 space-y-1">
                <li>Abre tu app bancaria (Zimple, Continental, etc.)</li>
                <li>Busca la opción "Pagar con QR" o "SIPAP"</li>
                <li>Escanea este código</li>
                <li>Verifica el monto</li>
                <li>Confirma con tu PIN o huella</li>
              </ol>
            </div>

            {/* Apps compatibles */}
            <div className="text-sm text-gray-500">
              <p className="font-semibold mb-2">Apps compatibles:</p>
              <div className="flex flex-wrap gap-2 justify-center">
                <span className="px-2 py-1 bg-gray-100 rounded">Zimple</span>
                <span className="px-2 py-1 bg-gray-100 rounded">Continental</span>
                <span className="px-2 py-1 bg-gray-100 rounded">Atlas</span>
                <span className="px-2 py-1 bg-gray-100 rounded">Itaú</span>
                <span className="px-2 py-1 bg-gray-100 rounded">Visión</span>
                <span className="px-2 py-1 bg-gray-100 rounded">GNB</span>
              </div>
            </div>

            {/* Nota */}
            <p className="text-xs text-gray-400 mt-4">
              El pago será confirmado automáticamente en pocos segundos
            </p>
          </div>
        )}
      </Modal>
    </>
  );
};

export default PagoSIPAP;
```

---

## 🔐 Configuración y Seguridad

### 1. Variables de Entorno

**Archivo:** `backend/.env`

```bash
# SIPAP QR Configuration
SIPAP_AMBIENTE=staging  # staging o production

# Banco Continental
SIPAP_CONTINENTAL_MERCHANT_ID=MERCHANT_12345
SIPAP_CONTINENTAL_API_KEY=api_key_continental_xyz
SIPAP_CONTINENTAL_API_SECRET=api_secret_continental_abc123
SIPAP_CONTINENTAL_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\nMIIBIjANBg...\n-----END PUBLIC KEY-----"

# Banco Atlas (alternativa)
SIPAP_ATLAS_MERCHANT_ID=MERCHANT_67890
SIPAP_ATLAS_API_KEY=api_key_atlas_xyz
SIPAP_ATLAS_API_SECRET=api_secret_atlas_abc456
SIPAP_ATLAS_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\n..."

# Banco Itaú (alternativa)
SIPAP_ITAU_MERCHANT_ID=MERCHANT_11111
SIPAP_ITAU_API_KEY=api_key_itau_xyz
SIPAP_ITAU_API_SECRET=api_secret_itau_abc789
SIPAP_ITAU_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\n..."
```

### 2. Settings Django

**Archivo:** `backend/backend/settings/base.py`

```python
# SIPAP QR CONFIGURATION
SIPAP_AMBIENTE = os.environ.get('SIPAP_AMBIENTE', 'staging')
SIPAP_BANCO_AGREGADOR = os.environ.get('SIPAP_BANCO_AGREGADOR', 'continental')

# Credenciales (se cargan desde ConfiguracionSistema o .env)
SIPAP_CONTINENTAL_MERCHANT_ID = os.environ.get('SIPAP_CONTINENTAL_MERCHANT_ID', '')
SIPAP_CONTINENTAL_API_KEY = os.environ.get('SIPAP_CONTINENTAL_API_KEY', '')
SIPAP_CONTINENTAL_API_SECRET = os.environ.get('SIPAP_CONTINENTAL_API_SECRET', '')
SIPAP_CONTINENTAL_PUBLIC_KEY = os.environ.get('SIPAP_CONTINENTAL_PUBLIC_KEY', '')

# QR Settings
SIPAP_QR_EXPIRATION_MINUTES = 15  # QR válido por 15 minutos
SIPAP_MAX_MONTO = 100000000  # Gs. 100 millones (límite SIPAP)
SIPAP_MIN_MONTO = 1000  # Gs. 1,000 mínimo
```

---

## ⚖️ Comparación: SIPAP vs Bancard

| Aspecto | SIPAP QR | Bancard |
|---------|----------|---------|
| **Implementación Actual** | ❌ No existe | ✅ 80% completo |
| **Tiempo Desarrollo** | 2 semanas | 3 días |
| **Comisión** | 🟢 1-1.5% | 🟡 2.5-3.5% |
| **Cobertura** | 🟢 10+ bancos | 🟢 Universal |
| **Requiere Tarjeta** | ❌ No | ✅ Sí |
| **Requiere App** | ✅ Sí (bancaria) | ❌ No (web) |
| **Confirmación** | 🟢 Instantánea | 🟢 Instantánea |
| **Seguridad** | 🟢 RSA-2048 | 🟢 HMAC-SHA256 |
| **Expira QR** | ✅ 15 min | ❌ N/A |
| **Rollback** | 🟡 Limitado | ✅ Sí |
| **Sandbox** | 🟡 Limitado | ✅ Completo |
| **Documentación** | 🟡 Regular | 🟢 Excelente |
| **Soporte 24/7** | ❌ Horario oficina | ✅ Sí |
| **Setup Fee** | Gs. 300K-500K | Gs. 500K-1M |
| **Mensual** | Gs. 50K | Gs. 150K |

---

## 🚀 Plan de Implementación

### Fase 1: Preparación Comercial (1 semana)

1. **Contactar Banco Agregador**
   - Banco Continental: +595 21 414-3000
   - Banco Atlas: +595 21 495-3000
   - Banco Itaú: +595 21 218-1000

2. **Documentación Requerida**
   - RUC de la empresa
   - Contrato social
   - Cédula del representante legal
   - Comprobante de dirección
   - Cuenta bancaria corporativa

3. **Contrato y Certificación**
   - Firmar contrato con banco
   - Recibir credenciales staging
   - Recibir certificado RSA público
   - Testing en ambiente staging
   - Aprobación para producción

### Fase 2: Desarrollo Backend (5 días)

**Día 1-2:**
- [ ] Crear `SIPAPService` en `apps/api_integrations/services/`
- [ ] Implementar `generar_qr_dinamico()`
- [ ] Implementar validación de firma RSA
- [ ] Tests unitarios

**Día 3:**
- [ ] Crear webhook `/api/webhooks/sipap/`
- [ ] Implementar `procesar_webhook()`
- [ ] Logging en `LogsWebhooks`
- [ ] Tests de integración

**Día 4:**
- [ ] Endpoints en `apps/cobros/`:
  - `POST /cobros/generar_qr_sipap/`
  - `GET /cobros/estado_pago_sipap/?txn_id=X`
- [ ] Integrar con `PagosClientes`

**Día 5:**
- [ ] Testing con staging
- [ ] Documentación API
- [ ] Code review

### Fase 3: Frontend (3 días)

**Día 1:**
- [ ] Componente `PagoSIPAP.tsx`
- [ ] Service `sipap.service.ts`
- [ ] Integrar en portal de clientes

**Día 2:**
- [ ] UI/UX polish
- [ ] Countdown timer
- [ ] Manejo de errores
- [ ] Loading states

**Día 3:**
- [ ] Testing E2E
- [ ] Responsive design
- [ ] Accessibility

### Fase 4: Deploy y Monitoreo (2 días)

- [ ] Configurar credenciales de producción
- [ ] Deploy a servidor
- [ ] Configurar webhook URL pública
- [ ] Monitoreo y alertas
- [ ] Documentación para usuarios

---

## 💰 Costos Estimados

### Setup Inicial
- Contrato banco agregador: Gs. 300,000 - 500,000
- Desarrollo (80 horas @ Gs. 25,000/hora): Gs. 2,000,000
- Testing y QA: Gs. 500,000
- **Total Setup: Gs. 2,800,000 - 3,000,000**

### Costos Mensuales
- Mantenimiento banco: Gs. 50,000
- Comisión por transacción: 1-1.5%

### ROI
Con 100 transacciones/mes de Gs. 500,000:
- Volumen: Gs. 50,000,000
- Comisión SIPAP (1.5%): Gs. 750,000
- vs Bancard (3%): Gs. 1,500,000
- **Ahorro mensual: Gs. 750,000**
- **ROI: 4 meses**

---

## 📚 Documentación Oficial

### Banco Central del Paraguay
- Web: https://www.bcp.gov.py/sipap
- Email: sipap@bcp.gov.py
- Teléfono: +595 21 617-2000

### Bancos Agregadores
1. **Banco Continental**
   - Web: https://www.bancontinental.com.py/sipap
   - Email: sipap@bancontinental.com.py
   - Docs: https://developers.bancontinental.com.py

2. **Banco Atlas**
   - Web: https://www.atlas.com.py/empresas
   - Email: comercial@atlas.com.py

3. **Banco Itaú**
   - Web: https://www.itau.com.py/empresas
   - Email: empresas@itau.com.py

---

## ✅ Recomendación Final

### **Estrategia Multi-Gateway (Óptima)**

```
Implementar AMBOS sistemas:
┌────────────────────────────────┐
│  Portal Cliente                │
│  "Elige cómo pagar:"           │
│                                │
│  ┌──────────┐  ┌──────────┐   │
│  │ Bancard  │  │ SIPAP QR │   │
│  │ Tarjeta  │  │ Bancario │   │
│  └──────────┘  └──────────┘   │
└────────────────────────────────┘
```

**Razones:**
1. ✅ **Bancard primero** (3 días - ya 80% listo)
2. ✅ **SIPAP después** (2 semanas - menor comisión)
3. ✅ Flexibilidad para clientes
4. ✅ Optimización de costos
5. ✅ Redundancia (backup)

**Cronograma:**
- **Sprint 1 (1 semana):** Completar Bancard MVP
- **Sprint 2 (2 semanas):** Implementar SIPAP
- **Sprint 3 (1 semana):** Integración y testing

---

**Documento creado:** 16 de Abril, 2026  
**Versión:** 1.0  
**Autor:** Sistema de Análisis Técnico
