import * as SecureStore from 'expo-secure-store';
import axios from 'axios';

const BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
const TOKEN_KEY = 'cantina_auth_token';
const USER_KEY = 'cantina_user';

export async function login(username, password) {
  const response = await axios.post(`${BASE_URL}/auth/login/`, { username, password });
  const { token, user } = response.data;
  await SecureStore.setItemAsync(TOKEN_KEY, token);
  await SecureStore.setItemAsync(USER_KEY, JSON.stringify(user));
  return { token, user };
}

export async function logout() {
  try {
    const token = await getToken();
    if (token) {
      await axios.post(
        `${BASE_URL}/auth/logout/`,
        {},
        { headers: { Authorization: `Token ${token}` } }
      ).catch(() => {});
    }
  } finally {
    await clearToken();
  }
}

export async function getToken() {
  return SecureStore.getItemAsync(TOKEN_KEY);
}

export async function clearToken() {
  await SecureStore.deleteItemAsync(TOKEN_KEY);
  await SecureStore.deleteItemAsync(USER_KEY);
}

export async function getCurrentUser() {
  const raw = await SecureStore.getItemAsync(USER_KEY);
  return raw ? JSON.parse(raw) : null;
}

export async function isAuthenticated() {
  const token = await getToken();
  return !!token;
}
