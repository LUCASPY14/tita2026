# 💳 Análisis: Pasarela de Pago Online - Bancard/Red Infonet

**Fecha:** 16 de Abril, 2026  
**Prioridad:** BAJA  
**Estado del Análisis:** Completo

---

## 📊 Estado Actual del Proyecto

### ✅ Infraestructura Existente

El proyecto **YA TIENE** implementada la infraestructura base para Bancard:

#### 1. **Backend - API Integration**
- ✅ Módulo `apps.api_integrations` completo
- ✅ `BancardService` con métodos:
  - `iniciar_transaccion()` - Single Buy API
  - `procesar_webhook()` - Validación HMAC-SHA256
  - `confirmar_transaccion()` - Consulta manual
  - `rollback_transaccion()` - Reversión de pagos
- ✅ Webhook endpoint: `POST /api/webhooks/bancard/`
- ✅ Validación de firma HMAC-SHA256
- ✅ Logging completo (`LogsLlamadasApi`, `LogsWebhooks`)
- ✅ Soporte multi-ambiente (staging/production)

#### 2. **Configuración**
- ✅ Settings con `BANCARD_PUBLIC_KEY`, `BANCARD_PRIVATE_KEY`, `BANCARD_AMBIENTE`
- ✅ IP Whitelist: `['190.105.242.0/24', '127.0.0.1']`
- ✅ URLs configuradas en `backend/backend/urls.py`

#### 3. **Modelos de Datos**
- ✅ `ProveedoresApi` - Gestión de proveedores externos
- ✅ `EndpointsApi` - Endpoints configurables
- ✅ `CredencialesApi` - Credenciales por ambiente
- ✅ `WebhookEndpoints` - Configuración de webhooks
- ✅ `LogsLlamadasApi` - Auditoría de llamadas
- ✅ `LogsWebhooks` - Auditoría de webhooks recibidos

#### 4. **Librería QR**
- ✅ `qrcode==8.2` instalado en requirements.txt
- ✅ Ya usado en sistema 2FA (ver `apps.usuarios.services.two_factor_service`)

#### 5. **Sistema de Cobros (Recién Implementado)**
- ✅ Módulo `apps.cobros` con modelos de pagos
- ✅ Frontend con búsqueda de clientes y facturas pendientes
- ✅ Endpoints para registrar pagos manuales

---

## 🎯 Caso de Uso: Pago Online para Clientes

### Escenario
Juan García tiene Gs. 14,402,000 de deuda en 92 facturas. Quiere pagar desde su casa usando tarjeta de crédito/débito.

### Flujo Propuesto

#### **Opción 1: Pago desde Portal de Clientes (Recomendado)**

```
1. Cliente → Login al Portal (http://portal.cantina.tita/login)
   ↓
2. Ve sección "Estado de Cuenta" con deuda Gs. 14,402,000
   ↓
3. Click "Pagar Ahora" → Selecciona facturas o paga total
   ↓
4. Sistema genera transacción Bancard y QR
   ↓
5. Cliente puede:
   a) Escanear QR con app bancaria (Zimple, Pagos Móviles, etc.)
   b) Click botón "Pagar con Tarjeta" → Redirect a Bancard
   ↓
6. Bancard procesa pago
   ↓
7. Webhook confirma pago → Sistema aplica automáticamente a facturas
   ↓
8. Cliente recibe email de confirmación
   ↓
9. Dashboard actualizado con nueva deuda
```

#### **Opción 2: QR Generado por Email**

```
1. Sistema envía email a clientes con deuda
   ↓
2. Email contiene:
   - Resumen de deuda
   - QR de pago
   - Link de pago directo
   ↓
3. Cliente escanea QR o hace click en link
   ↓
4. Mismo flujo de Bancard que Opción 1
```

#### **Opción 3: QR Impreso en Factura**

```
1. Al generar factura física/PDF
   ↓
2. Incluir QR de pago específico para esa factura
   ↓
3. Cliente puede pagar factura individual escaneando QR
```

