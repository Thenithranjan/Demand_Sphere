/**
 * Forecast Page — Retail AI Frontend
 * ====================================
 * Exposes AI-powered product demand forecasting from XGBoost models.
 * Includes actual vs predicted charts and seasonal/festival trends.
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, Target, Calendar, Download, Sparkles } from 'lucide-react';
import { useDynamicForecast, useProductForecasts, useProducts } from '../hooks';
import { ForecastLineChart } from '../components/charts';
import StatsCard from '../components/shared/StatsCard';
import SkeletonCard from '../components/shared/SkeletonCard';
import { useTheme } from '../contexts/ThemeContext';
import { cn, formatCurrency, formatNumber, formatPercent, downloadCSV } from '../utils';
import { fadeIn, staggerContainer } from '../animations/variants';

export default function ForecastPage() {
  const { isDark } = useTheme();
  const [selectedProductId, setSelectedProductId] = useState('P0015'); // Default product for demo

  // Get products list for select dropdown
  const { data: productsData } = useProducts({ limit: 100 });
  const selectedProduct = productsData?.items.find((p) => p.ProductID === selectedProductId);

  // Fetch dynamic AI-powered XGBoost forecasts
  const { data: dynamicForecast, isLoading: dynamicLoading, error: dynamicError } = useDynamicForecast(selectedProductId);

  // Fetch historical forecast entries from DB
  const { data: historicalForecasts, isLoading: historyLoading } = useProductForecasts(selectedProductId);

  const handleExport = () => {
    if (!historicalForecasts || historicalForecasts.length === 0) return;
    
    const exportData = historicalForecasts.map(f => ({
      ProductID: f.ProductID,
      YearMonth: f.YearMonth,
      Quantity: f.Quantity,
      Revenue: f.Revenue,
      Category: f.Category,
      Brand: f.Brand,
      Season: f.Season,
      Festival: f.Festival,
      TargetQuantity: f.TargetQuantity,
      TargetRevenue: f.TargetRevenue,
    }));
    
    downloadCSV(exportData, `demand_forecast_${selectedProductId}`);
  };

  return (
    <motion.div variants={fadeIn} initial="hidden" animate="visible" className="space-y-6">
      {/* ─── Page Header ──────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className={cn('text-2xl font-bold', isDark ? 'text-zinc-100' : 'text-zinc-900')}>
            Demand Forecasting
          </h1>
          <p className="text-sm text-zinc-500 mt-1">
            XGBoost ML-driven quantity and revenue projections
          </p>
        </div>

        {/* Product Selector */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-zinc-500 font-medium">Select Product:</span>
          <select
            value={selectedProductId}
            onChange={(e) => setSelectedProductId(e.target.value)}
            className={cn(
              'px-3 py-2 rounded-xl text-sm font-medium outline-none border transition-colors max-w-xs',
              isDark
                ? 'bg-zinc-900 border-zinc-800 text-zinc-200'
                : 'bg-white border-zinc-200 text-zinc-800 shadow-sm'
            )}
          >
            {productsData?.items.map((p) => (
              <option key={p.ProductID} value={p.ProductID}>
                {p.ProductID} — {p.ProductName.slice(0, 30)}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Selected Product info */}
      {selectedProduct && (
        <div className={cn(
          'p-4 rounded-2xl border text-sm flex flex-wrap items-center justify-between gap-4',
          isDark ? 'bg-zinc-900/40 border-zinc-800/80' : 'bg-white border-zinc-200/50 shadow-sm'
        )}>
          <div>
            <h2 className={cn('font-semibold text-base', isDark ? 'text-zinc-200' : 'text-zinc-800')}>
              {selectedProduct.ProductName}
            </h2>
            <p className="text-xs text-zinc-500 mt-0.5">
              Category: {selectedProduct.Category} ({selectedProduct.SubCategory}) | Brand: {selectedProduct.Brand}
            </p>
          </div>
          <div className="text-right">
            <span className="text-zinc-500 text-xs block">Unit Price</span>
            <span className="font-semibold text-emerald-500 text-base">
              {formatCurrency(selectedProduct.Price)}
            </span>
          </div>
        </div>
      )}

      {/* ─── AI Forecast Summary Cards ────────────────────────── */}
      {dynamicLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      ) : dynamicError ? (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl text-sm">
          Failed to compute dynamic forecast: No historical lag sales feature vectors found for this product.
        </div>
      ) : dynamicForecast ? (
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 md:grid-cols-3 gap-4"
        >
          <StatsCard
            title="Next Month Quantity (Projected)"
            value={`${formatNumber(dynamicForecast.next_month_quantity)} Units`}
            icon={TrendingUp}
            gradient="bg-gradient-to-r from-brand-500 to-indigo-500"
          />
          <StatsCard
            title="Next Month Revenue (Projected)"
            value={formatCurrency(dynamicForecast.next_month_revenue)}
            icon={Target}
            gradient="bg-gradient-to-r from-emerald-500 to-teal-500"
          />
          <StatsCard
            title="Forecast Confidence"
            value={formatPercent(dynamicForecast.confidence * 100)}
            icon={Sparkles}
            gradient="bg-gradient-to-r from-violet-500 to-purple-500"
          />
        </motion.div>
      ) : null}

      {/* ─── Forecast Line Chart & Projections ────────────────── */}
      {historyLoading ? (
        <div className="grid grid-cols-1 gap-6">
          <SkeletonCard className="h-80" />
        </div>
      ) : historicalForecasts && historicalForecasts.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Chart Wrapper */}
          <div className="lg:col-span-2">
            <ForecastLineChart data={historicalForecasts} />
          </div>

          {/* Forecast Projections Sidebar */}
          <div className={cn(
            'rounded-2xl p-5 border flex flex-col justify-between',
            isDark ? 'bg-zinc-900/60 border-zinc-800/60 backdrop-blur-xl' : 'bg-white border-zinc-200 shadow-sm'
          )}>
            <div className="space-y-4">
              <h3 className={cn('text-sm font-semibold', isDark ? 'text-zinc-200' : 'text-zinc-800')}>
                Quarter Projections
              </h3>
              <p className="text-xs text-zinc-500 leading-relaxed">
                Calculated based on category-wise seasonality tags and dynamic lag coefficients.
              </p>

              {dynamicForecast && (
                <div className="space-y-3 pt-2">
                  <div className="flex items-center justify-between py-2 border-b">
                    <span className="text-xs text-zinc-500">Next Quarter Quantity</span>
                    <span className={cn('font-semibold text-sm', isDark ? 'text-zinc-200' : 'text-zinc-800')}>
                      {formatNumber(dynamicForecast.next_quarter_quantity)} Units
                    </span>
                  </div>
                  <div className="flex items-center justify-between py-2 border-b">
                    <span className="text-xs text-zinc-500">Next Quarter Revenue</span>
                    <span className="font-semibold text-emerald-500 text-sm">
                      {formatCurrency(dynamicForecast.next_quarter_revenue)}
                    </span>
                  </div>
                </div>
              )}
            </div>

            <button
              onClick={handleExport}
              className="mt-6 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium text-white gradient-brand hover:opacity-90 transition-opacity"
            >
              <Download className="w-4 h-4" /> Download Forecast Report
            </button>
          </div>
        </div>
      ) : (
        <div className="text-center py-12 text-zinc-500">
          No historical database forecasts recorded for this product.
        </div>
      )}
    </motion.div>
  );
}
