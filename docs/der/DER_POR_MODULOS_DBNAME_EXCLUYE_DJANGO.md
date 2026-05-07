# DER Por Modulos (db_table/db_column) - Sin Tablas Django

Generado: 2026-03-06 21:13:11

Incluye todas las tablas por modulo usando nombres reales de BD (`db_table`, `db_column`).
No incluye tablas internas de Django.

## Modulo: almuerzos

```mermaid
erDiagram
    suscripciones_almuerzo ||--o{ pagos_almuerzo_mensual : id_suscripcion
    cuentas_almuerzo_mensual ||--o{ pagos_cuentas_almuerzo : id_cuenta
    alergenos ||--o{ productos_alergenos : id_alergeno
    suscripciones_almuerzo ||--o{ registros_consumo_almuerzo : id_suscripcion
    tipos_almuerzo ||--o{ registros_consumo_almuerzo : id_tipo_almuerzo
    planes_almuerzo ||--o{ suscripciones_almuerzo : id_plan_almuerzo

    alergenos {
        int id_alergeno PK
    }

    cuentas_almuerzo_mensual {
        int id_cuenta PK
        int id_hijo FK
    }

    pagos_almuerzo_mensual {
        int id_pago_almuerzo PK
        int id_suscripcion FK
        int id_venta FK
    }

    pagos_cuentas_almuerzo {
        int id_pago PK
        int id_cuenta FK
        int id_empleado_registro FK
    }

    planes_almuerzo {
        int id_plan_almuerzo PK
    }

    productos_alergenos {
        int id_producto_alergeno PK
        int id_alergeno FK
        int id_producto FK
    }

    registros_consumo_almuerzo {
        int id_registro_consumo PK
        int id_hijo FK
        int id_suscripcion FK
        int id_tipo_almuerzo FK
        int nro_tarjeta FK
        int id_empleado_registro FK
    }

    suscripciones_almuerzo {
        int id_suscripcion PK
        int id_hijo FK
        int id_plan_almuerzo FK
    }

    tipos_almuerzo {
        int id_tipo_almuerzo PK
    }

```

## Modulo: api_integrations

```mermaid
erDiagram
    proveedores_api ||--o{ credenciales_api : id_proveedor
    proveedores_api ||--o{ endpoints_api : id_proveedor
    endpoints_api ||--o{ logs_llamadas_api : id_endpoint
    webhook_endpoints ||--o{ logs_webhooks : id_webhook
    proveedores_api ||--o{ webhook_endpoints : id_proveedor

    credenciales_api {
        int id_credencial PK
        int id_proveedor FK
    }

    endpoints_api {
        int id_endpoint PK
        int id_proveedor FK
    }

    logs_llamadas_api {
        int id_log PK
        int id_endpoint FK
        int id_empleado FK
    }

    logs_webhooks {
        int id_log PK
        int id_webhook FK
    }

    proveedores_api {
        int id_proveedor PK
    }

    webhook_endpoints {
        int id_webhook PK
        int id_proveedor FK
    }

```

## Modulo: clientes

```mermaid
erDiagram
    clientes ||--o{ autorizaciones_saldo_negativo : id_cliente
    tipos_cliente ||--o{ clientes : id_tipo_cliente
    clientes ||--o{ hijos : id_cliente_responsable
    hijos ||--o{ historial_grados_hijos : id_hijo
    hijos ||--o{ restricciones_hijos : id_hijo

    autorizaciones_saldo_negativo {
        int id_autorizacion PK
        int id_venta FK
        int id_cliente FK
        int id_empleado_autoriza FK
    }

    clientes {
        int id_cliente PK
        int id_lista FK
        int id_tipo_cliente FK
    }

    grados {
        int id_grado PK
    }

    hijos {
        int id_hijo PK
        int id_cliente_responsable FK
    }

    historial_grados_hijos {
        int id_historial PK
        int id_hijo FK
    }

    logs_autorizaciones {
        int id_log PK
        int id_tarjeta_autorizacion FK
    }

    restricciones_hijos {
        int id_restriccion PK
        int id_hijo FK
    }

    tipos_cliente {
        int id_tipo_cliente PK
    }

```

## Modulo: compras

