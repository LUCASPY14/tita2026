# 🔍 Comparación Técnica: Pasarelas de Pago en Paraguay

## 📊 Matriz de Comparación

| Característica | Bancard/Infonet | SIPAP QR | Tigo Money | Red Infonet QR (Zimple) |
|----------------|-----------------|----------|------------|-------------------------|
| **Implementación Actual** | ✅ 80% completo | ❌ No | ❌ No | ❌ No |
| **Cobertura** | 🟢 Nacional | 🟢 Nacional | 🟡 Solo Tigo | 🟡 Usuarios Zimple |
| **Tarjetas Soportadas** | Visa, Master, Cabal, Diners, Amex | N/A (QR bancario) | N/A (billetera) | N/A (QR) |
| **Comisión** | 2.5-3.5% | 1-1.5% | 2-3% | 1.5-2% |
| **Confirmación** | Inmediata (webhook) | Inmediata | Inmediata | Inmediata |
| **Setup Fee** | Gs. 500K-1M | Gs. 300K-500K | Gs. 200K | Incluido en Bancard |
| **Mantenimiento Mensual** | Gs. 150K | Gs. 50K | Gs. 100K | Incluido |
| **Tiempo Implementación** | 3 días | 2 semanas | 1 semana | 3 días |
| **Documentación API** | 🟢 Excelente | 🟡 Regular | 🟡 Regular | 🟢 Buena |
| **Soporte Técnico** | 🟢 24/7 | 🟡 Horario oficina | 🟡 Horario oficina | 🟢 24/7 |
| **Seguridad** | HMAC-SHA256 | RSA | Token | HMAC-SHA256 |
| **Certificación PCI-DSS** | ✅ Sí | N/A | ✅ Sí | ✅ Sí |
| **Rollback Soporte** | ✅ Sí | ❌ No | 🟡 Limitado | ✅ Sí |
| **Testing Sandbox** | ✅ Staging completo | 🟡 Limitado | ✅ Sandbox | ✅ Staging |

---

## 💡 Análisis por Caso de Uso

### Caso 1: Cliente con Smartphone + App Bancaria

**Mejor Opción: SIPAP QR**
- ✅ Comisión más baja (1%)
- ✅ No necesita tarjeta
- ✅ Funciona con cualquier banco
- ✅ Confirmación instantánea
- ❌ Requiere implementación nueva (2 semanas)

**Alternativa: Bancard QR (Zimple)**
- ✅ Implementación rápida (3 días)
- ✅ Misma infraestructura que pagos con tarjeta
- ❌ Solo usuarios con Zimple activo
- ❌ Menor cobertura que SIPAP

### Caso 2: Cliente con Tarjeta de Crédito/Débito

**Mejor Opción: Bancard Single Buy**
- ✅ Infraestructura ya implementada
- ✅ Acepta todas las tarjetas
- ✅ Confirmación inmediata
- ✅ Opción de cuotas (tarjetas de crédito)
- ❌ Comisión más alta (3.5%)

### Caso 3: Cliente sin Tarjeta ni App Bancaria

**Mejor Opción: Tigo Money**
- ✅ Alta penetración en Paraguay
- ✅ Solo necesita celular
- ✅ Integración con telefonía
- ❌ Solo usuarios Tigo

**Alternativa: Transferencia Bancaria Manual**
- Mantener opción actual de pago en caja

---

## 🏗️ Arquitectura Técnica Propuesta

### Opción A: Solo Bancard (Recomendado para MVP)

```
┌─────────────────┐
│  Portal Cliente │
│  (React)        │
└────────┬────────┘
         │
         │ POST /cobros/iniciar_pago_online/
         ▼
┌─────────────────────────────────┐
│  Backend Django                 │
│  ┌──────────────────────────┐  │
│  │ PagoBancardService       │  │
│  │  - generar_pago_cliente  │  │
│  │  - generar_qr            │  │
│  │  - procesar_webhook      │  │
│  └────────┬─────────────────┘  │
└───────────┼─────────────────────┘
            │
            │ HTTPS POST single_buy
            ▼
┌─────────────────────────────────┐
│  Bancard API                    │
│  https://vpos.infonet.com.py    │
└────────┬────────────────────────┘
         │
         │ Webhook POST (HMAC-SHA256)
         ▼
┌─────────────────────────────────┐
│  /api/webhooks/bancard/         │
│  - Validar firma                │
│  - Aplicar pago a facturas      │
│  - Actualizar saldo             │
│  - Enviar email confirmación    │
└─────────────────────────────────┘
```