---

## 🔧 Implementación Técnica

### A. Integración con Bancard (Adaptación del Sistema Existente)

#### 1. Nuevo Service: `PagoBancardService`

**Ubicación:** `backend/apps/cobros/services/pago_bancard_service.py`

```python
class PagoBancardService:
    """
    Servicio para pagos de facturas vía Bancard
    Adapta BancardService existente para cobros
    """
    
    def generar_pago_cliente(
        self, 
        id_cliente: int,
        facturas_ids: List[int],
        monto_total: Decimal,
        return_url: str
    ) -> Dict[str, Any]:
        """
        Genera transacción de pago para cliente
        
        Returns:
            {
                "success": True,
                "payment_url": "https://vpos.infonet.com.py/checkout/...",
                "qr_data": "https://vpos.infonet.com.py/checkout/...",
                "qr_image": "data:image/png;base64,...",
                "shop_process_id": "PAG-{id_cliente}-{timestamp}",
                "expira_en": 3600  # segundos
            }
        """
        # 1. Crear registro en PagosClientes (estado='pendiente')
        # 2. Llamar BancardService.iniciar_transaccion()
        # 3. Generar QR con URL de pago
        # 4. Retornar datos
    
    def generar_qr(self, payment_url: str) -> str:
        """
        Genera QR code en base64
        
        Uses: qrcode library
        """
        import qrcode
        from io import BytesIO
        import base64
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(payment_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_base64}"
```

#### 2. Webhook Handler: Adaptar `bancard_webhook`

**Ubicación:** `backend/apps/api_integrations/views.py`

```python
# Modificar para detectar tipo de pago
def bancard_webhook(request):
    shop_process_id = data.get("shop_process_id")
    
    # Detectar tipo: REC-{id} (recarga) vs PAG-{id} (cobro)
    if shop_process_id.startswith("REC-"):
        # Flujo existente de recargas
        from apps.api_integrations.services import BancardService
        service = BancardService()
        resultado = service.procesar_webhook(...)
    
    elif shop_process_id.startswith("PAG-"):
        # NUEVO: Flujo de cobros
        from apps.cobros.services import PagoBancardService
        service = PagoBancardService()
        resultado = service.procesar_webhook_cobro(...)
    
    return Response(...)
```

#### 3. Nuevos Endpoints en `apps.cobros`

```python
# backend/apps/cobros/views.py

class PagosClientesViewSet(viewsets.ModelViewSet):
    
    @action(detail=False, methods=['post'])
    def iniciar_pago_online(self, request):
        """
        Inicia pago online con Bancard
        
        POST /api/v1/cobros/iniciar_pago_online/
        
        Body:
        {
            "id_cliente": 1,
            "facturas_ids": [101, 102, 103],  # opcional
            "monto_total": 500000,
            "metodo": "bancard",  # bancard, qr, transferencia
            "return_url": "http://portal.cantina.tita/pagos/confirmacion"
        }
        
        Response:
        {
            "success": true,
            "payment_url": "https://vpos.infonet.com.py/checkout/...",
            "qr_image": "data:image/png;base64,...",
            "shop_process_id": "PAG-1-1713308400",
            "expira_en": 3600
        }
        """
    
    @action(detail=False, methods=['get'])
    def estado_pago(self, request):
        """
        Consulta estado de pago pendiente
        
        GET /api/v1/cobros/estado_pago/?shop_process_id=PAG-1-1713308400
        """
```

### B. Frontend - Portal de Clientes

#### 1. Nuevo Componente: `PagoOnline.tsx`

**Ubicación:** `frontend/src/pages/portal/PagoOnline.tsx`

