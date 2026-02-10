/**
 * EJEMPLO: Servicio de Monedas para React + Axios
 * Archivo: src/services/currencyService.js
 */

import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';
const TOKEN = localStorage.getItem('token'); // JWT token

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Authorization': `Bearer ${TOKEN}`,
    'Content-Type': 'application/json',
  },
});

// ==================== CRUD DE MONEDAS ====================

/**
 * Obtener todas las monedas de la empresa
 */
export const getCurrencies = async (params = {}) => {
  const { is_active, skip = 0, limit = 100 } = params;
  const response = await api.get('/currencies/', {
    params: { is_active, skip, limit }
  });
  return response.data;
};

/**
 * Crear nueva moneda
 */
export const createCurrency = async (currencyData) => {
  const response = await api.post('/currencies/', currencyData);
  return response.data;
};

/**
 * Obtener moneda por ID
 */
export const getCurrency = async (currencyId) => {
  const response = await api.get(`/currencies/${currencyId}`);
  return response.data;
};

/**
 * Actualizar moneda
 */
export const updateCurrency = async (currencyId, data) => {
  const response = await api.put(`/currencies/${currencyId}`, data);
  return response.data;
};

/**
 * Eliminar moneda (soft delete)
 */
export const deleteCurrency = async (currencyId) => {
  const response = await api.delete(`/currencies/${currencyId}`);
  return response.data;
};

// ==================== TASAS DE CAMBIO ====================

/**
 * Actualizar tasa de cambio (crea registro histórico)
 */
export const updateCurrencyRate = async (currencyId, rateUpdate) => {
  const response = await api.put(`/currencies/${currencyId}/rate`, rateUpdate);
  return response.data;
};

/**
 * Obtener historial de cambios de tasa
 */
export const getRateHistory = async (currencyId, limit = 100) => {
  const response = await api.get(`/currencies/${currencyId}/rate/history`, {
    params: { limit }
  });
  return response.data;
};

/**
 * Obtener estadísticas de moneda
 */
export const getCurrencyStatistics = async (currencyId) => {
  const response = await api.get(`/currencies/${currencyId}/statistics`);
  return response.data;
};

// ==================== CONVERSIÓN ====================

/**
 * Convertir monto entre monedas
 * @param {string} fromCurrency - Moneda origen (ej: "USD")
 * @param {string} toCurrency - Moneda destino (ej: "VES")
 * @param {number} amount - Monto a convertir
 */
export const convertCurrency = async (fromCurrency, toCurrency, amount) => {
  const response = await api.get('/currencies/convert', {
    params: {
      from_currency: fromCurrency,
      to_currency: toCurrency,
      amount: amount,
    }
  });
  return response.data;
};

// ==================== IGTF ====================

/**
 * Calcular IGTF para una transacción
 * @param {number} amount - Monto en moneda extranjera
 * @param {number} currencyId - ID de moneda
 * @param {string} paymentMethod - Método de pago (transfer, cash, etc.)
 */
export const calculateIGTF = async (amount, currencyId, paymentMethod = 'transfer') => {
  const response = await api.post('/currencies/igtf/calculate', null, {
    params: {
      amount: amount,
      currency_id: currencyId,
      payment_method: paymentMethod,
    }
  });
  return response.data;
};

/**
 * Obtener configuraciones IGTF de la empresa
 */
export const getIGTFConfigs = async (currencyId = null) => {
  const response = await api.get('/currencies/igtf/config', {
    params: { currency_id: currencyId }
  });
  return response.data;
};

/**
 * Crear configuración personalizada de IGTF
 */
export const createIGTFConfig = async (configData) => {
  const response = await api.post('/currencies/igtf/config', configData);
  return response.data;
};

// ==================== UTILIDADES ====================

/**
 * Obtener factores de conversión de todas las monedas
 */
export const getConversionFactors = async () => {
  const response = await api.get('/currencies/factors');
  return response.data;
};

/**
 * Validar código ISO 4217
 * @param {string} code - Código de 3 letras (ej: "USD")
 */
export const validateISOCode = async (code) => {
  const response = await api.post('/currencies/validate/iso-4217', null, {
    params: { code }
  });
  return response.data;
};

// ==================== EJEMPLOS DE USO ====================

/**
 * Ejemplo 1: Crear moneda USD
 */
export const exampleCreateUSD = async () => {
  try {
    const usd = await createCurrency({
      code: "USD",
      name: "US Dollar",
      symbol: "$",
      exchange_rate: "36.5000000000",
      decimal_places: 2,
      is_base_currency: false,
      conversion_method: "direct",
      applies_igtf: true,
      igtf_rate: "3.00",
      igtf_min_amount: "1000.00",
      rate_update_method: "api_bcv",
      rate_source_url: "https://www.bcv.org.ve"
    });
    console.log('USD creado:', usd);
    return usd;
  } catch (error) {
    console.error('Error creando USD:', error.response?.data || error.message);
    throw error;
  }
};

/**
 * Ejemplo 2: Actualizar tasa con historial
 */
export const exampleUpdateRate = async (currencyId) => {
  try {
    const updated = await updateCurrencyRate(currencyId, {
      new_rate: "37.5000000000",
      change_reason: "Actualización diaria BCV",
      change_type: "automatic_api",
      change_source: "api_bcv"
    });
    console.log('Tasa actualizada:', updated);
    return updated;
  } catch (error) {
    console.error('Error actualizando tasa:', error.response?.data);
    throw error;
  }
};

/**
 * Ejemplo 3: Convertir $100 USD a VES
 */
export const exampleConvert = async () => {
  try {
    const result = await convertCurrency("USD", "VES", 100);
    console.log('Conversión:', result);
    // Resultado:
    // {
    //   original_amount: 100.0,
    //   original_currency: "USD",
    //   converted_amount: 3650.0,
    //   target_currency: "VES",
    //   exchange_rate_used: 36.5,
    //   conversion_method: "direct",
    //   rate_metadata: { ... }
    // }
    return result;
  } catch (error) {
    console.error('Error en conversión:', error.response?.data);
    throw error;
  }
};

/**
 * Ejemplo 4: Calcular IGTF para pago de $1500
 */
export const exampleCalculateIGTF = async (currencyId) => {
  try {
    const igtf = await calculateIGTF(1500, currencyId, 'transfer');
    console.log('IGTF:', igtf);
    // Resultado:
    // {
    //   original_amount: 1500.0,
    //   igtf_amount: 45.0,
    //   igtf_applied: true,
    //   total_with_igtf: 1545.0,
    //   metadata: {
    //     currency_code: "USD",
    //     applies: true,
    //     rate: 3.0,
    //     reason: "IGTF 3.0% aplicado"
    //   }
    // }
    return igtf;
  } catch (error) {
    console.error('Error calculando IGTF:', error.response?.data);
    throw error;
  }
};
