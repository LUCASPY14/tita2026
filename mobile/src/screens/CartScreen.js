import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  TextInput,
  Modal,
  ScrollView,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { MaterialIcons } from '@expo/vector-icons';
import api from '../services/api';

export default function CartScreen({ route, navigation }) {
  const { cart: initialCart = [], setCart: setParentCart } = route.params || {};
  const [cart, setCart] = useState(initialCart);
  const [notas, setNotas] = useState('');
  const [loading, setLoading] = useState(false);
  const [restricciones, setRestricciones] = useState([]);
  const [showRestrictionsModal, setShowRestrictionsModal] = useState(false);
  const [restrictionWarnings, setRestrictionWarnings] = useState([]);
  const [userInfo, setUserInfo] = useState(null);

  useEffect(() => {
    loadUserDataAndRestrictions();
  }, []);

  useEffect(() => {
    checkRestrictions();
  }, [cart, restricciones]);

  const loadUserDataAndRestrictions = async () => {
    try {
      // Cargar datos del usuario
      const userData = await AsyncStorage.getItem('userInfo');
      if (userData) {
        const user = JSON.parse(userData);
        setUserInfo(user);
        
        // Cargar hijos y sus restricciones
        await loadRestrictions(user.id);
      }
    } catch (error) {
      console.error('Error cargando datos del usuario:', error);
    }
  };

  const loadRestrictions = async (userId) => {
    try {
      // Obtener hijos del usuario
      const response = await api.get('/hijos/', {
        params: { id_cliente_responsable: userId }
      });
      
      const hijos = response.data?.results || response.data || [];
      let todasLasRestricciones = [];
      
      // Cargar restricciones de todos los hijos
      for (const hijo of hijos) {
        if (hijo.restricciones && hijo.restricciones.length > 0) {
          const restriccionesActivas = hijo.restricciones.filter(r => 
            r.estado === true && r.severidad
          );
          
          // Agregar información del hijo a cada restricción
          const restriccionesConHijo = restriccionesActivas.map(r => ({
            ...r,
            hijo: {
              id: hijo.id_hijo,
              nombre: hijo.nombre,
              apellido: hijo.apellido
            }
          }));
          
          todasLasRestricciones = [...todasLasRestricciones, ...restriccionesConHijo];
        }
      }
      
      setRestricciones(todasLasRestricciones);
    } catch (error) {
      console.error('Error cargando restricciones:', error);
    }
  };

  const checkRestrictions = () => {
    if (!cart.length || !restricciones.length) {
      setRestrictionWarnings([]);
      return;
    }

    const warnings = [];
    
    restricciones.forEach(restriccion => {
      cart.forEach(producto => {
        // Verificar si el nombre del producto contiene palabras relacionadas con la restricción
        const productName = producto.nombre.toLowerCase();
        const restriccionTipo = restriccion.tipo_restriccion.toLowerCase();
        const descripcion = (restriccion.descripcion || '').toLowerCase();
        
        let hasConflict = false;
        
        // Verificaciones básicas por tipo de restricción
        if (restriccionTipo.includes('alergia') || restriccionTipo.includes('alérgic')) {
          // Verificar alergias comunes
          const alergenos = ['maní', 'nuez', 'almendra', 'leche', 'huevo', 'pescado', 'mariscos', 'soja', 'trigo', 'gluten'];
          hasConflict = alergenos.some(alergeno => 
            productName.includes(alergeno) || descripcion.includes(alergeno)
          );
        } else if (restriccionTipo.includes('gluten')) {
          hasConflict = productName.includes('pan') || productName.includes('pasta') || 
                       productName.includes('trigo') || productName.includes('harina');
        } else if (restriccionTipo.includes('lactosa') || restriccionTipo.includes('leche')) {
          hasConflict = productName.includes('leche') || productName.includes('queso') || 
                       productName.includes('yogurt') || productName.includes('crema');
        }
        
        // Verificar palabras específicas en la descripción de la restricción
        if (descripcion) {
          const palabrasProhibidas = descripcion.split(/[\s,;]+/).filter(p => p.length > 3);
          hasConflict = hasConflict || palabrasProhibidas.some(palabra => 
            productName.includes(palabra)
          );
        }

        if (hasConflict) {
          warnings.push({
            producto: producto,
            restriccion: restriccion,
            severidad: restriccion.severidad,
            mensaje: `${producto.nombre} puede contener ${restriccion.tipo_restriccion.toLowerCase()}`
          });
        }
      });
    });
    
    setRestrictionWarnings(warnings);
  };

  const getSeverityColor = (severidad) => {
    switch (severidad?.toLowerCase()) {
      case 'crítica':
      case 'critica':
        return '#ef4444';
      case 'alta':
        return '#f97316';
      case 'media':
        return '#eab308';
      case 'baja':
        return '#22c55e';
      default:
        return '#6b7280';
    }
  };

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

  const hasRestrictionWarnings = () => {
    return restrictionWarnings.length > 0;
  };

  const hasCriticalRestrictions = () => {
    return restrictionWarnings.some(w => 
      w.severidad?.toLowerCase() === 'crítica' || w.severidad?.toLowerCase() === 'critica'
    );
  };

  const showRestrictionAlert = () => {
    if (!hasRestrictionWarnings()) return true;
    
    const criticalWarnings = restrictionWarnings.filter(w => 
      w.severidad?.toLowerCase() === 'crítica' || w.severidad?.toLowerCase() === 'critica'
    );
    
    if (criticalWarnings.length > 0) {
      // Restricciones críticas - mostrar modal detallado
      setShowRestrictionsModal(true);
      return false;
    } else {
      // Restricciones no críticas - mostrar alert simple
      const warningMessages = restrictionWarnings.map(w => 
        `• ${w.mensaje} (${w.restriccion.hijo.nombre} - ${w.severidad})`
      ).join('\n');
      
      Alert.alert(
        '⚠️ Advertencia de Restricciones',
        `Se detectaron las siguientes restricciones alimentarias:\n\n${warningMessages}\n\n¿Deseas continuar con el pedido?`,
        [
          { text: 'Cancelar', style: 'cancel' },
          { text: 'Continuar', onPress: () => proceedWithOrder() }
        ]
      );
      return false;
    }
  };

  const proceedWithOrder = () => {
    // Agregar nota sobre las restricciones verificadas
    const restrictionNote = restrictionWarnings.length > 0 
      ? `[RESTRICCIONES VERIFICADAS] ${restrictionWarnings.map(w => w.mensaje).join('; ')}`
      : '';
    
    const finalNotes = [notas.trim(), restrictionNote].filter(n => n.length > 0).join(' | ');
    
    executeOrder(finalNotes);
  };

  async function executeOrder(finalNotes = '') {
    setLoading(true);
    try {
      const detalles = cart.map((item) => ({
        id_producto: item.id,
        cantidad: item.cantidad,
        precio_unitario: Number(item.precio),
      }));
      
      const ventaData = {
        tipo_venta: 'Contado',
        detalles,
        ...(finalNotes.trim() && { observaciones: finalNotes.trim() }),
      };

      await api.post('/ventas/', ventaData);
      setParentCart?.([]);
      Alert.alert('¡Pedido confirmado!', 'Tu pedido fue registrado. ¡Buen provecho!', [
        { text: 'OK', onPress: () => navigation.navigate('Menu') },
      ]);
    } catch (error) {
      const mensaje =
        error.response?.data?.detail ||
        error.response?.data?.non_field_errors?.[0] ||
        JSON.stringify(error.response?.data) ||
        'No se pudo enviar el pedido.';
      Alert.alert('Error', mensaje);
    } finally {
      setLoading(false);
    }
  }

  async function handleConfirmar() {
    if (cart.length === 0) {
      Alert.alert('Carrito vacío', 'Agregá productos antes de confirmar.');
      return;
    }

    // Verificar restricciones antes de proceder
    if (showRestrictionAlert()) {
      proceedWithOrder();
    }
  }

  function renderItem({ item }) {
    const warning = restrictionWarnings.find(w => w.producto.id === item.id);
    
    return (
      <View style={[
        styles.item,
        warning && { borderLeftWidth: 4, borderLeftColor: getSeverityColor(warning.severidad) }
      ]}>
        <View style={styles.itemInfo}>
          <View style={styles.itemHeader}>
            <Text style={styles.itemNombre}>{item.nombre}</Text>
            {warning && (
              <MaterialIcons
                name="warning"
                size={16}
                color={getSeverityColor(warning.severidad)}
                style={styles.warningIcon}
              />
            )}
          </View>
          <Text style={styles.itemPrecio}>
            Gs. {Number(item.precio).toLocaleString('es-PY', { maximumFractionDigits: 0 })} c/u
          </Text>
          {warning && (
            <Text style={[styles.warningText, { color: getSeverityColor(warning.severidad) }]}>
              ⚠️ {warning.mensaje} ({warning.restriccion.hijo.nombre})
            </Text>
          )}
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
          Gs. {Math.round(Number(item.precio) * item.cantidad).toLocaleString('es-PY', { maximumFractionDigits: 0 })}
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Modal para restricciones críticas */}
      <Modal
        visible={showRestrictionsModal}
        animationType="slide"
        transparent={false}
        onRequestClose={() => setShowRestrictionsModal(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>🚨 Restricciones Críticas Detectadas</Text>
            <TouchableOpacity
              style={styles.modalCloseBtn}
              onPress={() => setShowRestrictionsModal(false)}
            >
              <MaterialIcons name="close" size={24} color="#666" />
            </TouchableOpacity>
          </View>
          
          <ScrollView style={styles.modalContent}>
            <Text style={styles.modalDescription}>
              Se han detectado productos que pueden entrar en conflicto con restricciones críticas.
              Por favor, revisa cuidadosamente antes de continuar:
            </Text>
            
            {restrictionWarnings
              .filter(w => w.severidad?.toLowerCase() === 'crítica' || w.severidad?.toLowerCase() === 'critica')
              .map((warning, index) => (
                <View key={index} style={styles.criticalWarningCard}>
                  <View style={styles.criticalWarningHeader}>
                    <MaterialIcons name="warning" size={24} color="#ef4444" />
                    <Text style={styles.criticalWarningTitle}>
                      {warning.restriccion.tipo_restriccion} - {warning.restriccion.hijo.nombre}
                    </Text>
                  </View>
                  
                  <Text style={styles.criticalWarningProduct}>
                    Producto: {warning.producto.nombre}
                  </Text>
                  
                  <Text style={styles.criticalWarningMessage}>
                    {warning.mensaje}
                  </Text>
                  
                  {warning.restriccion.descripcion && (
                    <Text style={styles.criticalWarningDescription}>
                      Descripción: {warning.restriccion.descripcion}
                    </Text>
                  )}
                  
                  {warning.restriccion.observaciones && (
                    <Text style={styles.criticalWarningObservations}>
                      Observaciones: {warning.restriccion.observaciones}
                    </Text>
                  )}
                  
                  {warning.restriccion.requiere_autorizacion && (
                    <View style={styles.authorizationBadge}>
                      <MaterialIcons name="security" size={16} color="#f59e0b" />
                      <Text style={styles.authorizationText}>Requiere autorización especial</Text>
                    </View>
                  )}
                </View>
              ))}
            
            <Text style={styles.modalWarning}>
              ⚠️ Las restricciones críticas pueden representar riesgo para la salud. 
              Solo continúa si estás completamente seguro de que el estudiante puede consumir estos productos.
            </Text>
          </ScrollView>
          
          <View style={styles.modalFooter}>
            <TouchableOpacity
              style={styles.modalCancelBtn}
              onPress={() => setShowRestrictionsModal(false)}
            >
              <Text style={styles.modalCancelText}>Revisar Carrito</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={styles.modalConfirmBtn}
              onPress={() => {
                setShowRestrictionsModal(false);
                proceedWithOrder();
              }}
            >
              <Text style={styles.modalConfirmText}>Continuar de Todas Formas</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

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
              {/* Resumen de restricciones */}
              {hasRestrictionWarnings() && (
                <View style={styles.restrictionsAlert}>
                  <View style={styles.restrictionsHeader}>
                    <MaterialIcons
                      name="warning"
                      size={20}
                      color={hasCriticalRestrictions() ? '#ef4444' : '#f59e0b'}
                    />
                    <Text style={[
                      styles.restrictionsTitle,
                      { color: hasCriticalRestrictions() ? '#ef4444' : '#f59e0b' }
                    ]}>
                      {hasCriticalRestrictions() ? 'Restricciones Críticas' : 'Restricciones Detectadas'}
                    </Text>
                  </View>
                  
                  <Text style={styles.restrictionsCount}>
                    {restrictionWarnings.length} producto(s) con restricciones
                  </Text>
                  
                  <TouchableOpacity
                    style={styles.restrictionsDetailBtn}
                    onPress={() => navigation.navigate('Profile')}
                  >
                    <Text style={styles.restrictionsDetailText}>Ver restricciones en perfil</Text>
                    <MaterialIcons name="arrow-forward" size={16} color="#4F46E5" />
                  </TouchableOpacity>
                </View>
              )}
              
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
                <Text style={styles.totalAmount}>Gs. {Math.round(total).toLocaleString('es-PY', { maximumFractionDigits: 0 })}</Text>
              </View>
              <TouchableOpacity
                style={[
                  styles.confirmBtn, 
                  loading && styles.confirmDisabled,
                  hasRestrictionWarnings() && styles.confirmWithWarning
                ]}
                onPress={handleConfirmar}
                disabled={loading}
              >
                {loading ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <View style={styles.confirmBtnContent}>
                    <Text style={styles.confirmText}>
                      {hasRestrictionWarnings() ? 'Confirmar (con restricciones)' : 'Confirmar Pedido'}
                    </Text>
                    {hasRestrictionWarnings() && (
                      <MaterialIcons name="warning" size={20} color="#fff" />
                    )}
                  </View>
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
  itemHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  itemNombre: { fontSize: 15, fontWeight: '600', color: '#222', flex: 1 },
  itemPrecio: { fontSize: 12, color: '#888', marginTop: 2 },
  warningIcon: {
    marginLeft: 8,
  },
  warningText: {
    fontSize: 11,
    marginTop: 4,
    fontWeight: '500',
  },
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
  restrictionsAlert: {
    backgroundColor: '#fef7e7',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#f59e0b',
  },
  restrictionsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  restrictionsTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 6,
  },
  restrictionsCount: {
    fontSize: 12,
    color: '#6b7280',
    marginBottom: 8,
  },
  restrictionsDetailBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  restrictionsDetailText: {
    fontSize: 12,
    color: '#4F46E5',
    fontWeight: '500',
  },
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
  confirmWithWarning: {
    backgroundColor: '#f59e0b',
  },
  confirmBtnContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  confirmDisabled: { backgroundColor: '#A5D6A7' },
  confirmText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  
  // Modal styles
  modalContainer: {
    flex: 1,
    backgroundColor: '#fff',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    paddingTop: 50,
    backgroundColor: '#fef2f2',
    borderBottomWidth: 1,
    borderBottomColor: '#fecaca',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ef4444',
    flex: 1,
  },
  modalCloseBtn: {
    padding: 4,
  },
  modalContent: {
    flex: 1,
    padding: 20,
  },
  modalDescription: {
    fontSize: 16,
    color: '#374151',
    marginBottom: 20,
    lineHeight: 22,
  },
  criticalWarningCard: {
    backgroundColor: '#fef2f2',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#ef4444',
  },
  criticalWarningHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  criticalWarningTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ef4444',
    marginLeft: 8,
    flex: 1,
  },
  criticalWarningProduct: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1f2937',
    marginBottom: 4,
  },
  criticalWarningMessage: {
    fontSize: 14,
    color: '#ef4444',
    marginBottom: 8,
  },
  criticalWarningDescription: {
    fontSize: 13,
    color: '#6b7280',
    marginBottom: 6,
    lineHeight: 18,
  },
  criticalWarningObservations: {
    fontSize: 13,
    color: '#6b7280',
    marginBottom: 8,
    lineHeight: 18,
  },
  authorizationBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#f3f4f6',
  },
  authorizationText: {
    fontSize: 12,
    color: '#f59e0b',
    marginLeft: 6,
    fontWeight: '500',
  },
  modalWarning: {
    backgroundColor: '#fffbeb',
    padding: 16,
    borderRadius: 8,
    fontSize: 14,
    color: '#92400e',
    lineHeight: 20,
    borderWidth: 1,
    borderColor: '#fcd34d',
    marginTop: 10,
  },
  modalFooter: {
    flexDirection: 'row',
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
    gap: 12,
  },
  modalCancelBtn: {
    flex: 1,
    backgroundColor: '#f3f4f6',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  modalCancelText: {
    color: '#374151',
    fontSize: 16,
    fontWeight: '600',
  },
  modalConfirmBtn: {
    flex: 1,
    backgroundColor: '#ef4444',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  modalConfirmText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
});
