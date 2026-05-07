# DER Por Modulos (Sin Tablas Django)

Generado: 2026-03-06 21:09:24

Incluye todas las tablas detectadas por modulo en `backend/apps`.
Para cada tabla se listan campos PK y FK.

## Modulo: almuerzos

```mermaid
erDiagram
    SUSCRIPCIONESALMUERZO ||--o{ PAGOSALMUERZOMENSUAL : fk
    CUENTASALMUERZOMENSUAL ||--o{ PAGOSCUENTASALMUERZO : fk
    ALERGENOS ||--o{ PRODUCTOSALERGENOS : fk
    SUSCRIPCIONESALMUERZO ||--o{ REGISTROSCONSUMOALMUERZO : fk
    TIPOSALMUERZO ||--o{ REGISTROSCONSUMOALMUERZO : fk
    PLANESALMUERZO ||--o{ SUSCRIPCIONESALMUERZO : fk

    ALERGENOS {
        int id_alergeno PK
    }

    CUENTASALMUERZOMENSUAL {
        int id_cuenta PK
        int id_hijo FK
    }

    PAGOSALMUERZOMENSUAL {
        int id_pago_almuerzo PK
        int id_suscripcion FK
        int id_venta FK
    }

    PAGOSCUENTASALMUERZO {
        int id_pago PK
        int id_cuenta FK
        int id_empleado_registro FK
    }

    PLANESALMUERZO {
        int id_plan_almuerzo PK
    }

    PRODUCTOSALERGENOS {
        int id_producto_alergeno PK
        int id_alergeno FK
        int id_producto FK
    }

    REGISTROSCONSUMOALMUERZO {
        int id_registro_consumo PK
        int id_hijo FK
        int id_suscripcion FK
        int id_tipo_almuerzo FK
        int nro_tarjeta FK
        int id_empleado_registro FK
    }

    SUSCRIPCIONESALMUERZO {
        int id_suscripcion PK
        int id_hijo FK
        int id_plan_almuerzo FK
    }

    TIPOSALMUERZO {
        int id_tipo_almuerzo PK
    }

```

## Modulo: api_integrations

```mermaid
erDiagram
    PROVEEDORESAPI ||--o{ CREDENCIALESAPI : fk
    PROVEEDORESAPI ||--o{ ENDPOINTSAPI : fk
    ENDPOINTSAPI ||--o{ LOGSLLAMADASAPI : fk
    WEBHOOKENDPOINTS ||--o{ LOGSWEBHOOKS : fk
    PROVEEDORESAPI ||--o{ WEBHOOKENDPOINTS : fk

    CREDENCIALESAPI {
        int id_credencial PK
        int id_proveedor FK
    }

    ENDPOINTSAPI {
        int id_endpoint PK
        int id_proveedor FK
    }

    LOGSLLAMADASAPI {
        int id_log PK
        int id_endpoint FK
        int id_empleado FK
    }

    LOGSWEBHOOKS {
        int id_log PK
        int id_webhook FK
    }

    PROVEEDORESAPI {
        int id_proveedor PK
    }

    WEBHOOKENDPOINTS {
        int id_webhook PK
        int id_proveedor FK
    }

```

## Modulo: clientes

```mermaid
erDiagram
    CLIENTES ||--o{ AUTORIZACIONESSALDONEGATIVO : fk
    TIPOSCLIENTE ||--o{ CLIENTES : fk
    CLIENTES ||--o{ HIJOS : fk
    HIJOS ||--o{ HISTORIALGRADOSHIJOS : fk
    HIJOS ||--o{ RESTRICCIONESHIJOS : fk

    AUTORIZACIONESSALDONEGATIVO {
        int id_autorizacion PK
        int id_venta FK
        int id_cliente FK
        int id_empleado_autoriza FK
    }

    CLIENTES {
        int id_cliente PK
        int id_lista FK
        int id_tipo_cliente FK
    }

    GRADOS {
        int id_grado PK
    }

    HIJOS {
        int id_hijo PK
        int id_cliente_responsable FK
    }

    HISTORIALGRADOSHIJOS {
        int id_historial PK
        int id_hijo FK
    }

    LOGSAUTORIZACIONES {
        int id_log PK
        int id_tarjeta_autorizacion FK
    }

    RESTRICCIONESHIJOS {
        int id_restriccion PK
        int id_hijo FK
    }

    TIPOSCLIENTE {
        int id_tipo_cliente PK
    }

```

## Modulo: compras

