/**
 * Recommendations Page — Demand Sphere Frontend
 * ============================================
 * Exposes AI-powered hybrid product recommendations.
 * Combines Collaborative Filtering and Content-Based models with fallback logic.
 */

import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, ShoppingBag, Award, ArrowRight, User } from 'lucide-react';
import { useRecommendations, useCustomers, useProducts } from '../hooks';
import StatsCard from '../components/shared/StatsCard';
import SkeletonCard from '../components/shared/SkeletonCard';
import { useTheme } from '../contexts/ThemeContext';
import { cn, formatPercent } from '../utils';
import { fadeIn, staggerContainer } from '../animations/variants';

export default function RecommendationsPage() {
  const { isDark } = useTheme();
  const location = useLocation();
  const [selectedCustomerId, setSelectedCustomerId] = useState('C00015'); // Default demo customer

  // Read customer query parameter if navigating from Customers list page
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const queryCustId = params.get('customer');
    if (queryCustId) {
      setSelectedCustomerId(queryCustId);
    }
  }, [location]);

  // Fetch customers list for select dropdown
  const { data: customersData } = useCustomers({ limit: 500 });
  const selectedCustomer = customersData?.items.find((c) => c.CustomerID === selectedCustomerId);

  // Fetch recommendations
  const { data: recData, isLoading: recLoading, refetch } = useRecommendations(selectedCustomerId, 10);

  // Fetch product list for full descriptions
  const { data: productsData } = useProducts({ limit: 500 });

  const getProductDetails = (productId: string) => {
    return productsData?.items.find((p) => p.ProductID === productId);
  };

  return (
    <motion.div variants={fadeIn} initial="hidden" animate="visible" className="space-y-6">
      {/* ─── Page Header ──────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className={cn('text-2xl font-bold', isDark ? 'text-zinc-100' : 'text-zinc-900')}>
            AI Recommendations
          </h1>
          <p className="text-sm text-zinc-500 mt-1">
            Personalized hybrid recommendations (Collaborative + Content Similarity)
          </p>
        </div>

        {/* Customer Selector */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-zinc-500 font-medium">Select Customer:</span>
          <select
            value={selectedCustomerId}
            onChange={(e) => setSelectedCustomerId(e.target.value)}
            className={cn(
              'px-3 py-2 rounded-xl text-sm font-medium outline-none border transition-colors max-w-xs',
              isDark
                ? 'bg-zinc-900 border-zinc-800 text-zinc-200'
                : 'bg-white border-zinc-200 text-zinc-800 shadow-sm'
            )}
          >
            {customersData?.items.map((c) => (
              <option key={c.CustomerID} value={c.CustomerID}>
                {c.CustomerID} — {c.FullName}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Selected Customer Profile Summary */}
      {selectedCustomer && (
        <div className={cn(
          'p-5 rounded-2xl border flex flex-col md:flex-row md:items-center md:justify-between gap-6',
          isDark ? 'bg-zinc-900/40 border-zinc-800/80' : 'bg-white border-zinc-200/50 shadow-sm'
        )}>
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl gradient-brand flex items-center justify-center text-white font-bold">
              <User className="w-6 h-6" />
            </div>
            <div>
              <h2 className={cn('font-bold text-lg', isDark ? 'text-zinc-200' : 'text-zinc-800')}>
                {selectedCustomer.FullName}
              </h2>
              <p className="text-xs text-zinc-500 mt-0.5">
                City: {selectedCustomer.City} | Membership: {selectedCustomer.Membership}
              </p>
            </div>
          </div>

          {/* Preferences */}
          <div className="flex flex-wrap items-center gap-6">
            <div className="text-sm">
              <span className="text-zinc-500 text-xs block">Preferred Category</span>
              <span className={cn('font-semibold', isDark ? 'text-zinc-300' : 'text-zinc-700')}>
                {selectedCustomer.PreferredCategory || 'All'}
              </span>
            </div>
            <div className="text-sm">
              <span className="text-zinc-500 text-xs block">Preferred Fabric</span>
              <span className={cn('font-semibold', isDark ? 'text-zinc-300' : 'text-zinc-700')}>
                {selectedCustomer.PreferredFabric || 'Cotton'}
              </span>
            </div>
            <div className="text-sm">
              <span className="text-zinc-500 text-xs block">Preferred Price Range</span>
              <span className={cn('font-semibold', isDark ? 'text-zinc-300' : 'text-zinc-700')}>
                {selectedCustomer.PreferredPriceRange || 'Standard'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* ─── AI Pipeline Explainer ────────────────────────────── */}
      <div className={cn(
        'p-4 rounded-xl border text-xs text-zinc-500 bg-brand-500/5 border-brand-500/10 flex items-start gap-3'
      )}>
        <Sparkles className="w-5 h-5 text-brand-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-zinc-300 block mb-0.5">Recommendation Pipeline Logic:</span>
          Uses Collaborative Filtering to predict preference scores based on similar customers' purchase histories, combined with Content-Based attribute similarity (Category, Brand, Fabric, Color). Includes business filters to filter out previously purchased items. If a customer is new (cold start), popular products in their preferred category are automatically suggested.
        </div>
      </div>

      {/* ─── Recommended Products Grid ────────────────────────── */}
      {recLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
          {Array.from({ length: 10 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : recData?.recommended_products && recData.recommended_products.length > 0 ? (
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4"
        >
          {recData.recommended_products.map((item, idx) => {
            const p = getProductDetails(item.ProductID);
            return (
              <motion.div
                key={item.ProductID}
                whileHover={{ y: -4 }}
                className={cn(
                  'relative rounded-2xl p-4 border overflow-hidden flex flex-col justify-between group transition-all duration-300',
                  isDark ? 'bg-zinc-900/60 border-zinc-800/60 hover:bg-zinc-900 hover:border-zinc-700' : 'bg-white border-zinc-200 hover:shadow-lg'
                )}
              >
                <div>
                  {/* Rank badge */}
                  <span className="absolute top-3 left-3 bg-brand-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full z-10">
                    #{idx + 1}
                  </span>

                  {/* Similarity Score */}
                  <div className="text-right mb-2">
                    <span className="text-[10px] text-zinc-500 block">AI Match Score</span>
                    <span className="text-xs font-semibold text-brand-400">
                      {formatPercent(item.Score * 100)}
                    </span>
                  </div>

                  {/* Product Title */}
                  <h3 className={cn('text-sm font-semibold mt-2 group-hover:text-brand-400 transition-colors', isDark ? 'text-zinc-200' : 'text-zinc-800')}>
                    {item.ProductName}
                  </h3>
                  <p className="text-xs text-zinc-500 mt-0.5">
                    ProductID: {item.ProductID}
                  </p>
                </div>

                <div className="mt-4 pt-3 border-t border-zinc-800">
                  {p ? (
                    <div className="space-y-1.5 text-xs text-zinc-500">
                      <div className="flex justify-between">
                        <span>Category:</span>
                        <span className="font-medium">{p.Category}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Brand:</span>
                        <span className="font-medium">{p.Brand}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Fabric:</span>
                        <span className="font-medium">{p.Fabric || 'Cotton'}</span>
                      </div>
                    </div>
                  ) : null}
                </div>
              </motion.div>
            );
          })}
        </motion.div>
      ) : (
        <div className="text-center py-12 text-zinc-500">
          No recommendations found. Please select a returning customer.
        </div>
      )}
    </motion.div>
  );
}
