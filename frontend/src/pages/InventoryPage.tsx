/**
 * Inventory Page — Demand Sphere Frontend
 * ======================================
 * Stock management with alerts, low-stock warnings,
 * recommendations, and warehouse analytics.
 */

import { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { AlertTriangle, AlertCircle, Package, Warehouse as WarehouseIcon } from 'lucide-react';
import {
  useInventory, useInventoryAlerts, useInventoryLowStock,
  useInventoryRecommendations, useInventorySummary, useInventoryAnalytics,
} from '../hooks';
import DataTable, { type Column } from '../components/shared/DataTable';
import StatsCard from '../components/shared/StatsCard';
import StatusBadge from '../components/shared/StatusBadge';
import { InventoryStatusChart } from '../components/charts';
import { useTheme } from '../contexts/ThemeContext';
import { cn, formatNumber } from '../utils';
import { staggerContainer, fadeIn } from '../animations/variants';
import type { Inventory, InventoryAlert } from '../types';

export default function InventoryPage() {
  const { isDark } = useTheme();
  const location = useLocation();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [activeTab, setActiveTab] = useState<'all' | 'alerts' | 'low-stock' | 'recommendations'>(() => {
    const params = new URLSearchParams(location.search);
    const tab = params.get('tab');
    return (tab === 'alerts' || tab === 'low-stock' || tab === 'recommendations') ? tab : 'all';
  });

  const { data: inventoryData, isLoading } = useInventory({ skip: (page - 1) * pageSize, limit: pageSize });
  const { data: alerts } = useInventoryAlerts();
  const { data: lowStock } = useInventoryLowStock();
  const { data: recommendations } = useInventoryRecommendations();
  const { data: warehouseData } = useInventoryAnalytics();

  const inventoryColumns: Column<Inventory>[] = [
    { key: 'ProductID', label: 'Product ID', sortable: true, className: 'font-mono text-xs' },
    { key: 'Warehouse', label: 'Warehouse' },
    {
      key: 'CurrentStock', label: 'Stock', sortable: true,
      render: (item) => <span className="font-medium">{formatNumber(item.CurrentStock ?? 0)}</span>,
    },
    { key: 'SafetyStock', label: 'Safety', render: (item) => formatNumber(item.SafetyStock ?? 0) },
    { key: 'ReorderPoint', label: 'Reorder Pt', render: (item) => formatNumber(item.ReorderPoint ?? 0) },
    {
      key: 'StockUtilisation', label: 'Utilisation', sortable: true,
      render: (item) => (
        <div className="flex items-center gap-2">
          <div className={cn('h-1.5 rounded-full flex-1 max-w-[60px]', isDark ? 'bg-zinc-800' : 'bg-zinc-200')}>
            <div
              className="h-full rounded-full bg-brand-500"
              style={{ width: `${Math.min((item.StockUtilisation ?? 0) * 100, 100)}%` }}
            />
          </div>
          <span className="text-xs text-zinc-500">{((item.StockUtilisation ?? 0) * 100).toFixed(0)}%</span>
        </div>
      ),
    },
    {
      key: 'InventoryStatus', label: 'Status',
      render: (item) => <StatusBadge status={item.InventoryStatus || 'Healthy'} />,
    },
  ];

  const alertColumns: Column<InventoryAlert>[] = [
    { key: 'ProductID', label: 'Product ID', className: 'font-mono text-xs' },
    { key: 'ProductName', label: 'Product' },
    { key: 'Warehouse', label: 'Warehouse' },
    {
      key: 'CurrentStock', label: 'Current',
      render: (item) => <span className="text-red-400 font-bold">{item.CurrentStock}</span>,
    },
    { key: 'SafetyStock', label: 'Safety' },
    { key: 'ForecastDemand', label: 'Forecast' },
    {
      key: 'Recommendation', label: 'Action',
      render: (item) => {
        const color = item.Recommendation.includes('Immediately') ? 'text-red-500' :
          item.Recommendation.includes('Plan') ? 'text-amber-500' :
          item.Recommendation.includes('OK') ? 'text-emerald-500' : 'text-blue-500';
        return <span className={cn('text-xs font-medium', color)}>{item.Recommendation}</span>;
      },
    },
  ];

  const tabs = [
    { key: 'all' as const, label: 'All Inventory', count: inventoryData?.total },
    { key: 'alerts' as const, label: 'Critical Alerts', count: alerts?.length, color: 'text-red-500' },
    { key: 'low-stock' as const, label: 'Low Stock', count: lowStock?.length, color: 'text-amber-500' },
    { key: 'recommendations' as const, label: 'Recommendations', count: recommendations?.length },
  ];

  return (
    <motion.div variants={fadeIn} initial="hidden" animate="visible" className="space-y-6">
      {/* Header */}
      <div>
        <h1 className={cn('text-2xl font-bold', isDark ? 'text-zinc-100' : 'text-zinc-900')}>Inventory</h1>
        <p className="text-sm text-zinc-500 mt-1">Stock management & AI-powered restocking alerts</p>
      </div>

      {/* Summary Cards */}
      <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard title="Total Items" value={formatNumber(inventoryData?.total ?? 0)} icon={Package} gradient="bg-gradient-to-r from-blue-500 to-cyan-500" />
        <StatsCard title="Critical Alerts" value={formatNumber(alerts?.length ?? 0)} icon={AlertCircle} gradient="bg-gradient-to-r from-red-500 to-orange-500" />
        <StatsCard title="Low Stock" value={formatNumber(lowStock?.length ?? 0)} icon={AlertTriangle} gradient="bg-gradient-to-r from-amber-500 to-yellow-500" />
        <StatsCard title="Warehouses" value={formatNumber(warehouseData?.warehouse_metrics?.length ?? 0)} icon={WarehouseIcon} gradient="bg-gradient-to-r from-violet-500 to-purple-500" />
      </motion.div>

      {/* Chart */}
      {warehouseData?.warehouse_metrics && (
        <InventoryStatusChart data={warehouseData.warehouse_metrics} />
      )}

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
            {tab.label}
            {tab.count != null && (
              <span className={cn('text-xs font-bold', tab.color || 'text-zinc-500')}>{tab.count}</span>
            )}
          </button>
        ))}
      </div>

      {/* Table based on active tab */}
      {activeTab === 'all' && (
        <DataTable
          data={inventoryData?.items ?? []}
          columns={inventoryColumns}
          isLoading={isLoading}
          searchPlaceholder="Search inventory..."
          searchKeys={['ProductID', 'Warehouse']}
          totalItems={inventoryData?.total}
          page={page}
          pageSize={pageSize}
          onPageChange={setPage}
          onPageSizeChange={(s) => { setPageSize(s); setPage(1); }}
        />
      )}

      {(activeTab === 'alerts' || activeTab === 'low-stock' || activeTab === 'recommendations') && (
        <DataTable
          data={activeTab === 'alerts' ? (alerts ?? []) : activeTab === 'low-stock' ? (lowStock ?? []) : (recommendations ?? [])}
          columns={alertColumns}
          searchPlaceholder="Search alerts..."
          searchKeys={['ProductName', 'Warehouse', 'Recommendation']}
        />
      )}
    </motion.div>
  );
}
