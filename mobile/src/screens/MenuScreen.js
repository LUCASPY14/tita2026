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
  Image,
} from 'react-native';
import api from '../services/api';
import { logout } from '../services/auth.service';

export default function MenuScreen({ navigation }) {
  const [productos, setProductos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [cart, setCart] = useState([]);

  const fetchMenu = useCallback(async () => {
    try {
      const { data } = await api.get('/productos/', { params: { disponible: true } });
      setProductos(Array.isArray(data) ? data : data.results || []);
    } catch (error) {
      Alert.alert('Error', 'No se pudo cargar el menú. Verificá tu conexión.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchMenu();
  }, [fetchMenu]);

  useEffect(() => {
    navigation.setOptions({
      headerRight: () => (
        <View style={styles.headerButtons}>
          <TouchableOpacity onPress={() => navigation.navigate('Cart', { cart, setCart })}>
            <Text style={styles.cartIcon}>🛒 {cart.reduce((s, i) => s + i.cantidad, 0)}</Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={handleLogout} style={styles.logoutBtn}>
            <Text style={styles.logoutText}>Salir</Text>
          </TouchableOpacity>
        </View>
      ),
    });
  }, [cart, navigation]);

  async function handleLogout() {
    try {
      await logout();
      navigation.replace('Login');
    } catch {
      navigation.replace('Login');
    }
  }

  function addToCart(producto) {
    setCart((prev) => {
      const existing = prev.find((i) => i.id === producto.id);
      if (existing) {
        return prev.map((i) =>
          i.id === producto.id ? { ...i, cantidad: i.cantidad + 1 } : i
        );
      }
      return [...prev, { ...producto, cantidad: 1 }];
    });
  }

  function getCartQuantity(productoId) {
    return cart.find((i) => i.id === productoId)?.cantidad || 0;
  }

  function renderProducto({ item }) {
    const qty = getCartQuantity(item.id);
    return (
      <View style={styles.card}>
        {item.imagen && (
          <Image source={{ uri: item.imagen }} style={styles.imagen} resizeMode="cover" />
        )}
        <View style={styles.cardBody}>
          <Text style={styles.nombre}>{item.nombre}</Text>
          {item.descripcion ? (
            <Text style={styles.descripcion} numberOfLines={2}>
              {item.descripcion}
            </Text>
          ) : null}
          <View style={styles.cardFooter}>
            <Text style={styles.precio}>${Number(item.precio).toFixed(2)}</Text>
            <TouchableOpacity style={styles.addButton} onPress={() => addToCart(item)}>
              <Text style={styles.addButtonText}>
                {qty > 0 ? `+1 (${qty})` : 'Agregar'}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    );
  }

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#2196F3" />
        <Text style={styles.loadingText}>Cargando menú...</Text>
      </View>
    );
  }

  return (
    <FlatList
      data={productos}
      keyExtractor={(item) => String(item.id)}
      renderItem={renderProducto}
      contentContainerStyle={styles.list}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={() => { setRefreshing(true); fetchMenu(); }}
          colors={['#2196F3']}
        />
      }
      ListEmptyComponent={
        <View style={styles.centered}>
          <Text style={styles.emptyText}>No hay productos disponibles hoy.</Text>
        </View>
      }
    />
  );
}

const styles = StyleSheet.create({
  list: { padding: 12 },
  card: {
    backgroundColor: '#fff',
    borderRadius: 10,
    marginBottom: 12,
    overflow: 'hidden',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.12,
    shadowRadius: 3,
  },
  imagen: { width: '100%', height: 140 },
  cardBody: { padding: 12 },
  nombre: { fontSize: 17, fontWeight: '600', color: '#1A237E', marginBottom: 4 },
  descripcion: { fontSize: 13, color: '#666', marginBottom: 8 },
  cardFooter: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  precio: { fontSize: 18, fontWeight: 'bold', color: '#27AE60' },
  addButton: {
    backgroundColor: '#2196F3',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 6,
  },
  addButtonText: { color: '#fff', fontWeight: '600', fontSize: 14 },
  centered: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingTop: 60 },
  loadingText: { marginTop: 10, color: '#888' },
  emptyText: { color: '#999', fontSize: 16 },
  headerButtons: { flexDirection: 'row', alignItems: 'center', gap: 12, marginRight: 4 },
  cartIcon: { fontSize: 18, color: '#fff' },
  logoutBtn: { paddingHorizontal: 4 },
  logoutText: { color: '#fff', fontSize: 14 },
});
