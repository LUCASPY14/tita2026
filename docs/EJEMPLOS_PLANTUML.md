# EJEMPLOS PlantUML - CANTINA TITA
## Diagramas Complementarios a Mermaid

> **Nota**: PlantUML ofrece mayor detalle para diagramas UML complejos.
> Para ver estos diagramas, presiona `Alt+D` en VS Code.

---

## 📚 Diagrama de Clases - Modelos Django CORE

### Tarjetas con Métodos y Propiedades

```plantuml
@startuml Diagrama_Clases_Tarjetas
!theme cerulean-outline

skinparam classAttributeIconSize 0
skinparam shadowing false
skinparam class {
    BackgroundColor White
    BorderColor #2C3E50
    ArrowColor #3498DB
}

class Tarjeta <<Model>> {
    ' === FIELDS ===
    - id: AutoField(PK)
    - numero_tarjeta: CharField(20, unique)
    - saldo_actual: DecimalField(10,2)
    - limite_credito: DecimalField(10,2)
    - bloqueada: BooleanField(default=False)
    - fecha_emision: DateTimeField(auto_now_add)
    - estado: CharField(choices)
    
    ' === FOREIGN KEYS ===
    - cliente: ForeignKey(Cliente)
    - hijo: ForeignKey(Hijo, null=True)
    
    ' === METHODS ===
    + cargar_saldo(monto: Decimal): CargaSaldo
    + consumir(monto: Decimal, venta: Venta): ConsumoTarjeta
    + bloquear(motivo: str): void
    + desbloquear(): void
    + get_saldo_disponible(): Decimal
    + puede_consumir(monto: Decimal): bool
    + get_consumos_mes(mes: int, anio: int): QuerySet
    
    ' === PROPERTIES ===
    {abstract} saldo_total: Decimal
    {abstract} esta_bloqueada: bool
}

class Cliente <<Model>> {
    - id: AutoField(PK)
    - nombre: CharField(100)
    - apellido: CharField(100)
    - documento: CharField(20, unique)
    - telefono: CharField(20)
    - email: EmailField()
    - limite_credito: DecimalField(10,2)
    - cuenta_corriente: DecimalField(10,2)
    - activo: BooleanField(default=True)
    
    + get_tarjetas_activas(): QuerySet
    + get_saldo_total(): Decimal
    + autorizar_credito(monto: Decimal): bool
}

class Hijo <<Model>> {
    - id: AutoField(PK)
    - nombre: CharField(100)
    - apellido: CharField(100)
    - fecha_nacimiento: DateField()
    - documento: CharField(20, unique)
    - grado_actual: CharField(50)
    - seccion: CharField(10)
    - activo: BooleanField(default=True)
    
    + get_restricciones_activas(): QuerySet
    + tiene_restriccion(alergeno: str): bool
    + get_edad(): int
}

class CargaSaldo <<Model>> {
    - id: AutoField(PK)
    - monto: DecimalField(10,2)
    - comision: DecimalField(10,2)
    - tipo_carga: CharField(choices)
    - fecha_carga: DateTimeField(auto_now_add)
    - estado: CharField(choices)
    
    - tarjeta: ForeignKey(Tarjeta)
    - medio_pago: ForeignKey(MedioPago)
    - empleado: ForeignKey(Empleado)
    
    + procesar(): void
    + cancelar(): void
    + get_monto_neto(): Decimal
}

class ConsumoTarjeta <<Model>> {
    - id: AutoField(PK)
    - monto: DecimalField(10,2)
    - fecha_consumo: DateTimeField(auto_now_add)
    - tipo_consumo: CharField(choices)
    - saldo_anterior: DecimalField(10,2)
    - saldo_nuevo: DecimalField(10,2)
    
    - tarjeta: ForeignKey(Tarjeta)
    - venta: ForeignKey(Venta, null=True)
    - medio_pago: ForeignKey(MedioPago)
}

class MedioPago <<Model>> {
    - id: AutoField(PK)
    - nombre: CharField(50, unique)
    - tipo: CharField(choices)
    - comision_porcentaje: DecimalField(5,2)
    - comision_fija: DecimalField(10,2)
    - activo: BooleanField(default=True)
    
    + calcular_comision(monto: Decimal): Decimal
}

' === RELATIONSHIPS ===
Cliente "1" --> "0..*" Tarjeta : posee
Cliente "1" --> "0..*" Hijo : tiene
Hijo "1" o--> "0..*" Tarjeta : usa

Tarjeta "1" --> "0..*" CargaSaldo : recibe
Tarjeta "1" --> "0..*" ConsumoTarjeta : genera

MedioPago "1" --> "0..*" CargaSaldo : procesa
MedioPago "1" --> "0..*" ConsumoTarjeta : acepta

note right of Tarjeta
    **Estado de Tarjeta**
    - ACTIVA
    - BLOQUEADA
    - INACTIVA
    - VENCIDA
end note

note right of CargaSaldo
    **Tipos de Carga**
    - EFECTIVO
    - TRANSFERENCIA
    - ONLINE
    - POS
end note

@enduml
```

