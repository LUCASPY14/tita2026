/**
 * Manual Jest mock for src/services/api.ts
 * Bypasses import.meta.env (Vite-specific) which Jest/CRA cannot parse.
 */
import axios from 'axios';

const api = axios.create({ baseURL: 'http://localhost:8000/api/v1' });

export default api;
