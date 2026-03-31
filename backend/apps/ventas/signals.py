"""
Signals para el módulo de ventas
Automatización de actualización de saldos y aplicación de notas de crédito
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from decimal import Decimal

from .models import AplicacionPagosVentas, NotasCreditoCliente, Ventas


@receiver(post_save, sender=AplicacionPagosVentas)
def actualizar_saldo_venta(sender, instance, created, **kwargs):
    """
    Actualiza el saldo_pendiente de la venta cuando se registra un pago.

    Reglas:
    - Reduce saldo_pendiente por el monto aplicado
    - Si saldo llega a 0 → estado_pago = 'Pagada'
    - Si saldo > 0 y < monto_total → estado_pago = 'Parcial'
    - Usa transaction.atomic() para garantizar consistencia

    Ejemplo:
        Venta de Gs. 100,000 con 3 pagos:
        - Pago 1: 40,000 → saldo_pendiente = 60,000 (Parcial)
        - Pago 2: 30,000 → saldo_pendiente = 30,000 (Parcial)
        - Pago 3: 30,000 → saldo_pendiente = 0 (Pagada)
    """
    if not created:  # pragma: no cover
        return

    with transaction.atomic():
        venta = instance.id_venta
        venta.saldo_pendiente = venta.saldo_pendiente - instance.monto_aplicado

        # Prevenir saldo negativo por error
        if venta.saldo_pendiente < 0:  # pragma: no cover
            venta.saldo_pendiente = Decimal("0.00")

        # Actualizar estado de pago
        if venta.saldo_pendiente == 0:
            venta.estado_pago = "Pagada"
        elif venta.saldo_pendiente < venta.monto_total:
            venta.estado_pago = "Parcial"
        else:
            venta.estado_pago = "Pendiente"

        venta.save(update_fields=["saldo_pendiente", "estado_pago"])


@receiver(post_save, sender=NotasCreditoCliente)
def aplicar_nota_credito_cliente(sender, instance, created, **kwargs):
    """
    Aplica la nota de crédito a la venta origen cuando cambia a estado 'Aplicada'.

    Reglas:
    - Si estado = 'Aplicada' y tiene venta origen → reduce saldo_pendiente
    - Si nota > saldo_pendiente → ajusta saldo a 0 (el excedente queda como crédito)
    - Actualiza estado_pago de la venta según saldo resultante

    Ejemplo:
        Venta: monto_total = 150,000, saldo_pendiente = 100,000
        Nota de crédito: 40,000
        Resultado: saldo_pendiente = 60,000, estado_pago = 'Parcial'
    """
    # Solo procesar si está en estado 'Aplicada' y tiene venta origen
    if instance.estado != "Aplicada" or not instance.id_venta_origen:
        return

    with transaction.atomic():
        venta = instance.id_venta_origen

        # Reducir saldo pendiente
        venta.saldo_pendiente = venta.saldo_pendiente - instance.monto_total

        # Si la nota es mayor al saldo, ajustar a 0
        # (el excedente se maneja en un modelo de saldos a favor - futura implementación)
        if venta.saldo_pendiente < 0:
            venta.saldo_pendiente = Decimal("0.00")

        # Actualizar estado de pago
        if venta.saldo_pendiente == 0:
            venta.estado_pago = "Pagada"
        elif venta.saldo_pendiente < venta.monto_total:
            venta.estado_pago = "Parcial"

        venta.save(update_fields=["saldo_pendiente", "estado_pago"])


@receiver(post_save, sender=Ventas)
def emitir_documento_tributario(sender, instance, created, **kwargs):
    """
    Emite automáticamente un DocumentoTributario (factura) cuando se crea
    una venta en estado pagado o contado.

    - Busca el timbrado vigente.
    - Asigna el próximo número secuencial disponible de forma atómica.
    - Si no hay timbrado vigente, la venta igual se guarda (documento queda pendiente).
    - También registra el movimiento en la caja activa si existe turno abierto.
    """
    if not created:
        return
    if instance.estado not in ("activa", "completada", "Completada", "activo"):
        return

    from datetime import date
    from django.utils import timezone
    from apps.contabilidad.models import Timbrados, DocumentosTributarios, CierresCaja, MovimientosCaja

    hoy = date.today()
    timbrado = Timbrados.objects.filter(
        estado=True,
        es_electronico=0,
        fecha_inicio__lte=hoy,
        fecha_fin__gte=hoy,
    ).order_by("-fecha_inicio").first()

    if timbrado:
        try:
            with transaction.atomic():
                usados = DocumentosTributarios.objects.filter(
                    nro_timbrado=timbrado
                ).select_for_update().count()
                nro = timbrado.nro_inicial + usados
                if nro <= timbrado.nro_final:
                    DocumentosTributarios.objects.create(
                        nro_timbrado=timbrado,
                        nro_secuencial=nro,
                        tipo_documento="FACTURA",
                        monto_total=instance.monto_total,
                        fecha_emision=timezone.now(),
                        # Referencia cruzada: permite recuperar el doc desde la venta
                        nro_preimpreso_interno=str(instance.pk),
                    )
        except Exception:
            # No interrumpir la venta si falla generación de factura
            pass

    # Registrar movimiento en caja activa
    try:
        # Filtrar por la caja específica que procesó esta venta para evitar
        # asignar el movimiento al turno equivocado cuando hay múltiples cajas abiertas
        if instance.id_caja_id:
            turno = CierresCaja.objects.filter(
                estado="abierto",
                id_caja_id=instance.id_caja_id,
            ).order_by("-fecha_hora_apertura").first()
        else:
            turno = CierresCaja.objects.filter(
                estado="abierto"
            ).order_by("-fecha_hora_apertura").first()
        if turno and instance.id_medio_pago_id:
            MovimientosCaja.objects.create(
                id_cierre=turno,
                id_venta=instance,
                tipo_movimiento="Venta",
                monto=instance.monto_total,
                fecha_movimiento=timezone.now(),
                descripcion=f"Venta #{instance.nro_factura_venta}",
                id_medio_pago=instance.id_medio_pago,
            )
    except Exception:
        pass