```mermaid
erDiagram
    COMPRAS ||--o{ APLICACIONPAGOSCOMPRAS : fk
    PAGOSPROVEEDORES ||--o{ APLICACIONPAGOSCOMPRAS : fk
    PROVEEDORES ||--o{ COMPRAS : fk
    COMPRAS ||--o{ DETALLESCOMPRA : fk
    NOTASCREDITOPROVEEDOR ||--o{ DETALLESNOTACREDITOPROVEEDOR : fk
    COMPRAS ||--o{ NOTASCREDITOPROVEEDOR : fk
    PROVEEDORES ||--o{ NOTASCREDITOPROVEEDOR : fk

    APLICACIONPAGOSCOMPRAS {
        int id_aplicacion PK
        int id_compra FK
        int id_pago_proveedor FK
    }

    COMPRAS {
        int id_compra PK
        int id_proveedor FK
        int id_documento FK
    }

    DETALLESCOMPRA {
        int id_detalle PK
        int id_compra FK
        int id_producto FK
    }

    DETALLESNOTACREDITOPROVEEDOR {
        int id_detalle_nc_proveedor PK
        int id_nota_proveedor FK
        int id_producto FK
    }

    NOTASCREDITOPROVEEDOR {
        int id_nota_proveedor PK
        int id_compra_original FK
        int id_proveedor FK
    }

    PAGOSPROVEEDORES {
        int id_pago_proveedor PK
        int id_medio_pago FK
    }

    PROVEEDORES {
        int id_proveedor PK
    }

```

## Modulo: contabilidad

```mermaid
erDiagram
    TARIFASCOMISION ||--o{ AUDITORIACOMISIONES : fk
    CAJAS ||--o{ CIERRESCAJA : fk
    DOCUMENTOSTRIBUTARIOS ||--o{ DOCUMENTOIMPUESTOS : fk
    IMPUESTOS ||--o{ DOCUMENTOIMPUESTOS : fk
    TIMBRADOS ||--o{ DOCUMENTOSTRIBUTARIOS : fk
    CIERRESCAJA ||--o{ MOVIMIENTOSCAJA : fk
    PUNTOSEXPEDICION ||--o{ TIMBRADOS : fk

    AUDITORIACOMISIONES {
        int id_auditoria PK
        int id_empleado_modifico FK
        int id_tarifa FK
    }

    CAJAS {
        int id_caja PK
    }

    CIERRESCAJA {
        int id_cierre PK
        int id_caja FK
        int id_empleado FK
    }

    CONCILIACIONPAGOS {
        int id_conciliacion PK
        int id_pago_venta FK
    }

    DATOSEMPRESA {
        int id_empresa PK
    }

    DOCUMENTOIMPUESTOS {
        int id_documento PK
        int id_documento FK
        int id_impuesto FK
    }

    DOCUMENTOSTRIBUTARIOS {
        int id_documento PK
        int nro_timbrado FK
    }

    IMPUESTOS {
        int id_impuesto PK
    }

    MOVIMIENTOSCAJA {
        int id_movimiento PK
        int id_cierre FK
        int id_medio_pago FK
        int id_venta FK
    }

    PUNTOSEXPEDICION {
        int id_punto PK
    }

    TARIFASCOMISION {
        int id_tarifa PK
        int id_medio_pago FK
    }

    TIMBRADOS {
        int nro_timbrado PK
        int id_punto FK
    }

```

## Modulo: core

```mermaid
erDiagram
    TARJETAS ||--o{ CARGASSALDO : fk
    TARJETAS ||--o{ CONSUMOSTARJETA : fk
    TARJETAS ||--o{ TRANSACCIONESONLINE : fk

    CACHECONFIGURACION {
        int id_cache PK
    }

    CARGASSALDO {
        int id_carga PK
        int id_cliente_origen FK
        int nro_tarjeta FK
    }

    CONFIGURACIONSISTEMA {
        int id_config PK
        int updated_by FK
    }

    CONSUMOSTARJETA {
        int id_consumo PK
        int id_empleado_registro FK
        int nro_tarjeta FK
    }

    LIMITESTRANSACCION {
        int id_limite PK
        int id_rol FK
        int id_empleado_configurador FK
    }

    MEDIOSPAGO {
        int id_medio_pago PK
    }

    REGISTROAUTORIZACIONES {
        int id_autorizacion PK
        int id_empleado_solicitante FK
        int id_empleado_autorizador FK
        int id_empleado_autorizador_2 FK
        int id_venta FK
        int id_compra FK
        int id_ajuste FK
    }

    TARJETAS {
        int nro_tarjeta PK
        int id_hijo FK
    }

    TARJETASAUTORIZACION {
        int id_tarjeta_autorizacion PK
        int id_empleado FK
    }

    TRANSACCIONESONLINE {
        int id_transaccion PK
        int nro_tarjeta FK
        int id_usuario_portal FK
    }

```

## Modulo: inventario