---

## 🏗️ Diagrama de Componentes - Arquitectura Backend

```plantuml
@startuml Arquitectura_Backend
!theme vibrant

skinparam componentStyle rectangle
skinparam shadowing false

package "Frontend Layer" #LightBlue {
    component [React SPA] as react
    component [Redux Store] as redux
    component [API Client] as apiclient
    
    react --> redux
    react --> apiclient
}

package "API Gateway" #LightGreen {
    component [Nginx] as nginx
    component [Load Balancer] as lb
    
    nginx --> lb
}

package "Application Layer" #LightYellow {
    package "Django Apps" {
        component [API v1] as api
        component [Authentication] as auth
        component [WebSocket] as ws
        
        component [Apps.Ventas] as ventas
        component [Apps.Inventario] as inventario
        component [Apps.Almuerzos] as almuerzos
        component [Apps.Clientes] as clientes
        
        api --> ventas
        api --> inventario
        api --> almuerzos
        api --> clientes
    }
    
    component [Gunicorn] as gunicorn
    component [Celery Workers] as celery
    component [Celery Beat] as beat
    
    gunicorn --> api
    beat --> celery
}

package "Data Layer" #LightCoral {
    database "MySQL\nMaster" as mysql_m
    database "MySQL\nSlave 1" as mysql_s1
    database "MySQL\nSlave 2" as mysql_s2
    
    mysql_m .down.> mysql_s1 : replication
    mysql_m .down.> mysql_s2 : replication
}

package "Cache Layer" #LightPink {
    component [Redis Master] as redis_m
    component [Redis Replica] as redis_r
    
    redis_m .> redis_r : replication
}

package "Queue Layer" #Lavender {
    component [RabbitMQ] as rabbitmq
}

package "External Services" #LightGray {
    component [Email Service] as email
    component [SMS Gateway] as sms
    component [Payment Gateway] as payment
    component [WhatsApp API] as whatsapp
}

' === CONNECTIONS ===
apiclient --> nginx : HTTPS
lb --> gunicorn : HTTP

api --> auth : validate
api --> redis_m : cache
api --> mysql_m : write
api --> mysql_s1 : read

celery --> rabbitmq : consume
api --> rabbitmq : publish

celery --> mysql_m : write
celery --> email : send
celery --> sms : send
celery --> payment : process
celery --> whatsapp : send

@enduml
```

---

## 🔄 Diagrama de Estados - Ciclo de Vida de Venta

```plantuml
@startuml Estados_Venta
!theme cerulean

skinparam state {
    BackgroundColor White
    BorderColor #2C3E50
    ArrowColor #3498DB
}

[*] --> PENDIENTE : Crear venta

state PENDIENTE {
    PENDIENTE : entry / validar_stock()
    PENDIENTE : do / reservar_productos()
}

PENDIENTE --> EN_PROCESO : Confirmar
PENDIENTE --> CANCELADA : Cancelar

state EN_PROCESO {
    EN_PROCESO : entry / procesar_pago()
    EN_PROCESO : do / descontar_stock()
}

EN_PROCESO --> COMPLETADA : Pago exitoso
EN_PROCESO --> RECHAZADA : Pago rechazado
EN_PROCESO --> CANCELADA : Timeout

state COMPLETADA {
    COMPLETADA : entry / generar_factura()
    COMPLETADA : entry / enviar_comprobante()
    COMPLETADA : do / actualizar_reportes()
}

COMPLETADA --> ANULADA : Nota de crédito (dentro de 24h)

state CANCELADA {
    CANCELADA : entry / liberar_stock()
    CANCELADA : entry / notificar_cliente()
}

state RECHAZADA {
    RECHAZADA : entry / liberar_stock()
    RECHAZADA : entry / registrar_intento()
}

state ANULADA {
    ANULADA : entry / reversar_stock()
    ANULADA : entry / reversar_saldo()
    ANULADA : entry / emitir_nota_credito()
}

COMPLETADA --> [*]
CANCELADA --> [*]
RECHAZADA --> [*]
ANULADA --> [*]

note right of EN_PROCESO
    **Validaciones**
    • Stock disponible
    • Saldo suficiente
    • Cliente activo
    • Límite de crédito
end note

note right of COMPLETADA
    **Acciones Automáticas**
    • Factura SET (Paraguay)
    • Email/SMS comprobante
    • Actualizar KPIs
    • Trigger Analytics
end note

@enduml
```

