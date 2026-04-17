# 📱 App Móvil Cantina Tita - React Native + Expo

## Stack Tecnológico

- **React Native** 0.73.6
- **Expo** ~50.0.0
- **React Navigation** 6.x (navegación nativa)
- **Axios** para comunicación con API
- **AsyncStorage** para almacenamiento local
- **Expo SecureStore** para credenciales seguras
- **Expo Image Picker** para fotos

## 🚀 Instalación y Ejecución

```bash
cd mobile
npm install

# Iniciar servidor de desarrollo
npm start

# Ejecutar en Android
npm run android

# Ejecutar en iOS (requiere Mac con Xcode)
npm run ios

# Ejecutar en navegador web
npm run web
```

## 📱 Pantallas Disponibles

### 1. **LoginScreen** - Autenticación
- Login de estudiantes/padres
- Validación de credenciales
- Almacenamiento seguro de tokens

### 2. **MenuScreen** - Menú Principal
- Vista de productos del día
- Categorización de productos
- Agregar al carrito
- Navegación a otras secciones

### 3. **AccountScreen** - Cuenta y Saldo ⭐ MEJORADO
**Funcionalidades:**
- ✅ Visualización de saldo actual
- ✅ Tarjeta NFC asociada
- ✅ Reportes de consumo detallados
- ✅ Historial de recargas
- ✅ Resumen mensual (recargas vs consumos)
- ✅ **NUEVO: Botón "Cargar Saldo con QR SIPAP"**
  - Integración completa con SIPAP (Sistema de Pagos del Paraguay)
  - Pago desde cualquier banco con QR
  - Compatible con Zimple, Continental, Atlas, Itaú, BNF, BBVA, etc.

**Pantalla de cuenta incluye:**
```
┌─────────────────────────────┐
│   Saldo disponible          │
│   Gs. 125.000               │
│   Tarjeta: 1234567890       │
└─────────────────────────────┘
┌─────────────────────────────┐
│ 📱 Cargar Saldo con QR      │
│ 🇵🇾 Paga desde cualquier... │
└─────────────────────────────┘
┌──────────┬──────────────────┐
│ Recargas │ Consumos del mes │
│ Gs. ...  │ Gs. ...          │
└──────────┴──────────────────┘
Últimos movimientos
├─ 💳 Recarga - Gs. 50.000
├─ 🛒 Consumo - Gs. 8.500
└─ ...
```

### 4. **SIPAPPaymentScreen** ⭐ NUEVO
**Pantalla completa de pago con QR SIPAP**

#### Flujo de uso:
1. **Paso 1: Ingreso de monto**
   - Input de monto a cargar (mínimo Gs. 10.000)
   - Sugerencias: Gs. 50.000 - 100.000
   - Descripción opcional
   - Validaciones de monto

2. **Paso 2: Generación de QR**
   - QR generado dinámicamente (válido 15 minutos)
   - Countdown timer visible
   - Monto y descripción claramente mostrados
   - Instrucciones paso a paso para pagar

3. **Paso 3: Confirmación automática**
   - Polling automático cada 3 segundos
   - Notificación visual de "Esperando confirmación..."
   - Confirmación instantánea cuando el banco procesa el pago

4. **Paso 4: Resultado**
   - ✅ Éxito: Pantalla de confirmación con monto
   - ❌ Error: Mensaje de error con opción de reintentar
   - ⏰ Expirado: Opción de generar nuevo QR

#### Características técnicas:
- Integración con endpoint `/api/v1/cobros/generar_qr_sipap/`
- Polling inteligente con timeout de 15 minutos
- Manejo de estados: pendiente, aprobado, rechazado, expirado
- UX optimizada para mobile
- Imágenes QR en base64 renderizadas nativamente

### 5. **CartScreen** - Carrito de Compras
- Ver productos seleccionados
- Modificar cantidades
- Calcular total
- Confirmar pedido

### 6. **ProfileScreen** - Perfil de Usuario
- Información del usuario
- Foto de perfil (con opción de actualizar)
- Selección de hijo/estudiante
- Acceso a restricciones alimentarias

### 7. **RestrictionsScreen** - Restricciones Alimentarias
- Lista de alergias/restricciones del estudiante
- Niveles de severidad (Crítica, Alta, Media, Baja)
- Navegación a agregar nueva restricción

### 8. **AddRestrictionScreen** - Agregar Restricción
- Formulario para nueva restricción
- Selección de nivel de severidad
- Notas adicionales

## 🔐 Servicios

### `api.js`
Cliente Axios configurado con:
- Base URL del backend
- Interceptores de autenticación
- Manejo de tokens JWT

### `auth.service.js`
- `login(username, password)` - Autenticación
- `logout()` - Cerrar sesión
- `isAuthenticated()` - Verificar sesión
- `getToken()` - Obtener token JWT
- Almacenamiento seguro con SecureStore

### `sipap.service.js` ⭐ NUEVO
**Servicio completo para integración SIPAP**

#### Métodos disponibles:
```javascript
// Generar QR para carga de saldo
generarQRCargaSaldo(idCliente, monto, descripcion)

// Consultar estado de un pago
consultarEstadoPago(txnId)

// Polling para esperar confirmación
esperarConfirmacion(txnId, onUpdate, intervaloMs, maxIntentos)

// Utilidades de formateo
formatearMonto(monto)          // "Gs. 125.000"
calcularTiempoRestante(expiraAt) // segundos
formatearTiempo(segundos)      // "14:35"
```

## 🎨 Diseño y UX