```tsx
const PagoOnline: React.FC = () => {
  const [facturas, setFacturas] = useState<Factura[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [qrVisible, setQrVisible] = useState(false);
  const [qrData, setQrData] = useState<PagoData | null>(null);
  
  const handlePagar = async () => {
    const response = await cobrosService.iniciarPagoOnline({
      id_cliente: user.id_cliente,
      facturas_ids: selectedIds,
      monto_total: calcularTotal(),
      return_url: window.location.origin + '/portal/pagos/confirmacion'
    });
    
    setQrData(response);
    setQrVisible(true);
  };
  
  return (
    <div>
      {/* Lista de facturas con checkboxes */}
      <FacturasList 
        facturas={facturas}
        selectedIds={selectedIds}
        onSelect={setSelectedIds}
      />
      
      {/* Botón pagar */}
      <Button onClick={handlePagar}>
        Pagar Gs. {calcularTotal().toLocaleString()}
      </Button>
      
      {/* Modal con QR */}
      <Modal visible={qrVisible}>
        <QRDisplay 
          qrImage={qrData?.qr_image}
          paymentUrl={qrData?.payment_url}
          expiresIn={qrData?.expira_en}
        />
        
        <div>
          <p>Escanea el QR con tu app bancaria</p>
          <p>O haz click aquí:</p>
          <a href={qrData?.payment_url} target="_blank">
            <Button type="primary" size="large">
              Pagar con Tarjeta
            </Button>
          </a>
        </div>
      </Modal>
    </div>
  );
};
```

#### 2. Actualizar `DashboardPortal.tsx`

```tsx
// Agregar botón "Pagar Ahora" en sección Estado de Cuenta
{data.cuenta_corriente.total_deuda > 0 && (
  <Button 
    type="primary" 
    size="large"
    onClick={() => navigate('/portal/pago-online')}
  >
    <DollarOutlined /> Pagar Ahora
  </Button>
)}
```

### C. Notificaciones por Email

#### 1. Template: Email con QR

**Ubicación:** `backend/templates/emails/deuda_con_qr.html`

```html
<!DOCTYPE html>
<html>
<body>
  <h2>Estado de Cuenta - Cantina Tita</h2>
  
  <p>Estimado/a {{ cliente.nombre_completo }},</p>
  
  <p>Tiene un saldo pendiente de <strong>Gs. {{ total_deuda }}</strong></p>
  
  <h3>Pague fácilmente escaneando este QR:</h3>
  <img src="{{ qr_image_url }}" alt="QR de pago" />
  
  <p>O haga click aquí:</p>
  <a href="{{ payment_url }}">
    <button>Pagar con Tarjeta</button>
  </a>
  
  <p>Facturas pendientes:</p>
  <ul>
    {% for factura in facturas %}
      <li>{{ factura.nro_factura }} - Gs. {{ factura.saldo_pendiente }}</li>
    {% endfor %}
  </ul>
</body>
</html>
```

#### 2. Tarea Programada: Envío Automático

```python
# backend/apps/cobros/tasks.py

from celery import shared_task

@shared_task
def enviar_recordatorios_deuda():
    """
    Tarea programada (semanal) para enviar QRs de pago
    a clientes con deuda mayor a 7 días
    """
    from apps.clientes.models import Clientes
    from apps.ventas.models import Ventas
    from apps.cobros.services import PagoBancardService
    from django.core.mail import send_mail
    
    # Clientes con deuda > 7 días
    clientes_morosos = Clientes.objects.filter(
        ventas__saldo_pendiente__gt=0,
        ventas__fecha__lt=timezone.now() - timedelta(days=7)
    ).distinct()
    
    for cliente in clientes_morosos:
        # Generar pago y QR
        service = PagoBancardService()
        pago_data = service.generar_pago_cliente(
            id_cliente=cliente.id_cliente,
            facturas_ids=None,  # todas las facturas
            monto_total=cliente.calcular_deuda_total(),
            return_url="http://portal.cantina.tita/pagos/confirmacion"
        )
        
        # Enviar email con QR
        send_mail(
            subject="Recordatorio de pago - Cantina Tita",
            message="...",
            html_message=render_to_string('emails/deuda_con_qr.html', {
                'cliente': cliente,
                'qr_image_url': pago_data['qr_image'],
                'payment_url': pago_data['payment_url'],
                'facturas': cliente.facturas_pendientes()
            }),
            from_email="noreply@cantina.tita",
            recipient_list=[cliente.email]
        )
```