```mermaid
erDiagram
    LOTESPRODUCTO ||--o{ ALERTASVENCIMIENTO : fk
    AJUSTESINVENTARIO ||--o{ DETALLESAJUSTE : fk
    MOVIMIENTOSSTOCK ||--o{ DETALLESAJUSTE : fk

    AJUSTESINVENTARIO {
        int id_ajuste PK
        int id_empleado_solicita FK
        int id_empleado_aprueba FK
    }

    ALERTASSTOCK {
        int id_alerta PK
        int id_producto FK
    }

    ALERTASVENCIMIENTO {
        int id_alerta PK
        int id_lote FK
        int id_empleado_responsable FK
    }

    COSTOSHISTORICOS {
        int id_costo_historico PK
        int id_compra FK
        int id_producto FK
    }

    DETALLESAJUSTE {
        int id_detalle PK
        int id_ajuste FK
        int id_movimiento_stock FK
        int id_producto FK
    }

    LOTESPRODUCTO {
        int id_lote PK
        int id_producto FK
        int id_compra FK
    }

    MOVIMIENTOSSTOCK {
        int id_movimiento_stock PK
        int id_compra FK
        int id_venta FK
        int id_empleado_autoriza FK
        int id_producto FK
    }

    STOCKUNICO {
        int id_stock PK
        int id_producto FK
    }

```

## Modulo: notificaciones

```mermaid
erDiagram
    ALERTASAUTOMATICAS ||--o{ ALERTADESTINATARIOS : fk
    PLANTILLASEMAIL ||--o{ CAMPANASCOMUNICACION : fk
    PLANTILLASSMS ||--o{ CAMPANASCOMUNICACION : fk
    PLANTILLASEMAIL ||--o{ EMAILSENVIADOS : fk
    ALERTASAUTOMATICAS ||--o{ HISTORIALALERTAS : fk
    PLANTILLASSMS ||--o{ SMSENVIADOS : fk

    ALERTADESTINATARIOS {
        int id_destinatario PK
        int id_alerta FK
        int id_empleado FK
    }

    ALERTASAUTOMATICAS {
        int id_alerta PK
    }

    ALERTASSISTEMA {
        int id_alerta PK
    }

    ANOMALIASDETECTADAS {
        int id_anomalia PK
    }

    CAMPANASCOMUNICACION {
        int id_campana PK
        int created_by FK
        int id_email_template FK
        int id_sms_template FK
    }

    EMAILSENVIADOS {
        int id_email PK
        int id_cliente FK
        int enviado_por FK
        int id_template FK
    }

    HISTORIALALERTAS {
        int id_historial PK
        int id_alerta FK
        int resuelto_por FK
    }

    NOTIFICACIONESPORTAL {
        int id_notificacion PK
        int id_usuario_portal FK
    }

    NOTIFICACIONESSALDO {
        int id_notificacion PK
        int nro_tarjeta FK
    }

    PLANTILLASEMAIL {
        int id_template PK
        int created_by FK
    }

    PLANTILLASSMS {
        int id_template PK
    }

    PREFERENCIASNOTIFICACION {
        int id_preferencia PK
        int id_usuario_portal FK
    }

    RESTRICCIONESHORARIAS {
        int id_restriccion PK
    }

    SMSENVIADOS {
        int id_sms PK
        int id_cliente FK
        int enviado_por FK
        int id_template FK
    }

    SOLICITUDESNOTIFICACION {
        int id_solicitud PK
        int id_cliente FK
        int nro_tarjeta FK
    }

```

## Modulo: productos

```mermaid
erDiagram
    PRODUCTOS ||--o{ HISTORICOPRECIOS : fk
    LISTASPRECIOS ||--o{ PRECIOSPORLISTA : fk
    PRODUCTOS ||--o{ PRECIOSPORLISTA : fk
    CATEGORIAS ||--o{ PRODUCTOS : fk
    UNIDADESMEDIDA ||--o{ PRODUCTOS : fk

    CATEGORIAS {
        int id_categoria PK
        int id_categoria_padre FK
    }

    HISTORICOPRECIOS {
        int id_historico PK
        int id_empleado FK
        int id_producto FK
    }

    LISTASPRECIOS {
        int id_lista PK
    }

    PRECIOSPORLISTA {
        int id_precio PK
        int id_lista FK
        int id_producto FK
    }

    PRODUCTOS {
        int id_producto PK
        int id_categoria FK
        int id_impuesto FK
        int id_unidad_medida FK
    }

    UNIDADESMEDIDA {
        int id_unidad_medida PK
    }

```

## Modulo: reportes

```mermaid
erDiagram
    PLANTILLASTAREA ||--o{ DESTINATARIOSTAREA : fk
    PLANTILLASTAREA ||--o{ EJECUCIONESTAREA : fk
    KPIMETRICAS ||--o{ VALORESKPI : fk

    DASHBOARDS {
        int id_dashboard PK
        int id_empleado FK
    }

    DESTINATARIOSTAREA {
        int id_destinatario PK
        int id_empleado FK
        int id_plantilla FK
    }

    EJECUCIONESTAREA {
        int id_ejecucion PK
        int ejecutado_por FK
        int id_plantilla FK
    }

    KPIMETRICAS {
        int id_kpi PK
    }

    PLANTILLASREPORTE {
        int id_template PK
        int created_by FK
    }

    PLANTILLASTAREA {
        int id_plantilla PK
        int created_by FK
    }

    VALORESKPI {
        int id_valor PK
        int id_kpi FK
    }

```

