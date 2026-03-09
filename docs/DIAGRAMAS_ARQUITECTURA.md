# DIAGRAMAS DE ARQUITECTURA - SISTEMA CANTINA TITA

**Fecha de creación**: 6 de Marzo, 2026  
**Versión**: 1.0  
**Proyecto**: Sistema Integral de Gestión Cantina Escolar TITA

---

## 📋 TABLA DE CONTENIDOS

1. [Introducción](#introducción)
2. [Diagramas Entidad-Relación (DER)](#diagramas-entidad-relación-der)
   - [Módulo CORE - Tarjetas y Transacciones](#1-módulo-core---tarjetas-y-transacciones)
   - [Módulo CLIENTES](#2-módulo-clientes)
   - [Módulo PRODUCTOS e INVENTARIO](#3-módulo-productos-e-inventario)
   - [Módulo VENTAS](#4-módulo-ventas)
   - [Módulo ALMUERZOS](#5-módulo-almuerzos)
   - [Módulo COMPRAS](#6-módulo-compras)
   - [Módulo CONTABILIDAD](#7-módulo-contabilidad)
   - [Módulo USUARIOS](#8-módulo-usuarios)
   - [Módulo REPORTES](#9-módulo-reportes)
   - [Módulo NOTIFICACIONES](#10-módulo-notificaciones)
   - [Módulo API_INTEGRATIONS](#11-módulo-api_integrations)
3. [Diagramas de Casos de Uso](#diagramas-de-casos-de-uso)
4. [Diagramas de Secuencia](#diagramas-de-secuencia)
   - [Carga Online de Saldo](#carga-online-de-saldo)
   - [Venta con Tarjeta en POS](#venta-con-tarjeta-en-pos)
   - [Detección Automática de Anomalías](#detección-automática-de-anomalías)
5. [Diagrama de Despliegue](#diagrama-de-despliegue)
6. [Glosario Técnico](#glosario-técnico)

---

## INTRODUCCIÓN

Este documento contiene la documentación completa de los diagramas de arquitectura del Sistema Cantina TITA. Los diagramas fueron generados a partir del análisis exhaustivo de **97 modelos Django** distribuidos en **12 aplicaciones**.

### Propósito

- **Documentación técnica**: Referencia para desarrolladores y arquitectos
- **Onboarding**: Facilitar la integración de nuevos miembros del equipo
- **Mantenimiento**: Guía para evolución y refactorización del sistema
- **Auditoría**: Base para revisiones de arquitectura y cumplimiento

### Alcance

Los diagramas cubren:
- ✅ Estructura completa de base de datos (97 tablas)
- ✅ Relaciones entre entidades (FK, O2O, M2M)
- ✅ Flujos de negocio críticos (45 casos de uso)
- ✅ Secuencias de transacciones complejas
- ✅ Arquitectura de despliegue en producción

### Tecnologías Representadas

- **Backend**: Django 6.0.2, Python 3.11+
- **Base de Datos**: MySQL 8.0 (Master-Slave Replication)
- **Cache**: Redis 7.x (Master-Replica)
- **Message Broker**: RabbitMQ / Celery
- **Frontend**: React 18, TypeScript
- **Infraestructura**: Docker, Kubernetes, AWS/Azure

---

## DIAGRAMAS ENTIDAD-RELACIÓN (DER)

Los DER presentados corresponden al **modelo lógico** de la base de datos. Cada diagrama muestra:

- **PK**: Primary Key (Clave primaria)
- **FK**: Foreign Key (Clave foránea)
- **UK**: Unique Key (Clave única)
- **O2O**: Relación One-to-One
- **Cardinalidad**: 1:1, 1:N, N:M

### Convenciones de Notación

```
||--o{  : Uno a muchos (1:N)
||--||  : Uno a uno (1:1)
}o--o{  : Muchos a muchos (N:M)
}o--||  : Muchos a uno (N:1)
```

---

### 1. Módulo CORE - Tarjetas y Transacciones

**Propósito**: Gestión del núcleo del negocio - tarjetas estudiantiles, cargas de saldo, consumos y transacciones online.

**Entidades Principales** (11 tablas):
- `TARJETAS`: Tarjetas asignadas a clientes/estudiantes
- `CARGAS_SALDO`: Recargas de saldo (efectivo, transferencia, online)
- `CONSUMOS_TARJETA`: Uso de saldo en compras
- `TRANSACCIONES_ONLINE`: Pagos digitales (gateway)
- `MEDIOS_PAGO`: Configuración de formas de pago
- `TARJETAS_AUTORIZACION`: Tokens de autorización para operaciones
- `LIMITES_TRANSACCION`: Límites por rol y tipo de operación
- `REGISTRO_AUTORIZACIONES`: Historial de autorizaciones requeridas
- `CONFIGURACION_SISTEMA`: Parámetros configurables
- `CACHE_SISTEMA`: Cache de configuraciones

**Características Clave**:
- ✅ Saldo en tiempo real con límite de crédito
- ✅ Bloqueo preventivo de tarjetas
- ✅ Trazabilidad completa de movimientos
- ✅ Autorización de saldo negativo por cliente
- ✅ Control de límites por rol de empleado

**Relaciones Críticas**:
- Una TARJETA puede tener múltiples CARGAS_SALDO (1:N)
- Una TARJETA puede tener múltiples CONSUMOS_TARJETA (1:N)
- Un MEDIO_PAGO se usa en múltiples transacciones (1:N)
- Un ROL define múltiples LIMITES_TRANSACCION (1:N)

---

### 2. Módulo CLIENTES

**Propósito**: Gestión de clientes (padres), hijos (estudiantes), restricciones alimentarias y autorizaciones especiales.

**Entidades Principales** (8 tablas):
- `CLIENTES`: Padres/tutores responsables
- `HIJOS`: Estudiantes asociados a clientes
- `RESTRICCIONES_HIJOS`: Alergias, intolerancias, dietas especiales
- `HISTORIAL_GRADOS`: Evolución académica del estudiante
- `AUTORIZACIONES_SALDO_NEGATIVO`: Permisos para crédito
- `LOGS_AUTORIZACION_TARJETAS`: Auditoría de cambios en tarjetas
- `METODOS_CONTACTO`: Teléfonos, emails de contacto
- `DIRECCIONES_CLIENTE`: Domicilios registrados

**Características Clave**:
- ✅ Cliente con múltiples hijos
- ✅ Límite de crédito por cliente
- ✅ Cuenta corriente (saldo pendiente)
- ✅ Verificación de email/teléfono (KYC básico)
- ✅ Restricciones alimentarias con nivel de severidad
- ✅ Historial completo de grados cursados

**Reglas de Negocio**:
- Un CLIENTE puede tener N HIJOS (1:N)
- Un HIJO puede tener 1 tarjeta activa (1:1 lógico)
- Restricciones con fecha inicio/fin (vigencia temporal)
- Autorización de saldo negativo con plazo y monto máximo

---

### 3. Módulo PRODUCTOS e INVENTARIO

**Propósito**: Catálogo de productos, gestión de stock con trazabilidad FIFO, control de costos promedio ponderado y alertas inteligentes.

**Entidades Principales** (14 tablas):
- `CATEGORIAS`: Clasificación jerárquica de productos
- `PRODUCTOS`: Catálogo completo de artículos
- `UNIDADES_MEDIDA`: Kg, Lt, Unidad, etc.
- `STOCK_UNICO`: Stock actual por producto (O2O)
- `LISTAS_PRECIOS`: Precios diferenciados por tipo cliente
- `HISTORIAL_PRECIOS`: Trazabilidad de cambios de precio
- `MOVIMIENTOS_STOCK`: Todos los movimientos (entrada/salida)
- `LOTES_PRODUCTO`: Control FIFO con vencimiento
- `ALERTAS_STOCK`: Notificaciones de stock bajo
- `ALERTAS_VENCIMIENTO`: Avisos de productos próximos a vencer
- `COSTOS_HISTORICOS`: Evolución del costo promedio
- `AJUSTES_INVENTARIO`: Diferencias inventario físico vs sistema

**Características Clave**:
- ✅ Categorías infinitas anidadas (parent-child recursivo)
- ✅ Stock único por producto (relación O2O)
- ✅ Cálculo automático de costo promedio ponderado
- ✅ Control de lotes con FIFO
- ✅ Alertas automáticas de vencimiento (configurable por producto)
- ✅ Reserva de stock para pedidos
- ✅ Multi-precio según tipo de cliente

**Algoritmos Implementados**:
- **Costo Promedio Ponderado**: `nuevo_costo = (stock_actual * costo_actual + cantidad_ingreso * costo_ingreso) / (stock_actual + cantidad_ingreso)`
- **FIFO**: Al descontar stock, se consume primero el lote más antiguo
- **Alertas Inteligentes**: Stock mínimo + días antes del vencimiento

---

### 4. Módulo VENTAS

**Propósito**: Punto de venta (POS), facturación electrónica, promociones, notas de crédito y gestión de documentos tributarios.

**Entidades Principales** (9 tablas):
- `VENTAS`: Cabecera de venta/factura
- `DETALLES_VENTA`: Líneas de productos vendidos
- `DOCUMENTOS_TRIBUTARIOS`: Facturas electrónicas, timbrados
- `NOTAS_CREDITO_VENTA`: Devoluciones y ajustes
- `PROMOCIONES`: Descuentos por producto/categoría/período
- `DETALLES_PROMOCION`: Reglas de aplicación de promociones
- `COMISIONES_MEDIO_PAGO`: Costo por tipo de pago
- `HISTORIAL_VENTAS_ANULADAS`: Auditoría de anulaciones
- `RESERVAS_PRODUCTOS`: Apartado de productos

**Características Clave**:
- ✅ Venta con múltiples medios de pago
- ✅ Aplicación automática de promociones
- ✅ Facturación electrónica (SET-Paraguay)
- ✅ Notas de crédito reversibles
- ✅ Comisiones por medio de pago
- ✅ Anulación con motivo y auditoría completa
- ✅ Integración con tarjetas (consumo de saldo)

**Flujo de Venta**:
1. Crear VENTA (cabecera)
2. Agregar DETALLES_VENTA (productos)
3. Aplicar PROMOCIONES (si aplica)
4. Calcular totales (subtotal, IVA, descuentos)
5. Generar DOCUMENTO_TRIBUTARIO (factura)
6. Registrar en CAJA (módulo contabilidad)
7. Descontar STOCK (módulo inventario)
8. Si paga con tarjeta: Crear CONSUMO_TARJETA

---

### 5. Módulo ALMUERZOS

**Propósito**: Suscripciones de almuerzos escolares, menús diarios, control de consumo, facturación mensual y gestión de restricciones alimentarias.

**Entidades Principales** (10 tablas):
- `PLANES_ALMUERZO`: Planes mensuales (ej: 20 días, 15 días)
- `SUSCRIPCIONES_ALMUERZO`: Estudiante inscrito en plan
- `MENUS_DIARIOS`: Menú del día con capacidad
- `ITEMS_MENU`: Platos/bebidas incluidos en menú
- `REGISTROS_CONSUMO_ALMUERZO`: Marcado de asistencia diaria
- `CUENTAS_ALMUERZO_MENSUAL`: Factura mensual generada
- `PAGOS_ALMUERZO_MENSUAL`: Pagos recibidos de suscripción
- `ALERGENOS`: Catálogo de alérgenos
- `PEDIDOS_ALMUERZO`: Reserva anticipada de almuerzo
- `PREFERENCIAS_ALIMENTARIAS`: Dietas especiales (vegetariano, celíaco, etc.)

**Características Clave**:
- ✅ Planes con días incluidos y días extras
- ✅ Control de cupos por menú diario
- ✅ Restricciones de alérgenos por hijo
- ✅ Cuenta mensual automática (cron task)
- ✅ Suspensión temporal de suscripción
- ✅ Registro de consumo diario con hora
- ✅ Cobro de días extras al precio configurado

**Flujo de Negocio**:
1. Cliente SUSCRIBE a su hijo a un PLAN_ALMUERZO
2. Sistema genera CUENTA_ALMUERZO_MENSUAL cada mes
3. Cada día, MENUS_DIARIOS disponibles
4. Estudiante consume almuerzo → REGISTRO_CONSUMO_ALMUERZO
5. Si excede días del plan → cobro extra en cuenta mensual
6. Cliente realiza PAGO_ALMUERZO_MENSUAL

---

### 6. Módulo COMPRAS

**Propósito**: Gestión de compras a proveedores, órdenes de compra, recepción de mercadería, pagos a proveedores y cuentas por pagar.

**Entidades Principales** (8 tablas):
- `PROVEEDORES`: Datos de proveedores
- `CUENTAS_PROVEEDOR`: Cuentas bancarias para pagos
- `ORDENES_COMPRA`: Pedidos a proveedores
- `DETALLES_COMPRA`: Productos solicitados
- `PAGOS_PROVEEDOR`: Registros de pagos realizados
- `APLICACION_PAGOS`: Aplicación de pago a compras específicas
- `NOTAS_CREDITO_COMPRA`: Devoluciones de proveedor
- `COTIZACIONES`: Presupuestos recibidos

**Características Clave**:
- ✅ Orden de compra con aprobación
- ✅ Recepción parcial de mercadería
- ✅ Control de fechas (esperada vs real)
- ✅ Pago múltiple (un pago aplica a varias compras)
- ✅ Nota de crédito de proveedor
- ✅ Días de crédito por proveedor
- ✅ Límite de crédito

**Flujo de Compra**:
1. Crear ORDEN_COMPRA (estado: PENDIENTE)
2. Aprobar orden (empleado autorizado)
3. Recepcionar mercadería (fecha_entrega_real)
4. Crear LOTES_PRODUCTO (módulo inventario)
5. Generar MOVIMIENTOS_STOCK (entrada)
6. Actualizar COSTO_PROMEDIO (Stock)
7. Registrar PAGO_PROVEEDOR
8. Aplicar pago a compras (APLICACION_PAGOS)

---

### 7. Módulo CONTABILIDAD

**Propósito**: Gestión de caja, movimientos financieros, asientos contables, plan de cuentas, facturación electrónica (SET) y cierre de caja.

**Entidades Principales** (12 tablas):
- `EMPRESAS`: Datos tributarios de la empresa
- `TIMBRADOS`: Timbrados de SET para facturación
- `PUNTOS_EXPEDICION`: Sucursales/puntos de venta
- `CAJAS`: Cajas registradoras activas
- `MOVIMIENTOS_CAJA`: Ingresos/egresos de caja
- `DETALLES_MOVIMIENTO`: Denominaciones (billetes, monedas)
- `CIERRES_CAJA`: Cierre diario con cuadre
- `DIFERENCIAS_CIERRE`: Faltantes/sobrantes detectados
- `ASIENTOS_CONTABLES`: Registros contables (debe/haber)
- `DETALLES_ASIENTO`: Líneas de asiento
- `PLAN_CUENTAS`: Catálogo de cuentas contables
- `IMPUESTOS`: IVA, renta, etc.

**Características Clave**:
- ✅ Múltiples cajas concurrentes
- ✅ Arqueo de caja con diferencias
- ✅ Asientos contables automáticos (ventas, compras)
- ✅ Plan de cuentas jerárquico (hasta N niveles)
- ✅ Timbrados con fecha de vencimiento
- ✅ Facturación electrónica (XML firmado)
- ✅ Control de numeración de documentos

**Proceso de Cierre de Caja**:
1. Abrir CAJA (saldo_inicial)
2. Registrar MOVIMIENTOS_CAJA durante el día
3. Cerrar CAJA: ingresar saldo físico
4. Comparar saldo_sistema vs saldo_fisico
5. Registrar DIFERENCIAS_CIERRE (si existen)
6. Generar ASIENTO_CONTABLE automático
7. Requiere aprobación de supervisor si hay diferencias

---

### 8. Módulo USUARIOS

**Propósito**: Autenticación, autorización, gestión de roles y permisos, auditoría, 2FA, sesiones, patrones de acceso y alertas de seguridad.

**Entidades Principales** (15 tablas):
- `EMPLEADOS`: Usuarios del sistema
- `ROLES`: Perfiles de acceso (administrador, cajero, gerente, etc.)
- `PERMISOS`: Acciones permitidas (crear_venta, ver_reportes, etc.)
- `PERMISOS_ROL`: Asignación de permisos a roles (CRUD granular)
- `PERFILES_USUARIO`: Configuración personalizada (tema, idioma, timezone)
- `SESIONES_USUARIO`: Sesiones activas (multi-dispositivo)
- `TOKENS_ACCESO`: JWT, refresh tokens
- `AUTENTICACION_2FA`: Configuración de autenticación de dos factores
- `INTENTOS_2FA`: Historial de intentos de verificación
- `INTENTOS_LOGIN`: Registro de accesos (exitosos y fallidos)
- `HISTORIAL_ACCESO`: Auditoría de acciones en el sistema
- `EVENTOS_AUDITORIA`: Log detallado de cambios (antes/después)
- `PATRONES_ACCESO`: ML para detección de anomalías
- `ALERTAS_SEGURIDAD`: Notificaciones de eventos sospechosos

**Características Clave**:
- ✅ Autenticación 2FA obligatoria para administradores
- ✅ Permisos granulares (CREATE, READ, UPDATE, DELETE)
- ✅ Sesiones multi-dispositivo con revocación
- ✅ Auditoría completa (quién, qué, cuándo, desde dónde)
- ✅ Detección de patrones anómalos (horarios, IPs)
- ✅ Bloqueo automático tras N intentos fallidos
- ✅ Tokens con expiración y refresh automático

**Niveles de Seguridad**:
- **Nivel 1**: Empleado básico (sin 2FA)
- **Nivel 2**: Cajero/supervisor (2FA opcional)
- **Nivel 3**: Administrador (2FA obligatorio)
- **Nivel 4**: Gerente/dueño (2FA + alertas en tiempo real)

---

### 9. Módulo REPORTES

**Propósito**: Generación de reportes, dashboards con KPIs, tareas programadas, suscripciones a reportes y exportación de datos.

**Entidades Principales** (11 tablas):
- `PLANTILLAS_REPORTE`: Definición SQL de reportes
- `PARAMETROS_REPORTE`: Filtros configurables
- `REPORTES_GENERADOS`: Historial de ejecuciones
- `DESTINATARIOS_REPORTE`: Envío por email/WhatsApp
- `SUSCRIPCIONES_REPORTE`: Reportes automáticos (diario, semanal, mensual)
- `DASHBOARDS`: Paneles personalizables
- `WIDGETS_DASHBOARD`: Gráficos en dashboard
- `KPIS`: Indicadores clave de rendimiento
- `TAREAS_PROGRAMADAS`: Cron jobs configurables
- `EJECUCIONES_TAREA`: Historial de ejecuciones
- `CACHE_REPORTES`: Cache de reportes pesados

**Características Clave**:
- ✅ Reportes con SQL dinámico
- ✅ Parámetros con validación de tipo
- ✅ Múltiples formatos (PDF, Excel, CSV)
- ✅ Suscripciones con cron expression
- ✅ Dashboards con drag-and-drop de widgets
- ✅ KPIs con fórmulas personalizadas
- ✅ Cache inteligente para reportes pesados

**Reportes Pre-configurados**:
- Ventas diarias/mensuales/anuales
- Productos más vendidos
- Clientes con mayor consumo
- Stock valorizado
- Cuentas por cobrar/pagar
- Almuerzos consumidos vs plan
- Rendimiento de cajas

---

### 10. Módulo NOTIFICACIONES

**Propósito**: Sistema multi-canal de comunicación (Email, SMS, Push, WhatsApp), campañas de marketing, alertas automáticas y detección de anomalías.

**Entidades Principales** (13 tablas):
- `PLANTILLAS_NOTIFICACION`: Templates de mensajes
- `NOTIFICACIONES_EMAIL`: Emails enviados
- `NOTIFICACIONES_SMS`: SMS enviados
- `NOTIFICACIONES_PUSH`: Push notifications
- `CAMPANAS`: Campañas de comunicación masiva
- `DESTINATARIOS_CAMPANA`: Target de campaña
- `PREFERENCIAS_NOTIFICACION`: Opt-in/opt-out por canal
- `ALERTAS_AUTOMATICAS`: Triggers de alertas
- `LOG_NOTIFICACIONES`: Trazabilidad de envíos
- `ANOMALIAS_DETECTADAS`: Detección basada en reglas/ML
- `RESTRICCIONES_HORARIAS`: No molestar (horarios permitidos)
- `ESTADISTICAS_ENVIO`: Métricas de campañas (tasa apertura, clics)

**Características Clave**:
- ✅ Multi-canal (Email, SMS, Push, WhatsApp Business)
- ✅ Templates con variables dinámicas (Jinja2)
- ✅ Campañas segmentadas por tipo de usuario
- ✅ Tracking de apertura y clics (Email)
- ✅ Confirmación de entrega (SMS)
- ✅ Detección de rebotes (bounce detection)
- ✅ Restricciones horarias (no spam nocturno)
- ✅ Integración con Twilio, SendGrid, Firebase

**Alertas Automáticas**:
- Stock bajo
- Productos por vencer (< 7 días)
- Tarjeta bloqueada
- Saldo bajo en tarjeta
- Consumo anómalo detectado
- Cierre de caja con diferencias
- Factura vencida no pagada

---

### 11. Módulo API_INTEGRATIONS

**Propósito**: Integración con APIs externas, webhooks, sincronizaciones bidireccionales, logs de llamadas y métricas de performance.

**Entidades Principales** (9 tablas):
- `PROVEEDORES_API`: Configuración de APIs externas
- `ENDPOINTS_API`: Catálogo de endpoints disponibles
- `CREDENCIALES_API`: API keys, tokens, OAuth
- `LOGS_LLAMADAS_API`: Trazabilidad de requests/responses
- `WEBHOOKS_RECIBIDOS`: Eventos recibidos de terceros
- `METRICAS_API`: Performance (latencia, tasa de éxito)
- `SINCRONIZACIONES`: Jobs de sincronización
- `LOGS_SINCRONIZACION`: Ejecuciones de sync
- `TRANSFORMACIONES_DATOS`: ETL scripts

**Características Clave**:
- ✅ Configuración multi-ambiente (dev, staging, prod)
- ✅ Retry automático con backoff exponencial
- ✅ Rate limiting por endpoint
- ✅ Validación de schemas (request/response)
- ✅ Webhooks con firma HMAC
- ✅ Sincronización bidireccional
- ✅ Transformación de datos (ETL)

**Integraciones Soportadas**:
- **Pagos**: Bancard, Pagopar, PayPal
- **Email**: SendGrid, Amazon SES
- **SMS**: Twilio, Vonage
- **WhatsApp**: WhatsApp Business API
- **Contabilidad**: Integración con software contable externo
- **ERP**: Sincronización con sistemas legacy

---

## DIAGRAMAS DE CASOS DE USO

Los casos de uso representan las interacciones entre **actores** (usuarios, sistemas externos) y el sistema Cantina TITA.

### Actores del Sistema

| Actor | Descripción | Permisos |
|-------|-------------|----------|
| **Cliente/Padre** | Padre o tutor del estudiante | Consultar saldo, cargar saldo online, gestionar hijos |
| **Estudiante** | Usuario de la tarjeta | Consumir saldo, ver almuerzo del día |
| **Cajero** | Empleado de caja | Realizar ventas, cargar saldo, emitir facturas, abrir/cerrar caja |
| **Administrador** | Admin del sistema | Gestión completa, configuraciones, autorizaciones |
| **Gerente** | Gerente/dueño | Reportes financieros, análisis, aprobaciones críticas |
| **Proveedor Externo** | API externa | Confirmaciones de mercadería, webhooks de pago |
| **Sistema Automatizado** | Tareas programadas | Alertas, cálculos automáticos, detección anomalías |

### Casos de Uso por Módulo

#### Gestión de Clientes (6 casos)
- **UC1**: Registrar Cliente
- **UC2**: Gestionar Hijos/Estudiantes
- **UC3**: Emitir Tarjeta
- **UC4**: Bloquear/Desbloquear Tarjeta
- **UC5**: Consultar Saldo
- **UC6**: Ver Historial Movimientos

#### Operaciones de Tarjetas (5 casos)
- **UC7**: Cargar Saldo (efectivo, transferencia)
- **UC8**: Consumir Saldo (compra)
- **UC9**: Realizar Pago Online (gateway)
- **UC10**: Autorizar Saldo Negativo
- **UC11**: Revertir Transacción

#### Ventas y POS (5 casos)
- **UC12**: Realizar Venta
- **UC13**: Aplicar Promociones
- **UC14**: Emitir Factura Electrónica
- **UC15**: Generar Nota de Crédito
- **UC16**: Procesar Pago Múltiple

#### Almuerzos (5 casos)
- **UC17**: Suscribirse a Plan Almuerzo
- **UC18**: Configurar Menú Diario
- **UC19**: Registrar Consumo Almuerzo
- **UC20**: Generar Cuenta Mensual (automático)
- **UC21**: Gestionar Restricciones Alimentarias

#### Inventario (5 casos)
- **UC22**: Registrar Entrada Mercadería
- **UC23**: Ajustar Stock (inventario físico)
- **UC24**: Generar Alerta Vencimiento (automático)
- **UC25**: Calcular Costo Promedio (automático)
- **UC26**: Consultar Stock Disponible

#### Compras (4 casos)
- **UC27**: Crear Orden Compra
- **UC28**: Recepcionar Mercadería
- **UC29**: Registrar Pago Proveedor
- **UC30**: Conciliar Cuenta Proveedor

#### Contabilidad (5 casos)
- **UC31**: Abrir Caja
- **UC32**: Registrar Movimiento Caja
- **UC33**: Cerrar Caja (con cuadre)
- **UC34**: Generar Asiento Contable (automático)
- **UC35**: Emitir Reporte Financiero

#### Reportes y BI (5 casos)
- **UC36**: Generar Reporte Ventas
- **UC37**: Consultar Dashboard KPIs
- **UC38**: Programar Reporte Automático
- **UC39**: Exportar Datos (Excel, CSV)
- **UC40**: Analizar Tendencias

#### Seguridad y Auditoría (5 casos)
- **UC41**: Autenticación 2FA
- **UC42**: Gestionar Permisos Rol
- **UC43**: Auditar Operaciones
- **UC44**: Detectar Anomalías (automático)
- **UC45**: Autorizar Operación Crítica

---

## DIAGRAMAS DE SECUENCIA

Los diagramas de secuencia muestran la interacción temporal entre componentes del sistema para casos de uso complejos.

### Carga Online de Saldo

**Actores**: Cliente, Portal Web, API Backend, Gateway de Pago

**Flujo Principal**:
1. Cliente accede al portal web
2. Autenticación con credenciales
3. Sistema solicita código 2FA por email
4. Cliente ingresa código y obtiene token JWT
5. Cliente selecciona tarjeta y monto a cargar
6. Sistema valida límites y crea transacción pendiente
7. Redirección a gateway de pago (Bancard/Pagopar)
8. Cliente ingresa datos de tarjeta de crédito
9. Gateway procesa pago

**Flujos Alternativos**:
- **Pago Exitoso**: 
  - Webhook notifica aprobación
  - Sistema acredita saldo en tarjeta
  - Se invalida cache de Redis
  - Se envía comprobante por email
- **Pago Rechazado**:
  - Webhook notifica rechazo
  - Transacción marcada como RECHAZADO
  - Notificación al cliente
- **Timeout**:
  - Tras 5 minutos sin confirmación
  - Transacción marcada como EXPIRADO

**Componentes Involucrados**:
- Portal Web (React SPA)
- API Backend (Django)
- Servicio Auth (JWT + 2FA)
- Servicio Tarjetas
- Gateway de Pago (externo)
- Base de Datos MySQL
- Cache Redis
- Servicio Email

**Tiempo Promedio**: 12-45 segundos (dependiendo del gateway)

---

### Venta con Tarjeta en POS

**Actores**: Estudiante, Terminal POS, Sistema Backend

**Flujo Principal**:
1. Estudiante presenta tarjeta (NFC/QR)
2. POS lee tarjeta y consulta saldo
3. Sistema valida tarjeta (no bloqueada, saldo disponible)
4. Cajero escanea productos
5. Sistema verifica stock disponible por cada producto
6. POS calcula total (aplicando promociones si aplica)
7. Estudiante confirma compra
8. Sistema valida límites de transacción

**Proceso Transaccional** (ACID):
```sql
BEGIN TRANSACTION;
  - INSERT INTO ventas
  - INSERT INTO detalles_venta (por cada producto)
  - UPDATE stock_unico (descontar cantidades)
  - INSERT INTO movimientos_stock
  - UPDATE tarjetas (descontar saldo)
  - INSERT INTO consumos_tarjeta
  - INSERT INTO movimientos_caja
  - UPDATE cajas (incrementar saldo)
COMMIT;
```

**Flujos Alternativos**:
- **Tarjeta Bloqueada**: Rechazar operación inmediatamente
- **Saldo Insuficiente SIN Autorización**: Rechazar venta
- **Saldo Insuficiente CON Autorización**: 
  - Verificar autorización de saldo negativo
  - Permitir venta si está dentro del límite autorizado
- **Stock Insuficiente**: Notificar producto no disponible

**Monitoreo de Performance**:
- Tracking de tiempo de ejecución
- Alerta si transacción > 1000ms
- Registro en tabla de performance para análisis

**Tiempo Promedio**: 200-400ms

---

### Detección Automática de Anomalías

**Trigger**: Cron job cada 15 minutos

**Análisis Paralelo**:
El sistema ejecuta múltiples verificaciones en paralelo:

1. **Stock Crítico**:
   - Consulta productos con stock < stock_mínimo
   - Genera alertas para responsable de inventario
   - Envía email con lista de productos
   - Actualiza dashboard con badge rojo

2. **Lotes Próximos a Vencer**:
   - Consulta lotes con vencimiento < 7 días
   - Calcula nivel de urgencia:
     - ALTA: < 3 días
     - MEDIA: 3-7 días
   - Envía email a responsable
   - Si < 3 días: envía SMS urgente al gerente

3. **Consumos Anómalos**:
   - Calcula estadísticas de consumo (promedio, desviación estándar)
   - Detecta tarjetas con consumo > 300% del promedio
   - Ejemplo: Promedio $15.000, detecta tarjeta con $150.000 en un día
   - **Acción automática**: Bloqueo preventivo de tarjeta
   - Notifica a supervisor y gerente por email + SMS
   - Registra evento en auditoría

4. **Intentos Login Sospechosos**:
   - Detecta usuarios con > 5 intentos fallidos
   - Identifica patrones: misma IP, horarios inusuales
   - **Acción automática**: Bloqueo temporal de cuenta
   - Alerta al equipo de seguridad
   - Dashboard de seguridad: alerta roja

**Resultado**:
- Dashboard actualizado en tiempo real
- Badges con cantidad de alertas por tipo
- Emails/SMS enviados a responsables
- Bloqueos preventivos automáticos
- Log completo de ejecución

**Tiempo de Ejecución**: 2-5 segundos (dependiendo de volumen de datos)

---

## DIAGRAMA DE DESPLIEGUE

El diagrama de despliegue muestra la arquitectura física de producción del sistema Cantina TITA.

### Capas de la Arquitectura

#### 1. Capa de Usuarios
- **App Móvil**: React Native (iOS/Android) - Aplicación para padres
- **Portal Web**: React SPA - Portal de clientes y empleados
- **Terminal POS**: Electron Desktop App - Punto de venta en cantina

#### 2. Capa de Red - CDN & Balanceo
- **CloudFlare CDN**: 
  - Cache de assets estáticos (imágenes, CSS, JS)
  - Protección DDoS
  - SSL/TLS universal
  - Invalidación de cache automática en deploy
- **Load Balancer** (Nginx/HAProxy):
  - Balanceo round-robin
  - SSL Termination
  - Health checks
  - Rate limiting
  - IP whitelisting para endpoints admin

#### 3. Zona DMZ - Frontend
- **2 Servidores Frontend** (Alta disponibilidad):
  - Nginx como reverse proxy
  - Servir React SPA compilado
  - Redirección HTTP → HTTPS
  - Compresión gzip/brotli
  - Cache headers optimizados

#### 4. Capa de Aplicación - Backend
- **3 Servidores API** (Horizontal scaling):
  - Django 6.0.2 + Django REST Framework
  - Gunicorn WSGI Server (4 workers por servidor)
  - Port 8000 (interno)
  - Auto-scaling basado en CPU > 70%

#### 5. Servicios de Fondo - Workers
- **2 Celery Workers**:
  - Procesamiento asíncrono de tareas
  - 4 threads por worker
  - Tareas: emails, PDF, reportes pesados, sincronizaciones
- **Celery Beat** (Scheduler):
  - Tareas programadas (cron)
  - Generación de reportes automáticos
  - Detección de anomalías
  - Cierre automático de cuentas mensuales

#### 6. Capa de Cache y Mensajería
- **Redis Master** (Write):
  - Cache de sesiones
  - Cache de queries frecuentes
  - Configuración del sistema
  - Pub/Sub para notificaciones real-time
- **Redis Replica** (Read):
  - Replicación asíncrona del master
  - Read-only para consultas
  - Failover automático
- **RabbitMQ** (Message Broker):
  - Cola de tareas Celery
  - Garantiza delivery (persistent queues)
  - Dead letter queue para errores

#### 7. Capa de Datos - Base de Datos
- **MySQL Master** (Write):
  - MySQL 8.0 con InnoDB
  - Binary logging habilitado
  - Backup diario a las 2 AM
  - Connection pooling (50 conexiones)
- **2 MySQL Slaves** (Read):
  - Replicación master-slave (asíncrona)
  - Read-only para reportes y consultas
  - Balanceo entre slaves para queries SELECT

#### 8. Almacenamiento
- **AWS S3** (Object Storage):
  - Archivos de usuarios (fotos, documentos)
  - Backups de base de datos
  - Reportes generados (PDF, Excel)
  - Versionado habilitado
  - Lifecycle policies (borrado automático tras 90 días)
- **Backup Server**:
  - Snapshots diarios de BD
  - Mysqldump completo + incremental
  - Retención: 30 días
  - Upload automático a S3

#### 9. Monitoreo y Logs
- **Prometheus**: Recolección de métricas
  - Request latency
  - Queries SQL lentas (> 100ms)
  - Uso de cache (hit rate)
  - Errores HTTP (4xx, 5xx)
- **Grafana**: Dashboards visuales
  - Dashboard de requests/segundo
  - Dashboard de performance de BD
  - Dashboard de uso de recursos
- **ELK Stack** (Elasticsearch + Logstash + Kibana):
  - Centralización de logs
  - Búsqueda full-text en logs
  - Alertas basadas en logs
- **Sentry**: Error Tracking & APM
  - Captura de excepciones Python
  - Source maps de React
  - Alertas por email/Slack
  - Performance monitoring

#### 10. Servicios Externos
- **Payment Gateways**:
  - Bancard (Paraguay)
  - Pagopar
  - Integración con webhooks
- **Email Service**:
  - SendGrid: Emails transaccionales
  - Amazon SES: Emails masivos (campañas)
- **SMS Service**:
  - Twilio: SMS internacionales
  - Proveedor local para Paraguay
- **WhatsApp Business API**:
  - Notificaciones vía WhatsApp
  - Confirmaciones de pago

### Flujo de una Request

```
Cliente → CDN (cache) → Load Balancer → Frontend Server → API Server → Redis Cache (si existe)
                                                               ↓
                                                          MySQL Slave (lectura)
                                                               ↓
                                                        MySQL Master (escritura)
```

### Estrategia de Escalabilidad

- **Vertical**: Aumentar CPU/RAM de servidores API
- **Horizontal**: Agregar más servidores API (auto-scaling)
- **Database Sharding**: Particionar BD por tipo de dato (futura implementación)
- **Read Replicas**: Agregar más slaves MySQL según carga de reportes

### Backup y Disaster Recovery

- **RPO** (Recovery Point Objective): 1 hora
- **RTO** (Recovery Time Objective): 30 minutos
- **Estrategia**:
  - Backups diarios en S3
  - Replicación cross-region de S3
  - Snapshots de volúmenes cada 6 horas
  - Plan de recuperación documentado

---

## GLOSARIO TÉCNICO

### Términos de Negocio

- **Tarjeta**: Medio de pago prepago asignado a un estudiante
- **Carga de Saldo**: Acreditación de dinero a una tarjeta
- **Consumo**: Uso de saldo de tarjeta en compra
- **Saldo Negativo**: Permitir consumo mayor al saldo (crédito)
- **Plan Almuerzo**: Suscripción mensual de almuerzos
- **Menú Diario**: Oferta de almuerzo del día
- **FIFO**: First In, First Out - Control de lotes por antigüedad
- **Costo Promedio Ponderado**: Método de valorización de inventario
- **Factura Electrónica**: Documento tributario digital (SET Paraguay)
- **Timbrado**: Autorización de numeración de documentos

### Términos Técnicos

- **DER**: Diagrama Entidad-Relación
- **PK**: Primary Key (Clave primaria)
- **FK**: Foreign Key (Clave foránea)
- **UK**: Unique Key (Clave única)
- **O2O**: One-to-One (Relación 1:1)
- **CRUD**: Create, Read, Update, Delete
- **JWT**: JSON Web Token (autenticación stateless)
- **2FA**: Two-Factor Authentication
- **OTP**: One-Time Password
- **HMAC**: Hash-based Message Authentication Code
- **ETL**: Extract, Transform, Load
- **ACID**: Atomicity, Consistency, Isolation, Durability
- **API**: Application Programming Interface
- **REST**: Representational State Transfer
- **Webhook**: HTTP callback automático
- **Cron**: Tarea programada con expresión temporal
- **Cache Invalidation**: Limpieza de cache para refrescar datos
- **Load Balancer**: Balanceador de carga
- **CDN**: Content Delivery Network
- **SSL/TLS**: Secure Sockets Layer / Transport Layer Security
- **Binary Log**: Registro binario de MySQL para replicación
- **Connection Pooling**: Reutilización de conexiones a BD

### Acrónimos del Proyecto

- **TITA**: Nombre del sistema (Tecnología Integral para el Área de Alimentos)
- **POS**: Point of Sale (Punto de Venta)
- **KPI**: Key Performance Indicator
- **BI**: Business Intelligence
- **SET**: Sub-Secretaría de Estado de Tributación (Paraguay)
- **RUC**: Registro Único del Contribuyente
- **IVA**: Impuesto al Valor Agregado

---

## NOTAS FINALES

### Versionado de Diagramas

Este documento corresponde a la **versión 1.0** de los diagramas de arquitectura, basado en la estructura de base de datos del **Sprint 5 (Marzo 2026)**.

**Control de Cambios**:
| Versión | Fecha | Autor | Descripción |
|---------|-------|-------|-------------|
| 1.0 | 2026-03-06 | Sistema | Versión inicial completa |

### Mantenimiento

Los diagramas deben actualizarse cuando:
- Se agreguen nuevas tablas o campos críticos
- Se modifiquen relaciones entre entidades
- Se implementen nuevos casos de uso
- Se cambie la arquitectura de despliegue

**Responsable**: Equipo de Arquitectura  
**Frecuencia**: Trimestral o ante cambios mayores

### Herramientas Utilizadas

- **Generación de Diagramas**: Mermaid.js
- **Renderizado**: GitHub Copilot + VS Code
- **Análisis de Modelos**: Django ORM introspection
- **Documentación**: Markdown

### Referencias

- **Django Models**: `backend/apps/*/models.py`
- **API Endpoints**: `backend/api/v1/urls.py`
- **Configuración**: `backend/backend/settings/`
- **Tests**: `backend/apps/*/tests_*.py`

---

**© 2026 Cantina TITA. Todos los derechos reservados.**

Este documento es confidencial y de uso interno exclusivamente.