```mermaid
erDiagram
    compras ||--o{ aplicacion_pagos_compras : id_compra
    pagos_proveedores ||--o{ aplicacion_pagos_compras : id_pago_proveedor
    proveedores ||--o{ compras : id_proveedor
    compras ||--o{ detalles_compra : id_compra
    notas_credito_proveedor ||--o{ detalles_nota_credito_proveedor : id_nota_proveedor
    compras ||--o{ notas_credito_proveedor : id_compra_original
    proveedores ||--o{ notas_credito_proveedor : id_proveedor

    aplicacion_pagos_compras {
        int id_aplicacion PK
        int id_compra FK
        int id_pago_proveedor FK
    }

    compras {
        int id_compra PK
        int id_proveedor FK
        int id_documento FK
    }

    detalles_compra {
        int id_detalle PK
        int id_compra FK
        int id_producto FK
    }

    detalles_nota_credito_proveedor {
        int id_detalle_nc_proveedor PK
        int id_nota_proveedor FK
        int id_producto FK
    }

    notas_credito_proveedor {
        int id_nota_proveedor PK
        int id_compra_original FK
        int id_proveedor FK
    }

    pagos_proveedores {
        int id_pago_proveedor PK
        int id_medio_pago FK
    }

    proveedores {
        int id_proveedor PK
    }

```

## Modulo: contabilidad

```mermaid
erDiagram
    tarifas_comision ||--o{ auditoria_comisiones : id_tarifa
    cajas ||--o{ cierres_caja : id_caja
    documentos_tributarios ||--o{ documento_impuestos : id_documento
    impuestos ||--o{ documento_impuestos : id_impuesto
    timbrados ||--o{ documentos_tributarios : nro_timbrado
    cierres_caja ||--o{ movimientos_caja : id_cierre
    puntos_expedicion ||--o{ timbrados : id_punto

    auditoria_comisiones {
        int id_auditoria PK
        int id_empleado_modifico FK
        int id_tarifa FK
    }

    cajas {
        int id_caja PK
    }

    cierres_caja {
        int id_cierre PK
        int id_caja FK
        int id_empleado FK
    }

    conciliacion_pagos {
        int id_conciliacion PK
        int id_pago_venta FK
    }

    datos_empresa {
        int id_empresa PK
    }

    documento_impuestos {
        int id_documento PK
        int id_documento FK
        int id_impuesto FK
    }

    documentos_tributarios {
        int id_documento PK
        int nro_timbrado FK
    }

    impuestos {
        int id_impuesto PK
    }

    movimientos_caja {
        int id_movimiento PK
        int id_cierre FK
        int id_medio_pago FK
        int id_venta FK
    }

    puntos_expedicion {
        int id_punto PK
    }

    tarifas_comision {
        int id_tarifa PK
        int id_medio_pago FK
    }

    timbrados {
        int nro_timbrado PK
        int id_punto FK
    }

```

## Modulo: core

```mermaid
erDiagram
    tarjetas ||--o{ cargas_saldo : nro_tarjeta
    tarjetas ||--o{ consumos_tarjeta : nro_tarjeta
    tarjetas ||--o{ transacciones_online : nro_tarjeta

    cache_configuracion {
        int id_cache PK
    }

    cargas_saldo {
        int id_carga PK
        int id_cliente_origen FK
        int nro_tarjeta FK
    }

    configuracion_sistema {
        int id_config PK
        int updated_by FK
    }

    consumos_tarjeta {
        int id_consumo PK
        int id_empleado_registro FK
        int nro_tarjeta FK
    }

    limites_transaccion {
        int id_limite PK
        int id_rol FK
        int id_empleado_configurador FK
    }

    medios_pago {
        int id_medio_pago PK
    }

    registro_autorizaciones {
        int id_autorizacion PK
        int id_empleado_solicitante FK
        int id_empleado_autorizador FK
        int id_empleado_autorizador_2 FK
        int id_venta FK
        int id_compra FK
        int id_ajuste FK
    }

    tarjetas {
        int nro_tarjeta PK
        int id_hijo FK
    }

    tarjetas_autorizacion {
        int id_tarjeta_autorizacion PK
        int id_empleado FK
    }

    transacciones_online {
        int id_transaccion PK
        int nro_tarjeta FK
        int id_usuario_portal FK
    }

```

## Modulo: inventario

