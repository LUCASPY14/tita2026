import * as SecureStore from 'expo-secure-store';
import axios from 'axios';
import {
  login,
  logout,
  getToken,
  clearToken,
  getCurrentUser,
  isAuthenticated,
} from '../auth.service';

jest.mock('axios');
jest.mock('expo-secure-store');

describe('Auth Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('login', () => {
    it('should login successfully and store token and user', async () => {
      const mockToken = 'test-token';
      const mockUser = { id: 1, username: 'testuser', email: 'test@example.com' };
      
      axios.post.mockResolvedValue({
        data: { token: mockToken, user: mockUser },
      });

      const result = await login('testuser', 'password123');

      expect(axios.post).toHaveBeenCalledWith(
        expect.stringContaining('/auth/login/'),
        { username: 'testuser', password: 'password123' }
      );
      expect(SecureStore.setItemAsync).toHaveBeenCalledWith('cantina_auth_token', mockToken);
      expect(SecureStore.setItemAsync).toHaveBeenCalledWith(
        'cantina_user',
        JSON.stringify(mockUser)
      );
      expect(result).toEqual({ token: mockToken, user: mockUser });
    });

    it('should throw error on login failure', async () => {
      axios.post.mockRejectedValue(new Error('Invalid credentials'));

      await expect(login('baduser', 'badpass')).rejects.toThrow('Invalid credentials');
    });
  });

  describe('logout', () => {
    it('should logout and clear tokens', async () => {
      const mockToken = 'test-token';
      SecureStore.getItemAsync.mockResolvedValue(mockToken);
      axios.post.mockResolvedValue({ data: {} });

      await logout();

      expect(axios.post).toHaveBeenCalledWith(
        expect.stringContaining('/auth/logout/'),
        {},
        { headers: { Authorization: `Token ${mockToken}` } }
      );
      expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('cantina_auth_token');
      expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('cantina_user');
    });

    it.skip('should clear tokens even if API call fails', async () => {
      SecureStore.getItemAsync.mockResolvedValue('test-token');
      axios.post.mockRejectedValue(new Error());

      await logout();

      expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('cantina_auth_token');
      expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('cantina_user');
    });

    it('should clear tokens when no token exists', async () => {
      SecureStore.getItemAsync.mockResolvedValue(null);

      await logout();

      expect(axios.post).not.toHaveBeenCalled();
      expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('cantina_auth_token');
      expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('cantina_user');
    });
  });

  describe('getToken', () => {
    it('should return stored token', async () => {
      const mockToken = 'test-token-123';
      SecureStore.getItemAsync.mockResolvedValue(mockToken);

      const token = await getToken();

      expect(SecureStore.getItemAsync).toHaveBeenCalledWith('cantina_auth_token');
      expect(token).toBe(mockToken);
    });

    it('should return null when no token stored', async () => {
      SecureStore.getItemAsync.mockResolvedValue(null);

      const token = await getToken();

      expect(token).toBeNull();
    });
  });

  describe('clearToken', () => {
    it('should delete both token and user data', async () => {
      await clearToken();

      expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('cantina_auth_token');
      expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('cantina_user');
    });
  });

  describe('getCurrentUser', () => {
    it('should return parsed user data', async () => {
      const mockUser = { id: 1, username: 'testuser', email: 'test@example.com' };
      SecureStore.getItemAsync.mockResolvedValue(JSON.stringify(mockUser));

      const user = await getCurrentUser();

      expect(SecureStore.getItemAsync).toHaveBeenCalledWith('cantina_user');
      expect(user).toEqual(mockUser);
    });

    it('should return null when no user data stored', async () => {
      SecureStore.getItemAsync.mockResolvedValue(null);

      const user = await getCurrentUser();

      expect(user).toBeNull();
    });

    it('should handle invalid JSON', async () => {
      SecureStore.getItemAsync.mockResolvedValue('invalid-json');

      await expect(getCurrentUser()).rejects.toThrow();
    });
  });

  describe('isAuthenticated', () => {
    it('should return true when token exists', async () => {
      SecureStore.getItemAsync.mockResolvedValue('test-token');

      const result = await isAuthenticated();

      expect(result).toBe(true);
    });

    it('should return false when no token', async () => {
      SecureStore.getItemAsync.mockResolvedValue(null);

      const result = await isAuthenticated();

      expect(result).toBe(false);
    });
  });
});
