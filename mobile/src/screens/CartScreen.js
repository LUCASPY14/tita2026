import React, { useState } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  TextInput,
} from 'react-native';
import api from '../services/api';

export default function CartScreen({ route, navigation }) {
  const { cart: initialCart = [], setCart: setParentCart } = route.params || {};
  const [cart, setCart] = useState(initialCart);
  const [notas, setNotas] = useState('');
  const [loading, setLoading] = useState(false);

  function updateCantidad(id, delta) {
    setCart((prev) => {
      const updated = prev
        .map((i) => (i.id === id ? { ...i, cantidad: i.cantidad + delta } : i))
        .filter((i) => i.cantidad > 0);
      setParentCart?.(updated);
      return updated;
    });
  }

  const total = cart.reduce((sum, item) => sum + Number(item.precio) * item.cantidad, 0);

  async function handleConfirmar() {
    if (cart.length === 0) {
      Alert.alert('Carrito vacío', 'Agregá productos antes de confirmar.');
      return;
    }
    setLoading(true);
    try {
      const items = cart.map((i) => ({ producto: i.id, cantidad: i.cantidad }));
      await api.post('/pedidos/', { items, notas: notas.trim() || undefined });
      setParentCart?.([]);
      Alert.alert('¡Pedido confirmado!', 'Tu pedido fue registrado. ¡Buen provecho!', [
        { text: 'OK', onPress: () => navigation.navigate('Menu') },
      ]);
    } catch (error) {
      const mensaje =
        error.response?.data?.detail ||
        JSON.stringify(error.response?.data) ||
        'No se pudo enviar el pedido.';
      Alert.alert('Error', mensaje);
    } finally {
      setLoading(false);
    }
  }

  function renderItem({ item }) {
    return (
      <View style={styles.item}>
        <View style={styles.itemInfo}>
          <Text style={styles.itemNombre}>{item.nombre}</Text>
          <Text style={styles.itemPrecio}>${Number(item.precio).toFixed(2)} c/u</Text>
        </View>
        <View style={styles.quantityControl}>
          <TouchableOpacity style={styles.qtyBtn} onPress={() => updateCantidad(item.id, -1)}>
            <Text style={styles.qtyBtnText}>−</Text>
          </TouchableOpacity>
          <Text style={styles.qty}>{item.cantidad}</Text>
          <TouchableOpacity style={styles.qtyBtn} onPress={() => updateCantidad(item.id, 1)}>
            <Text style={styles.qtyBtnText}>+</Text>
          </TouchableOpacity>
        </View>
        <Text style={styles.subtotal}>
          ${(Number(item.precio) * item.cantidad).toFixed(2)}
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={cart}
        keyExtractor={(item) => String(item.id)}
        renderItem={renderItem}
        ItemSeparatorComponent={() => <View style={styles.separator} />}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyText}>Tu carrito está vacío.</Text>
          </View>
        }
        ListFooterComponent={
          cart.length > 0 ? (
            <View style={styles.footer}>
              <TextInput
                style={styles.notas}
                placeholder="Notas o aclaraciones (opcional)"
                value={notas}
                onChangeText={setNotas}
                multiline
                maxLength={200}
              />
              <View style={styles.totalRow}>
                <Text style={styles.totalLabel}>Total:</Text>
                <Text style={styles.totalAmount}>${total.toFixed(2)}</Text>
              </View>
              <TouchableOpacity
                style={[styles.confirmBtn, loading && styles.confirmDisabled]}
                onPress={handleConfirmar}
                disabled={loading}
              >
                {loading ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text style={styles.confirmText}>Confirmar Pedido</Text>
                )}
              </TouchableOpacity>
            </View>
          ) : null
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F5' },
  item: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    padding: 12,
    alignItems: 'center',
  },
  itemInfo: { flex: 1 },
  itemNombre: { fontSize: 15, fontWeight: '600', color: '#222' },
  itemPrecio: { fontSize: 12, color: '#888', marginTop: 2 },
  quantityControl: { flexDirection: 'row', alignItems: 'center', marginHorizontal: 8 },
  qtyBtn: {
    width: 30,
    height: 30,
    backgroundColor: '#E3F2FD',
    borderRadius: 15,
    alignItems: 'center',
    justifyContent: 'center',
  },
  qtyBtnText: { fontSize: 18, color: '#1565C0', fontWeight: 'bold' },
  qty: { fontSize: 16, fontWeight: '600', marginHorizontal: 8, minWidth: 20, textAlign: 'center' },
  subtotal: { fontSize: 15, fontWeight: 'bold', color: '#27AE60', minWidth: 60, textAlign: 'right' },
  separator: { height: 1, backgroundColor: '#EEE' },
  empty: { alignItems: 'center', paddingTop: 80 },
  emptyText: { color: '#999', fontSize: 16 },
  footer: { padding: 16 },
  notas: {
    backgroundColor: '#fff',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#DDD',
    padding: 10,
    marginBottom: 12,
    minHeight: 60,
    fontSize: 14,
  },
  totalRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
    paddingHorizontal: 4,
  },
  totalLabel: { fontSize: 18, fontWeight: '600', color: '#333' },
  totalAmount: { fontSize: 20, fontWeight: 'bold', color: '#1565C0' },
  confirmBtn: {
    backgroundColor: '#27AE60',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
  },
  confirmDisabled: { backgroundColor: '#A5D6A7' },
  confirmText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
});
