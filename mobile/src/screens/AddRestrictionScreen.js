import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Alert,
  Switch,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Picker } from '@react-native-picker/picker';
import { MaterialIcons } from '@expo/vector-icons';
import api from '../services/api';

const AddRestrictionScreen = ({ route, navigation }) => {
  const { hijoId, hijoNombre, restriccion, isEdit = false } = route.params;

  // Form state
  const [formData, setFormData] = useState({
    tipo_restriccion: '',
    descripcion: '',
    observaciones: '',
    severidad: 'Media',
    requiere_autorizacion: false,
    estado: true,
  });

  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (isEdit && restriccion) {
      setFormData({
        tipo_restriccion: restriccion.tipo_restriccion || '',
        descripcion: restriccion.descripcion || '',
        observaciones: restriccion.observaciones || '',
        severidad: restriccion.severidad || 'Media',
        requiere_autorizacion: restriccion.requiere_autorizacion || false,
        estado: restriccion.estado !== false, // Default to true if undefined
      });
    }
  }, [isEdit, restriccion]);

  const tiposRestricion = [
    'Alergia',
    'Intolerancia',
    'Médica',
    'Dieta especial',
    'Religiosa/Cultural',
    'Otra'
  ];

  const nivelesGravedad = [
    { value: 'Baja', label: 'Baja', color: '#22c55e' },
    { value: 'Media', label: 'Media', color: '#eab308' },
    { value: 'Alta', label: 'Alta', color: '#f97316' },
    { value: 'Crítica', label: 'Crítica', color: '#ef4444' },
  ];

  const validateForm = () => {
    const newErrors = {};

    if (!formData.tipo_restriccion.trim()) {
      newErrors.tipo_restriccion = 'El tipo de restricción es obligatorio';
    } else if (formData.tipo_restriccion.length < 3) {
      newErrors.tipo_restriccion = 'El tipo debe tener al menos 3 caracteres';
    } else if (formData.tipo_restriccion.length > 100) {
      newErrors.tipo_restriccion = 'El tipo no puede exceder 100 caracteres';
    }

    if (formData.descripcion.trim() && formData.descripcion.length < 10) {
      newErrors.descripcion = 'La descripción debe tener al menos 10 caracteres';
    } else if (formData.descripcion.length > 500) {
      newErrors.descripcion = 'La descripción no puede exceder 500 caracteres';
    }

    if (formData.observaciones.length > 500) {
      newErrors.observaciones = 'Las observaciones no pueden exceder 500 caracteres';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async () => {
    if (!validateForm()) {
      Alert.alert('Error', 'Por favor corrige los errores en el formulario');
      return;
    }

    setLoading(true);

    try {
      const payload = {
        ...formData,
        id_hijo: hijoId,
      };

      let response;
      if (isEdit) {
        response = await api.put(`/restricciones/${restriccion.id_restriccion}/`, payload);
      } else {
        response = await api.post('/restricciones/', payload);
      }

      Alert.alert(
        'Éxito',
        `Restricción ${isEdit ? 'actualizada' : 'creada'} correctamente`,
        [
          {
            text: 'OK',
            onPress: () => navigation.goBack()
          }
        ]
      );
    } catch (error) {
      console.error('Error guardando restricción:', error);
      const errorMessage = error.response?.data?.message || 
                          error.response?.data?.detail ||
                          `Error al ${isEdit ? 'actualizar' : 'crear'} la restricción`;
      Alert.alert('Error', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const updateFormField = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  const getSeverityColor = (severidad) => {
    const nivel = nivelesGravedad.find(n => n.value === severidad);
    return nivel?.color || '#6b7280';
  };

  return (
    <KeyboardAvoidingView 
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}
        >
          <MaterialIcons name="arrow-back" size={24} color="#ffffff" />
        </TouchableOpacity>
        <View style={styles.headerInfo}>
          <Text style={styles.headerTitle}>
            {isEdit ? 'Editar restricción' : 'Nueva restricción'}
          </Text>
          <Text style={styles.headerSubtitle}>{hijoNombre}</Text>
        </View>
        <TouchableOpacity
          style={[
            styles.saveButton,
            loading && styles.saveButtonDisabled
          ]}
          onPress={handleSave}
          disabled={loading}
        >
          <MaterialIcons 
            name="save" 
            size={24} 
            color={loading ? "#9ca3af" : "#ffffff"} 
          />
        </TouchableOpacity>
      </View>

      <ScrollView 
        style={styles.scrollContainer}
        showsVerticalScrollIndicator={false}
      >
        {/* Tipo de restricción */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Información básica</Text>
          
          <View style={styles.fieldContainer}>
            <Text style={styles.fieldLabel}>
              Tipo de restricción *
            </Text>
            <View style={[
              styles.pickerContainer,
              errors.tipo_restriccion && styles.fieldError
            ]}>
              <Picker
                selectedValue={formData.tipo_restriccion}
                onValueChange={(value) => updateFormField('tipo_restriccion', value)}
                style={styles.picker}
              >
                <Picker.Item label="Seleccionar tipo..." value="" />
                {tiposRestricion.map((tipo) => (
                  <Picker.Item key={tipo} label={tipo} value={tipo} />
                ))}
              </Picker>
            </View>
            {errors.tipo_restriccion && (
              <Text style={styles.errorText}>{errors.tipo_restriccion}</Text>
            )}
          </View>

          {/* Campo personalizable si selecciona "Otra" */}
          {formData.tipo_restriccion === 'Otra' && (
            <View style={styles.fieldContainer}>
              <Text style={styles.fieldLabel}>
                Especificar tipo personalizado *
              </Text>
              <TextInput
                style={[
                  styles.textInput,
                  errors.tipo_restriccion && styles.fieldError
                ]}
                value={formData.tipo_restriccion === 'Otra' ? '' : formData.tipo_restriccion}
                onChangeText={(value) => updateFormField('tipo_restriccion', value)}
                placeholder="Ej: Intolerancia al gluten"
                maxLength={100}
              />
            </View>
          )}

          {/* Nivel de severidad */}
          <View style={styles.fieldContainer}>
            <Text style={styles.fieldLabel}>
              Nivel de severidad *
            </Text>
            <View style={styles.severityContainer}>
              {nivelesGravedad.map((nivel) => (
                <TouchableOpacity
                  key={nivel.value}
                  style={[
                    styles.severityOption,
                    formData.severidad === nivel.value && {
                      backgroundColor: nivel.color,
                      borderColor: nivel.color,
                    }
                  ]}
                  onPress={() => updateFormField('severidad', nivel.value)}
                >
                  <Text style={[
                    styles.severityOptionText,
                    formData.severidad === nivel.value && styles.severityOptionTextSelected
                  ]}>
                    {nivel.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        </View>

        {/* Descripción detallada */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Descripción detallada</Text>
          
          <View style={styles.fieldContainer}>
            <Text style={styles.fieldLabel}>
              Descripción
              {formData.descripcion.trim() && (
                <Text style={styles.fieldOptional}> ({formData.descripcion.length}/500)</Text>
              )}
            </Text>
            <TextInput
              style={[
                styles.textArea,
                errors.descripcion && styles.fieldError
              ]}
              value={formData.descripcion}
              onChangeText={(value) => updateFormField('descripcion', value)}
              placeholder="Describe la restricción en detalle (ej: alérgicos específicos, síntomas, etc.)"
              multiline
              numberOfLines={4}
              maxLength={500}
              textAlignVertical="top"
            />
            {errors.descripcion && (
              <Text style={styles.errorText}>{errors.descripcion}</Text>
            )}
            <Text style={styles.helperText}>
              Mínimo 10 caracteres si decides completar este campo
            </Text>
          </View>
        </View>

        {/* Observaciones adicionales */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Observaciones adicionales</Text>
          
          <View style={styles.fieldContainer}>
            <Text style={styles.fieldLabel}>
              Observaciones para el personal
              {formData.observaciones.trim() && (
                <Text style={styles.fieldOptional}> ({formData.observaciones.length}/500)</Text>
              )}
            </Text>
            <TextInput
              style={[
                styles.textArea,
                errors.observaciones && styles.fieldError
              ]}
              value={formData.observaciones}
              onChangeText={(value) => updateFormField('observaciones', value)}
              placeholder="Instrucciones especiales, ubicación de medicamentos, contactos de emergencia, etc."
              multiline
              numberOfLines={3}
              maxLength={500}
              textAlignVertical="top"
            />
            {errors.observaciones && (
              <Text style={styles.errorText}>{errors.observaciones}</Text>
            )}
          </View>
        </View>

        {/* Configuración adicional */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Configuración</Text>
          
          {/* Requiere autorización */}
          <View style={styles.switchContainer}>
            <View style={styles.switchInfo}>
              <Text style={styles.switchLabel}>Requiere autorización</Text>
              <Text style={styles.switchDescription}>
                Las excepciones a esta restricción necesitarán autorización especial
              </Text>
            </View>
            <Switch
              value={formData.requiere_autorizacion}
              onValueChange={(value) => updateFormField('requiere_autorizacion', value)}
              trackColor={{ false: '#e5e7eb', true: '#4F46E5' }}
              thumbColor={formData.requiere_autorizacion ? '#ffffff' : '#f3f4f6'}
            />
          </View>

          {/* Estado activo */}
          <View style={styles.switchContainer}>
            <View style={styles.switchInfo}>
              <Text style={styles.switchLabel}>Restricción activa</Text>
              <Text style={styles.switchDescription}>
                Si está desactivada, no se aplicará en las verificaciones
              </Text>
            </View>
            <Switch
              value={formData.estado}
              onValueChange={(value) => updateFormField('estado', value)}
              trackColor={{ false: '#e5e7eb', true: '#22c55e' }}
              thumbColor={formData.estado ? '#ffffff' : '#f3f4f6'}
            />
          </View>
        </View>

        {/* Vista previa */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Vista previa</Text>
          <View style={[
            styles.previewCard,
            { borderLeftColor: getSeverityColor(formData.severidad) }
          ]}>
            <View style={styles.previewHeader}>
              <MaterialIcons
                name="info-outline"
                size={20}
                color={getSeverityColor(formData.severidad)}
              />
              <Text style={styles.previewTipo}>
                {formData.tipo_restriccion || 'Tipo por definir'}
              </Text>
              <View style={[
                styles.previewSeverityBadge,
                { backgroundColor: getSeverityColor(formData.severidad) }
              ]}>
                <Text style={styles.previewSeverityText}>
                  {formData.severidad}
                </Text>
              </View>
            </View>
            
            {formData.descripcion.trim() && (
              <Text style={styles.previewDescription}>
                {formData.descripcion}
              </Text>
            )}
            
            <View style={styles.previewMeta}>
              {formData.requiere_autorizacion && (
                <View style={styles.previewAuthBadge}>
                  <MaterialIcons name="security" size={12} color="#f59e0b" />
                  <Text style={styles.previewAuthText}>Requiere autorización</Text>
                </View>
              )}
              
              {!formData.estado && (
                <View style={styles.previewInactiveBadge}>
                  <MaterialIcons name="visibility-off" size={12} color="#6b7280" />
                  <Text style={styles.previewInactiveText}>Inactiva</Text>
                </View>
              )}
            </View>
          </View>
        </View>

        {/* Spacer para el keyboard */}
        <View style={{ height: 50 }} />
      </ScrollView>
    </KeyboardAvoidingView>
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
  saveButton: {
    padding: 8,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.2)',
  },
  saveButtonDisabled: {
    backgroundColor: 'rgba(255,255,255,0.1)',
  },
  scrollContainer: {
    flex: 1,
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
  fieldContainer: {
    marginBottom: 20,
  },
  fieldLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  fieldOptional: {
    fontSize: 14,
    color: '#6b7280',
    fontWeight: 'normal',
  },
  pickerContainer: {
    backgroundColor: '#f9fafb',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#d1d5db',
  },
  picker: {
    height: 50,
  },
  textInput: {
    backgroundColor: '#f9fafb',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#d1d5db',
    padding: 12,
    fontSize: 16,
    color: '#1f2937',
    minHeight: 50,
  },
  textArea: {
    backgroundColor: '#f9fafb',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#d1d5db',
    padding: 12,
    fontSize: 16,
    color: '#1f2937',
    minHeight: 100,
  },
  fieldError: {
    borderColor: '#ef4444',
    borderWidth: 2,
  },
  errorText: {
    color: '#ef4444',
    fontSize: 12,
    marginTop: 4,
  },
  helperText: {
    color: '#6b7280',
    fontSize: 12,
    marginTop: 4,
  },
  severityContainer: {
    flexDirection: 'row',
    gap: 10,
    flexWrap: 'wrap',
  },
  severityOption: {
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderWidth: 2,
    borderColor: '#e5e7eb',
    backgroundColor: '#ffffff',
  },
  severityOptionText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6b7280',
  },
  severityOptionTextSelected: {
    color: '#ffffff',
  },
  switchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  switchInfo: {
    flex: 1,
    marginRight: 15,
  },
  switchLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 4,
  },
  switchDescription: {
    fontSize: 14,
    color: '#6b7280',
    lineHeight: 18,
  },
  previewCard: {
    backgroundColor: '#f9fafb',
    padding: 15,
    borderRadius: 12,
    borderLeftWidth: 4,
  },
  previewHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  previewTipo: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
    marginLeft: 8,
    flex: 1,
  },
  previewSeverityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  previewSeverityText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '600',
  },
  previewDescription: {
    fontSize: 14,
    color: '#4b5563',
    marginBottom: 8,
    lineHeight: 20,
  },
  previewMeta: {
    flexDirection: 'row',
    gap: 12,
  },
  previewAuthBadge: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  previewAuthText: {
    fontSize: 12,
    color: '#f59e0b',
    marginLeft: 4,
  },
  previewInactiveBadge: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  previewInactiveText: {
    fontSize: 12,
    color: '#6b7280',
    marginLeft: 4,
  },
});

export default AddRestrictionScreen;