### Colores principales:
- **Primario**: `#2196F3` (Azul - headers, botones principales)
- **Secundario**: `#F59E0B` (Ámbar - saldo, alertas)
- **Éxito**: `#10B981` (Verde - SIPAP, recargas)
- **Error**: `#EF4444` (Rojo - errores)
- **Fondo**: `#F9FAFB` (Gris claro)

### Componentes de UI:
- Cards con elevación y sombras
- Botones con gradientes
- Iconos de Material Icons y FontAwesome5
- Inputs con validación visual
- Loading states con ActivityIndicator

## 🔄 Integración con Backend

### Endpoints utilizados:

#### Cuenta y Saldo:
```
GET /api/v1/tarjetas/?id_hijo={hijoId}
GET /api/v1/recargas/?nro_tarjeta={nro}
GET /api/v1/consumos/?nro_tarjeta={nro}
```

#### SIPAP QR: ⭐
```
POST /api/v1/cobros/generar_qr_sipap/
Body: {
  id_cliente: number,
  monto: number,
  descripcion: string
}

GET /api/v1/cobros/estado_pago_sipap/{txnId}/
```

#### Restricciones:
```
GET /api/v1/hijos/{hijoId}/
GET /api/v1/hijos/?id_cliente_responsable={userId}
```

## 🎯 Casos de Uso Principales

### 1. Carga de Saldo con QR SIPAP
**Actor:** Padre/Tutor  
**Flujo:**
1. Abre la app y navega a "Mi Cuenta"
2. Ve el saldo actual de su hijo
3. Presiona "Cargar Saldo con QR"
4. Ingresa monto (ej: Gs. 50.000)
5. Presiona "Generar QR"
6. Abre su app bancaria (Zimple, Continental, etc.)
7. Escanea el QR mostrado
8. Confirma el pago en su banco
9. La app automáticamente detecta el pago
10. Saldo actualizado instantáneamente

**Beneficios:**
- ✅ No necesita transferencia bancaria manual
- ✅ Confirmación instantánea
- ✅ Funciona con cualquier banco paraguayo
- ✅ Sin comisiones adicionales
- ✅ QR válido por 15 minutos

### 2. Consulta de Movimientos
**Actor:** Padre/Tutor  
**Flujo:**
1. Abre "Mi Cuenta"
2. Ve resumen mensual: recargas vs consumos
3. Scroll hacia abajo para ver historial detallado
4. Cada movimiento muestra:
   - Tipo (recarga 💳 o consumo 🛒)
   - Fecha
   - Monto
5. Pull-to-refresh para actualizar datos

### 3. Gestión de Restricciones Alimentarias
**Actor:** Padre/Tutor  
**Flujo:**
1. Navega a "Perfil"
2. Selecciona hijo
3. Presiona "Restricciones"
4. Ve lista de alergias/restricciones
5. Presiona "+" para agregar nueva
6. Selecciona severidad (Crítica, Alta, Media, Baja)
7. Agrega notas adicionales
8. Guarda restricción

## 🧪 Testing

### Comandos de prueba:
```bash
# Verificar que las dependencias están instaladas
npm ls

# Limpiar caché de Expo
expo start -c

# Ver logs en tiempo real
expo start --dev-client
```

### Credenciales de prueba (Backend en desarrollo):
```
Usuario: juangarcia
Password: Portal123!
```

## 📋 Checklist de Funcionalidades

### Implementado ✅
- [x] Login y autenticación
- [x] Vista de menú de productos
- [x] Carrito de compras
- [x] Perfil de usuario
- [x] Cuenta y saldo actual
- [x] Historial de recargas
- [x] Historial de consumos
- [x] Reportes mensuales
- [x] Restricciones alimentarias
- [x] **Integración SIPAP QR completa**
- [x] **Carga de saldo con QR**
- [x] **Polling automático de confirmación**
- [x] **Manejo de estados de pago**

### Pendiente / Futuras Mejoras 🚧
- [ ] Notificaciones push (cuando el pago se confirma)
- [ ] Historial de pagos SIPAP realizados
- [ ] Compartir QR por WhatsApp
- [ ] Modo oscuro
- [ ] Biometría para login
- [ ] Estadísticas de consumo con gráficos
- [ ] Límites de gasto configurable
- [ ] Alertas de saldo bajo

## 🔒 Seguridad

- Tokens JWT almacenados en SecureStore
- Comunicación HTTPS con backend
- Validación de certificados SSL
- Timeout automático de sesión
- Sanitización de inputs

## 🌐 Configuración de Backend

**Actualizar la URL del backend:**

Editar `mobile/src/services/api.js`:
```javascript
const API_URL = 'http://TU_IP:8000/api/v1'; // Desarrollo
// const API_URL = 'https://api.cantinatita.com/api/v1'; // Producción
```

## 📦 Publicación

### Android (APK/AAB):
```bash
expo build:android
```

### iOS (IPA):
```bash
expo build:ios
```

### Expo Go (Desarrollo):
```bash
expo publish
```

## 🤝 Soporte

Para problemas con SIPAP QR:
1. Verificar que el backend tiene configuradas las credenciales de Banco Continental
2. Verificar que el endpoint `/cobros/generar_qr_sipap/` responde correctamente
3. Revisar logs del backend para errores de integración

## 📝 Notas Importantes

⚠️ **SIPAP QR requiere:**
- Backend configurado con credenciales de Banco Continental
- Webhook URL registrada en Continental
- Certificados SSL en producción
- IP del servidor whitelistada por Continental

📄 **Documentación adicional:**
- Ver `backend/README_SIPAP.md` para configuración del backend
- Ver `backend/IMPLEMENTACION_SIPAP_QR.md` para detalles técnicos
