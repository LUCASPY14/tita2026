import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
  RefreshControl,
  ScrollView,
} from 'react-native';
import api from '../services/api';

/**
 * AccountScreen — muestra el saldo y resumen de cuenta de un hijo (alumno).
 * Accesible desde MenuScreen → "Mi Cuenta".
 */
export default function AccountScreen({ route, navigation }) {
  const { hijoId, hijoNombre } = route.params || {};

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [tarjeta, setTarjeta] = useState(null);
  const [movimientos, setMovimientos] = useState([]);
  const [resumen, setResumen] = useState({ total_recargas: 0, total_consumos: 0, saldo_actual: 0 });

  useEffect(() => {
    navigation.setOptions({ title: hijoNombre ? `Cuenta: ${hijoNombre}` : 'Mi Cuenta' });
    cargarDatos();
  }, [hijoId]);

  const cargarDatos = useCallback(async () => {
    try {
      setLoading(true);
      // Obtener tarjeta del hijo
      const tarjetaRes = await api.get('/tarjetas/', { params: { id_hijo: hijoId } });
      const tarjetas = tarjetaRes.data?.results || tarjetaRes.data || [];
      const t = tarjetas[0] || null;
      setTarjeta(t);

      if (t) {
        // Obtener últimos movimientos (recargas y consumos)
        const [recargasRes, consumosRes] = await Promise.all([
          api.get('/recargas/', { params: { nro_tarjeta: t.nro_tarjeta, page_size: 10, ordering: '-fecha' } }),
          api.get('/consumos/', { params: { nro_tarjeta: t.nro_tarjeta, page_size: 10, ordering: '-fecha' } }),
        ]);

        const recargas = (recargasRes.data?.results || recargasRes.data || []).map(r => ({
          ...r,
          tipo: 'recarga',
          fecha: r.fecha_recarga || r.fecha_creacion || '',
        }));
        const consumos = (consumosRes.data?.results || consumosRes.data || []).map(c => ({
          ...c,
          tipo: 'consumo',
          fecha: c.fecha_consumo || c.fecha || '',
        }));

        // Mezclar y ordenar por fecha desc
        const todos = [...recargas, ...consumos].sort(
          (a, b) => new Date(b.fecha) - new Date(a.fecha)
        );
        setMovimientos(todos.slice(0, 20));

        // Resumen
        const totalRecargas = recargas.reduce((s, r) => s + Number(r.monto || 0), 0);
        const totalConsumos = consumos.reduce((s, c) => s + Number(c.monto || 0), 0);
        setResumen({
          total_recargas: totalRecargas,
          total_consumos: totalConsumos,
          saldo_actual: Number(t.saldo_actual || 0),
        });
      }
    } catch (error) {
      Alert.alert('Error', 'No se pudo cargar la información de la cuenta.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [hijoId]);

  const onRefresh = () => {
    setRefreshing(true);
    cargarDatos();
  };

  const formatMonto = (v) => `Gs. ${Number(v).toLocaleString('es-PY')}`;

  const formatFecha = (iso) => {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleDateString('es-PY', { day: '2-digit', month: '2-digit', year: 'numeric' });
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#F59E0B" />
        <Text style={styles.loadingText}>Cargando cuenta...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#F59E0B']} />}
    >
      {/* Tarjeta de saldo */}
      <View style={styles.saldoCard}>
        <Text style={styles.saldoLabel}>Saldo disponible</Text>
        <Text style={styles.saldoMonto}>{formatMonto(resumen.saldo_actual)}</Text>
        {tarjeta && (
          <Text style={styles.tarjetaNro}>Tarjeta: {tarjeta.nro_tarjeta}</Text>
        )}
      </View>

      {/* Resumen */}
      <View style={styles.resumenRow}>
        <View style={[styles.resumenItem, { backgroundColor: '#ECFDF5' }]}>
          <Text style={styles.resumenLabel}>Recargas del mes</Text>
          <Text style={[styles.resumenMonto, { color: '#059669' }]}>{formatMonto(resumen.total_recargas)}</Text>
        </View>
        <View style={[styles.resumenItem, { backgroundColor: '#FEF3C7' }]}>
          <Text style={styles.resumenLabel}>Consumos del mes</Text>
          <Text style={[styles.resumenMonto, { color: '#D97706' }]}>{formatMonto(resumen.total_consumos)}</Text>
        </View>
      </View>

      {/* Movimientos */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Últimos movimientos</Text>
        {movimientos.length === 0 ? (
          <Text style={styles.emptyText}>Sin movimientos recientes</Text>
        ) : (
          movimientos.map((mov, idx) => (
            <View key={idx} style={styles.movItem}>
              <View style={[styles.movIcon, { backgroundColor: mov.tipo === 'recarga' ? '#ECFDF5' : '#FEF3C7' }]}>
                <Text style={{ fontSize: 18 }}>{mov.tipo === 'recarga' ? '💳' : '🛒'}</Text>
              </View>
              <View style={styles.movInfo}>
                <Text style={styles.movTipo}>{mov.tipo === 'recarga' ? 'Recarga' : 'Consumo'}</Text>
                <Text style={styles.movFecha}>{formatFecha(mov.fecha)}</Text>
              </View>
              <Text style={[styles.movMonto, { color: mov.tipo === 'recarga' ? '#059669' : '#D97706' }]}>
                {mov.tipo === 'recarga' ? '+' : '-'}{formatMonto(mov.monto)}
              </Text>
            </View>
          ))
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  loadingText: {
    marginTop: 12,
    color: '#6B7280',
    fontSize: 14,
  },
  saldoCard: {
    margin: 16,
    borderRadius: 16,
    backgroundColor: '#F59E0B',
    padding: 24,
    alignItems: 'center',
    elevation: 4,
    shadowColor: '#F59E0B',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
  },
  saldoLabel: {
    color: '#FEF3C7',
    fontSize: 13,
    fontWeight: '500',
    marginBottom: 8,
  },
  saldoMonto: {
    color: '#fff',
    fontSize: 34,
    fontWeight: 'bold',
    letterSpacing: -0.5,
  },
  tarjetaNro: {
    color: '#FEF3C7',
    fontSize: 11,
    marginTop: 8,
    fontFamily: 'monospace',
  },
  resumenRow: {
    flexDirection: 'row',
    marginHorizontal: 16,
    gap: 12,
    marginBottom: 16,
  },
  resumenItem: {
    flex: 1,
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  resumenLabel: {
    fontSize: 11,
    color: '#6B7280',
    marginBottom: 4,
    textAlign: 'center',
  },
  resumenMonto: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  section: {
    marginHorizontal: 16,
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 12,
  },
  emptyText: {
    color: '#9CA3AF',
    textAlign: 'center',
    paddingVertical: 16,
    fontSize: 14,
  },
  movItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
  },
  movIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  movInfo: {
    flex: 1,
  },
  movTipo: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  movFecha: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
  movMonto: {
    fontSize: 15,
    fontWeight: '700',
  },
});