```mermaid
erDiagram
    lotes_producto ||--o{ alertas_vencimiento : id_lote
    ajustes_inventario ||--o{ detalles_ajuste : id_ajuste
    movimientos_stock ||--o{ detalles_ajuste : id_movimiento_stock

    ajustes_inventario {
        int id_ajuste PK
        int id_empleado_solicita FK
        int id_empleado_aprueba FK
    }

    alertas_stock {
        int id_alerta PK
        int id_producto FK
    }

    alertas_vencimiento {
        int id_alerta PK
        int id_lote FK
        int id_empleado_responsable FK
    }

    costos_historicos {
        int id_costo_historico PK
        int id_compra FK
        int id_producto FK
    }

    detalles_ajuste {
        int id_detalle PK
        int id_ajuste FK
        int id_movimiento_stock FK
        int id_producto FK
    }

    lotes_producto {
        int id_lote PK
        int id_producto FK
        int id_compra FK
    }

    movimientos_stock {
        int id_movimiento_stock PK
        int id_compra FK
        int id_venta FK
        int id_empleado_autoriza FK
        int id_producto FK
    }

    stock_unico {
        int id_stock PK
        int id_producto FK
    }

```

## Modulo: notificaciones

```mermaid
erDiagram
    alertas_automaticas ||--o{ alerta_destinatarios : id_alerta
    plantillas_email ||--o{ campanas_comunicacion : id_email_template
    plantillas_sms ||--o{ campanas_comunicacion : id_sms_template
    plantillas_email ||--o{ emails_enviados : id_template
    alertas_automaticas ||--o{ historial_alertas : id_alerta
    plantillas_sms ||--o{ sms_enviados : id_template

    alerta_destinatarios {
        int id_destinatario PK
        int id_alerta FK
        int id_empleado FK
    }

    alertas_automaticas {
        int id_alerta PK
    }

    alertas_sistema {
        int id_alerta PK
    }

    anomalias_detectadas {
        int id_anomalia PK
    }

    campanas_comunicacion {
        int id_campana PK
        int created_by FK
        int id_email_template FK
        int id_sms_template FK
    }

    emails_enviados {
        int id_email PK
        int id_cliente FK
        int enviado_por FK
        int id_template FK
    }

    historial_alertas {
        int id_historial PK
        int id_alerta FK
        int resuelto_por FK
    }

    notificaciones_portal {
        int id_notificacion PK
        int id_usuario_portal FK
    }

    notificaciones_saldo {
        int id_notificacion PK
        int nro_tarjeta FK
    }

    plantillas_email {
        int id_template PK
        int created_by FK
    }

    plantillas_sms {
        int id_template PK
    }

    preferencias_notificacion {
        int id_preferencia PK
        int id_usuario_portal FK
    }

    restricciones_horarias {
        int id_restriccion PK
    }

    sms_enviados {
        int id_sms PK
        int id_cliente FK
        int enviado_por FK
        int id_template FK
    }

    solicitudes_notificacion {
        int id_solicitud PK
        int id_cliente FK
        int nro_tarjeta FK
    }

```

## Modulo: productos

```mermaid
erDiagram
    productos ||--o{ historico_precios : id_producto
    listas_precios ||--o{ precios_por_lista : id_lista
    productos ||--o{ precios_por_lista : id_producto
    categorias ||--o{ productos : id_categoria
    unidades_medida ||--o{ productos : id_unidad_medida

    categorias {
        int id_categoria PK
        int id_categoria_padre FK
    }

    historico_precios {
        int id_historico PK
        int id_empleado FK
        int id_producto FK
    }

    listas_precios {
        int id_lista PK
    }

    precios_por_lista {
        int id_precio PK
        int id_lista FK
        int id_producto FK
    }

    productos {
        int id_producto PK
        int id_categoria FK
        int id_impuesto FK
        int id_unidad_medida FK
    }

    unidades_medida {
        int id_unidad_medida PK
    }

```

## Modulo: reportes