## Modulo: usuarios

```mermaid
erDiagram
    EMPLEADOS ||--o{ AUDITORIAEMPLEADOS : fk
    ROLES ||--o{ EMPLEADOS : fk
    EMPLEADOS ||--o{ PERFILESUSUARIO : fk
    ROLES ||--o{ ROLESPERMISOS : fk
    PERMISOS ||--o{ ROLESPERMISOS : fk
    EMPLEADOS ||--o{ ROLESPERMISOS : fk
    USUARIOSPORTAL ||--o{ TOKENSVERIFICACION : fk

    AUDITORIAEMPLEADOS {
        int id_auditoria PK
        int id_empleado FK
    }

    AUDITORIAOPERACIONES {
        int id_auditoria PK
    }

    AUDITORIAUSUARIOSWEB {
        int id_auditoria PK
        int id_cliente FK
    }

    AUTENTICACION2FA {
        int id_2fa PK
    }

    BLOQUEOSCUENTA {
        int id_bloqueo PK
    }

    EMPLEADOS {
        int id_empleado PK
        int id_rol FK
    }

    INTENTOS2FA {
        int id_intento PK
    }

    INTENTOSLOGIN {
        int id_intento PK
    }

    PATRONESACCESO {
        int id_patron PK
    }

    PERFILESUSUARIO {
        int id_perfil PK
        int id_empleado FK
    }

    PERMISOS {
        int id PK
    }

    RENOVACIONESSESION {
        int id_renovacion PK
    }

    ROLES {
        int id_rol PK
    }

    ROLESPERMISOS {
        int id PK
        int id_rol FK
        int id_permiso FK
        int asignado_por FK
    }

    SESIONESACTIVAS {
        int id_sesion PK
    }

    TOKENSRECUPERACION {
        int id_token PK
        int id_cliente FK
    }

    TOKENSVERIFICACION {
        int id_token PK
        int id_usuario_portal FK
    }

    USUARIOSPORTAL {
        int id_usuario_portal PK
        int id_cliente FK
    }

    USUARIOSWEBCLIENTES {
        int id_cliente PK
        int id_cliente FK
    }

```

## Modulo: ventas

```mermaid
erDiagram
    PAGOSVENTA ||--o{ APLICACIONPAGOSVENTAS : fk
    VENTAS ||--o{ APLICACIONPAGOSVENTAS : fk
    PROMOCIONES ||--o{ CATEGORIASPROMOCION : fk
    NOTASCREDITOCLIENTE ||--o{ DETALLESNOTACREDITO : fk
    VENTAS ||--o{ DETALLESVENTA : fk
    VENTAS ||--o{ NOTASCREDITOCLIENTE : fk
    VENTAS ||--o{ PAGOSVENTA : fk
    PROMOCIONES ||--o{ PRODUCTOSPROMOCION : fk
    PROMOCIONES ||--o{ PROMOCIONESAPLICADAS : fk
    VENTAS ||--o{ PROMOCIONESAPLICADAS : fk

    APLICACIONPAGOSVENTAS {
        int id_aplicacion PK
        int id_pago_venta FK
        int id_venta FK
    }

    CATEGORIASPROMOCION {
        int id_categoria_promocion PK
        int id_categoria FK
        int id_promocion FK
    }

    DETALLESNOTACREDITO {
        int id_detalle_nota PK
        int id_nota FK
        int id_producto FK
    }

    DETALLESVENTA {
        int id_detalle PK
        int id_producto FK
        int id_venta FK
    }

    NOTASCREDITOCLIENTE {
        int id_nota PK
        int id_cliente FK
        int id_empleado_autoriza FK
        int id_venta_origen FK
    }

    PAGOSVENTA {
        int id_pago_venta PK
        int id_medio_pago FK
        int nro_tarjeta_usada FK
        int id_venta FK
    }

    PRODUCTOSPROMOCION {
        int id_producto_promocion PK
        int id_producto FK
        int id_promocion FK
    }

    PROMOCIONES {
        int id_promocion PK
    }

    PROMOCIONESAPLICADAS {
        int id_aplicacion PK
        int id_promocion FK
        int id_venta FK
    }

    VENTAS {
        int id_venta PK
        int autorizado_por FK
        int id_cliente FK
        int id_empleado_cajero FK
        int id_hijo FK
        int id_medio_pago FK
        int id_documento FK
    }

```

