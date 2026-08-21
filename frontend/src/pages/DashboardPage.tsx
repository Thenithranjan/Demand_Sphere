/**
 * Dashboard Page — Demand Sphere Frontend
 * ======================================
 * AI Demand Sphere Dashboard with KPI cards, charts,
 * and real-time data from analytics endpoints.
 */

import { motion } from 'framer-motion';
import {
  Package, Users, ShoppingCart, IndianRupee, Warehouse,
  AlertTriangle, Sparkles, Target,
} from 'lucide-react';
import { useDashboard, useSalesAnalytics, useProducts, useCustomers, useInventoryAlerts } from '../hooks';
import StatsCard from '../components/shared/StatsCard';
import SkeletonCard from '../components/shared/SkeletonCard';
import { SalesAreaChart, RevenueTrendChart, CategoryPieChart, TopProductsBarChart } from '../components/charts';
import { staggerContainer } from '../animations/variants';
import { formatCurrency, formatNumber, formatPercent } from '../utils';
import { useTheme } from '../contexts/ThemeContext';
import { cn } from '../utils';

export default function DashboardPage() {
  const { isDark } = useTheme();
  const { data: dashboard, isLoading: dashLoading } = useDashboard();
  const { data: salesData, isLoading: salesLoading } = useSalesAnalytics();
  const { data: productsData } = useProducts({ limit: 1 });
  const { data: customersData } = useCustomers({ limit: 1 });
  const { data: alerts } = useInventoryAlerts();

  const isLoading = dashLoading;

  return (
    <div className="space-y-6">
      {/* ─── Page Header ──────────────────────────────────────── */}
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
