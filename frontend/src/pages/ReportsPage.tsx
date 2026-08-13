/**
 * Reports Page — Retail AI Frontend
 * ===================================
 * Generates and exports client-side reports for Sales, Inventory,
 * Forecasts, and Customer recommendations.
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Download, FileText, Calendar, Table, Sparkles, Warehouse, TrendingUp, ShoppingBag } from 'lucide-react';
import { useSales, useInventory, useProducts, useInventoryLowStock, useCustomerAnalytics } from '../hooks';
import { useTheme } from '../contexts/ThemeContext';
import { cn, downloadCSV, formatDate } from '../utils';
import { fadeIn } from '../animations/variants';
import { toast } from 'sonner';

export default function ReportsPage() {
  const { isDark } = useTheme();
  const [dateRange, setDateRange] = useState({ start: '2025-01-01', end: '2025-12-31' });

  // Fetch datasets for packaging into reports
  const { data: sales } = useSales({ limit: 500 });
  const { data: inventory } = useInventory({ limit: 500 });
  const { data: lowStock } = useInventoryLowStock();
  const { data: customers } = useCustomerAnalytics();

  const handleExport = (type: 'sales' | 'inventory' | 'forecast' | 'customers' | 'recs') => {
    try {
      if (type === 'sales') {
        if (!sales?.items?.length) return toast.error('No sales data available');
        const formatted = sales.items.map(s => ({
          SaleID: s.SaleID,
          InvoiceID: s.InvoiceID,
          CustomerID: s.CustomerID,
          ProductID: s.ProductID,
          SubCategory: s.SubCategory,
          SaleDate: s.SaleDate,
          Quantity: s.Quantity,
          FinalPrice: s.FinalPrice,
          Season: s.Season,
          Festival: s.Festival,
        }));
        downloadCSV(formatted, 'sales_report');
      } else if (type === 'inventory') {
        if (!inventory?.items?.length) return toast.error('No inventory data available');
        const formatted = inventory.items.map(i => ({
          ProductID: i.ProductID,
          Warehouse: i.Warehouse,
          CurrentStock: i.CurrentStock,
          SafetyStock: i.SafetyStock,
          ReorderPoint: i.ReorderPoint,
          InventoryStatus: i.InventoryStatus,
        }));
        downloadCSV(formatted, 'inventory_report');
      } else if (type === 'forecast') {
        if (!lowStock?.length) return toast.error('No low stock alerts available for forecasting');
        const formatted = lowStock.map(l => ({
          ProductID: l.ProductID,
          ProductName: l.ProductName,
          Warehouse: l.Warehouse,
          CurrentStock: l.CurrentStock,
          SafetyStock: l.SafetyStock,
          ForecastDemand: l.ForecastDemand,
          Recommendation: l.Recommendation,
        }));
        downloadCSV(formatted, 'restock_recommendations_report');
      } else if (type === 'customers') {
        if (!customers?.best_customers?.length) return toast.error('No VIP customer data available');
        const formatted = customers.best_customers.map(c => ({
          CustomerID: c.CustomerID,
          FullName: c.FullName,
          TotalSpent: c.total_spent,
          TotalOrders: c.total_orders,
        }));
        downloadCSV(formatted, 'vip_customers_report');
      }
      toast.success('Report downloaded successfully');
    } catch {
      toast.error('Failed to generate report');
    }
  };

  const reportCards = [
    {
      type: 'sales' as const,
      title: 'Sales & Revenue Report',
      desc: 'All invoice transactions, quantities, and seasonal festival labels.',
      icon: ShoppingBag,
      color: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/30',
    },
    {
      type: 'inventory' as const,
      title: 'Inventory Health Report',
      desc: 'Warehouse capacities, safety stock levels, reorder targets, and health states.',
      icon: Warehouse,
      color: 'bg-blue-500/10 text-blue-500 border-blue-500/30',
    },
    {
      type: 'forecast' as const,
      title: 'AI Restock Recommendation Report',
      desc: 'Demand forecasts combined with safety targets to generate replenishment triggers.',
      icon: TrendingUp,
      color: 'bg-violet-500/10 text-violet-500 border-violet-500/30',
    },
    {
      type: 'customers' as const,
      title: 'VIP & Customer Segment Report',
      desc: 'High-LTV customer rankings, membership tiers, and segment metrics.',
      icon: Table,
      color: 'bg-amber-500/10 text-amber-500 border-amber-500/30',
    },
  ];

  return (
    <motion.div variants={fadeIn} initial="hidden" animate="visible" className="space-y-6">
      {/* Header */}
      <div>
        <h1 className={cn('text-2xl font-bold', isDark ? 'text-zinc-100' : 'text-zinc-900')}>
          Reports
        </h1>
        <p className="text-sm text-zinc-500 mt-1">
          Export data sheets and forecasting spreadsheets
        </p>
      </div>

      {/* Date Range Selector */}
      <div className={cn(
        'p-5 rounded-2xl border flex flex-wrap gap-4 items-center',
        isDark ? 'bg-zinc-900/40 border-zinc-800' : 'bg-white border-zinc-200 shadow-sm'
      )}>
        <div className="flex items-center gap-2 text-sm text-zinc-400">
          <Calendar className="w-4 h-4 text-zinc-500" />
          <span>Report Scope:</span>
        </div>
        <div className="flex items-center gap-3">
          <input
            type="date"
            value={dateRange.start}
            onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
            className={cn('px-3 py-1.5 rounded-xl text-sm border outline-none', isDark ? 'bg-zinc-800 border-zinc-700' : 'bg-zinc-50 border-zinc-200')}
          />
          <span className="text-zinc-600">to</span>
          <input
            type="date"
            value={dateRange.end}
            onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
            className={cn('px-3 py-1.5 rounded-xl text-sm border outline-none', isDark ? 'bg-zinc-800 border-zinc-700' : 'bg-zinc-50 border-zinc-200')}
          />
        </div>
      </div>

      {/* Reports Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {reportCards.map((card) => (
          <div
            key={card.type}
            className={cn(
              'rounded-2xl p-5 border flex flex-col justify-between hover-lift transition-all',
              isDark ? 'bg-zinc-900/60 border-zinc-800/60 backdrop-blur-xl' : 'bg-white border-zinc-200 shadow-sm'
            )}
          >
            <div className="flex gap-4">
              <div className={cn('w-12 h-12 rounded-xl flex items-center justify-center shrink-0 border', card.color)}>
                <card.icon className="w-6 h-6" />
              </div>
              <div>
                <h3 className={cn('text-sm font-semibold', isDark ? 'text-zinc-200' : 'text-zinc-800')}>
                  {card.title}
                </h3>
                <p className="text-xs text-zinc-500 mt-1 leading-relaxed">
                  {card.desc}
                </p>
              </div>
            </div>

            <button
              onClick={() => handleExport(card.type)}
              className="mt-6 flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-xl text-sm font-medium text-white gradient-brand hover:opacity-90 transition-opacity"
            >
              <Download className="w-4 h-4" /> Download CSV
            </button>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
