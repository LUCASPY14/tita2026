import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  ScrollView,
  Image,
  TextInput,
  Modal,
} from 'react-native';
import { MaterialIcons, FontAwesome5 } from '@expo/vector-icons';
import sipapService from '../services/sipap.service';

/**
 * Pantalla de pago con QR SIPAP
 * - Carga de saldo para tarjeta
 * - Pago de deuda pendiente
 */
export default function SIPAPPaymentScreen({ route, navigation }) {
  const { 
    idCliente, 
    tipo = 'carga', // 'carga' o 'pago'
    montoInicial = 0,
    descripcionInicial = '',
    onExito
  } = route.params || {};

  const [paso, setPaso] = useState('input'); // 'input', 'qr', 'confirmado', 'error'
  const [monto, setMonto] = useState(montoInicial ? montoInicial.toString() : '');
  const [descripcion, setDescripcion] = useState(descripcionInicial);
  const [qrData, setQrData] = useState(null);
  const [tiempoRestante, setTiempoRestante] = useState(0);
  const [estadoPago, setEstadoPago] = useState(null);
  const [error, setError] = useState('');
  const [generando, setGenerando] = useState(false);

  useEffect(() => {
    navigation.setOptions({
      title: tipo === 'carga' ? 'Cargar Saldo' : 'Pagar Deuda',
    });
  }, [tipo]);

  useEffect(() => {
    if (paso === 'qr' && tiempoRestante > 0) {
      const timer = setInterval(() => {
        setTiempoRestante((prev) => {
          if (prev <= 1) {
            clearInterval(timer);
            setPaso('error');
            setError('El QR ha expirado');
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      return () => clearInterval(timer);
    }
  }, [paso, tiempoRestante]);

  const formatearMontoInput = (valor) => {
    const numero = valor.replace(/\D/g, '');
    if (!numero) return '';
    return parseInt(numero, 10).toLocaleString('es-PY');
  };

  const obtenerMontoNumerico = () => {
    return parseInt(monto.replace(/\D/g, ''), 10) || 0;
  };

  const validarMonto = () => {
    const montoNum = obtenerMontoNumerico();
    if (!montoNum || montoNum <= 0) {
      Alert.alert('Error', 'Ingresa un monto válido');
      return false;
    }
    if (montoNum < 10000) {
      Alert.alert('Error', 'El monto mínimo es Gs. 10.000');
      return false;
    }
    return true;
  };

  const handleGenerarQR = async () => {
    if (!validarMonto()) return;

    try {
      setGenerando(true);
      setPaso('qr');
      setError('');

      const response = await sipapService.generarQRCargaSaldo(
        idCliente,
        obtenerMontoNumerico(),
        descripcion || (tipo === 'carga' ? 'Carga de saldo' : 'Pago de deuda')
      );

      setQrData(response);
      setTiempoRestante(response.qr_data.expira_en);

      // Iniciar polling para verificar pago
      iniciarPolling(response.qr_data.txn_id);
    } catch (err) {
      setPaso('error');
      setError(err.message || 'Error al generar QR');
      Alert.alert('Error', err.message || 'No se pudo generar el QR');
    } finally {
      setGenerando(false);
    }
  };

  const iniciarPolling = async (txnId) => {
    try {
      await sipapService.esperarConfirmacion(
        txnId,
        (estado) => {
          setEstadoPago(estado);
        },
        3000,
        300
      );

      // Pago confirmado
      setPaso('confirmado');
      if (onExito) {
        onExito(txnId, obtenerMontoNumerico());
      }
    } catch (err) {
      if (err.message.includes('expirado')) {
        setPaso('error');
        setError('El QR ha expirado');
      } else if (err.message.includes('rechazado')) {
        setPaso('error');
        setError('El pago fue rechazado');
      }
      // En caso de timeout, no mostrar error (puede seguir pendiente)
    }
  };

  const handleCancelar = () => {
    Alert.alert(
      'Cancelar',
      '¿Estás seguro de cancelar?',
      [
        { text: 'No', style: 'cancel' },
        {
          text: 'Sí',
          style: 'destructive',
          onPress: () => navigation.goBack(),
        },
      ]
    );
  };

  const handleVolver = () => {
    navigation.goBack();
  };

  const renderInputMonto = () => (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <MaterialIcons 
          name="qr-code-2" 
          size={80} 
          color="#10B981" 
        />
        <Text style={styles.title}>
          {tipo === 'carga' ? 'Cargar Saldo con QR' : 'Pagar con QR SIPAP'}
        </Text>
        <Text style={styles.subtitle}>
          🇵🇾 Escaneá desde tu app bancaria
        </Text>
      </View>

      <View style={styles.inputContainer}>
        <Text style={styles.label}>Monto a {tipo === 'carga' ? 'cargar' : 'pagar'}</Text>
        <View style={styles.inputWrapper}>
          <Text style={styles.currencyPrefix}>Gs.</Text>
          <TextInput
            style={styles.input}
            value={monto}
            onChangeText={(text) => setMonto(formatearMontoInput(text))}
            keyboardType="numeric"
            placeholder="0"
            placeholderTextColor="#9CA3AF"
          />
        </View>
        <Text style={styles.hint}>
          Mínimo: Gs. 10.000 • Sugerido: Gs. 50.000 - 100.000
        </Text>
      </View>

      {tipo === 'carga' && (
        <View style={styles.inputContainer}>
          <Text style={styles.label}>Descripción (opcional)</Text>
          <TextInput
            style={[styles.input, styles.textInput]}
            value={descripcion}
            onChangeText={setDescripcion}
            placeholder="Carga de saldo"
            placeholderTextColor="#9CA3AF"
          />
        </View>
      )}

      <View style={styles.infoBox}>
        <MaterialIcons name="info" size={24} color="#3B82F6" />
        <View style={styles.infoTextContainer}>
          <Text style={styles.infoTitle}>Bancos compatibles</Text>
          <Text style={styles.infoText}>
            Continental, Atlas, Itaú, BNF, BBVA, Regional, GNB, y todos los bancos con Zimple
          </Text>
        </View>
      </View>

      <View style={styles.buttonContainer}>
        <TouchableOpacity
          style={styles.cancelButton}
          onPress={handleCancelar}
        >
          <Text style={styles.cancelButtonText}>Cancelar</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[
            styles.generateButton,
            (!validarMonto() || generando) && styles.generateButtonDisabled,
          ]}
          onPress={handleGenerarQR}
          disabled={!validarMonto() || generando}
        >
          {generando ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.generateButtonText}>Generar QR</Text>
          )}
        </TouchableOpacity>
      </View>
    </ScrollView>
  );

  const renderQR = () => (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.qrHeader}>
        <Text style={styles.qrTitle}>Escaneá el QR</Text>
        <View style={styles.timerContainer}>
          <MaterialIcons name="timer" size={20} color="#EF4444" />
          <Text style={styles.timerText}>
            {sipapService.formatearTiempo(tiempoRestante)}
          </Text>
        </View>
      </View>

      {qrData?.qr_data?.qr_image && (
        <View style={styles.qrContainer}>
          <Image
            source={{ uri: qrData.qr_data.qr_image }}
            style={styles.qrImage}
            resizeMode="contain"
          />
        </View>
      )}

      <View style={styles.qrInfo}>
        <Text style={styles.qrAmount}>
          {sipapService.formatearMonto(obtenerMontoNumerico())}
        </Text>
        <Text style={styles.qrDescription}>
          {descripcion || (tipo === 'carga' ? 'Carga de saldo' : 'Pago de deuda')}
        </Text>
      </View>

      <View style={styles.instructionsBox}>
        <Text style={styles.instructionsTitle}>📱 Cómo pagar:</Text>
        <Text style={styles.instructionsText}>
          1. Abrí tu app bancaria (Zimple, Continental, etc.){'\n'}
          2. Buscá la opción "Pagar con QR" o "Escanear QR"{'\n'}
          3. Apuntá la cámara a este código{'\n'}
          4. Confirmá el pago en tu app
        </Text>
      </View>

      {estadoPago && estadoPago.estado === 'pendiente' && (
        <View style={styles.statusBox}>
          <ActivityIndicator size="small" color="#F59E0B" />
          <Text style={styles.statusText}>Esperando confirmación...</Text>
        </View>
      )}

      <TouchableOpacity
        style={styles.backButton}
        onPress={handleVolver}
      >
        <Text style={styles.backButtonText}>Cancelar</Text>
      </TouchableOpacity>
    </ScrollView>
  );

  const renderConfirmado = () => (
    <View style={styles.container}>
      <View style={styles.successContainer}>
        <MaterialIcons name="check-circle" size={100} color="#10B981" />
        <Text style={styles.successTitle}>¡Pago Confirmado!</Text>
        <Text style={styles.successAmount}>
          {sipapService.formatearMonto(obtenerMontoNumerico())}
        </Text>
        <Text style={styles.successMessage}>
          {tipo === 'carga' 
            ? 'Tu saldo se ha cargado correctamente' 
            : 'Tu pago ha sido procesado exitosamente'}
        </Text>

        <TouchableOpacity
          style={styles.doneButton}
          onPress={handleVolver}
        >
          <Text style={styles.doneButtonText}>Continuar</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  const renderError = () => (
    <View style={styles.container}>
      <View style={styles.errorContainer}>
        <MaterialIcons name="error" size={100} color="#EF4444" />
        <Text style={styles.errorTitle}>Error</Text>
        <Text style={styles.errorMessage}>{error}</Text>

        <TouchableOpacity
          style={styles.retryButton}
          onPress={() => {
            setPaso('input');
            setError('');
            setQrData(null);
          }}
        >
          <Text style={styles.retryButtonText}>Intentar de nuevo</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.backButton}
          onPress={handleVolver}
        >
          <Text style={styles.backButtonText}>Volver</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  switch (paso) {
    case 'input':
      return renderInputMonto();
    case 'qr':
      return renderQR();
    case 'confirmado':
      return renderConfirmado();
    case 'error':
      return renderError();
    default:
      return renderInputMonto();
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  content: {
    padding: 20,
  },
  header: {
    alignItems: 'center',
    marginBottom: 30,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
    marginTop: 16,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: '#6B7280',
    marginTop: 8,
    textAlign: 'center',
  },
  inputContainer: {
    marginBottom: 24,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#E5E7EB',
    paddingHorizontal: 16,
  },
  currencyPrefix: {
    fontSize: 20,
    fontWeight: '600',
    color: '#6B7280',
    marginRight: 8,
  },
  input: {
    flex: 1,
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
    paddingVertical: 16,
  },
  textInput: {
    fontSize: 16,
    backgroundColor: '#fff',
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#E5E7EB',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  hint: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 8,
  },
  infoBox: {
    flexDirection: 'row',
    backgroundColor: '#DBEAFE',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
  },
  infoTextContainer: {
    flex: 1,
    marginLeft: 12,
  },
  infoTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1E40AF',
    marginBottom: 4,
  },
  infoText: {
    fontSize: 12,
    color: '#1E3A8A',
    lineHeight: 18,
  },
  buttonContainer: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 8,
  },
  cancelButton: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#E5E7EB',
    paddingVertical: 16,
    alignItems: 'center',
  },
  cancelButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6B7280',
  },
  generateButton: {
    flex: 1,
    backgroundColor: '#10B981',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  generateButtonDisabled: {
    backgroundColor: '#D1D5DB',
  },
  generateButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  qrHeader: {
    alignItems: 'center',
    marginBottom: 24,
  },
  qrTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 12,
  },
  timerContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEE2E2',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  timerText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#EF4444',
    marginLeft: 8,
  },
  qrContainer: {
    backgroundColor: '#fff',
    borderRadius: 20,
    padding: 20,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
    marginBottom: 24,
  },
  qrImage: {
    width: 280,
    height: 280,
  },
  qrInfo: {
    alignItems: 'center',
    marginBottom: 24,
  },
  qrAmount: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#10B981',
    marginBottom: 8,
  },
  qrDescription: {
    fontSize: 16,
    color: '#6B7280',
  },
  instructionsBox: {
    backgroundColor: '#FEF3C7',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
  },
  instructionsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#92400E',
    marginBottom: 8,
  },
  instructionsText: {
    fontSize: 14,
    color: '#78350F',
    lineHeight: 22,
  },
  statusBox: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FEF3C7',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  statusText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#92400E',
    marginLeft: 8,
  },
  backButton: {
    backgroundColor: '#fff',
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#E5E7EB',
    paddingVertical: 14,
    alignItems: 'center',
  },
  backButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6B7280',
  },
  successContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  successTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#10B981',
    marginTop: 24,
    marginBottom: 16,
  },
  successAmount: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 8,
  },
  successMessage: {
    fontSize: 16,
    color: '#6B7280',
    textAlign: 'center',
    marginBottom: 32,
  },
  doneButton: {
    backgroundColor: '#10B981',
    borderRadius: 12,
    paddingHorizontal: 48,
    paddingVertical: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  doneButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  errorTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#EF4444',
    marginTop: 24,
    marginBottom: 16,
  },
  errorMessage: {
    fontSize: 16,
    color: '#6B7280',
    textAlign: 'center',
    marginBottom: 32,
  },
  retryButton: {
    backgroundColor: '#10B981',
    borderRadius: 12,
    paddingHorizontal: 48,
    paddingVertical: 16,
    marginBottom: 16,
  },
  retryButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
  },
});
