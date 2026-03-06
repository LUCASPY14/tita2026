/**
 * Tests para hook useDebounce
 * Tests de funcionalidad de debounce
 */
import { renderHook, act } from '@testing-library/react';
import { useDebounce } from '../../src/hooks/useDebounce';

describe('🧪 useDebounce Hook Tests', () => {
  
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test('✅ CRÍTICO: should return initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('initial', 300));
    
    expect(result.current).toBe('initial');
  });

  test('✅ CRÍTICO: should debounce value changes', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'initial', delay: 300 } }
    );
    
    expect(result.current).toBe('initial');
    
    // Cambiar el valor
    rerender({ value: 'changed', delay: 300 });
    
    // Inmediatamente, el valor no debe cambiar
    expect(result.current).toBe('initial');
    
    // Avanzar el tiempo menos del delay
    act(() => {
      jest.advanceTimersByTime(200);
    });
    expect(result.current).toBe('initial');
    
    // Avanzar el tiempo completo
    act(() => {
      jest.advanceTimersByTime(100);
    });
    expect(result.current).toBe('changed');
  });

  test('✅ CRÍTICO: should reset timer on rapid changes', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'initial', delay: 300 } }
    );
    
    // Primera cambio
    rerender({ value: 'change1', delay: 300 });
    
    // Avanzar solo 100ms
    act(() => {
      jest.advanceTimersByTime(100);
    });
    
    // Segundo cambio antes que se complete el debounce
    rerender({ value: 'change2', delay: 300 });
    
    // El valor aún debe ser initial
    expect(result.current).toBe('initial');
    
    // Avanzar el tiempo completo
    act(() => {
      jest.advanceTimersByTime(300);
    });
    
    // Ahora debe ser el último valor
    expect(result.current).toBe('change2');
  });

  test('✅ CRÍTICO: should use default delay of 500ms when not provided', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value),
      { initialProps: { value: 'initial' } }
    );
    
    rerender({ value: 'changed' });
    
    // Con delay por defecto (500ms)
    act(() => {
      jest.advanceTimersByTime(499);
    });
    expect(result.current).toBe('initial');
    
    act(() => {
      jest.advanceTimersByTime(1);
    });
    expect(result.current).toBe('changed');
  });

  test('✅ CRÍTICO: should handle number values', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: 0 } }
    );
    
    expect(result.current).toBe(0);
    
    rerender({ value: 100 });
    
    act(() => {
      jest.advanceTimersByTime(300);
    });
    
    expect(result.current).toBe(100);
  });

  test('✅ CRÍTICO: should cleanup on unmount', () => {
    const { unmount } = renderHook(() => useDebounce('test', 300));
    
    // No debe lanzar error al desmontar
    expect(() => unmount()).not.toThrow();
  });
});
