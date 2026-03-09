# DER Consolidado (Sin Tablas Django)

Generado: 2026-03-06 21:00:54

Este diagrama consolida entidades y relaciones de negocio en un solo erDiagram.
Se excluyen tablas internas de Django (`auth_*`, `django_*`, `contenttypes_*`, `sessions_*`).

```mermaid
erDiagram
    CLIENTES ||--o{ TARJETAS : posee
    HIJOS ||--o{ TARJETAS : usa
    TARJETAS ||--o{ CARGAS_SALDO : recibe
    TARJETAS ||--o{ CONSUMOS_TARJETA : genera
    MEDIOS_PAGO ||--o{ CARGAS_SALDO : acepta
    MEDIOS_PAGO ||--o{ CONSUMOS_TARJETA : procesa
    ROLES ||--o{ LIMITES_TRANSACCION : define
    TARJETAS ||--o{ TRANSACCIONES_ONLINE : procesa
    EMPLEADOS ||--o{ REGISTRO_AUTORIZACIONES : aprueba
    CLIENTES ||--o{ HIJOS : tiene
    HIJOS ||--o{ RESTRICCIONES_HIJOS : tiene
    HIJOS ||--o{ HISTORIAL_GRADOS : cursÃ³
    CLIENTES ||--o{ AUTORIZACIONES_SALDO_NEGATIVO : autoriza
    CATEGORIAS ||--o{ CATEGORIAS : subcategoria_de
    CATEGORIAS ||--o{ PRODUCTOS : agrupa
    PRODUCTOS }o--|| UNIDADES_MEDIDA : mide_en
    PRODUCTOS ||--o{ LISTAS_PRECIOS : define
    PRODUCTOS ||--o{ HISTORIAL_PRECIOS : registra
    PRODUCTOS ||--|| STOCK_UNICO : tiene
    PRODUCTOS ||--o{ MOVIMIENTOS_STOCK : mueve
    PRODUCTOS ||--o{ LOTES_PRODUCTO : agrupa
    STOCK_UNICO ||--o{ ALERTAS_STOCK : genera
    LOTES_PRODUCTO ||--o{ ALERTAS_VENCIMIENTO : alerta
    MOVIMIENTOS_STOCK ||--o{ COSTOS_HISTORICOS : calcula
    VENTAS ||--o{ DETALLES_VENTA : contiene
    VENTAS }o--|| CLIENTES : realiza
    VENTAS ||--o{ DOCUMENTOS_TRIBUTARIOS : genera
    DETALLES_VENTA }o--|| PRODUCTOS : vende
    DETALLES_VENTA }o--o| PROMOCIONES : aplica
    PROMOCIONES ||--o{ DETALLES_PROMOCION : define
    PLANES_ALMUERZO ||--o{ SUSCRIPCIONES_ALMUERZO : ofrece
    SUSCRIPCIONES_ALMUERZO }o--|| HIJOS : para
    SUSCRIPCIONES_ALMUERZO ||--o{ REGISTROS_CONSUMO_ALMUERZO : usa
    SUSCRIPCIONES_ALMUERZO ||--o{ CUENTAS_ALMUERZO_MENSUAL : genera
    MENUS_DIARIOS ||--o{ ITEMS_MENU : incluye
    REGISTROS_CONSUMO_ALMUERZO }o--|| MENUS_DIARIOS : consume
    PROVEEDORES ||--o{ ORDENES_COMPRA : recibe
    ORDENES_COMPRA ||--o{ DETALLES_COMPRA : contiene
    ORDENES_COMPRA ||--o{ PAGOS_PROVEEDOR : paga
    DETALLES_COMPRA }o--|| PRODUCTOS : compra
    PAGOS_PROVEEDOR ||--o{ APLICACION_PAGOS : aplica
    CAJAS ||--o{ MOVIMIENTOS_CAJA : registra
    CAJAS ||--o{ CIERRES_CAJA : cierra
    MOVIMIENTOS_CAJA ||--o{ DETALLES_MOVIMIENTO : desglosa
    CIERRES_CAJA ||--o{ DIFERENCIAS_CIERRE : detecta
    EMPRESAS ||--o{ TIMBRADOS : tiene
    PLAN_CUENTAS ||--o{ PLAN_CUENTAS : subcuenta
    ASIENTOS_CONTABLES ||--o{ DETALLES_ASIENTO : contiene
    DETALLES_ASIENTO }o--|| PLAN_CUENTAS : afecta
    EMPLEADOS }o--|| ROLES : tiene
    ROLES ||--o{ PERMISOS_ROL : posee
    PERMISOS_ROL }o--|| PERMISOS : asigna
    EMPLEADOS ||--|| PERFILES_USUARIO : configura
    EMPLEADOS ||--o{ SESIONES_USUARIO : inicia
    EMPLEADOS ||--o{ AUTENTICACION_2FA : usa
    EMPLEADOS ||--o{ INTENTOS_LOGIN : intenta
    EMPLEADOS ||--o{ HISTORIAL_ACCESO : accede
    EMPLEADOS ||--o{ EVENTOS_AUDITORIA : genera
    EMPLEADOS ||--o{ ALERTAS_SEGURIDAD : recibe
    PLANTILLAS_REPORTE ||--o{ REPORTES_GENERADOS : genera
    PLANTILLAS_REPORTE ||--o{ SUSCRIPCIONES_REPORTE : programa
    DASHBOARDS ||--o{ WIDGETS_DASHBOARD : contiene
    WIDGETS_DASHBOARD }o--|| KPIS : muestra
    TAREAS_PROGRAMADAS ||--o{ EJECUCIONES_TAREA : ejecuta
    PLANTILLAS_NOTIFICACION ||--o{ NOTIFICACIONES_EMAIL : genera
    PLANTILLAS_NOTIFICACION ||--o{ NOTIFICACIONES_SMS : genera
    CAMPANAS ||--o{ NOTIFICACIONES_EMAIL : envia
    ALERTAS_AUTOMATICAS ||--o{ HISTORIAL_ALERTAS : dispara
    PROVEEDORES_API ||--o{ ENDPOINTS_API : expone
    PROVEEDORES_API ||--o{ CREDENCIALES_API : usa
    ENDPOINTS_API ||--o{ LOGS_LLAMADAS_API : registra
    PROVEEDORES_API ||--o{ SINCRONIZACIONES : configura
    SINCRONIZACIONES ||--o{ LOGS_SINCRONIZACION : ejecuta

    TARJETAS {
        int id_tarjeta PK
        varchar numero_tarjeta UK
        int id_cliente FK
        int id_hijo FK
        decimal saldo_actual
        decimal limite_credito
        boolean bloqueada
        datetime fecha_emision
        varchar estado
    }

    CARGAS_SALDO {
        int id_carga PK
        int id_tarjeta FK
        int id_medio_pago FK
        decimal monto
        decimal comision
        varchar tipo_carga
        datetime fecha_carga
        int id_empleado FK
        varchar estado
    }

    CONSUMOS_TARJETA {
        int id_consumo PK
        int id_tarjeta FK
        int id_medio_pago FK
        decimal monto
        datetime fecha_consumo
        varchar tipo_consumo
        int id_venta FK
        decimal saldo_anterior
        decimal saldo_nuevo
    }

    MEDIOS_PAGO {
        int id_medio PK
        varchar nombre UK
        varchar tipo
        decimal comision_porcentaje
        decimal comision_fija
        boolean activo
    }

    TARJETAS_AUTORIZACION {
        int id_tarjeta_aut PK
        varchar codigo UK
        varchar tipo_autorizacion
        boolean activo
        datetime fecha_expiracion
        int usos_maximos
        decimal monto_maximo
        json condiciones
    }

    LIMITES_TRANSACCION {
        int id_limite PK
        int id_rol FK
        varchar tipo_operacion
        decimal monto_minimo
        decimal monto_maximo
        boolean requiere_autorizacion
        int nivel_autorizacion
    }

    REGISTRO_AUTORIZACIONES {
        int id_autorizacion PK
        varchar tipo_operacion
        int id_operacion
        int id_solicitante FK
        int id_autorizador FK
        decimal monto_operacion
        varchar estado
        datetime fecha_solicitud
        text observaciones
    }

    TRANSACCIONES_ONLINE {
        int id_transaccion PK
        int id_tarjeta FK
        int id_medio_pago FK
        decimal monto
        datetime fecha_transaccion
        varchar estado_pago
        varchar referencia_pago
        varchar gateway
    }

    CLIENTES {
        int id_cliente PK
        varchar nombre
        varchar apellido
        varchar documento UK
        varchar telefono
        varchar email
        decimal limite_credito
        decimal cuenta_corriente
        boolean activo
        datetime fecha_registro
    }

    HIJOS {
        int id_hijo PK
        int id_cliente FK
        varchar nombre
        varchar apellido
        date fecha_nacimiento
        varchar documento UK
        varchar grado_actual
        varchar seccion
        boolean activo
    }

    RESTRICCIONES_HIJOS {
        int id_restriccion PK
        int id_hijo FK
        varchar tipo_restriccion
        varchar alergeno
        varchar nivel_severidad
        date fecha_inicio
        date fecha_fin
        boolean activo
    }

    HISTORIAL_GRADOS {
        int id_historial PK
        int id_hijo FK
        varchar grado
        int anio
        date fecha_inicio
        date fecha_fin
    }

    AUTORIZACIONES_SALDO_NEGATIVO {
        int id_autorizacion PK
        int id_cliente FK
        decimal saldo_negativo_autorizado
        decimal monto_maximo
        date fecha_autorizacion
        date fecha_vencimiento
        boolean activo
    }

    CATEGORIAS {
        int id_categoria PK
        varchar nombre UK
        int id_categoria_padre FK
        boolean activo
        int orden
    }

    PRODUCTOS {
        int id_producto PK
        varchar codigo_barra UK
        varchar nombre
        int id_categoria FK
        int id_unidad FK
        decimal costo_actual
        decimal precio_venta
        boolean activo
    }

    UNIDADES_MEDIDA {
        int id_unidad PK
        varchar nombre UK
        varchar simbolo
        varchar tipo
    }

    LISTAS_PRECIOS {
        int id_lista_precio PK
        int id_producto FK
        varchar tipo_cliente
        decimal precio
        date fecha_vigencia_desde
        boolean activo
    }

    HISTORIAL_PRECIOS {
        int id_historial PK
        int id_producto FK
        decimal precio_anterior
        decimal precio_nuevo
        varchar motivo
        datetime fecha_cambio
    }

    STOCK_UNICO {
        int id_stock PK
        int id_producto FK
        decimal cantidad_actual
        decimal cantidad_reservada
        decimal costo_promedio
        decimal valor_total_stock
        datetime fecha_ultimo_movimiento
    }

    MOVIMIENTOS_STOCK {
        int id_movimiento PK
        int id_producto FK
        varchar tipo_movimiento
        decimal cantidad
        decimal costo_unitario
        int id_empleado FK
        datetime fecha_movimiento
    }

    LOTES_PRODUCTO {
        int id_lote PK
        int id_producto FK
        varchar numero_lote UK
        decimal cantidad_actual
        decimal costo_unitario
        date fecha_vencimiento
        boolean activo
    }

    ALERTAS_STOCK {
        int id_alerta PK
        int id_stock FK
        varchar tipo_alerta
        varchar nivel_urgencia
        boolean resuelta
        datetime fecha_alerta
    }

    ALERTAS_VENCIMIENTO {
        int id_alerta PK
        int id_lote FK
        int dias_para_vencimiento
        boolean notificada
        datetime fecha_alerta
    }

    COSTOS_HISTORICOS {
        int id_costo PK
        int id_producto FK
        decimal costo_anterior
        decimal costo_nuevo
        datetime fecha_calculo
    }

    VENTAS {
        int id_venta PK
        varchar numero_factura UK
        int id_cliente FK
        int id_empleado FK
        datetime fecha_venta
        decimal subtotal
        decimal iva
        decimal total
        varchar estado
        boolean anulada
    }

    DETALLES_VENTA {
        int id_detalle PK
        int id_venta FK
        int id_producto FK
        decimal cantidad
        decimal precio_unitario
        decimal descuento_monto
        decimal total
    }

    DOCUMENTOS_TRIBUTARIOS {
        int id_documento PK
        int id_venta FK
        varchar tipo_documento
        varchar numero_documento UK
        varchar timbrado
        datetime fecha_emision
        decimal total
        varchar estado
    }

    PROMOCIONES {
        int id_promocion PK
        varchar codigo UK
        varchar nombre
        decimal descuento_porcentaje
        date fecha_inicio
        date fecha_fin
        boolean activo
    }

    DETALLES_PROMOCION {
        int id_detalle_promocion PK
        int id_promocion FK
        int id_producto FK
        int id_categoria FK
        decimal valor_aplicacion
    }

    PLANES_ALMUERZO {
        int id_plan PK
        varchar nombre UK
        decimal precio_mensual
        int dias_incluidos
        decimal precio_dia_extra
        boolean activo
    }

    SUSCRIPCIONES_ALMUERZO {
        int id_suscripcion PK
        int id_hijo FK
        int id_plan FK
        date fecha_inicio
        varchar estado
        int dias_consumidos
        boolean activo
    }

    MENUS_DIARIOS {
        int id_menu PK
        date fecha UK
        varchar nombre
        decimal precio
        int capacidad_maxima
        boolean activo
    }

    ITEMS_MENU {
        int id_item PK
        int id_menu FK
        varchar tipo_item
        varchar nombre
        boolean contiene_alergenos
    }

    REGISTROS_CONSUMO_ALMUERZO {
        int id_consumo PK
        int id_suscripcion FK
        int id_menu FK
        date fecha_consumo
        boolean confirmado
        boolean fue_extra
    }

    CUENTAS_ALMUERZO_MENSUAL {
        int id_cuenta PK
        int id_suscripcion FK
        int mes
        int anio
        int dias_extras
        decimal total
        varchar estado_pago
    }

    PROVEEDORES {
        int id_proveedor PK
        varchar razon_social
        varchar ruc UK
        varchar telefono
        int dias_credito
        decimal limite_credito
        boolean activo
    }

    ORDENES_COMPRA {
        int id_compra PK
        varchar numero_orden UK
        int id_proveedor FK
        datetime fecha_orden
        decimal total
        varchar estado
        varchar estado_pago
        boolean aprobada
    }

    DETALLES_COMPRA {
        int id_detalle PK
        int id_compra FK
        int id_producto FK
        decimal cantidad
        decimal costo_unitario
        decimal total
    }

    PAGOS_PROVEEDOR {
        int id_pago PK
        varchar numero_pago UK
        int id_proveedor FK
        decimal monto_total
        datetime fecha_pago
        varchar estado
    }

    APLICACION_PAGOS {
        int id_aplicacion PK
        int id_pago FK
        int id_compra FK
        decimal monto_aplicado
    }

    CAJAS {
        int id_caja PK
        varchar nombre UK
        decimal saldo_inicial
        decimal saldo_actual
        varchar estado
        int id_empleado_responsable FK
        boolean activa
    }

    MOVIMIENTOS_CAJA {
        int id_movimiento PK
        int id_caja FK
        varchar tipo_movimiento
        decimal monto
        int id_empleado FK
        datetime fecha_movimiento
        decimal saldo_anterior
        decimal saldo_nuevo
    }

    DETALLES_MOVIMIENTO {
        int id_detalle PK
        int id_movimiento FK
        varchar tipo_denominacion
        int cantidad
        decimal valor_unitario
        decimal subtotal
    }

    CIERRES_CAJA {
        int id_cierre PK
        int id_caja FK
        datetime fecha_cierre
        decimal saldo_sistema
        decimal saldo_fisico
        decimal diferencia
        boolean aprobado
    }

    DIFERENCIAS_CIERRE {
        int id_diferencia PK
        int id_cierre FK
        int id_medio_pago FK
        decimal diferencia
        text justificacion
    }

    EMPRESAS {
        int id_empresa PK
        varchar razon_social
        varchar ruc UK
        varchar direccion
        varchar logo_url
        boolean activa
    }

    TIMBRADOS {
        int id_timbrado PK
        int id_empresa FK
        varchar numero_timbrado UK
        varchar tipo_documento
        int numero_actual
        date fecha_vencimiento
        boolean activo
    }

    PLAN_CUENTAS {
        int id_cuenta PK
        varchar codigo UK
        varchar nombre
        int id_cuenta_padre FK
        varchar tipo_cuenta
        varchar naturaleza
        boolean acepta_movimiento
    }

    ASIENTOS_CONTABLES {
        int id_asiento PK
        varchar numero_asiento UK
        date fecha_asiento
        decimal total_debe
        decimal total_haber
        boolean balanceado
        varchar estado
    }

    DETALLES_ASIENTO {
        int id_detalle PK
        int id_asiento FK
        int id_cuenta FK
        varchar tipo_movimiento
        decimal monto
        text concepto
    }

    EMPLEADOS {
        int id_empleado PK
        varchar usuario UK
        varchar contrasena_hash
        varchar nombre
        varchar email
        int id_rol FK
        boolean activo
    }

    ROLES {
        int id_rol PK
        varchar nombre_rol UK
        text descripcion
        int nivel_jerarquia
        boolean activo
    }

    PERMISOS {
        int id_permiso PK
        varchar codigo UK
        varchar nombre
        varchar modulo
        varchar accion
    }

    PERMISOS_ROL {
        int id_permiso_rol PK
        int id_rol FK
        int id_permiso FK
        boolean puede_crear
        boolean puede_leer
        boolean puede_actualizar
        boolean puede_eliminar
    }

    PERFILES_USUARIO {
        int id_perfil PK
        int id_empleado FK
        varchar tema
        varchar idioma
        json dashboard_config
    }

    SESIONES_USUARIO {
        int id_sesion PK
        int id_empleado FK
        varchar session_key UK
        varchar ip_address
        datetime fecha_inicio
        boolean activo
    }

    AUTENTICACION_2FA {
        int id_2fa PK
        varchar usuario
        varchar secret_key
        boolean habilitado
    }

    INTENTOS_LOGIN {
        int id_intento PK
        varchar usuario
        varchar ip_address
        datetime fecha_intento
        boolean exitoso
        varchar motivo_fallo
        int intentos_consecutivos
    }

    HISTORIAL_ACCESO {
        int id_acceso PK
        int id_empleado FK
        varchar recurso
        varchar accion
        varchar ip_address
        datetime fecha_acceso
        boolean exitoso
    }

    EVENTOS_AUDITORIA {
        int id_evento PK
        int id_empleado FK
        varchar tipo_evento
        varchar entidad_afectada
        int id_registro
        json datos_anteriores
        json datos_nuevos
        datetime fecha_evento
    }

    ALERTAS_SEGURIDAD {
        int id_alerta PK
        int id_empleado FK
        varchar tipo_alerta
        varchar nivel_severidad
        boolean revisada
        datetime fecha_alerta
    }

    PATRONES_ACCESO {
        int id_patron PK
        int id_empleado FK
        time hora_inicio_habitual
        json dias_laborales
        json ips_habituales
    }

    PLANTILLAS_REPORTE {
        int id_plantilla PK
        varchar nombre UK
        text query_sql
        varchar formato_salida
        boolean activa
    }

    REPORTES_GENERADOS {
        int id_reporte PK
        int id_plantilla FK
        int id_empleado FK
        datetime fecha_generacion
        int registros_procesados
        varchar estado
    }

    SUSCRIPCIONES_REPORTE {
        int id_suscripcion PK
        int id_plantilla FK
        int id_empleado FK
        varchar frecuencia
        boolean activa
    }

    DASHBOARDS {
        int id_dashboard PK
        varchar nombre UK
        boolean publico
        json layout_config
    }

    WIDGETS_DASHBOARD {
        int id_widget PK
        int id_dashboard FK
        int id_kpi FK
        varchar tipo_widget
        int posicion_x
        int posicion_y
    }

    KPIS {
        int id_kpi PK
        varchar nombre UK
        text formula
        decimal valor_actual
        datetime fecha_calculo
    }

    TAREAS_PROGRAMADAS {
        int id_tarea PK
        varchar nombre UK
        varchar expresion_cron
        datetime proxima_ejecucion
        boolean activo
    }

    EJECUCIONES_TAREA {
        int id_ejecucion PK
        int id_tarea FK
        datetime fecha_inicio
        varchar estado
    }

    PLANTILLAS_NOTIFICACION {
        int id_plantilla PK
        varchar nombre UK
        varchar canal
        varchar asunto
        text contenido
        boolean activa
    }

    NOTIFICACIONES_EMAIL {
        int id_email PK
        int id_plantilla FK
        varchar destinatario_email
        varchar asunto
        datetime fecha_envio
        varchar estado
    }

    NOTIFICACIONES_SMS {
        int id_sms PK
        int id_plantilla FK
        varchar numero_telefono
        text mensaje
        datetime fecha_envio
        varchar estado
        decimal costo
    }

    CAMPANAS {
        int id_campana PK
        varchar nombre UK
        datetime fecha_inicio
        int total_destinatarios
        int enviados
        varchar estado
    }

    ALERTAS_AUTOMATICAS {
        int id_alerta PK
        varchar nombre UK
        varchar tipo_alerta
        json condiciones_trigger
        boolean activo
    }

    HISTORIAL_ALERTAS {
        int id_historial PK
        int id_alerta_config FK
        datetime fecha_disparo
        boolean enviada
    }

    ANOMALIAS_DETECTADAS {
        int id_anomalia PK
        varchar tipo_anomalia
        varchar entidad_afectada
        decimal valor_esperado
        decimal valor_detectado
        datetime fecha_deteccion
    }

    PROVEEDORES_API {
        int id_proveedor_api PK
        varchar nombre UK
        varchar url_base
        varchar tipo_autenticacion
        boolean activo
    }

    ENDPOINTS_API {
        int id_endpoint PK
        int id_proveedor_api FK
        varchar codigo UK
        varchar ruta
        varchar metodo_http
        json schema_request
        json schema_response
    }

    CREDENCIALES_API {
        int id_credencial PK
        int id_proveedor_api FK
        varchar ambiente
        varchar api_key
        varchar access_token
        datetime token_expiracion
    }

    LOGS_LLAMADAS_API {
        int id_log PK
        int id_endpoint FK
        int codigo_estado_http
        int tiempo_respuesta_ms
        boolean exitoso
        datetime fecha_llamada
    }

    SINCRONIZACIONES {
        int id_sincronizacion PK
        varchar nombre UK
        int id_proveedor_api FK
        varchar entidad_local
        varchar frecuencia_cron
        boolean activo
    }

    LOGS_SINCRONIZACION {
        int id_log_sync PK
        int id_sincronizacion FK
        int registros_procesados
        int registros_exitosos
        varchar estado
    }

```

Fuente: `cantina_tita/docs/DIAGRAMAS_ARQUITECTURA_CARTA.md`