**Ventajas:**
- ✅ Implementación rápida (3 días)
- ✅ Reutiliza infraestructura existente
- ✅ Un solo proveedor = menos complejidad
- ✅ Bajo riesgo

**Desventajas:**
- ❌ Comisión más alta
- ❌ No soporta SIPAP QR nativo

### Opción B: Multi-Gateway (Futuro)

```
┌─────────────────┐
│  Portal Cliente │
└────────┬────────┘
         │
         │ Selector de método
         ▼
┌────────────────────────────────┐
│  PaymentGatewayFactory         │
│  ┌──────────┬──────────┬─────┐ │
│  │ Bancard  │  SIPAP   │Tigo │ │
│  └──────────┴──────────┴─────┘ │
└────────────────────────────────┘
         │
         │ Interface común
         ▼
┌────────────────────────────────┐
│  AbstractPaymentService        │
│  - iniciar_transaccion()       │
│  - generar_qr()                │
│  - procesar_webhook()          │
│  - confirmar_pago()            │
└────────────────────────────────┘
```

**Ventajas:**
- ✅ Flexibilidad para clientes
- ✅ Optimización de comisiones
- ✅ Redundancia (backup si un proveedor falla)

**Desventajas:**
- ❌ Mayor complejidad
- ❌ Múltiples webhooks
- ❌ Mayor tiempo de desarrollo (3-4 semanas)
- ❌ Múltiples contratos comerciales

---

## 🔐 Consideraciones de Seguridad

### 1. Validación de Webhooks

**Bancard:**
```python
def _validar_webhook_signature(shop_process_id, operation, signature):
    """
    Firma = HMAC-SHA256(private_key, shop_process_id + operation_json)
    """
    operation_json = json.dumps(operation, separators=(',', ':'), sort_keys=True)
    mensaje = f"{shop_process_id}{operation_json}"
    
    firma_calculada = hmac.new(
        private_key.encode('utf-8'),
        mensaje.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(firma_calculada, signature)
```

**Nivel de Seguridad:** 🟢 Alto (HMAC-SHA256 con secret key)

**SIPAP:**
```python
def _validar_sipap_signature(mensaje, signature, public_key):
    """
    Firma RSA con clave pública del banco
    """
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    
    public_key_obj = load_pem_public_key(public_key.encode())
    
    try:
        public_key_obj.verify(
            signature,
            mensaje.encode(),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return True
    except:
        return False
```

**Nivel de Seguridad:** 🟢 Muy Alto (RSA-2048)

### 2. Almacenamiento de Credenciales

**Actual (No Seguro):**
```python
# settings.py
BANCARD_PRIVATE_KEY = os.environ.get('BANCARD_PRIVATE_KEY')
```

**Recomendado:**
```python
# Usar Django Secret Manager o AWS Secrets Manager
from apps.core.models import ConfiguracionSistema

def get_bancard_private_key():
    config = ConfiguracionSistema.objects.get(
        clave='BANCARD_PRIVATE_KEY',
        estado=True
    )
    # Desencriptar con Fernet
    from cryptography.fernet import Fernet
    cipher = Fernet(settings.SECRET_KEY.encode())
    return cipher.decrypt(config.valor.encode()).decode()
```

### 3. IP Whitelisting

**Configuración Actual:**
```python
BANCARD_IP_WHITELIST = ['190.105.242.0/24', '127.0.0.1']
```

