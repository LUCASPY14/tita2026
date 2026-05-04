/**
 * Componente PagoSIPAP
 * 
 * Muestra QR SIPAP para pago de deuda de cliente con:
 * - Imagen QR escaneablE con apps bancarias
 * - Countdown timer de expiración
 * - Polling automático para confirmar pago
 * - Información del cliente y monto
 * - Indicadores visuales de estado
 * 
 * @example
 * ```tsx
 * <PagoSIPAP
 *   idCliente={1}
 *   monto={14402000}
 *   onPagoConfirmado={(txnId) => console.log('Pago confirmado:', txnId)}
 *   onError={(error) => console.error(error)}
 * />
 * ```
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Modal, Button, Spin, Alert, Typography, Divider, Card, Row, Col, Space } from 'antd';
import { 
  QrcodeOutlined, 
  ClockCircleOutlined, 
  CheckCircleOutlined, 
  CloseCircleOutlined,
  ReloadOutlined,
  BankOutlined
} from '@ant-design/icons';
import { 
  portalAuthService,
  sipapUtils,
  GenerarQRSIPAPResponse, 
  EstadoPagoSIPAP 
} from '../../services/portalAuth.service';

const { Title, Text, Paragraph } = Typography;

interface PagoSIPAPProps {
  idCliente: number;
  monto?: number;               // Opcional - si no se especifica usa total deuda
  descripcion?: string;         // Opcional - descripción del pago
  visible: boolean;             // Control del modal
  onClose: () => void;          // Callback al cerrar
  onPagoConfirmado?: (txnId: string, monto: number) => void;  // Callback cuando se confirma
  onError?: (error: string) => void;  // Callback de error
}

type EstadoComponente = 'generando' | 'mostrando_qr' | 'confirmado' | 'error' | 'expirado';

const PagoSIPAP: React.FC<PagoSIPAPProps> = ({
  idCliente,
  monto,
  descripcion,
  visible,
  onClose,
  onPagoConfirmado,
  onError
}) => {
  const [estado, setEstado] = useState<EstadoComponente>('generando');
  const [qrData, setQrData] = useState<GenerarQRSIPAPResponse | null>(null);
  const [estadoPago, setEstadoPago] = useState<EstadoPagoSIPAP | null>(null);
  const [tiempoRestante, setTiempoRestante] = useState<number>(0);
  const [errorMsg, setErrorMsg] = useState<string>('');

  /**
   * Generar QR SIPAP al abrir el modal
   */
  const generarQR = useCallback(async () => {
    setEstado('generando');
    setErrorMsg('');

    try {
      const response = await portalAuthService.generarQRSIPAP({
        id_cliente: idCliente,
        monto,
        descripcion
      });

      setQrData(response);
      setTiempoRestante(response.qr_data.expira_en);
      setEstado('mostrando_qr');

      // Iniciar polling para verificar pago
      iniciarPolling(response.qr_data.txn_id);

    } catch (error: any) {
      const mensaje = error.response?.data?.detail || error.message || 'Error al generar QR';
      setErrorMsg(mensaje);
      setEstado('error');
      onError?.(mensaje);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [idCliente, monto, descripcion, onError]);

  /**
   * Iniciar polling para verificar confirmación de pago
   */
  const iniciarPolling = async (txnId: string) => {
    try {
      await portalAuthService.esperarConfirmacionSIPAP(
        txnId,
        (estado) => {
          setEstadoPago(estado);
        },
        3000,  // Cada 3 segundos
        300    // Max 15 minutos
      );

      // Pago confirmado
      setEstado('confirmado');
      onPagoConfirmado?.(txnId, qrData?.cliente.monto_a_pagar || 0);

    } catch (error: any) {
      if (error.message.includes('expirado')) {
        setEstado('expirado');
      } else if (error.message.includes('rechazado')) {
        setEstado('error');
        setErrorMsg('El pago fue rechazado');
      } else {
        // Timeout o error de red - no mostrar error, simplemente parar
        console.warn('Polling terminado:', error.message);
      }
    }
  };

  /**
   * Countdown timer
   */
  useEffect(() => {
    if (estado !== 'mostrando_qr' || tiempoRestante <= 0) {
      return;
    }

    const timer = setInterval(() => {
      setTiempoRestante((prev) => {
        const nuevo = prev - 1;
        
        // Si se acabó el tiempo, marcar como expirado
        if (nuevo <= 0) {
          setEstado('expirado');
          return 0;
        }
        
        return nuevo;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [estado, tiempoRestante]);

  /**
   * Generar QR cuando se abre el modal
   */
  useEffect(() => {
    if (visible) {
      generarQR();
    } else {
      // Resetear al cerrar
      setEstado('generando');
      setQrData(null);
      setEstadoPago(null);
      setTiempoRestante(0);
      setErrorMsg('');
    }
  }, [visible, generarQR]);

  /**
   * Renderizar contenido según estado
   */
  const renderContenido = () => {
    switch (estado) {
      case 'generando':
        return (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin size="large" />
            <Paragraph style={{ marginTop: 20 }}>
              Generando QR SIPAP...
            </Paragraph>
          </div>
        );

      case 'mostrando_qr':
        return (
          <>
            {/* Información del cliente */}
            <Card size="small" style={{ marginBottom: 16, background: '#f5f5f5' }}>
              <Row gutter={16}>
                <Col span={12}>
                  <Text strong>Cliente:</Text><br />
                  <Text>{qrData?.cliente.nombre_completo}</Text>
                </Col>
                <Col span={12}>
                  <Text strong>RUC/CI:</Text><br />
                  <Text>{qrData?.cliente.ruc_ci}</Text>
                </Col>
              </Row>
              <Divider style={{ margin: '12px 0' }} />
              <Row gutter={16}>
                <Col span={12}>
                  <Text strong>Deuda Total:</Text><br />
                  <Text>{sipapUtils.formatearMonto(qrData?.cliente.total_deuda || 0)}</Text>
                </Col>
                <Col span={12}>
                  <Text strong>Facturas:</Text><br />
                  <Text>{qrData?.cliente.cantidad_facturas}</Text>
                </Col>
              </Row>
            </Card>

            {/* Monto a pagar */}
            <div style={{ textAlign: 'center', marginBottom: 20 }}>
              <Title level={3} style={{ margin: 0, color: '#1890ff' }}>
                {sipapUtils.formatearMonto(qrData?.cliente.monto_a_pagar || 0)}
              </Title>
              <Text type="secondary">Monto a pagar</Text>
            </div>

            {/* QR Code */}
            <div style={{ textAlign: 'center', marginBottom: 20 }}>
              <div style={{ 
                display: 'inline-block', 
                padding: 20, 
                background: 'white',
                borderRadius: 8,
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
              }}>
                {qrData?.qr_data.qr_image && (
                  <img 
                    src={qrData.qr_data.qr_image} 
                    alt="QR SIPAP" 
                    style={{ 
                      width: 280, 
                      height: 280,
                      display: 'block'
                    }} 
                  />
                )}
              </div>
            </div>

            {/* Timer de expiración */}
            <Alert
              message={
                <Space>
                  <ClockCircleOutlined />
                  <span>
                    Expira en: <strong style={{ fontSize: 18, color: tiempoRestante < 60 ? '#ff4d4f' : '#1890ff' }}>
                      {sipapUtils.formatearTiempo(tiempoRestante)}
                    </strong>
                  </span>
                </Space>
              }
              type={tiempoRestante < 60 ? 'warning' : 'info'}
              style={{ marginBottom: 16 }}
            />

            {/* Instrucciones */}
            <Card size="small" title={<><BankOutlined /> Cómo pagar</>}>
              <ol style={{ paddingLeft: 20, margin: 0 }}>
                <li>Abre tu app bancaria (Zimple, Continental, Atlas, Itaú, etc.)</li>
                <li>Busca la opción "Escanear QR" o "Pagar con QR"</li>
                <li>Escanea este código QR con tu celular</li>
                <li>Confirma el pago en tu app</li>
                <li>Recibirás confirmación automática aquí</li>
              </ol>
            </Card>

            {/* Indicador de polling */}
            {estadoPago && (
              <div style={{ textAlign: 'center', marginTop: 16 }}>
                <Spin size="small" />
                <Text type="secondary" style={{ marginLeft: 8 }}>
                  Esperando confirmación...
                </Text>
              </div>
            )}
          </>
        );

      case 'confirmado':
        return (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <CheckCircleOutlined style={{ fontSize: 72, color: '#52c41a' }} />
            <Title level={3} style={{ color: '#52c41a', marginTop: 20 }}>
              ¡Pago Confirmado!
            </Title>
            <Paragraph>
              Monto: <strong>{sipapUtils.formatearMonto(qrData?.cliente.monto_a_pagar || 0)}</strong>
            </Paragraph>
            <Paragraph type="secondary">
              El pago fue aplicado automáticamente a las facturas pendientes.
            </Paragraph>
          </div>
        );

      case 'expirado':
        return (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <ClockCircleOutlined style={{ fontSize: 72, color: '#faad14' }} />
            <Title level={3} style={{ color: '#faad14', marginTop: 20 }}>
              QR Expirado
            </Title>
            <Paragraph>
              El código QR ha expirado. Por favor, genera uno nuevo.
            </Paragraph>
            <Button 
              type="primary" 
              icon={<ReloadOutlined />}
              onClick={generarQR}
            >
              Generar Nuevo QR
            </Button>
          </div>
        );

      case 'error':
        return (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <CloseCircleOutlined style={{ fontSize: 72, color: '#ff4d4f' }} />
            <Title level={3} style={{ color: '#ff4d4f', marginTop: 20 }}>
              Error
            </Title>
            <Paragraph>{errorMsg}</Paragraph>
            <Button 
              type="primary" 
              icon={<ReloadOutlined />}
              onClick={generarQR}
            >
              Reintentar
            </Button>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <Modal
      title={
        <Space>
          <QrcodeOutlined style={{ fontSize: 20 }} />
          <span>Pago con QR SIPAP</span>
        </Space>
      }
      open={visible}
      onCancel={onClose}
      footer={
        estado === 'confirmado' ? (
          <Button type="primary" onClick={onClose}>
            Cerrar
          </Button>
        ) : estado === 'mostrando_qr' ? (
          <Button onClick={onClose}>
            Cancelar
          </Button>
        ) : null
      }
      width={560}
      centered
    >
      {renderContenido()}
    </Modal>
  );
};

export default PagoSIPAP;
