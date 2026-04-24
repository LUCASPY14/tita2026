import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { Alert } from 'react-native';
import CartScreen from '../CartScreen';
import AsyncStorage from '@react-native-async-storage/async-storage';
import api from '../../services/api';

jest.mock('../../services/api');
jest.mock('@react-native-async-storage/async-storage');

describe('CartScreen', () => {
  const mockNavigation = {
    navigate: jest.fn(),
    goBack: jest.fn(),
  };

  const mockRoute = {
    params: {
      cart: [
        { id: 1, nombre: 'Pizza', precio: 25000, cantidad: 2 },
        { id: 2, nombre: 'Refresco', precio: 5000, cantidad: 1 },
      ],
      setCart: jest.fn(),
    },
  };

  beforeEach(() => {
    jest.clearAllMocks();
    jest.spyOn(Alert, 'alert').mockImplementation(() => {});
    AsyncStorage.getItem.mockResolvedValue(null);
    api.get.mockResolvedValue({ data: { results: [] } });
  });

  afterEach(() => {
    Alert.alert.mockRestore();
  });

  it('should render cart items', () => {
    const { getByText } = render(
      <CartScreen navigation={mockNavigation} route={mockRoute} />
    );

    expect(getByText('Pizza')).toBeTruthy();
    expect(getByText('Refresco')).toBeTruthy();
  });

  it('should show empty cart message when no items', () => {
    const emptyRoute = {
      params: {
        cart: [],
        setCart: jest.fn(),
      },
    };

    const { getByText } = render(
      <CartScreen navigation={mockNavigation} route={emptyRoute} />
    );

    expect(getByText(/carrito está vacío/i)).toBeTruthy();
  });

  it('should handle empty route params', () => {
    const emptyRoute = { params: null };

    const { getByText } = render(
      <CartScreen navigation={mockNavigation} route={emptyRoute} />
    );

    expect(getByText(/carrito está vacío/i)).toBeTruthy();
  });

  it('should attempt to load user data on mount', async () => {
    render(<CartScreen navigation={mockNavigation} route={mockRoute} />);

    await waitFor(() => {
      expect(AsyncStorage.getItem).toHaveBeenCalledWith('userInfo');
    });
  });

  it('should render with multiple items', () => {
    const multiItemRoute = {
      params: {
        cart: [
          { id: 1, nombre: 'Item 1', precio: 10000, cantidad: 1 },
          { id: 2, nombre: 'Item 2', precio: 20000, cantidad: 2 },
          { id: 3, nombre: 'Item 3', precio: 15000, cantidad: 1 },
        ],
        setCart: jest.fn(),
      },
    };

    const { getByText } = render(
      <CartScreen navigation={mockNavigation} route={multiItemRoute} />
    );

    expect(getByText('Item 1')).toBeTruthy();
    expect(getByText('Item 2')).toBeTruthy();
    expect(getByText('Item 3')).toBeTruthy();
  });
});