**Implementación en Webhook:**
```python
def bancard_webhook(request):
    ip_cliente = request.META.get('REMOTE_ADDR')
    
    # Validar IP está en whitelist
    from ipaddress import ip_address, ip_network
    
    ip_valida = False
    for allowed_range in settings.BANCARD_IP_WHITELIST:
        if ip_address(ip_cliente) in ip_network(allowed_range):
            ip_valida = True
            break
    
    if not ip_valida:
        # Loguear intento sospechoso
        LogsWebhooks.objects.create(
            evento_tipo='rejected_ip',
            ip_origen=ip_cliente,
            verificacion_ok=0,
            procesado_ok=0
        )
        return Response({'error': 'IP no autorizada'}, status=403)
    
    # Continuar procesamiento...
```

### 4. Prevención de Replay Attacks

```python
def procesar_webhook(shop_process_id, operation, signature):
    # 1. Validar firma
    if not self._validar_webhook_signature(...):
        return {'error': 'Firma inválida'}
    
    # 2. Validar timestamp (clock skew ±5 minutos)
    webhook_timestamp = operation.get('timestamp')
    now = datetime.now().timestamp()
    
    if abs(now - webhook_timestamp) > 300:  # 5 minutos
        return {'error': 'Webhook expirado o futuro'}
    
    # 3. Validar idempotencia (no procesar duplicados)
    recarga = CargasSaldo.objects.get(id_carga=recarga_id)
    
    if recarga.estado in ['completada', 'rechazada']:
        return {
            'success': True,
            'message': 'Ya procesado',
            'estado': recarga.estado
        }
    
    # Continuar procesamiento...
```

---

## 📈 Métricas y Monitoreo

### KPIs Recomendados

**Operacionales:**
- Tasa de éxito de pagos: `pagos_completados / pagos_iniciados`
- Tiempo promedio de confirmación: `avg(fecha_confirmacion - fecha_inicio)`
- Tasa de abandono: `pagos_cancelados / pagos_iniciados`
- Disponibilidad del servicio: `uptime_seconds / total_seconds`

**Financieros:**
- Volumen de transacciones: `sum(monto_total)`
- Comisiones pagadas: `sum(monto_total * comision_porcentaje)`
- Ticket promedio: `avg(monto_total)`
- Método de pago más usado: `count(id_medio_pago) group by medio`

**Seguridad:**
- Webhooks rechazados por IP: `count where verificacion_ok=0 and motivo='ip'`
- Webhooks con firma inválida: `count where verificacion_ok=0 and motivo='firma'`
- Intentos de replay: `count where motivo='duplicado'`

### Dashboard Propuesto

```python
# backend/apps/cobros/views.py

@action(detail=False, methods=['get'])
def metricas_pagos_online(self, request):
    """
    GET /api/v1/cobros/metricas_pagos_online/?fecha_desde=2026-04-01
    
    Response:
    {
        "periodo": {
            "fecha_desde": "2026-04-01",
            "fecha_hasta": "2026-04-16"
        },
        "operacionales": {
            "total_iniciados": 150,
            "total_completados": 135,
            "total_rechazados": 10,
            "total_cancelados": 5,
            "tasa_exito": 0.90,
            "tiempo_promedio_confirmacion": 45  # segundos
        },
        "financieros": {
            "volumen_total": 67500000,
            "comisiones_pagadas": 2025000,
            "ticket_promedio": 500000,
            "metodos": [
                {"nombre": "Tarjeta Crédito", "cantidad": 80, "monto": 40000000},
                {"nombre": "Tarjeta Débito", "cantidad": 55, "monto": 27500000}
            ]
        },
        "seguridad": {
            "webhooks_rechazados": 2,
            "firmas_invalidas": 1,
            "ips_bloqueadas": ["192.168.1.100"]
        }
    }
    """
```

---

## 🧪 Plan de Testing

### 1. Tests Unitarios

