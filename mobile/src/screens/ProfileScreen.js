import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Image,
  TouchableOpacity,
  Alert,
  RefreshControl,
  ActivityIndicator,
  ActionSheetIOS,
  Platform,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { MaterialIcons, FontAwesome5 } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import api from '../services/api';

const ProfileScreen = ({ navigation }) => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const [userInfo, setUserInfo] = useState(null);
  const [hijoSeleccionado, setHijoSeleccionado] = useState(null);
  const [hijos, setHijos] = useState([]);
  const [restricciones, setRestricciones] = useState([]);

  useEffect(() => {
    loadUserData();
  }, []);

  const loadUserData = async () => {
    try {
      setLoading(true);
      
      // Obtener datos del usuario logueado
      const userData = await AsyncStorage.getItem('userInfo');
      if (userData) {
        const user = JSON.parse(userData);
        setUserInfo(user);
        
        // Cargar hijos del usuario
        await loadHijos(user.id);
      }
    } catch (error) {
      console.error('Error cargando datos del usuario:', error);
      Alert.alert('Error', 'No se pudieron cargar los datos del perfil');
    } finally {
      setLoading(false);
    }
  };

  const loadHijos = async (userId) => {
    try {
      const response = await api.get('/hijos/', {
        params: { id_cliente_responsable: userId }
      });
      
      const hijosData = response.data?.results || response.data || [];
      setHijos(hijosData);
      
      // Seleccionar el primer hijo por defecto
      if (hijosData.length > 0 && !hijoSeleccionado) {
        setHijoSeleccionado(hijosData[0]);
        await loadRestricciones(hijosData[0].id_hijo);
      }
    } catch (error) {
      console.error('Error cargando hijos:', error);
    }
  };

  const loadRestricciones = async (hijoId) => {
    try {
      // Para obtener restricciones, podemos hacerlo a través del endpoint de hijos
      const response = await api.get(`/hijos/${hijoId}/`);
      const hijo = response.data;
      
      // Las restricciones pueden venir en el campo 'restricciones' del hijo
      setRestricciones(hijo.restricciones || []);
    } catch (error) {
      console.error('Error cargando restricciones:', error);
      setRestricciones([]);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadUserData();
    setRefreshing(false);
  };

  const handleHijoChange = async (hijo) => {
    setHijoSeleccionado(hijo);
    await loadRestricciones(hijo.id_hijo);
  };

  const getSeverityColor = (severidad) => {
    switch (severidad?.toLowerCase()) {
      case 'crítica':
      case 'critica':
        return '#ef4444'; // Rojo
      case 'alta':
        return '#f97316'; // Naranja
      case 'media':
        return '#eab308'; // Amarillo
      case 'baja':
        return '#22c55e'; // Verde
      default:
        return '#6b7280'; // Gris
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

  const requestCameraPermissions = async () => {
    const cameraPermission = await ImagePicker.requestCameraPermissionsAsync();
    const mediaLibraryPermission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    
    return cameraPermission.status === 'granted' && mediaLibraryPermission.status === 'granted';
  };

  const showPhotoActionSheet = () => {
    if (!hijoSeleccionado) {
      Alert.alert('Error', 'Por favor selecciona un hijo primero');
      return;
    }

    const options = ['Tomar Foto', 'Seleccionar de Galería', 'Cancelar'];
    const destructiveButtonIndex = 2;
    const cancelButtonIndex = 2;

    if (Platform.OS === 'ios') {
      ActionSheetIOS.showActionSheetWithOptions(
        {
          options,
          cancelButtonIndex,
          destructiveButtonIndex,
        },
        (buttonIndex) => {
          if (buttonIndex === 0) {
            takePhoto();
          } else if (buttonIndex === 1) {
            pickImage();
          }
        }
      );
    } else {
      // Para Android, mostrar Alert
      Alert.alert(
        'Seleccionar Foto',
        'Elige una opción para la foto del estudiante',
        [
          { text: 'Tomar Foto', onPress: takePhoto },
          { text: 'Galería', onPress: pickImage },
          { text: 'Cancelar', style: 'cancel' }
        ]
      );
    }
  };

  const takePhoto = async () => {
    const hasPermissions = await requestCameraPermissions();
    if (!hasPermissions) {
      Alert.alert('Error', 'Se necesitan permisos de cámara y galería');
      return;
    }

    try {
      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.8,
      });

      if (!result.canceled) {
        await uploadPhoto(result.assets[0]);
      }
    } catch (error) {
      Alert.alert('Error', 'No se pudo tomar la foto');
      console.error('Camera error:', error);
    }
  };

  const pickImage = async () => {
    const hasPermissions = await requestCameraPermissions();
    if (!hasPermissions) {
      Alert.alert('Error', 'Se necesitan permisos de galería');
      return;
    }

    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.8,
      });

      if (!result.canceled) {
        await uploadPhoto(result.assets[0]);
      }
    } catch (error) {
      Alert.alert('Error', 'No se pudo seleccionar la imagen');
      console.error('Image picker error:', error);
    }
  };

  const uploadPhoto = async (image) => {
    if (!hijoSeleccionado) {
      Alert.alert('Error', 'No hay hijo seleccionado');
      return;
    }

    setUploadingPhoto(true);
    
    try {
      // Crear FormData para upload
      const formData = new FormData();
      const filename = image.uri.split('/').pop();
      const match = /\.(\w+)$/.exec(filename);
      const type = match ? `image/${match[1]}` : 'image/jpeg';

      formData.append('foto_perfil', {
        uri: image.uri,
        type: type,
        name: filename || `photo_${Date.now()}.jpg`,
      });

      // Subir la foto
      const response = await api.patch(`/hijos/${hijoSeleccionado.id_hijo}/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // Actualizar el hijo seleccionado con la nueva foto
      const updatedHijo = { ...hijoSeleccionado, foto_perfil: response.data.foto_perfil };
      setHijoSeleccionado(updatedHijo);

      // Actualizar en la lista de hijos
      setHijos(prev => prev.map(h => 
        h.id_hijo === hijoSeleccionado.id_hijo ? updatedHijo : h
      ));

      Alert.alert('Éxito', 'Foto actualizada correctamente');
    } catch (error) {
      console.error('Upload error:', error);
      Alert.alert('Error', 'No se pudo subir la foto. Inténtalo de nuevo.');
    } finally {
      setUploadingPhoto(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>Cargando perfil...</Text>
      </View>
    );
  }

  return (
    <ScrollView 
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* Header del perfil */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}
        >
          <MaterialIcons name="arrow-back" size={24} color="#ffffff" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Perfil</Text>
      </View>

      {/* Información del usuario */}
      <View style={styles.userSection}>
        <View style={styles.userAvatar}>
          <FontAwesome5 name="user" size={32} color="#666" />
        </View>
        <Text style={styles.userName}>{userInfo?.nombres} {userInfo?.apellidos}</Text>
        <Text style={styles.userEmail}>{userInfo?.email}</Text>
      </View>

      {/* Selector de hijos */}
      {hijos.length > 1 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Seleccionar Hijo</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            {hijos.map((hijo) => (
              <TouchableOpacity
                key={hijo.id_hijo}
                style={[
                  styles.hijoCard,
                  hijoSeleccionado?.id_hijo === hijo.id_hijo && styles.hijoCardSelected
                ]}
                onPress={() => handleHijoChange(hijo)}
              >
                <Text style={[
                  styles.hijoName,
                  hijoSeleccionado?.id_hijo === hijo.id_hijo && styles.hijoNameSelected
                ]}>
                  {hijo.nombre}
                </Text>
                <Text style={styles.hijoGrade}>{hijo.grado || 'Sin grado'}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      )}

      {/* Información del hijo seleccionado */}
      {hijoSeleccionado && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Información del Estudiante</Text>
          <View style={styles.hijoInfo}>
            <TouchableOpacity 
              style={styles.hijoAvatarContainer}
              onPress={showPhotoActionSheet}
              disabled={uploadingPhoto}
            >
              {hijoSeleccionado.foto_perfil ? (
                <Image 
                  source={{ uri: hijoSeleccionado.foto_perfil }} 
                  style={styles.hijoAvatarImage}
                />
              ) : (
                <View style={styles.hijoAvatar}>
                  <FontAwesome5 name="child" size={24} color="#4F46E5" />
                </View>
              )}
              
              {/* Overlay para indicar que es tocable */}
              <View style={styles.photoOverlay}>
                {uploadingPhoto ? (
                  <ActivityIndicator size="small" color="#ffffff" />
                ) : (
                  <MaterialIcons name="camera-alt" size={16} color="#ffffff" />
                )}
              </View>
            </TouchableOpacity>
            
            <View style={styles.hijoDetails}>
              <Text style={styles.hijoFullName}>
                {hijoSeleccionado.nombre} {hijoSeleccionado.apellido}
              </Text>
              <Text style={styles.hijoGradeText}>
                Grado: {hijoSeleccionado.grado || 'No especificado'}
              </Text>
              {hijoSeleccionado.fecha_nacimiento && (
                <Text style={styles.hijoAge}>
                  Fecha de nacimiento: {hijoSeleccionado.fecha_nacimiento}
                </Text>
              )}
            </View>
          </View>
        </View>
      )}

      {/* Restricciones alimentarias */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Restricciones Alimentarias</Text>
          <TouchableOpacity
            style={styles.addButton}
            onPress={() => navigation.navigate('AddRestriction', { 
              hijoId: hijoSeleccionado?.id_hijo,
              hijoNombre: hijoSeleccionado?.nombre 
            })}
          >
            <MaterialIcons name="add" size={20} color="#ffffff" />
            <Text style={styles.addButtonText}>Agregar</Text>
          </TouchableOpacity>
        </View>

        {restricciones.length === 0 ? (
          <View style={styles.emptyState}>
            <FontAwesome5 name="check-circle" size={32} color="#22c55e" />
            <Text style={styles.emptyStateText}>Sin restricciones registradas</Text>
            <Text style={styles.emptyStateSubtext}>
              El estudiante no tiene restricciones alimentarias
            </Text>
          </View>
        ) : (
          <View style={styles.restriccionesList}>
            {restricciones.map((restriccion, index) => (
              <TouchableOpacity
                key={restriccion.id_restriccion || index}
                style={styles.restriccionCard}
                onPress={() => navigation.navigate('AddRestriction', {
                  hijoId: hijoSeleccionado?.id_hijo,
                  restriccion: restriccion,
                  isEdit: true
                })}
              >
                <View style={styles.restriccionHeader}>
                  <View style={styles.restriccionTitle}>
                    <MaterialIcons
                      name={getSeverityIcon(restriccion.severidad)}
                      size={20}
                      color={getSeverityColor(restriccion.severidad)}
                    />
                    <Text style={styles.restriccionTipo}>
                      {restriccion.tipo_restriccion}
                    </Text>
                  </View>
                  <View style={[
                    styles.severityBadge,
                    { backgroundColor: getSeverityColor(restriccion.severidad) }
                  ]}>
                    <Text style={styles.severityText}>
                      {restriccion.severidad}
                    </Text>
                  </View>
                </View>
                
                {restriccion.descripcion && (
                  <Text style={styles.restriccionDescription}>
                    {restriccion.descripcion}
                  </Text>
                )}
                
                {restriccion.requiere_autorizacion && (
                  <View style={styles.authorizationBadge}>
                    <MaterialIcons name="security" size={14} color="#f59e0b" />
                    <Text style={styles.authorizationText}>Requiere autorización</Text>
                  </View>
                )}
              </TouchableOpacity>
            ))}
          </View>
        )}
      </View>

      {/* Botones de acción */}
      <View style={styles.actions}>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => navigation.navigate('Restrictions', { 
            hijoId: hijoSeleccionado?.id_hijo 
          })}
        >
          <MaterialIcons name="list" size={20} color="#4F46E5" />
          <Text style={styles.actionButtonText}>Ver todas las restricciones</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f9fafb',
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
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
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  userSection: {
    backgroundColor: '#ffffff',
    padding: 20,
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  userAvatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#f3f4f6',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  userName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 4,
  },
  userEmail: {
    fontSize: 14,
    color: '#6b7280',
  },
  section: {
    backgroundColor: '#ffffff',
    margin: 15,
    borderRadius: 12,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 15,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  addButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#4F46E5',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  addButtonText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '600',
    marginLeft: 4,
  },
  hijoCard: {
    backgroundColor: '#f9fafb',
    padding: 15,
    borderRadius: 12,
    marginRight: 12,
    minWidth: 120,
    alignItems: 'center',
  },
  hijoCardSelected: {
    backgroundColor: '#4F46E5',
  },
  hijoName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1f2937',
  },
  hijoNameSelected: {
    color: '#ffffff',
  },
  hijoGrade: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 4,
  },
  hijoInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  hijoAvatar: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#ede9fe',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 15,
  },
  hijoAvatarContainer: {
    position: 'relative',
    marginRight: 15,
  },
  hijoAvatarImage: {
    width: 50,
    height: 50,
    borderRadius: 25,
    borderWidth: 2,
    borderColor: '#4F46E5',
  },
  photoOverlay: {
    position: 'absolute',
    bottom: -2,
    right: -2,
    backgroundColor: '#4F46E5',
    borderRadius: 10,
    width: 20,
    height: 20,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#ffffff',
  },
  hijoDetails: {
    flex: 1,
  },
  hijoFullName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1f2937',
  },
  hijoGradeText: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 2,
  },
  hijoAge: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 2,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyStateText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
    marginTop: 12,
  },
  emptyStateSubtext: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 4,
    textAlign: 'center',
  },
  restriccionesList: {
    gap: 12,
  },
  restriccionCard: {
    backgroundColor: '#f9fafb',
    padding: 15,
    borderRadius: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#e5e7eb',
  },
  restriccionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  restriccionTitle: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  restriccionTipo: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
    marginLeft: 8,
  },
  severityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  severityText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '600',
  },
  restriccionDescription: {
    fontSize: 14,
    color: '#4b5563',
    marginBottom: 8,
    lineHeight: 20,
  },
  authorizationBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  authorizationText: {
    fontSize: 12,
    color: '#f59e0b',
    marginLeft: 4,
    fontWeight: '500',
  },
  actions: {
    padding: 20,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    padding: 15,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  actionButtonText: {
    fontSize: 16,
    color: '#4F46E5',
    marginLeft: 8,
    fontWeight: '500',
  },
});

export default ProfileScreen;