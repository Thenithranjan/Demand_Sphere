/**
 * Analytics Page — Demand Sphere Frontend
 * =====================================
 * Complete Executive BI Dashboard showcasing Sales trends, Customer LTV,
 * and Warehouse capacity analytics.
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import { BarChart3, TrendingUp, Users, Warehouse } from 'lucide-react';
import { useDashboard, useSalesAnalytics, useCustomerAnalytics, useInventoryAnalytics } from '../hooks';
import { SalesAreaChart, RevenueTrendChart, CategoryPieChart, TopProductsBarChart, InventoryStatusChart } from '../components/charts';
import SkeletonCard from '../components/shared/SkeletonCard';
import DataTable, { type Column } from '../components/shared/DataTable';
import { useTheme } from '../contexts/ThemeContext';
import { cn, formatCurrency, formatNumber } from '../utils';
import { fadeIn } from '../animations/variants';

export default function AnalyticsPage() {
  const { isDark } = useTheme();
  const [activeTab, setActiveTab] = useState<'overview' | 'sales' | 'customers' | 'inventory'>('overview');

  // Fetch all analytics datasets
  const { data: dashboard, isLoading: dashLoading } = useDashboard();
  const { data: sales, isLoading: salesLoading } = useSalesAnalytics();
  const { data: customers, isLoading: custLoading } = useCustomerAnalytics();
  const { data: inventory, isLoading: invLoading } = useInventoryAnalytics();

  const tabs = [
    { key: 'overview' as const, label: 'Overview', icon: BarChart3 },
    { key: 'sales' as const, label: 'Sales Trends', icon: TrendingUp },
    { key: 'customers' as const, label: 'Customer segments', icon: Users },
    { key: 'inventory' as const, label: 'Inventory Warehouses', icon: Warehouse },
  ];

  return (
    <motion.div variants={fadeIn} initial="hidden" animate="visible" className="space-y-6">
      {/* Header */}
      <div>
        <h1 className={cn('text-2xl font-bold', isDark ? 'text-zinc-100' : 'text-zinc-900')}>
          Demand Sphere Intelligence
        </h1>
        <p className="text-sm text-zinc-500 mt-1">
          Executive business metrics, sales insights, and customer segmentation
        </p>
      </div>

      {/* Tabs */}
      <div className={cn('flex gap-1 p-1 rounded-xl border', isDark ? 'bg-zinc-900/60 border-zinc-800' : 'bg-zinc-100 border-zinc-200')}>
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all',
              activeTab === tab.key
                ? isDark ? 'bg-zinc-800 text-zinc-100' : 'bg-white text-zinc-900 shadow-sm'
                : 'text-zinc-500 hover:text-zinc-300'
            )}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* ─── TAB: OVERVIEW ────────────────────────────────────── */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {dashLoading ? (
            <>
              <SkeletonCard className="h-80" />
              <SkeletonCard className="h-80" />
            </>
          ) : dashboard && sales ? (
            <>
              <TopProductsBarChart data={dashboard.top_products ?? []} />
              <CategoryPieChart data={sales.subcategory_sales} />
            </>
          ) : null}
        </div>
      )}

      {/* ─── TAB: SALES ───────────────────────────────────────── */}
      {activeTab === 'sales' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {salesLoading ? (
            <>
              <SkeletonCard className="h-80" />
              <SkeletonCard className="h-80" />
            </>
          ) : sales ? (
            <>
              <SalesAreaChart data={sales.monthly_sales_trend} />
              <RevenueTrendChart data={sales.monthly_sales_trend} />
            </>
          ) : null}
        </div>
      )}

      {/* ─── TAB: CUSTOMERS ───────────────────────────────────── */}
      {activeTab === 'customers' && (
        <div className="space-y-6">
          {custLoading ? (
            <SkeletonCard className="h-80" />
          ) : customers ? (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* VIP Table */}
              <div className="lg:col-span-2 space-y-4">
                <h3 className={cn('text-sm font-semibold', isDark ? 'text-zinc-200' : 'text-zinc-800')}>
                  Top VIP Customers (by LTV)
                </h3>
                <div className={cn(
                  'rounded-xl border overflow-hidden',
                  isDark ? 'border-zinc-800/60 bg-zinc-900/30' : 'border-zinc-200 bg-white shadow-sm'
                )}>
                  <table className="w-full text-sm">
                    <thead>
                      <tr className={cn('border-b', isDark ? 'border-zinc-800 bg-zinc-900/50' : 'border-zinc-200 bg-zinc-50')}>
                        <th className="px-4 py-2 text-left text-xs font-semibold text-zinc-500 uppercase">Customer</th>
                        <th className="px-4 py-2 text-right text-xs font-semibold text-zinc-500 uppercase">Total Spent</th>
                        <th className="px-4 py-2 text-right text-xs font-semibold text-zinc-500 uppercase">Orders</th>
                      </tr>
                    </thead>
                    <tbody>
                      {customers.best_customers.map((c) => (
                        <tr key={c.CustomerID} className={cn('border-b last:border-0', isDark ? 'border-zinc-800/40' : 'border-zinc-100')}>
                          <td className="px-4 py-3 font-medium text-zinc-300">{c.FullName}</td>
                          <td className="px-4 py-3 text-right text-emerald-500 font-medium">{formatCurrency(c.total_spent)}</td>
                          <td className="px-4 py-3 text-right text-zinc-400">{c.total_orders}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Membership Breakdown */}
              <div className={cn(
                'rounded-xl p-5 border flex flex-col justify-between',
                isDark ? 'bg-zinc-900/60 border-zinc-800/60 backdrop-blur-xl' : 'bg-white border-zinc-200 shadow-sm'
              )}>
                <div>
                  <h3 className={cn('text-sm font-semibold mb-4', isDark ? 'text-zinc-200' : 'text-zinc-800')}>
                    Membership Segment Counts
                  </h3>
                  <div className="space-y-3">
                    {customers.membership_segments.map((seg) => (
                      <div key={seg.Membership} className="flex justify-between items-center py-2 border-b last:border-0 border-zinc-800/40">
                        <span className="text-sm text-zinc-400 capitalize">{seg.Membership} Tier</span>
                        <span className="font-semibold text-zinc-200">{formatNumber(seg.count)} Customers</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : null}
        </div>
      )}

      {/* ─── TAB: INVENTORY ───────────────────────────────────── */}
      {activeTab === 'inventory' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {invLoading ? (
            <>
              <SkeletonCard className="lg:col-span-2 h-80" />
              <SkeletonCard className="h-80" />
            </>
          ) : inventory ? (
            <>
              <div className="lg:col-span-2">
                <InventoryStatusChart data={inventory.warehouse_metrics} />
              </div>
              <div className={cn(
                'rounded-xl p-5 border flex flex-col justify-between',
                isDark ? 'bg-zinc-900/60 border-zinc-800/60 backdrop-blur-xl' : 'bg-white border-zinc-200 shadow-sm'
              )}>
                <div>
                  <h3 className={cn('text-sm font-semibold mb-4', isDark ? 'text-zinc-200' : 'text-zinc-800')}>
                    Warehouse Health Overview
                  </h3>
                  <div className="space-y-3">
                    {inventory.stock_health_distribution.map((dist) => (
                      <div key={dist.InventoryStatus} className="flex justify-between items-center py-2 border-b last:border-0 border-zinc-800/40">
                        <span className="text-sm text-zinc-400 capitalize">{dist.InventoryStatus}</span>
                        <span className="font-semibold text-zinc-200">{formatNumber(dist.count)} Items</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </>
          ) : null}
        </div>
      )}
    </motion.div>
  );
}