```python
# backend/apps/cobros/tests/test_pago_bancard_service.py

class PagoBancardServiceTest(TestCase):
    
    def test_generar_pago_cliente_exitoso(self):
        """Genera pago para cliente con facturas"""
        service = PagoBancardService()
        
        resultado = service.generar_pago_cliente(
            id_cliente=1,
            facturas_ids=[101, 102],
            monto_total=Decimal('500000'),
            return_url='http://test.com/return'
        )
        
        self.assertTrue(resultado['success'])
        self.assertIn('payment_url', resultado)
        self.assertIn('qr_image', resultado)
        self.assertTrue(resultado['shop_process_id'].startswith('PAG-'))
    
    def test_generar_qr_formato_correcto(self):
        """QR debe ser base64 válido"""
        service = PagoBancardService()
        
        qr = service.generar_qr('https://example.com/pago')
        
        self.assertTrue(qr.startswith('data:image/png;base64,'))
        
        # Decodificar base64 sin errores
        import base64
        base64_data = qr.split(',')[1]
        decoded = base64.b64decode(base64_data)
        self.assertGreater(len(decoded), 0)
    
    def test_webhook_firma_invalida_rechazada(self):
        """Webhook con firma inválida debe ser rechazado"""
        service = PagoBancardService()
        
        resultado = service.procesar_webhook_cobro(
            shop_process_id='PAG-1-123456',
            operation={'response': 'S'},
            signature='firma_invalida_123'
        )
        
        self.assertFalse(resultado['success'])
        self.assertIn('Firma inválida', resultado['error'])
    
    def test_idempotencia_webhook(self):
        """No procesar webhook duplicado"""
        # Procesar primera vez
        resultado1 = service.procesar_webhook_cobro(...)
        
        # Procesar segunda vez (duplicado)
        resultado2 = service.procesar_webhook_cobro(...)
        
        self.assertEqual(resultado2['message'], 'Ya procesado')
        self.assertEqual(resultado2['estado'], 'completada')
```

### 2. Tests de Integración

```python
class BancardIntegrationTest(TestCase):
    
    @patch('requests.post')
    def test_flujo_completo_pago_exitoso(self, mock_post):
        """Test de flujo completo desde inicio hasta confirmación"""
        
        # Mock response de Bancard
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'status': 'success',
            'process_id': 'BNC-123456'
        }
        
        # 1. Cliente inicia pago
        client = APIClient()
        client.force_authenticate(user=portal_user)
        
        response = client.post('/api/v1/cobros/iniciar_pago_online/', {
            'id_cliente': 1,
            'facturas_ids': [101],
            'monto_total': 500000
        })
        
        self.assertEqual(response.status_code, 200)
        shop_process_id = response.data['shop_process_id']
        
        # 2. Simular webhook de Bancard
        webhook_data = {
            'shop_process_id': shop_process_id,
            'operation': {'response': 'S', ...},
            'signature': self._generar_firma_valida(...)
        }
        
        webhook_response = client.post('/api/webhooks/bancard/', webhook_data)
        
        self.assertEqual(webhook_response.status_code, 200)
        
        # 3. Verificar pago aplicado a factura
        factura = Ventas.objects.get(id_venta=101)
        self.assertEqual(factura.saldo_pendiente, Decimal('0'))
        
        # 4. Verificar log de pago
        pago = PagosClientes.objects.get(shop_process_id=shop_process_id)
        self.assertEqual(pago.estado, 'Confirmado')
```

### 3. Tests E2E (Cypress)

