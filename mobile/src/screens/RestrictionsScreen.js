import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Alert,
  RefreshControl,
} from 'react-native';
import { MaterialIcons, FontAwesome5 } from '@expo/vector-icons';
import api from '../services/api';

const RestrictionsScreen = ({ route, navigation }) => {
  const { hijoId, hijoNombre } = route.params;
  const [restricciones, setRestricciones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadRestricciones();
  }, []);

  const loadRestricciones = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/hijos/${hijoId}/`);
      const hijo = response.data;
      setRestricciones(hijo.restricciones || []);
    } catch (error) {
      console.error('Error cargando restricciones:', error);
      Alert.alert('Error', 'No se pudieron cargar las restricciones');
      setRestricciones([]);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadRestricciones();
    setRefreshing(false);
  };

  const handleDeleteRestriction = async (restriccionId) => {
    Alert.alert(
      'Eliminar Restricción',
      '¿Estás seguro de que deseas eliminar esta restricción?',
      [
        { text: 'Cancelar', style: 'cancel' },
        { 
          text: 'Eliminar', 
          style: 'destructive',
          onPress: async () => {
            try {
              await api.delete(`/restricciones/${restriccionId}/`);
              Alert.alert('Éxito', 'Restricción eliminada correctamente');
              await loadRestricciones();
            } catch (error) {
              console.error('Error eliminando restricción:', error);
              Alert.alert('Error', 'No se pudo eliminar la restricción');
            }
          }
        }
      ]
    );
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

  const getSeverityIcon = (severidad) => {
    switch (severidad?.toLowerCase()) {
      case 'crítica':
      case 'critica':
        return 'warning';
      case 'alta':
        return 'error-outline';
      case 'media':
        return 'info-outline';
      case 'baja':
        return 'check-circle-outline';
      default:
        return 'help-outline';
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('es-ES');
    } catch {
      return dateString;
    }
  };

  const renderRestriction = ({ item }) => (
    <View style={[
      styles.restriccionCard,
      { borderLeftColor: getSeverityColor(item.severidad) }
    ]}>
      <View style={styles.restriccionHeader}>
        <View style={styles.restriccionTitle}>
          <MaterialIcons
            name={getSeverityIcon(item.severidad)}
            size={24}
            color={getSeverityColor(item.severidad)}
          />
          <View style={styles.titleText}>
            <Text style={styles.tipoRestriction}>
              {item.tipo_restriccion}
            </Text>
            <View style={[
              styles.severityBadge,
              { backgroundColor: getSeverityColor(item.severidad) }
            ]}>
              <Text style={styles.severityText}>
                {item.severidad}
              </Text>
            </View>
          </View>
        </View>
        
        <View style={styles.actionButtons}>
          <TouchableOpacity
            style={[styles.actionBtn, styles.editBtn]}
            onPress={() => navigation.navigate('AddRestriction', {
              hijoId: hijoId,
              hijoNombre: hijoNombre,
              restriccion: item,
              isEdit: true
            })}
          >
            <MaterialIcons name="edit" size={16} color="#4F46E5" />
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.actionBtn, styles.deleteBtn]}
            onPress={() => handleDeleteRestriction(item.id_restriccion)}
          >
            <MaterialIcons name="delete" size={16} color="#ef4444" />
          </TouchableOpacity>
        </View>
      </View>

      {item.descripcion && (
        <View style={styles.descripcionContainer}>
          <Text style={styles.descripcionLabel}>Descripción:</Text>
          <Text style={styles.descripcionText}>
            {item.descripcion}
          </Text>
        </View>
      )}

      {item.observaciones && (
        <View style={styles.observacionesContainer}>
          <Text style={styles.observacionesLabel}>Observaciones:</Text>
          <Text style={styles.observacionesText}>
            {item.observaciones}
          </Text>
        </View>
      )}

      <View style={styles.metadataContainer}>
        {item.requiere_autorizacion && (
          <View style={styles.authorizationBadge}>
            <MaterialIcons name="security" size={16} color="#f59e0b" />
            <Text style={styles.authorizationText}>
              Requiere autorización
            </Text>
          </View>
        )}

        <View style={styles.dateContainer}>
          <Text style={styles.dateLabel}>
            Registrada: {formatDate(item.fecha_registro)}
          </Text>
          {item.fecha_ultima_actualizacion && (
            <Text style={styles.dateLabel}>
              Actualizada: {formatDate(item.fecha_ultima_actualizacion)}
            </Text>
          )}
        </View>
      </View>

      {!item.estado && (
        <View style={styles.inactiveBadge}>
          <MaterialIcons name="visibility-off" size={14} color="#6b7280" />
          <Text style={styles.inactiveText}>Inactiva</Text>
        </View>
      )}
    </View>
  );

  const renderEmptyState = () => (
    <View style={styles.emptyContainer}>
      <FontAwesome5 name="check-circle" size={64} color="#22c55e" />
      <Text style={styles.emptyTitle}>
        Sin restricciones registradas
      </Text>
      <Text style={styles.emptySubtitle}>
        {hijoNombre} no tiene restricciones alimentarias
      </Text>
      <TouchableOpacity
        style={styles.addFirstButton}
        onPress={() => navigation.navigate('AddRestriction', {
          hijoId: hijoId,
          hijoNombre: hijoNombre
        })}
      >
        <MaterialIcons name="add" size={20} color="#ffffff" />
        <Text style={styles.addFirstButtonText}>
          Agregar primera restricción
        </Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}
        >
          <MaterialIcons name="arrow-back" size={24} color="#ffffff" />
        </TouchableOpacity>
        <View style={styles.headerInfo}>
          <Text style={styles.headerTitle}>Restricciones</Text>
          <Text style={styles.headerSubtitle}>{hijoNombre}</Text>
        </View>
        <TouchableOpacity
          style={styles.addHeaderButton}
          onPress={() => navigation.navigate('AddRestriction', {
            hijoId: hijoId,
            hijoNombre: hijoNombre
          })}
        >
          <MaterialIcons name="add" size={24} color="#ffffff" />
        </TouchableOpacity>
      </View>

      {/* Lista de restricciones */}
      <FlatList
        data={restricciones}
        renderItem={renderRestriction}
        keyExtractor={(item) => item.id_restriccion?.toString() || Math.random().toString()}
        ListEmptyComponent={renderEmptyState}
        refreshControl={
          <RefreshControl 
            refreshing={refreshing} 
            onRefresh={onRefresh}
            colors={['#4F46E5']}
          />
        }
        contentContainerStyle={restricciones.length === 0 ? styles.emptyListContainer : styles.listContainer}
        showsVerticalScrollIndicator={false}
      />

      {/* Floating Action Button */}
      {restricciones.length > 0 && (
        <TouchableOpacity
          style={styles.fab}
          onPress={() => navigation.navigate('AddRestriction', {
            hijoId: hijoId,
            hijoNombre: hijoNombre
          })}
        >
          <MaterialIcons name="add" size={28} color="#ffffff" />
        </TouchableOpacity>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  header: {
    backgroundColor: '#4F46E5',
    paddingTop: 50,
    paddingBottom: 20,
    paddingHorizontal: 20,
    flexDirection: 'row',
    alignItems: 'center',
  },
  backButton: {
    marginRight: 15,
  },
  headerInfo: {
    flex: 1,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#c7d2fe',
    marginTop: 2,
  },
  addHeaderButton: {
    padding: 8,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.2)',
  },
  listContainer: {
    padding: 15,
  },
  emptyListContainer: {
    flex: 1,
    justifyContent: 'center',
    padding: 20,
  },
  restriccionCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 20,
    marginBottom: 15,
    borderLeftWidth: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  restriccionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 15,
  },
  restriccionTitle: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    flex: 1,
  },
  titleText: {
    marginLeft: 12,
    flex: 1,
  },
  tipoRestriction: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 6,
  },
  severityBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  severityText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '600',
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  actionBtn: {
    padding: 8,
    borderRadius: 20,
    backgroundColor: '#f3f4f6',
  },
  editBtn: {
    backgroundColor: '#ede9fe',
  },
  deleteBtn: {
    backgroundColor: '#fee2e2',
  },
  descripcionContainer: {
    marginBottom: 12,
  },
  descripcionLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 4,
  },
  descripcionText: {
    fontSize: 14,
    color: '#4b5563',
    lineHeight: 20,
  },
  observacionesContainer: {
    marginBottom: 12,
  },
  observacionesLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 4,
  },
  observacionesText: {
    fontSize: 14,
    color: '#4b5563',
    lineHeight: 20,
  },
  metadataContainer: {
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
    paddingTop: 12,
  },
  authorizationBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  authorizationText: {
    fontSize: 13,
    color: '#f59e0b',
    marginLeft: 6,
    fontWeight: '500',
  },
  dateContainer: {
    gap: 2,
  },
  dateLabel: {
    fontSize: 12,
    color: '#6b7280',
  },
  inactiveBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
  },
  inactiveText: {
    fontSize: 12,
    color: '#6b7280',
    marginLeft: 4,
  },
  emptyContainer: {
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1f2937',
    marginTop: 20,
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 16,
    color: '#6b7280',
    textAlign: 'center',
    marginBottom: 30,
    lineHeight: 22,
  },
  addFirstButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#4F46E5',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 25,
  },
  addFirstButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  fab: {
    position: 'absolute',
    bottom: 25,
    right: 25,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#4F46E5',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 5.65,
    elevation: 8,
  },
});

export default RestrictionsScreen;