/**
 * Sales Page — Demand Sphere Frontend
 * ==================================
 * Transaction log displaying invoice list, seasonal tags,
 * festival categories, and CRUD operations.
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Plus, Trash2, X } from 'lucide-react';
import { useSales } from '../hooks';
import DataTable, { type Column } from '../components/shared/DataTable';
import StatusBadge from '../components/shared/StatusBadge';
import { useTheme } from '../contexts/ThemeContext';
import { cn, formatDate, formatCurrency } from '../utils';
import { fadeIn } from '../animations/variants';
import type { Sale } from '../types';
import { salesApi } from '../services/salesApi';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

// ─── Shared field style helper ────────────────────────────────────────────────
const useFieldClass = (isDark: boolean) =>
  cn(
    'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors',
    isDark
      ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
      : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
  );

export default function SalesPage() {
  const { isDark } = useTheme();
  const queryClient = useQueryClient();
  const fieldClass = useFieldClass(isDark);

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { data, isLoading } = useSales({
    skip: (page - 1) * pageSize,
    limit: pageSize,
  });

  // ─── Handle Add Sale Submit ───────────────────────────────────────────────────
  const handleAddSale = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsSubmitting(true);
    const formData = new FormData(e.currentTarget);
    const total = data?.total ?? 0;
    const saleDateRaw = formData.get('SaleDate') as string;
    const saleDate = saleDateRaw || new Date().toISOString().split('T')[0];
    const saleYear = parseInt(saleDate.split('-')[0], 10);
    const saleMonth = parseInt(saleDate.split('-')[1], 10);

    const newSale = {
      SaleID: (formData.get('SaleID') as string) || `S${String(total + 1).padStart(5, '0')}`,
      InvoiceID: (formData.get('InvoiceID') as string) || `INV-${Date.now()}`,
      CustomerID: formData.get('CustomerID') as string,
      ProductID: formData.get('ProductID') as string,
      SubCategory: (formData.get('SubCategory') as string) || undefined,
      SaleDate: saleDate,
      Quantity: parseInt(formData.get('Quantity') as string, 10),
      MRP: parseFloat(formData.get('MRP') as string) || undefined,
      DiscountPercent: parseFloat(formData.get('DiscountPercent') as string) || undefined,
      FinalPrice: parseFloat(formData.get('FinalPrice') as string),
      Festival: (formData.get('Festival') as string) || undefined,
      Season: (formData.get('Season') as string) || undefined,
      SaleMonth: saleMonth,
      SaleYear: saleYear,
    };

    try {
      await salesApi.create(newSale);
      toast.success('Sale record added successfully');
      setIsAddModalOpen(false);
      queryClient.invalidateQueries({ queryKey: ['sales'] });
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to add sale';
      toast.error(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // ─── Handle Delete ────────────────────────────────────────────────────────────
  const handleDelete = async (sale: Sale) => {
    if (!confirm(`Delete sale "${sale.SaleID}"?`)) return;
    try {
      await salesApi.delete(sale.SaleID);
      toast.success('Sale record deleted');
      queryClient.invalidateQueries({ queryKey: ['sales'] });
    } catch {
      toast.error('Failed to delete sale');
    }
  };

  const columns: Column<Sale>[] = [
    { key: 'SaleID', label: 'Sale ID', sortable: true, className: 'font-mono text-xs' },
    { key: 'InvoiceID', label: 'Invoice No', className: 'font-mono text-xs' },
    { key: 'CustomerID', label: 'Customer ID', className: 'font-mono text-xs' },
    { key: 'ProductID', label: 'Product ID', className: 'font-mono text-xs' },
    { key: 'SubCategory', label: 'Item Sub-Category' },
    {
      key: 'SaleDate', label: 'Date', sortable: true,
      render: (item) => <span className="text-zinc-500 text-xs">{formatDate(item.SaleDate)}</span>,
    },
    { key: 'Quantity', label: 'Qty', sortable: true },
    {
      key: 'FinalPrice', label: 'Total Price', sortable: true,
      render: (item) => <span className="font-semibold text-emerald-500">{formatCurrency(item.FinalPrice)}</span>,
    },
    {
      key: 'Season', label: 'Season',
      render: (item) => <StatusBadge status={item.Season || 'Summer'} />,
    },
    {
      key: 'Festival', label: 'Festival',
      render: (item) => <span className="text-xs text-brand-400 font-medium">{item.Festival || 'None'}</span>,
    },
  ];

  return (
    <motion.div variants={fadeIn} initial="hidden" animate="visible" className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className={cn('text-2xl font-bold', isDark ? 'text-zinc-100' : 'text-zinc-900')}>Sales Transactions</h1>
          <p className="text-sm text-zinc-500 mt-1">
            Review transaction logs, invoice mappings, and seasonal attributes • {data?.total ?? 0} sales records
          </p>
        </div>
        {/* Add Sale Button */}
        <motion.button
          onClick={() => setIsAddModalOpen(true)}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-white gradient-brand hover:opacity-90 transition-opacity"
        >
          <Plus className="w-4 h-4" /> Add Sale
        </motion.button>
      </div>

      {/* Table */}
      <DataTable
        data={data?.items ?? []}
        columns={columns}
        isLoading={isLoading}
        searchPlaceholder="Search invoices or customer IDs..."
        searchKeys={['InvoiceID', 'CustomerID', 'ProductID', 'SubCategory', 'SaleID']}
        totalItems={data?.total}
        page={page}
        pageSize={pageSize}
        onPageChange={setPage}
        onPageSizeChange={(s) => { setPageSize(s); setPage(1); }}
        actions={(item) => (
          <div className="flex items-center gap-1">
            <button
              onClick={() => handleDelete(item)}
              className="p-1.5 rounded-lg text-zinc-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
              title="Delete Sale"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        )}
      />

      {/* ─── Add Sale Modal ──────────────────────────────────────────────────── */}
      {isAddModalOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto"
          onClick={() => setIsAddModalOpen(false)}
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            onClick={(e) => e.stopPropagation()}
            className={cn(
              'w-full max-w-xl rounded-2xl p-6 border my-8',
              isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200'
            )}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className={cn('text-lg font-bold', isDark ? 'text-zinc-100' : 'text-zinc-900')}>Add New Sale</h2>
                <p className="text-xs text-zinc-500 mt-0.5">Saved directly to the sales database</p>
              </div>
              <button onClick={() => setIsAddModalOpen(false)} className="text-zinc-500 hover:text-zinc-300 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleAddSale} className="space-y-4">
              {/* Row 1: Sale ID + Invoice ID */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Sale ID</label>
                  <input
                    type="text"
                    name="SaleID"
                    placeholder={`S${String((data?.total ?? 0) + 1).padStart(5, '0')}`}
                    defaultValue={`S${String((data?.total ?? 0) + 1).padStart(5, '0')}`}
                    className={fieldClass}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Invoice ID</label>
                  <input
                    type="text"
                    name="InvoiceID"
                    placeholder={`INV-${Date.now()}`}
                    className={fieldClass}
                  />
                </div>
              </div>

              {/* Row 2: Customer ID + Product ID */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Customer ID *</label>
                  <input
                    type="text"
                    name="CustomerID"
                    required
                    placeholder="e.g. C0001"
                    className={fieldClass}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Product ID *</label>
                  <input
                    type="text"
                    name="ProductID"
                    required
                    placeholder="e.g. P0001"
                    className={fieldClass}
                  />
                </div>
              </div>

              {/* Row 3: Sub-Category + Sale Date */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Sub-Category</label>
                  <input
                    type="text"
                    name="SubCategory"
                    placeholder="e.g. Veshti"
                    className={fieldClass}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Sale Date *</label>
                  <input
                    type="date"
                    name="SaleDate"
                    required
                    defaultValue={new Date().toISOString().split('T')[0]}
                    className={fieldClass}
                  />
                </div>
              </div>

              {/* Row 4: Quantity + MRP */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Quantity *</label>
                  <input
                    type="number"
                    name="Quantity"
                    required
                    min={1}
                    defaultValue={1}
                    className={fieldClass}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">MRP (₹)</label>
                  <input
                    type="number"
                    name="MRP"
                    step="0.01"
                    placeholder="0.00"
                    className={fieldClass}
                  />
                </div>
              </div>

              {/* Row 5: Discount % + Final Price */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Discount %</label>
                  <input
                    type="number"
                    name="DiscountPercent"
                    step="0.01"
                    min={0}
                    max={100}
                    placeholder="0"
                    className={fieldClass}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Final Price (₹) *</label>
                  <input
                    type="number"
                    name="FinalPrice"
                    required
                    step="0.01"
                    placeholder="0.00"
                    className={fieldClass}
                  />
                </div>
              </div>

              {/* Row 6: Season + Festival */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Season</label>
                  <select name="Season" className={cn(fieldClass, 'cursor-pointer')}>
                    <option value="">Select season</option>
                    {['Summer', 'Winter', 'Monsoon', 'Spring', 'Autumn'].map((s) => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Festival</label>
                  <select name="Festival" className={cn(fieldClass, 'cursor-pointer')}>
                    <option value="">None</option>
                    {['Diwali', 'Pongal', 'Christmas', 'Eid', 'Holi', 'Navratri', 'Onam', 'New Year'].map((f) => (
                      <option key={f} value={f}>{f}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Submit */}
              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className={cn(
                    'px-4 py-2 rounded-xl text-sm font-medium border transition-colors',
                    isDark
                      ? 'border-zinc-700 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800'
                      : 'border-zinc-200 text-zinc-600 hover:text-zinc-800 hover:bg-zinc-50'
                  )}
                >
                  Cancel
                </button>
                <motion.button
                  type="submit"
                  disabled={isSubmitting}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="px-5 py-2 rounded-xl text-sm font-semibold text-white gradient-brand hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? 'Adding...' : 'Add Sale'}
                </motion.button>
              </div>
            </form>
          </motion.div>
        </motion.div>
      )}
    </motion.div>
  );
}