```javascript
// cypress/e2e/pago-online.cy.js

describe('Pago Online - Flujo Completo', () => {
  
  beforeEach(() => {
    cy.loginPortal('jgarcia@demo.tita', 'Portal123!');
  });
  
  it('Cliente puede pagar facturas seleccionadas', () => {
    // 1. Navegar a página de pagos
    cy.visit('/portal/pago-online');
    
    // 2. Ver facturas pendientes
    cy.get('[data-testid="factura-item"]').should('have.length.at.least', 1);
    
    // 3. Seleccionar facturas
    cy.get('[data-testid="factura-checkbox"]').first().check();
    
    // 4. Ver monto total actualizado
    cy.get('[data-testid="monto-total"]').should('contain', 'Gs.');
    
    // 5. Iniciar pago
    cy.get('[data-testid="btn-pagar"]').click();
    
    // 6. Ver modal con QR
    cy.get('[data-testid="qr-modal"]').should('be.visible');
    cy.get('[data-testid="qr-image"]').should('be.visible');
    
    // 7. Ver link de pago
    cy.get('[data-testid="payment-link"]').should('have.attr', 'href')
      .and('include', 'vpos.infonet.com.py');
    
    // 8. Simular confirmación de pago (con API mock)
    cy.intercept('POST', '/api/webhooks/bancard/', {
      statusCode: 200,
      body: { success: true, estado: 'completada' }
    });
    
    // 9. Verificar actualización de dashboard
    cy.visit('/portal/dashboard');
    cy.get('[data-testid="saldo-pendiente"]').should('not.contain', 'Gs. 500,000');
  });
  
  it('Mostrar error si pago es rechazado', () => {
    // Similar al test anterior, pero con response='N'
    cy.intercept('POST', '/api/webhooks/bancard/', {
      statusCode: 200,
      body: { success: false, error: 'Pago rechazado' }
    });
    
    cy.get('[data-testid="alert-error"]').should('be.visible')
      .and('contain', 'Pago rechazado');
  });
});
```

---

## 🚀 Checklist de Deployment

### Pre-Producción

- [ ] **Credenciales Bancard Producción**
  - [ ] Public Key configurado
  - [ ] Private Key configurado y encriptado
  - [ ] Ambiente = 'production' en settings

- [ ] **Infraestructura**
  - [ ] Servidor con IP pública fija
  - [ ] IP registrada en whitelist de Bancard
  - [ ] SSL/HTTPS configurado (Let's Encrypt)
  - [ ] Dominio configurado (portal.cantina.tita)

- [ ] **Base de Datos**
  - [ ] Migrations aplicadas
  - [ ] Índices creados en PagosClientes
  - [ ] Backup automático configurado

- [ ] **Webhook**
  - [ ] URL pública accesible: https://api.cantina.tita/webhooks/bancard/
  - [ ] URL registrada en panel de Bancard
  - [ ] CSRF exempt configurado
  - [ ] IP whitelisting activo

- [ ] **Monitoring**
  - [ ] Logs configurados
  - [ ] Alertas para pagos fallidos
  - [ ] Dashboard de métricas activo
  - [ ] Sentry/error tracking integrado

### Testing Staging

- [ ] **Funcional**
  - [ ] Crear pago de prueba
  - [ ] Generar QR correctamente
  - [ ] Redirigir a Bancard staging
  - [ ] Webhook recibido y procesado
  - [ ] Pago aplicado a facturas
  - [ ] Email de confirmación enviado

- [ ] **Seguridad**
  - [ ] Firma HMAC validada
  - [ ] IP no autorizada rechazada
  - [ ] Webhook duplicado ignorado
  - [ ] Credentials no expuestas en logs

### Go-Live

- [ ] **Comunicación**
  - [ ] Email a clientes sobre nueva función
  - [ ] Tutorial en portal
  - [ ] FAQ actualizado
  - [ ] Soporte técnico capacitado

- [ ] **Monitoreo**
  - [ ] On-call configurado
  - [ ] Dashboard en vivo
  - [ ] Logs en tiempo real
  - [ ] Alertas activas

---

## 📞 Contactos Comerciales

### Bancard / Red Infonet
- **Web:** https://www.bancard.com.py
- **Comercial:** ventas@bancard.com.py
- **Soporte Técnico:** soporte@bancard.com.py / +595 21 123-4567
- **Documentación:** https://www.bancard.com.py/desarrolladores

### SIPAP (Banco Central del Paraguay)
- **Web:** https://www.bcp.gov.py/sipap
- **Contacto:** sipap@bcp.gov.py
- **Teléfono:** +595 21 617-2000

### Bancos Agregadores SIPAP
- **Banco Continental:** comercial@bancontinental.com.py
- **Banco Atlas:** comercial@atlas.com.py
- **Banco Itaú:** empresas@itau.com.py

---

**Documento creado:** 16 de Abril, 2026  
**Última actualización:** 16 de Abril, 2026  
**Versión:** 1.0