---

## 📦 Diagrama de Deployment - Producción

```plantuml
@startuml Deployment_Production
!theme vibrant

skinparam node {
    BackgroundColor White
    BorderColor #2C3E50
}

cloud "Internet" {
    actor Cliente
    actor Estudiante
    actor Empleado
}

node "CDN - CloudFlare" {
    artifact "Static Assets"
    artifact "Images"
}

node "Load Balancer\n(Nginx)" as lb {
}

node "Web Server 1\n(Ubuntu 22.04)" as web1 {
    component [Frontend\nReact 18.2] as fe1
    component [Nginx 1.24] as nginx1
    
    nginx1 --> fe1
}

node "Web Server 2\n(Ubuntu 22.04)" as web2 {
    component [Frontend\nReact 18.2] as fe2
    component [Nginx 1.24] as nginx2
    
    nginx2 --> fe2
}

node "API Server 1\n(Ubuntu 22.04)" as api1 {
    component [Django 4.2] as django1
    component [Gunicorn 21.2] as gun1
    
    gun1 --> django1
}

node "API Server 2\n(Ubuntu 22.04)" as api2 {
    component [Django 4.2] as django2
    component [Gunicorn 21.2] as gun2
    
    gun2 --> django2
}

node "Worker Server\n(Ubuntu 22.04)" as worker {
    component [Celery Worker 1] as cel1
    component [Celery Worker 2] as cel2
    component [Celery Beat] as beat
}

node "Database Server\n(Ubuntu 22.04)" as db {
    database "MySQL 8.0\nMaster" as mysql_m
    database "MySQL 8.0\nSlave 1" as mysql_s1
    database "MySQL 8.0\nSlave 2" as mysql_s2
    
    mysql_m .> mysql_s1
    mysql_m .> mysql_s2
}

node "Cache Server\n(Ubuntu 22.04)" as cache {
    database "Redis 7.2\nMaster" as redis_m
    database "Redis 7.2\nReplica" as redis_r
    
    redis_m .> redis_r
}

node "Queue Server\n(Ubuntu 22.04)" as queue {
    component [RabbitMQ 3.12] as rabbitmq
}

node "Monitoring\n(Ubuntu 22.04)" as monitor {
    component [Prometheus] as prom
    component [Grafana] as graf
    component [Sentry] as sentry
    
    prom --> graf
}

' === CONNECTIONS ===
Cliente --> lb : HTTPS
Estudiante --> lb : HTTPS
Empleado --> lb : HTTPS

lb --> nginx1 : Round Robin
lb --> nginx2 : Round Robin

nginx1 --> gun1
nginx2 --> gun2

django1 --> mysql_m : Write
django1 --> mysql_s1 : Read
django2 --> mysql_m : Write
django2 --> mysql_s2 : Read

django1 --> redis_m : Cache
django2 --> redis_m : Cache

django1 --> rabbitmq : Publish
cel1 --> rabbitmq : Consume
cel2 --> rabbitmq : Consume

cel1 --> mysql_m : Write
cel2 --> mysql_m : Write

django1 ..> prom : metrics
django2 ..> prom : metrics
django1 ..> sentry : errors
django2 ..> sentry : errors

note right of db
    **Database Specs**
    • CPU: 8 cores
    • RAM: 32 GB
    • Storage: 1 TB SSD
    • Backup: Diario 03:00 AM
end note

note right of api1
    **API Server Specs**
    • CPU: 4 cores
    • RAM: 8 GB
    • Gunicorn Workers: 8
    • Max Requests: 10,000
end note

@enduml
```

---

## 🎯 Diagrama de Actividad - Proceso de Cierre de Caja