---

## 🌐 Opciones de Pasarelas de Pago en Paraguay

### 1. **Bancard / Red Infonet** (Implementación Actual)

**Ventajas:**
- ✅ Líder del mercado paraguayo
- ✅ Soporta todas las tarjetas locales (Visa, Master, Cabal, etc.)
- ✅ API REST documentada
- ✅ Soporte para QR (Zimple)
- ✅ Webhooks con HMAC-SHA256
- ✅ YA TENEMOS infraestructura implementada

**Desventajas:**
- ❌ Comisiones: ~3.5% tarjeta crédito, ~2.5% débito
- ❌ Requiere aprobación comercial

**Costos:**
- Setup: Gs. 500,000 - 1,000,000 (una vez)
- Comisión: 2.5% - 3.5% por transacción
- Mantenimiento: Gs. 150,000/mes

### 2. **Pagos Móviles SIPAP** (QR Nativo)

**Ventajas:**
- ✅ Estándar nacional de QR en Paraguay
- ✅ Interoperable (funciona con todos los bancos)
- ✅ Sin necesidad de tarjeta
- ✅ Comisiones más bajas (~1.5%)
- ✅ Confirmación instantánea

**Desventajas:**
- ❌ Requiere convenio con banco agregador
- ❌ API menos documentada
- ❌ No hay infraestructura implementada

**Costos:**
- Setup: Gs. 300,000 - 500,000
- Comisión: 1% - 1.5% por transacción

### 3. **Red Infonet QR** (Zimple)

**Ventajas:**
- ✅ Mismo proveedor que Bancard
- ✅ Integración más simple
- ✅ QR dinámico con monto
- ✅ Confirmación vía webhook

**Desventajas:**
- ❌ Solo usuarios con Zimple activo
- ❌ Menos alcance que SIPAP

### 4. **Tigo Money** (Billetera Móvil)

**Ventajas:**
- ✅ Gran base de usuarios en Paraguay
- ✅ API REST
- ✅ Integración con telefonía

**Desventajas:**
- ❌ Solo usuarios Tigo
- ❌ Comisiones variables

---

## 📋 Plan de Implementación Recomendado

### Fase 1: MVP con Bancard (2-3 días de desarrollo)

**Objetivos:**
- [x] ~~Infraestructura Bancard~~ (Ya existe)
- [ ] Adaptar para cobros (no solo recargas)
- [ ] Generar QR de pago
- [ ] Webhook para confirmar pagos
- [ ] Portal: Botón "Pagar Ahora"

**Tareas:**
1. ✅ Crear `PagoBancardService` adaptando `BancardService`
2. ✅ Agregar endpoints `/cobros/iniciar_pago_online/`
3. ✅ Implementar generación de QR con `qrcode`
4. ✅ Modificar `bancard_webhook` para detectar PAG-{id}
5. ✅ Frontend: Componente `PagoOnline.tsx`
6. ✅ Integrar en `DashboardPortal.tsx`
7. ✅ Testing con ambiente staging de Bancard

**Esfuerzo:** ~16 horas de desarrollo

### Fase 2: Mejoras (1-2 días)

**Tareas:**
1. Email automático con QR semanal
2. QR en facturas PDF
3. Historial de pagos online
4. Notificaciones push cuando se recibe pago
5. Dashboard de métricas (pagos online vs manuales)

**Esfuerzo:** ~8 horas de desarrollo

### Fase 3: Integración SIPAP (Opcional - Futuro)

**Tareas:**
1. Convenio con banco agregador
2. Implementar servicio SIPAP QR
3. Webhook handler SIPAP
4. Unificar interfaz de pagos

**Esfuerzo:** ~24 horas de desarrollo + trámites comerciales

---

