import { renderHook, act, waitFor } from '@testing-library/react';
import { useFetch } from './useFetch';

describe('useFetch', () => {
  describe('estado inicial', () => {
    it('comienza en estado de carga', () => {
      const fetchFn = vi.fn().mockResolvedValue({ items: [] });
      const { result } = renderHook(() => useFetch(fetchFn));

      expect(result.current.loading).toBe(true);
      expect(result.current.data).toBeNull();
      expect(result.current.error).toBeNull();
    });
  });

  describe('carga exitosa', () => {
    it('actualiza data cuando fetch es exitoso', async () => {
      const mockData = { items: [1, 2, 3] };
      const fetchFn = vi.fn().mockResolvedValue(mockData);

      const { result } = renderHook(() => useFetch(fetchFn));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.data).toEqual(mockData);
      expect(result.current.error).toBeNull();
    });

    it('llama a fetchFunction al montar', async () => {
      const fetchFn = vi.fn().mockResolvedValue([]);

      renderHook(() => useFetch(fetchFn));

      await waitFor(() => {
        expect(fetchFn).toHaveBeenCalledTimes(1);
      });
    });

    it('maneja arrays vacios correctamente', async () => {
      const fetchFn = vi.fn().mockResolvedValue([]);

      const { result } = renderHook(() => useFetch(fetchFn));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.data).toEqual([]);
      expect(result.current.error).toBeNull();
    });
  });

  describe('manejo de errores', () => {
    it('captura Error y expone el mensaje', async () => {
      const fetchFn = vi.fn().mockRejectedValue(new Error('Fallo de red'));

      const { result } = renderHook(() => useFetch(fetchFn));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBe('Fallo de red');
      expect(result.current.data).toBeNull();
    });

    it('usa mensaje generico para errores no-Error', async () => {
      const fetchFn = vi.fn().mockRejectedValue('string error');

      const { result } = renderHook(() => useFetch(fetchFn));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBe('Error al cargar los datos');
    });
  });

  describe('refetch', () => {
    it('recarga los datos al llamar refetch', async () => {
      const mockData = { valor: 42 };
      const fetchFn = vi.fn().mockResolvedValue(mockData);

      const { result } = renderHook(() => useFetch(fetchFn));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      await act(async () => {
        await result.current.refetch();
      });

      expect(fetchFn).toHaveBeenCalledTimes(2);
      expect(result.current.data).toEqual(mockData);
    });

    it('limpia error previo al hacer refetch exitoso', async () => {
      let llamada = 0;
      const fetchFn = vi.fn().mockImplementation(() => {
        llamada++;
        if (llamada === 1) return Promise.reject(new Error('Error inicial'));
        return Promise.resolve({ ok: true });
      });

      const { result } = renderHook(() => useFetch(fetchFn));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBe('Error inicial');

      await act(async () => {
        await result.current.refetch();
      });

      expect(result.current.error).toBeNull();
      expect(result.current.data).toEqual({ ok: true });
    });

    it('actualiza error en refetch fallido', async () => {
      let llamada = 0;
      const fetchFn = vi.fn().mockImplementation(() => {
        llamada++;
        if (llamada === 1) return Promise.resolve({ ok: true });
        return Promise.reject(new Error('Error en refetch'));
      });

      const { result } = renderHook(() => useFetch(fetchFn));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      await act(async () => {
        await result.current.refetch();
      });

      expect(result.current.error).toBe('Error en refetch');
    });
  });

  describe('dependencias', () => {
    it('re-ejecuta fetch cuando cambian las dependencias', async () => {
      const fetchFn = vi.fn().mockResolvedValue([]);
      let dep = 1;

      const { result, rerender } = renderHook(() => useFetch(fetchFn, [dep]));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      dep = 2;
      rerender();

      await waitFor(() => {
        expect(fetchFn).toHaveBeenCalledTimes(2);
      });
    });
  });
});
