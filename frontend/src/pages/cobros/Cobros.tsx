import React, { useState } from 'react';
import {
  Card,
  Input,
  Button,
  Table,
  Form,
  InputNumber,
  Select,
  message,
  Modal,
  Divider,
  Typography,
  Space,
  Tag,
  Descriptions,
} from 'antd';
import {
  SearchOutlined,
  DollarOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import cobrosService, {
  ResumenCobros,
  FacturaPendiente,
  RegistrarPagoRequest,
} from '../../services/cobros.service';
import clientesService from '../../services/clientes.service';
import mediosPagoService from '../../services/mediosPago.service';

const { Title, Text } = Typography;
const { Option } = Select;

interface Cliente {
  id_cliente: number;
  nombres: string;
  apellidos: string;
  ruc_ci: string;
}

interface MedioPago {
  id_medio_pago: number;
  nombre: string;
}

const Cobros: React.FC = () => {
  const [form] = Form.useForm();
  const [searchForm] = Form.useForm();

  const [loading, setLoading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [clienteSeleccionado, setClienteSeleccionado] = useState<number | null>(null);
  const [resumenCobros, setResumenCobros] = useState<ResumenCobros | null>(null);
  const [mediosPago, setMediosPago] = useState<MedioPago[]>([]);
  const [selectedFacturas, setSelectedFacturas] = useState<number[]>([]);
  const [modalVisible, setModalVisible] = useState(false);

  // Cargar medios de pago al montar
  React.useEffect(() => {
    loadMediosPago();
  }, []);

  const loadMediosPago = async () => {
    try {
      const data = await mediosPagoService.getAll();
      setMediosPago(data);
    } catch (error) {
      console.error('Error al cargar medios de pago:', error);
    }
  };

  const buscarCliente = async (values: { busqueda: string }) => {
    setSearchLoading(true);
    try {
      const data = await clientesService.getAll({
        search: values.busqueda,
      });
      setClientes(data);
    } catch (error) {
      message.error('Error al buscar clientes');
    } finally {
      setSearchLoading(false);
    }
  };

  const seleccionarCliente = async (idCliente: number) => {
    setLoading(true);
    try {
      const data = await cobrosService.getFacturasPendientes(idCliente);
      setResumenCobros(data);
      setClienteSeleccionado(idCliente);
      setSelectedFacturas([]);
      form.resetFields();
    } catch (error) {
      message.error('Error al cargar facturas pendientes');
    } finally {
      setLoading(false);
    }
  };

  const handleRegistrarPago = () => {
    if (!clienteSeleccionado) {
      message.warning('Seleccione un cliente');
      return;
    }
    setModalVisible(true);
  };

  const handleSubmitPago = async (values: any) => {
    if (!clienteSeleccionado) return;

    setLoading(true);
    try {
      const aplicaciones = selectedFacturas.map((idVenta) => {
        const factura = resumenCobros?.facturas.find((f) => f.id_venta === idVenta);
        return {
          id_venta: idVenta,
          monto_aplicado: factura?.saldo_pendiente || 0,
        };
      });

      const request: RegistrarPagoRequest = {
        id_cliente: clienteSeleccionado,
        monto_total: values.monto_total,
        id_medio_pago: values.id_medio_pago,
        referencia: values.referencia,
        banco_emisor: values.banco_emisor,
        observaciones: values.observaciones,
        aplicaciones: aplicaciones.length > 0 ? aplicaciones : undefined,
      };

      await cobrosService.registrarPago(request);
      message.success('Pago registrado correctamente');
      setModalVisible(false);
      form.resetFields();
      
      // Recargar facturas pendientes
      seleccionarCliente(clienteSeleccionado);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Error al registrar el pago');
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      title: 'Nro. Factura',
      dataIndex: 'nro_factura_venta',
      key: 'nro_factura_venta',
    },
    {
      title: 'Fecha',
      dataIndex: 'fecha',
      key: 'fecha',
      render: (fecha: string) => new Date(fecha).toLocaleDateString(),
    },
    {
      title: 'Total',
      dataIndex: 'total_venta',
      key: 'total_venta',
      render: (total: number) => `Gs. ${total.toLocaleString()}`,
    },
    {
      title: 'Saldo Pendiente',
      dataIndex: 'saldo_pendiente',
      key: 'saldo_pendiente',
      render: (saldo: number) => (
        <Text strong style={{ color: '#ff4d4f' }}>
          Gs. {saldo.toLocaleString()}
        </Text>
      ),
    },
    {
      title: 'Días Vencido',
      dataIndex: 'dias_vencido',
      key: 'dias_vencido',
      render: (dias: number) => (
        <Tag color={dias > 30 ? 'red' : dias > 15 ? 'orange' : 'green'}>
          {dias} días
        </Tag>
      ),
    },
  ];

  const rowSelection = {
    selectedRowKeys: selectedFacturas,
    onChange: (selectedRowKeys: React.Key[]) => {
      setSelectedFacturas(selectedRowKeys as number[]);
    },
  };

  const calcularTotalSeleccionado = () => {
    if (!resumenCobros) return 0;
    return selectedFacturas.reduce((total, idVenta) => {
      const factura = resumenCobros.facturas.find((f) => f.id_venta === idVenta);
      return total + (factura?.saldo_pendiente || 0);
    }, 0);
  };

  return (
    <div className="p-6">
      <Title level={2}>
        <DollarOutlined className="mr-2" />
        Sistema de Cobros
      </Title>

      {/* Búsqueda de Cliente */}
      <Card className="mb-4">
        <Form
          form={searchForm}
          layout="inline"
          onFinish={buscarCliente}
        >
          <Form.Item
            name="busqueda"
            rules={[{ required: true, message: 'Ingrese criterio de búsqueda' }]}
            style={{ flex: 1 }}
          >
            <Input
              placeholder="Buscar por nombre, apellido o RUC/CI"
              prefix={<SearchOutlined />}
            />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={searchLoading}>
              Buscar Cliente
            </Button>
          </Form.Item>
        </Form>

        {clientes.length > 0 && (
          <div className="mt-4">
            <Divider>Resultados de Búsqueda</Divider>
            <Space direction="vertical" style={{ width: '100%' }}>
              {clientes.map((cliente) => (
                <Card
                  key={cliente.id_cliente}
                  hoverable
                  onClick={() => seleccionarCliente(cliente.id_cliente)}
                  className={clienteSeleccionado === cliente.id_cliente ? 'border-blue-500' : ''}
                >
                  <Space>
                    <FileTextOutlined style={{ fontSize: 24 }} />
                    <div>
                      <Text strong>
                        {cliente.nombres} {cliente.apellidos}
                      </Text>
                      <br />
                      <Text type="secondary">RUC/CI: {cliente.ruc_ci}</Text>
                    </div>
                  </Space>
                </Card>
              ))}
            </Space>
          </div>
        )}
      </Card>

      {/* Información del Cliente y Facturas Pendientes */}
      {resumenCobros && (
        <>
          <Card className="mb-4">
            <Descriptions title="Información del Cliente" bordered column={2}>
              <Descriptions.Item label="Nombre">
                {resumenCobros.cliente.nombre_completo}
              </Descriptions.Item>
              <Descriptions.Item label="RUC/CI">
                {resumenCobros.cliente.ruc_ci}
              </Descriptions.Item>
              <Descriptions.Item label="Límite de Crédito">
                <Text strong>Gs. {resumenCobros.cliente.limite_credito.toLocaleString()}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="Crédito Disponible">
                <Text
                  strong
                  style={{
                    color: resumenCobros.cliente.credito_disponible < 0 ? '#ff4d4f' : '#52c41a',
                  }}
                >
                  Gs. {resumenCobros.cliente.credito_disponible.toLocaleString()}
                </Text>
              </Descriptions.Item>
              <Descriptions.Item label="Total Pendiente" span={2}>
                <Text strong style={{ fontSize: 18, color: '#ff4d4f' }}>
                  Gs. {resumenCobros.resumen.total_pendiente.toLocaleString()}
                </Text>
              </Descriptions.Item>
            </Descriptions>
          </Card>

          <Card
            title={
              <Space>
                <FileTextOutlined />
                Facturas Pendientes ({resumenCobros.facturas.length})
              </Space>
            }
            extra={
              <Button
                type="primary"
                icon={<DollarOutlined />}
                onClick={handleRegistrarPago}
                disabled={resumenCobros.facturas.length === 0}
              >
                Registrar Pago
              </Button>
            }
          >
            <Table
              rowSelection={rowSelection}
              columns={columns}
              dataSource={resumenCobros.facturas}
              rowKey="id_venta"
              loading={loading}
              pagination={{ pageSize: 10 }}
            />

            {selectedFacturas.length > 0 && (
              <div className="mt-4 p-4 bg-blue-50 rounded">
                <Space>
                  <CheckCircleOutlined style={{ color: '#1890ff', fontSize: 20 }} />
                  <Text strong>
                    Facturas seleccionadas: {selectedFacturas.length}
                  </Text>
                  <Divider type="vertical" />
                  <Text strong style={{ fontSize: 16 }}>
                    Total: Gs. {calcularTotalSeleccionado().toLocaleString()}
                  </Text>
                </Space>
              </div>
            )}
          </Card>
        </>
      )}

      {/* Modal Registrar Pago */}
      <Modal
        title="Registrar Pago"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        confirmLoading={loading}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmitPago}
        >
          <Form.Item
            name="monto_total"
            label="Monto Total"
            rules={[{ required: true, message: 'Ingrese el monto' }]}
            initialValue={calcularTotalSeleccionado()}
          >
            <InputNumber
              style={{ width: '100%' }}
              min={0}
              formatter={(value) => `Gs. ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              parser={(value) => value!.replace(/Gs\.\s?|(,*)/g, '') as any}
            />
          </Form.Item>

          <Form.Item
            name="id_medio_pago"
            label="Medio de Pago"
            rules={[{ required: true, message: 'Seleccione medio de pago' }]}
          >
            <Select placeholder="Seleccione medio de pago">
              {mediosPago.map((medio) => (
                <Option key={medio.id_medio_pago} value={medio.id_medio_pago}>
                  {medio.nombre}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="referencia" label="Referencia">
            <Input placeholder="Nro. de transferencia, cheque, etc." />
          </Form.Item>

          <Form.Item name="banco_emisor" label="Banco Emisor">
            <Input placeholder="Nombre del banco" />
          </Form.Item>

          <Form.Item name="observaciones" label="Observaciones">
            <Input.TextArea rows={3} placeholder="Observaciones adicionales" />
          </Form.Item>

          {selectedFacturas.length > 0 && (
            <div className="p-3 bg-gray-50 rounded">
              <Text strong>El pago se aplicará a las facturas seleccionadas</Text>
              <br />
              <Text type="secondary">
                {selectedFacturas.length} factura(s) - Gs. {calcularTotalSeleccionado().toLocaleString()}
              </Text>
            </div>
          )}
        </Form>
      </Modal>
    </div>
  );
};

export default Cobros;
