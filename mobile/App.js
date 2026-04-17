import React, { useState, useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar } from 'expo-status-bar';
import { ActivityIndicator, View } from 'react-native';

import LoginScreen from './src/screens/LoginScreen';
import MenuScreen from './src/screens/MenuScreen';
import CartScreen from './src/screens/CartScreen';
import ProfileScreen from './src/screens/ProfileScreen';
import RestrictionsScreen from './src/screens/RestrictionsScreen';
import AddRestrictionScreen from './src/screens/AddRestrictionScreen';
import AccountScreen from './src/screens/AccountScreen';
import SIPAPPaymentScreen from './src/screens/SIPAPPaymentScreen';
import { isAuthenticated } from './src/services/auth.service';

const Stack = createNativeStackNavigator();

export default function App() {
  const [isReady, setIsReady] = useState(false);
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    isAuthenticated().then((auth) => {
      setLoggedIn(auth);
      setIsReady(true);
    });
  }, []);

  if (!isReady) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#E3F2FD' }}>
        <ActivityIndicator size="large" color="#2196F3" />
      </View>
    );
  }

  return (
    <NavigationContainer>
      <StatusBar style="auto" />
      <Stack.Navigator
        initialRouteName={loggedIn ? 'Menu' : 'Login'}
        screenOptions={{
          headerStyle: { backgroundColor: '#2196F3' },
          headerTintColor: '#fff',
          headerTitleStyle: { fontWeight: 'bold' },
        }}
      >
        <Stack.Screen
          name="Login"
          component={LoginScreen}
          options={{ title: 'Cantina Tita', headerShown: false }}
        />
        <Stack.Screen
          name="Menu"
          component={MenuScreen}
          options={{ title: 'Menú del Día' }}
        />
        <Stack.Screen
          name="Cart"
          component={CartScreen}
          options={{ title: 'Mi Pedido' }}
        />
        <Stack.Screen
          name="Profile"
          component={ProfileScreen}
          options={{ title: 'Perfil', headerShown: false }}
        />
        <Stack.Screen
          name="Restrictions"
          component={RestrictionsScreen}
          options={{ title: 'Restricciones', headerShown: false }}
        />
        <Stack.Screen
          name="AddRestriction"
          component={AddRestrictionScreen}
          options={{ title: 'Restricción', headerShown: false }}
        />
        <Stack.Screen
          name="Account"
          component={AccountScreen}
          options={{ title: 'Mi Cuenta', headerBackTitle: 'Volver' }}
        />
        <Stack.Screen
          name="SIPAPPayment"
          component={SIPAPPaymentScreen}
          options={{ title: 'Pago SIPAP QR', headerBackTitle: 'Volver' }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
