/** Métodos de pago de saldo aceptados en toda la aplicación. */
export const METODOS_PAGO = [
  { value: 'EFECTIVO',      label: 'Efectivo',              labelCorto: 'Efectivo',      autoconfirma: true  },
  { value: 'POS DEBITO',    label: 'POS Débito',            labelCorto: 'POS Débito',    autoconfirma: true  },
  { value: 'POS CREDITO',   label: 'POS Crédito',           labelCorto: 'POS Crédito',   autoconfirma: true  },
  { value: 'TRANSFERENCIA', label: 'Transferencia bancaria', labelCorto: 'Transferencia', autoconfirma: false },
] as const

/** Lookup rápido de etiqueta por valor. */
export const METODO_PAGO_LABEL: Record<string, string> = Object.fromEntries(
  METODOS_PAGO.map(m => [m.value, m.labelCorto]),
)
