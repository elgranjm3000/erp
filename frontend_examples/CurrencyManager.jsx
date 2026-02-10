/**
 * COMPONENTE REACT COMPLETO
 * Gestión de Monedas con IGTF y Conversión
 * Archivo: src/components/CurrencyManager.jsx
 */

import React, { useState, useEffect } from 'react';
import {
  getCurrencies,
  createCurrency,
  updateCurrencyRate,
  convertCurrency,
  calculateIGTF,
  getRateHistory
} from '../services/currencyService';

const CurrencyManager = () => {
  // Estados
  const [currencies, setCurrencies] = useState([]);
  const [selectedCurrency, setSelectedCurrency] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Estados para conversión
  const [fromCurrency, setFromCurrency] = useState('USD');
  const [toCurrency, setToCurrency] = useState('VES');
  const [amount, setAmount] = useState(100);
  const [conversionResult, setConversionResult] = useState(null);

  // Estados para IGTF
  const [igtfAmount, setIgtfAmount] = useState(1000);
  const [igtfResult, setIgtfResult] = useState(null);

  // Estados para actualizar tasa
  const [newRate, setNewRate] = useState('');
  const [rateReason, setRateReason] = useState('');

  // Cargar monedas al montar
  useEffect(() => {
    loadCurrencies();
  }, []);

  const loadCurrencies = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getCurrencies();
      setCurrencies(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error cargando monedas');
    } finally {
      setLoading(false);
    }
  };

  // ==================== CONVERSIÓN ====================

  const handleConvert = async () => {
    if (!fromCurrency || !toCurrency || !amount) return;

    setLoading(true);
    try {
      const result = await convertCurrency(fromCurrency, toCurrency, amount);
      setConversionResult(result);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error en conversión');
    } finally {
      setLoading(false);
    }
  };

  // ==================== IGTF ====================

  const handleCalculateIGTF = async () => {
    if (!selectedCurrency || !igtfAmount) return;

    setLoading(true);
    try {
      const result = await calculateIGTF(
        igtfAmount,
        selectedCurrency.id,
        'transfer'
      );
      setIgtfResult(result);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error calculando IGTF');
    } finally {
      setLoading(false);
    }
  };

  // ==================== ACTUALIZAR TASA ====================

  const handleUpdateRate = async () => {
    if (!selectedCurrency || !newRate) return;

    setLoading(true);
    try {
      await updateCurrencyRate(selectedCurrency.id, {
        new_rate: newRate,
        change_reason: rateReason || 'Actualización manual',
        change_type: 'manual',
        change_source: 'user_admin'
      });
      await loadCurrencies(); // Recargar
      setNewRate('');
      setRateReason('');
      alert('✅ Tasa actualizada correctamente');
    } catch (err) {
      setError(err.response?.data?.detail || 'Error actualizando tasa');
    } finally {
      setLoading(false);
    }
  };

  // ==================== RENDERIZADO ====================

  return (
    <div className="currency-manager container">
      <h1 className="text-3xl font-bold mb-6">
        🇻🇪 Gestión de Monedas - Venezuela
      </h1>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {/* Lista de Monedas */}
      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">💰 Monedas Configuradas</h2>

        {loading ? (
          <p>Cargando...</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {currencies.map((currency) => (
              <div
                key={currency.id}
                className={`p-4 border rounded-lg cursor-pointer transition ${
                  selectedCurrency?.id === currency.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-300 hover:border-blue-300'
                }`}
                onClick={() => setSelectedCurrency(currency)}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-xl font-bold">
                      {currency.symbol} {currency.code}
                    </h3>
                    <p className="text-gray-600">{currency.name}</p>
                  </div>
                  {currency.is_base_currency && (
                    <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-sm">
                      BASE
                    </span>
                  )}
                </div>

                <div className="mt-3 space-y-1">
                  <p className="text-sm">
                    <span className="font-semibold">Tasa:</span> {currency.exchange_rate}
                  </p>
                  {currency.applies_igtf && (
                    <p className="text-sm">
                      <span className="font-semibold">IGTF:</span> {currency.igtf_rate}%
                    </p>
                  )}
                  <p className="text-sm">
                    <span className="font-semibold">Método:</span> {currency.conversion_method || 'N/A'}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Conversor de Monedas */}
      <section className="mb-8 bg-gray-50 p-6 rounded-lg">
        <h2 className="text-2xl font-semibold mb-4">💱 Conversor de Monedas</h2>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">De:</label>
            <select
              className="w-full p-2 border rounded"
              value={fromCurrency}
              onChange={(e) => setFromCurrency(e.target.value)}
            >
              {currencies.map((c) => (
                <option key={c.id} value={c.code}>
                  {c.code} - {c.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">A:</label>
            <select
              className="w-full p-2 border rounded"
              value={toCurrency}
              onChange={(e) => setToCurrency(e.target.value)}
            >
              {currencies.map((c) => (
                <option key={c.id} value={c.code}>
                  {c.code} - {c.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Monto:</label>
            <input
              type="number"
              className="w-full p-2 border rounded"
              value={amount}
              onChange={(e) => setAmount(parseFloat(e.target.value))}
              min="0"
              step="0.01"
            />
          </div>

          <div className="flex items-end">
            <button
              onClick={handleConvert}
              disabled={loading}
              className="w-full bg-blue-600 text-white p-2 rounded hover:bg-blue-700 disabled:opacity-50"
            >
              Convertir
            </button>
          </div>
        </div>

        {conversionResult && (
          <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded">
            <p className="text-lg">
              <strong>{conversionResult.original_amount} {conversionResult.original_currency}</strong> =
            </p>
            <p className="text-2xl font-bold text-green-700">
              {conversionResult.converted_amount.toFixed(2)} {conversionResult.target_currency}
            </p>
            <p className="text-sm text-gray-600 mt-2">
              Tasa usada: {conversionResult.exchange_rate_used} ({conversionResult.conversion_method})
            </p>
          </div>
        )}
      </section>

      {/* Calculadora IGTF */}
      <section className="mb-8 bg-yellow-50 p-6 rounded-lg">
        <h2 className="text-2xl font-semibold mb-4">💳 Calculadora IGTF</h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Moneda:</label>
            <select
              className="w-full p-2 border rounded"
              value={selectedCurrency?.id || ''}
              onChange={(e) => {
                const currency = currencies.find(c => c.id === parseInt(e.target.value));
                setSelectedCurrency(currency);
              }}
            >
              <option value="">Seleccionar...</option>
              {currencies
                .filter(c => c.applies_igtf)
                .map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.code} - {c.name} (IGTF {c.igtf_rate}%)
                  </option>
                ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Monto:</label>
            <input
              type="number"
              className="w-full p-2 border rounded"
              value={igtfAmount}
              onChange={(e) => setIgtfAmount(parseFloat(e.target.value))}
              min="0"
              step="0.01"
            />
          </div>

          <div className="flex items-end">
            <button
              onClick={handleCalculateIGTF}
              disabled={loading || !selectedCurrency}
              className="w-full bg-yellow-600 text-white p-2 rounded hover:bg-yellow-700 disabled:opacity-50"
            >
              Calcular IGTF
            </button>
          </div>
        </div>

        {igtfResult && (
          <div className="mt-4 p-4 bg-white border border-yellow-200 rounded">
            {igtfResult.igtf_applied ? (
              <>
                <p className="text-lg">
                  <strong>Original:</strong> {igtfResult.original_amount} {selectedCurrency?.code}
                </p>
                <p className="text-lg text-red-600">
                  <strong>IGTF ({igtfResult.metadata.rate}%):</strong> {igtfResult.igtf_amount} {selectedCurrency?.code}
                </p>
                <p className="text-2xl font-bold text-red-700">
                  TOTAL: {igtfResult.total_with_igtf} {selectedCurrency?.code}
                </p>
              </>
            ) : (
              <p className="text-green-700">
                ✅ {igtfResult.metadata.reason}
              </p>
            )}
          </div>
        )}
      </section>

      {/* Actualizar Tasa */}
      {selectedCurrency && (
        <section className="mb-8 bg-blue-50 p-6 rounded-lg">
          <h2 className="text-2xl font-semibold mb-4">📊 Actualizar Tasa: {selectedCurrency.code}</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Nueva Tasa:</label>
              <input
                type="number"
                className="w-full p-2 border rounded"
                value={newRate}
                onChange={(e) => setNewRate(e.target.value)}
                step="0.0000000001"
                min="0"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Razón:</label>
              <input
                type="text"
                className="w-full p-2 border rounded"
                value={rateReason}
                onChange={(e) => setRateReason(e.target.value)}
                placeholder="Ej: Actualización BCV"
              />
            </div>

            <div className="flex items-end">
              <button
                onClick={handleUpdateRate}
                disabled={loading || !newRate}
                className="w-full bg-blue-600 text-white p-2 rounded hover:bg-blue-700 disabled:opacity-50"
              >
                Actualizar Tasa
              </button>
            </div>
          </div>

          <div className="mt-4 text-sm text-gray-600">
            <p>Tasa actual: <strong>{selectedCurrency.exchange_rate}</strong></p>
            <p>Última actualización: {new Date(selectedCurrency.last_rate_update).toLocaleString()}</p>
          </div>
        </section>
      )}
    </div>
  );
};

export default CurrencyManager;