```mermaid
erDiagram
    plantillas_tarea ||--o{ destinatarios_tarea : id_plantilla
    plantillas_tarea ||--o{ ejecuciones_tarea : id_plantilla
    kpi_metricas ||--o{ valores_kpi : id_kpi

    dashboards {
        int id_dashboard PK
        int id_empleado FK
    }

    destinatarios_tarea {
        int id_destinatario PK
        int id_empleado FK
        int id_plantilla FK
    }

    ejecuciones_tarea {
        int id_ejecucion PK
        int ejecutado_por FK
        int id_plantilla FK
    }

    kpi_metricas {
        int id_kpi PK
    }

    plantillas_reporte {
        int id_template PK
        int created_by FK
    }

    plantillas_tarea {
        int id_plantilla PK
        int created_by FK
    }

    valores_kpi {
        int id_valor PK
        int id_kpi FK
    }

```

## Modulo: usuarios

```mermaid
erDiagram
    empleados ||--o{ auditoria_empleados : id_empleado
    roles ||--o{ empleados : id_rol
    empleados ||--o{ perfiles_usuario : id_empleado
    roles ||--o{ roles_permisos : id_rol
    permisos ||--o{ roles_permisos : id_permiso
    empleados ||--o{ roles_permisos : asignado_por
    usuarios_portal ||--o{ tokens_verificacion : id_usuario_portal

    auditoria_empleados {
        int id_auditoria PK
        int id_empleado FK
    }

    auditoria_operaciones {
        int id_auditoria PK
    }

    auditoria_usuarios_web {
        int id_auditoria PK
        int id_cliente FK
    }

    autenticacion_2fa {
        int id_2fa PK
    }

    bloqueos_cuenta {
        int id_bloqueo PK
    }

    empleados {
        int id_empleado PK
        int id_rol FK
    }

    intentos_2fa {
        int id_intento PK
    }

    intentos_login {
        int id_intento PK
    }

    patrones_acceso {
        int id_patron PK
    }

    perfiles_usuario {
        int id_perfil PK
        int id_empleado FK
    }

    permisos {
        int id PK
    }

    renovaciones_sesion {
        int id_renovacion PK
    }

    roles {
        int id_rol PK
    }

    roles_permisos {
        int id PK
        int id_rol FK
        int id_permiso FK
        int asignado_por FK
    }

    sesiones_activas {
        int id_sesion PK
    }

    tokens_recuperacion {
        int id_token PK
        int id_cliente FK
    }

    tokens_verificacion {
        int id_token PK
        int id_usuario_portal FK
    }

    usuarios_portal {
        int id_usuario_portal PK
        int id_cliente FK
    }

    usuarios_web_clientes {
        int id_cliente PK
        int id_cliente FK
    }

```

## Modulo: ventas

```mermaid
erDiagram
    pagos_venta ||--o{ aplicacion_pagos_ventas : id_pago_venta
    ventas ||--o{ aplicacion_pagos_ventas : id_venta
    promociones ||--o{ categorias_promocion : id_promocion
    notas_credito_cliente ||--o{ detalles_nota_credito : id_nota
    ventas ||--o{ detalles_venta : id_venta
    ventas ||--o{ notas_credito_cliente : id_venta_origen
    ventas ||--o{ pagos_venta : id_venta
    promociones ||--o{ productos_promocion : id_promocion
    promociones ||--o{ promociones_aplicadas : id_promocion
    ventas ||--o{ promociones_aplicadas : id_venta

    aplicacion_pagos_ventas {
        int id_aplicacion PK
        int id_pago_venta FK
        int id_venta FK
    }

    categorias_promocion {
        int id_categoria_promocion PK
        int id_categoria FK
        int id_promocion FK
    }

    detalles_nota_credito {
        int id_detalle_nota PK
        int id_nota FK
        int id_producto FK
    }

    detalles_venta {
        int id_detalle PK
        int id_producto FK
        int id_venta FK
    }

    notas_credito_cliente {
        int id_nota PK
        int id_cliente FK
        int id_empleado_autoriza FK
        int id_venta_origen FK
    }

    pagos_venta {
        int id_pago_venta PK
        int id_medio_pago FK
        int nro_tarjeta_usada FK
        int id_venta FK
    }

    productos_promocion {
        int id_producto_promocion PK
        int id_producto FK
        int id_promocion FK
    }

    promociones {
        int id_promocion PK
    }

    promociones_aplicadas {
        int id_aplicacion PK
        int id_promocion FK
        int id_venta FK
    }

    ventas {
        int id_venta PK
        int autorizado_por FK
        int id_cliente FK
        int id_empleado_cajero FK
        int id_hijo FK
        int id_medio_pago FK
        int id_documento FK
    }

```

