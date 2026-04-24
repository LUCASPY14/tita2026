import api from '../api';
import * as authService from '../auth.service';

jest.mock('../auth.service');

describe('API Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should create axios instance with correct config', () => {
    expect(api).toBeDefined();
    expect(api.defaults).toBeDefined();
    expect(api.defaults.timeout).toBe(10000);
  });

  it('should have baseURL configured', () => {
    expect(api.defaults.baseURL).toBeDefined();
  });

  it('should have default content-type header', () => {
    expect(api.defaults.headers['Content-Type']).toBe('application/json');
  });

  describe('API methods', () => {
    it('should have get method', () => {
      expect(typeof api.get).toBe('function');
    });

    it('should have post method', () => {
      expect(typeof api.post).toBe('function');
    });

    it('should have put method', () => {
      expect(typeof api.put).toBe('function');
    });

    it('should have delete method', () => {
      expect(typeof api.delete).toBe('function');
    });
  });
});
