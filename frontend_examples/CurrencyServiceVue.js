/**
 * EJEMPLO: Servicio de Monedas para Vue 3
 * Archivo: src/services/currencyService.js
 */

import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Crear instancia de axios
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para agregar token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ==================== API DE MONEDAS ====================

export const currencyApi = {
  /**
   * Obtener todas las monedas
   */
  async getCurrencies(params = {}) {
    const response = await api.get('/currencies/', { params });
    return response.data;
  },

  /**
   * Crear moneda
   */
  async createCurrency(data) {
    const response = await api.post('/currencies/', data);
    return response.data;
  },

  /**
   * Actualizar tasa de cambio
   */
  async updateRate(currencyId, rateData) {
    const response = await api.put(`/currencies/${currencyId}/rate`, rateData);
    return response.data;
  },

  /**
   * Obtener historial de tasas
   */
  async getRateHistory(currencyId, limit = 100) {
    const response = await api.get(`/currencies/${currencyId}/rate/history`, {
      params: { limit }
    });
    return response.data;
  },

  /**
   * Convertir monedas
   */
  async convert(from, to, amount) {
    const response = await api.get('/currencies/convert', {
      params: {
        from_currency: from,
        to_currency: to,
        amount: amount,
      }
    });
    return response.data;
  },

  /**
   * Calcular IGTF
   */
  async calculateIGTF(amount, currencyId, paymentMethod = 'transfer') {
    const response = await api.post('/currencies/igtf/calculate', null, {
      params: {
        amount: amount,
        currency_id: currencyId,
        payment_method: paymentMethod,
      }
    });
    return response.data;
  },

  /**
   * Obtener factores de conversión
   */
  async getFactors() {
    const response = await api.get('/currencies/factors');
    return response.data;
  },

  /**
   * Validar código ISO
   */
  async validateISO(code) {
    const response = await api.post('/currencies/validate/iso-4217', null, {
      params: { code }
    });
    return response.data;
  },
};
