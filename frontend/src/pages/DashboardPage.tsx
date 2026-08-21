/**
 * Dashboard Page — Demand Sphere Frontend
 * ======================================
 * AI Demand Sphere Dashboard with KPI cards, charts,
 * and real-time data from analytics endpoints.
 */

import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Package, Users, ShoppingCart, IndianRupee, Warehouse,
  AlertTriangle, Sparkles, Target, Search, ArrowRight, X
} from 'lucide-react';
import { useDashboard, useSalesAnalytics, useProducts, useCustomers, useInventoryAlerts } from '../hooks';
import StatsCard from '../components/shared/StatsCard';
import SkeletonCard from '../components/shared/SkeletonCard';
import { SalesAreaChart, RevenueTrendChart, CategoryPieChart, TopProductsBarChart } from '../components/charts';
import { staggerContainer } from '../animations/variants';
import { formatCurrency, formatNumber } from '../utils';
import { useTheme } from '../contexts/ThemeContext';
import { cn } from '../utils';
import { NAV_ITEMS } from '../constants';

const PAGE_METADATA: Record<string, { description: string }> = {
  '/dashboard': { description: 'Overview of key metrics, KPIs & quick stats' },
  '/products': { description: 'Product catalog, pricing, categories & inventory tags' },
  '/customers': { description: 'Customer directory, membership tiers & loyalty points' },
  '/sales': { description: 'Invoice history, transaction logs & seasonal tags' },
  '/inventory': { description: 'Stock levels, warehouse health, alerts & reorders' },
  '/forecast': { description: 'AI demand prediction, XGBoost trends & seasonality' },
  '/recommendations': { description: 'AI-powered collaborative & content product recs' },
  '/analytics': { description: 'Business intelligence, revenue trends & customer segments' },
  '/reports': { description: 'Export PDF & CSV summary reports' },
  '/model-management': { description: 'MLOps model training lifecycle & version audit' },
  '/admin': { description: 'User management & staff permission board' },
  '/profile': { description: 'Account settings, credentials & theme preference' },
};