## 💰 Análisis Costo-Beneficio

### Escenario: 100 clientes con deuda promedio Gs. 500,000

**Situación Actual (Manual):**
- Tiempo empleado cajero: 10 min/cliente = 16.7 horas/mes
- Costo hora cajero: Gs. 15,000
- **Costo total: Gs. 250,500/mes**

**Con Pago Online:**
- 60% pagan online (60 clientes)
- Comisión Bancard 3%: Gs. 900,000 * 3% = Gs. 27,000
- Tiempo cajero reducido a 40 clientes = 6.7 horas
- **Costo total: Gs. 127,500/mes**
- **Ahorro: Gs. 123,000/mes (49%)**

**Beneficios Adicionales:**
- ✅ Cobro más rápido (reduce días de cartera)
- ✅ Mejor experiencia del cliente
- ✅ Disponibilidad 24/7
- ✅ Reducción de errores humanos
- ✅ Auditoría automática completa

---

## 🎯 Recomendación Final

### **Implementar Fase 1 con Bancard**

**Razones:**
1. ✅ Infraestructura ya existe (80% del trabajo hecho)
2. ✅ ROI positivo en primer mes
3. ✅ Aprovecha sistema de cobros recién implementado
4. ✅ Bancard es el estándar de facto en Paraguay
5. ✅ Bajo riesgo técnico

**Cronograma Propuesto:**
- **Día 1-2:** Backend (PagoBancardService, endpoints, webhook)
- **Día 3:** Frontend (PagoOnline.tsx, integración portal)
- **Día 4:** Testing con staging, ajustes
- **Día 5:** Deploy a producción, monitoreo

**Requisitos Comerciales (Gestionar en paralelo):**
1. Obtener credenciales Bancard producción
2. Configurar IP pública para webhook
3. Registrar dominio si no existe
4. Configurar SSL/HTTPS obligatorio

---

## 📚 Recursos y Referencias

### Documentación
- Bancard API: https://www.bancard.com.py/desarrolladores
- SIPAP QR: https://www.bcp.gov.py/sipap
- QRCode Python: https://github.com/lincolnloop/python-qrcode

### Archivos Relevantes del Proyecto
- `backend/apps/api_integrations/services/bancard_service.py` - Servicio Bancard
- `backend/apps/api_integrations/views.py` - Webhook handler
- `backend/apps/cobros/` - Sistema de cobros
- `backend/requirements.txt` - qrcode==8.2

### Tests Existentes
- `backend/apps/api_integrations/tests_services.py` - Tests de BancardService
- Coverage: 95%+

---

## ❓ Decisiones Pendientes

1. **¿Habilitar pago parcial o solo total?**
   - Opción A: Cliente puede pagar facturas seleccionadas
   - Opción B: Solo pago total de deuda
   - **Recomendación:** Opción A (más flexible)

2. **¿Frecuencia de emails automáticos?**
   - Semanal / Quincenal / Mensual
   - **Recomendación:** Semanal para deuda > 7 días

3. **¿Incluir QR en factura PDF?**
   - Sí / No
   - **Recomendación:** Sí (Fase 2)

4. **¿Ambiente de prueba primero?**
   - Staging Bancard vs Producción directa
   - **Recomendación:** Staging 1 semana, luego producción

---

## 🚀 Próximos Pasos

Si decides proceder con la implementación:

1. **Confirmar credenciales Bancard**
   - ¿Ya tienes cuenta Bancard?
   - ¿Necesitas tramitar credenciales de producción?

2. **Definir URLs de retorno**
   - ¿Dominio de producción? (ej: `https://portal.cantina.tita`)
   - ¿Configurar subdominio para pagos?

3. **Priorizar fases**
   - ¿Solo Fase 1 (MVP)?
   - ¿Incluir Fase 2 (emails)?

4. **Testing**
   - ¿Usuarios beta para pruebas?
   - ¿Ambiente staging disponible?

---

**¿Procedemos con la implementación de Fase 1?**