```plantuml
@startuml Actividad_Cierre_Caja
!theme vibrant

|Cajero|
start
:Solicitar cierre de caja;

|Sistema|
:Calcular saldo sistema;
:Obtener movimientos del día;

|Cajero|
:Contar efectivo físico;
:Contar tarjetas de crédito;
:Contar transferencias;

|Sistema|
:Calcular saldo físico ingresado;

if (Saldo físico == Saldo sistema?) then (Sí)
    |Sistema|
    :Generar cierre automático;
    :Estado: APROBADO;
    
    |Sistema|
    fork
        :Generar reporte PDF;
    fork again
        :Enviar email a gerencia;
    fork again
        :Actualizar KPIs;
    end fork
    
else (No)
    |Sistema|
    :Calcular diferencia;
    
    if (Diferencia > $100.000?) then (Sí - CRÍTICO)
        |Sistema|
        :Estado: RECHAZADO;
        :Bloquear cierre;
        :Alertar a gerente;
        
        |Gerente|
        :Revisar diferencia;
        
        if (Aprobar con justificación?) then (Sí)
            :Ingresar justificación;
            
            |Sistema|
            :Estado: APROBADO_CON_DIFERENCIA;
            :Registrar auditoría;
        else (No)
            :Rechazar cierre;
            
            |Cajero|
            :Recontar caja;
            
            stop
        endif
        
    else (No - MENOR)
        |Cajero|
        :Justificar diferencia;
        
        |Sistema|
        :Estado: APROBADO_CON_DIFERENCIA;
        :Registrar justificación;
    endif
endif

|Sistema|
:Generar asiento contable;
:Cerrar caja;

|Cajero|
:Imprimir comprobante;

stop

@enduml
```

---

## 🔐 Diagrama de Actividad - Autenticación 2FA

```plantuml
@startuml Actividad_2FA
!theme cerulean

|Usuario|
start
:Ingresar usuario y contraseña;

|Sistema|
:Validar credenciales;

if (Credenciales válidas?) then (No)
    |Sistema|
    :Incrementar intentos fallidos;
    
    if (Intentos >= 5?) then (Sí)
        :Bloquear cuenta temporalmente;
        :Enviar alerta de seguridad;
        
        |Usuario|
        #Pink:Cuenta bloqueada;
        stop
    else (No)
        |Usuario|
        #Orange:Credenciales incorrectas;
        stop
    endif
    
else (Sí)
    |Sistema|
    :Verificar si requiere 2FA;
    
    if (Rol requiere 2FA?) then (Sí)
        |Sistema|
        :Generar código 6 dígitos;
        :Guardar código con TTL 5 min;
        
        fork
            :Enviar código por email;
        fork again
            :Enviar código por SMS;
        end fork
        
        |Usuario|
        :Ingresar código 2FA;
        
        |Sistema|
        if (Código válido y no expirado?) then (Sí)
            :Marcar código como usado;
        else (No)
            |Usuario|
            #Orange:Código inválido o expirado;
            stop
        endif
        
    else (No)
        ' Continuar sin 2FA
    endif
    
    |Sistema|
    :Generar JWT Token;
    :Registrar sesión;
    :Actualizar último acceso;
    :Registrar IP y dispositivo;
    
    if (IP desconocida?) then (Sí)
        :Enviar alerta de nuevo dispositivo;
    endif
    
    |Usuario|
    #LightGreen:Acceso concedido;
    :Redirigir a dashboard;
endif

stop

@enduml
```

---

## 📋 Cómo usar estos diagramas

### Ver en VS Code
1. Abrir este archivo `.md`
2. Presionar `Alt+D` para preview PlantUML
3. Click derecho → "Export Current Diagram" para generar imagen

### Exportar para documentación
```bash
# Los diagramas se exportan automáticamente a:
docs/diagramas/
```

### Integrar en Markdown
```markdown
![Diagrama de Clases](diagramas/Diagrama_Clases_Tarjetas.svg)
```

---

## 🎯 Cuándo usar PlantUML vs Mermaid

| Tipo de Diagrama | Mermaid ⭐ | PlantUML 🔧 |
|------------------|-----------|-------------|
| ERD básico | ✅ Mejor | ⚠️ Overkill |
| Clases con métodos | ❌ Limitado | ✅ Mejor |
| Secuencia simple | ✅ Mejor | ⚠️ Igual |
| Secuencia compleja | ⚠️ Limitado | ✅ Mejor |
| Casos de uso | ✅ Mejor | ⚠️ Verboso |
| Componentes | ⚠️ Básico | ✅ Mejor |
| Deployment | ⚠️ Básico | ✅ Mejor |
| Estados | ✅ Bueno | ✅ Mejor |
| Actividad | ❌ No tiene | ✅ Solo PlantUML |

**Recomendación**: Usa Mermaid para documentación versionada en Git, PlantUML para diagramas técnicos complejos.