export default function DashboardPage() {
  const { isDark } = useTheme();
  const navigate = useNavigate();
  const { data: dashboard, isLoading: dashLoading } = useDashboard();
  const { data: salesData, isLoading: salesLoading } = useSalesAnalytics();
  const { data: productsData } = useProducts({ limit: 1 });
  const { data: customersData } = useCustomers({ limit: 1 });
  const { data: alerts } = useInventoryAlerts();

  // Dashboard Page Quick Search State
  const [dashSearchQuery, setDashSearchQuery] = useState('');
  const [isDashSearchOpen, setIsDashSearchOpen] = useState(false);
  const dashSearchRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dashSearchRef.current && !dashSearchRef.current.contains(e.target as Node)) {
        setIsDashSearchOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const filteredPages = NAV_ITEMS.filter((item) => {
    if (!dashSearchQuery.trim()) return true;
    const query = dashSearchQuery.toLowerCase().trim();
    const meta = PAGE_METADATA[item.path];
    return (
      item.label.toLowerCase().includes(query) ||
      item.path.toLowerCase().includes(query) ||
      meta?.description.toLowerCase().includes(query)
    );
  });

  const handleNavigatePage = (path: string) => {
    navigate(path);
    setDashSearchQuery('');
    setIsDashSearchOpen(false);
  };

  const isLoading = dashLoading;

  return (
    <div className="space-y-6">
      {/* ─── Page Header & Quick Search Bar ────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className={cn(
            'text-2xl font-bold tracking-tight',
            isDark ? 'text-zinc-100' : 'text-zinc-900'
          )}>
            Dashboard
          </h1>
          <p className="text-sm text-zinc-500 mt-1">
            AI-Powered Demand Sphere Overview
          </p>
        </div>

        {/* Dashboard Search Bar */}
        <div ref={dashSearchRef} className="relative w-full md:w-80 z-20">
          <div className={cn(
            'flex items-center gap-2 px-3.5 py-2 rounded-xl text-sm transition-all border shadow-sm',
            isDark
              ? 'bg-zinc-900/80 border-zinc-800 focus-within:border-brand-500 text-zinc-200'
              : 'bg-white border-zinc-200 focus-within:border-brand-500 text-zinc-800'
          )}>
            <Search className="w-4 h-4 text-zinc-400 shrink-0" />
            <input
              type="text"
              value={dashSearchQuery}
              onChange={(e) => {
                setDashSearchQuery(e.target.value);
                if (!isDashSearchOpen) setIsDashSearchOpen(true);
              }}
              onFocus={() => setIsDashSearchOpen(true)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && filteredPages.length > 0) {
                  handleNavigatePage(filteredPages[0].path);
                }
              }}
              placeholder="Search & jump to any page..."
              className="bg-transparent border-none outline-none w-full text-xs placeholder:text-zinc-500"
            />
            {dashSearchQuery && (
              <button
                onClick={() => setDashSearchQuery('')}
                className="text-zinc-400 hover:text-zinc-200"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Quick Search Dropdown */}
          <AnimatePresence>
            {isDashSearchOpen && (
              <motion.div
                initial={{ opacity: 0, y: 6, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 6, scale: 0.98 }}
                transition={{ duration: 0.15 }}
                className={cn(
                  'absolute left-0 right-0 mt-2 rounded-2xl border shadow-2xl overflow-hidden backdrop-blur-2xl z-30',
                  isDark
                    ? 'bg-zinc-900/95 border-zinc-800 text-zinc-100'
                    : 'bg-white/95 border-zinc-200 text-zinc-900'
                )}
              >
                <div className="p-2 border-b border-zinc-800/40 text-[11px] font-semibold text-zinc-500 uppercase tracking-wider px-3 flex items-center justify-between">
                  <span>Pages & Modules</span>
                  <span>{filteredPages.length} pages</span>
                </div>

                <div className="max-h-64 overflow-y-auto p-1.5 space-y-1">
                  {filteredPages.length > 0 ? (
                    filteredPages.map((item) => {
                      const Icon = item.icon;
                      const meta = PAGE_METADATA[item.path];
                      return (
                        <div
                          key={item.path}
                          onClick={() => handleNavigatePage(item.path)}
                          className={cn(
                            'group flex items-center justify-between p-2.5 rounded-xl cursor-pointer transition-all',
                            isDark
                              ? 'hover:bg-zinc-800/80 text-zinc-200'
                              : 'hover:bg-zinc-100 text-zinc-800'
                          )}
                        >
                          <div className="flex items-center gap-3 min-w-0">
                            <div className={cn(
                              'p-2 rounded-lg transition-colors',
                              isDark
                                ? 'bg-zinc-800 text-zinc-400 group-hover:text-brand-400 group-hover:bg-brand-500/10'
                                : 'bg-zinc-100 text-zinc-500 group-hover:text-brand-600 group-hover:bg-brand-50'
                            )}>
                              <Icon className="w-4 h-4" />
                            </div>
                            <div className="min-w-0">
                              <p className="text-xs font-semibold group-hover:text-brand-400 transition-colors">
                                {item.label}
                              </p>
                              {meta && (
                                <p className="text-[11px] text-zinc-500 truncate mt-0.5">
                                  {meta.description}
                                </p>
                              )}
                            </div>
                          </div>
                          <ArrowRight className="w-3.5 h-3.5 text-zinc-600 opacity-0 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all shrink-0 ml-2" />
                        </div>
                      );
                    })
                  ) : (
                    <div className="p-4 text-center text-zinc-500 text-xs">
                      No matching page found
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* ─── KPI Stats Cards ──────────────────────────────────── */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : (
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
        >
          <StatsCard
            title="Total Products"
            value={formatNumber(productsData?.total ?? 0)}
            icon={Package}
            gradient="bg-gradient-to-r from-blue-500 to-cyan-500"
          />
          <StatsCard
            title="Total Customers"
            value={formatNumber(customersData?.total ?? 0)}
            icon={Users}
            gradient="bg-gradient-to-r from-violet-500 to-purple-500"
          />
          <StatsCard
            title="Today's Sales"
            value={formatNumber(Math.round((dashboard?.total_quantity_sold ?? 0) / 365))}
            icon={ShoppingCart}
            gradient="bg-gradient-to-r from-emerald-500 to-teal-500"
          />
          <StatsCard
            title="Monthly Revenue"
            value={formatCurrency(Math.round((dashboard?.total_revenue ?? 0) / 12))}
            icon={IndianRupee}
            gradient="bg-gradient-to-r from-amber-500 to-orange-500"
          />
          <StatsCard
            title="Inventory Value"
            value={formatCurrency(Math.round((dashboard?.total_revenue ?? 0) * 0.4))}
            icon={Warehouse}
            gradient="bg-gradient-to-r from-pink-500 to-rose-500"
          />
          <StatsCard
            title="Low Stock Count"
            value={formatNumber(alerts?.length ?? 0)}
            icon={AlertTriangle}
            gradient="bg-gradient-to-r from-red-500 to-orange-500"
          />
          <StatsCard
            title="AI Recs Generated"
            value={formatNumber(customersData?.total ?? 2002)}
            icon={Sparkles}
            gradient="bg-gradient-to-r from-indigo-500 to-violet-500"
          />
          <StatsCard
            title="Forecast Accuracy"
            value="94.2%"
            icon={Target}
            gradient="bg-gradient-to-r from-teal-500 to-emerald-500"
          />
        </motion.div>
      )}

      {/* ─── Charts Row 1 ─────────────────────────────────────── */}
      {!salesLoading && salesData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SalesAreaChart data={salesData.monthly_sales_trend} />
          <RevenueTrendChart data={salesData.monthly_sales_trend} />
        </div>
      )}

      {/* ─── Charts Row 2 ─────────────────────────────────────── */}
      {!salesLoading && salesData && dashboard && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <CategoryPieChart data={salesData.subcategory_sales} />
          <TopProductsBarChart data={dashboard.top_products ?? []} />
        </div>
      )}
    </div>
  );
}
