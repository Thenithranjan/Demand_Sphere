/**
 * Customers Page — Demand Sphere Frontend
 * ======================================
 * Customer management with membership badges, loyalty points,
 * search/filter, CRUD operations, and recommendation navigation.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sparkles, Eye, Plus, Trash2, X } from 'lucide-react';
import { useCustomers, useSales } from '../hooks';
import DataTable, { type Column } from '../components/shared/DataTable';
import StatusBadge from '../components/shared/StatusBadge';
import { useTheme } from '../contexts/ThemeContext';
import { cn, formatNumber, formatDate, formatCurrency } from '../utils';
import { fadeIn } from '../animations/variants';
import type { Customer } from '../types';
import { customerApi } from '../services/customerApi';
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

export default function CustomersPage() {
  const { isDark } = useTheme();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const fieldClass = useFieldClass(isDark);

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [membership, setMembership] = useState('');
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { data, isLoading } = useCustomers({
    skip: (page - 1) * pageSize,
    limit: pageSize,
    membership: membership || undefined,
  });

  // Fetch sales for selected customer
  const { data: salesData } = useSales({
    customer_id: selectedCustomer?.CustomerID,
    limit: 20,
  });

  // ─── Handle Add Customer Submit ──────────────────────────────────────────────
  const handleAddCustomer = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsSubmitting(true);
    const formData = new FormData(e.currentTarget);
    const total = data?.total ?? 0;
    const newCustomer = {
      CustomerID: (formData.get('CustomerID') as string) || `C${String(total + 1).padStart(4, '0')}`,
      FullName: formData.get('FullName') as string,
      Gender: formData.get('Gender') as string,
      Age: parseInt(formData.get('Age') as string, 10),
      City: (formData.get('City') as string) || undefined,
      State: (formData.get('State') as string) || undefined,
      Membership: (formData.get('Membership') as string) || undefined,
      JoinDate: (formData.get('JoinDate') as string) || new Date().toISOString().split('T')[0],
      PreferredCategory: (formData.get('PreferredCategory') as string) || undefined,
      PreferredFabric: (formData.get('PreferredFabric') as string) || undefined,
      LoyaltyPoints: parseInt(formData.get('LoyaltyPoints') as string, 10) || 0,
    };

    try {
      await customerApi.create(newCustomer);
      toast.success('Customer added successfully');
      setIsAddModalOpen(false);
      queryClient.invalidateQueries({ queryKey: ['customers'] });
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to add customer';
      toast.error(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // ─── Handle Delete ───────────────────────────────────────────────────────────
  const handleDelete = async (customer: Customer) => {
    if (!confirm(`Delete "${customer.FullName}"?`)) return;
    try {
      await customerApi.delete(customer.CustomerID);
      toast.success('Customer deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      if (selectedCustomer?.CustomerID === customer.CustomerID) setSelectedCustomer(null);
    } catch {
      toast.error('Failed to delete customer');
    }
  };

  const columns: Column<Customer>[] = [
    { key: 'CustomerID', label: 'ID', sortable: true, className: 'font-mono text-xs' },
    {
      key: 'FullName', label: 'Customer', sortable: true,
      render: (item) => (
        <div>
          <p className={cn('font-medium', isDark ? 'text-zinc-200' : 'text-zinc-800')}>{item.FullName}</p>
          <p className="text-xs text-zinc-500">{item.City}, {item.State}</p>
        </div>
      ),
    },
    { key: 'Gender', label: 'Gender' },
    { key: 'Age', label: 'Age', sortable: true },
    {
      key: 'Membership', label: 'Membership',
      render: (item) => <StatusBadge status={item.Membership || 'Bronze'} />,
    },
    {
      key: 'LoyaltyPoints', label: 'Loyalty Points', sortable: true,
      render: (item) => (
        <span className="text-amber-500 font-medium">{formatNumber(item.LoyaltyPoints ?? 0)}</span>
      ),
    },
    { key: 'PreferredCategory', label: 'Preferred' },
    {
      key: 'JoinDate', label: 'Joined',
      render: (item) => <span className="text-zinc-500 text-xs">{formatDate(item.JoinDate)}</span>,
    },
  ];

  return (
    <motion.div variants={fadeIn} initial="hidden" animate="visible" className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className={cn('text-2xl font-bold', isDark ? 'text-zinc-100' : 'text-zinc-900')}>Customers</h1>
          <p className="text-sm text-zinc-500 mt-1">Manage customer relationships • {data?.total ?? 0} customers</p>
        </div>
        {/* Add Customer Button */}
        <motion.button
          onClick={() => setIsAddModalOpen(true)}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-white gradient-brand hover:opacity-90 transition-opacity"
        >
          <Plus className="w-4 h-4" /> Add Customer
        </motion.button>
      </div>

      {/* Membership Filter */}
      <div className="flex gap-2 flex-wrap">
        {['', 'Bronze', 'Silver', 'Gold', 'Platinum'].map((m) => (
          <button
            key={m}
            onClick={() => { setMembership(m); setPage(1); }}
            className={cn(
              'px-3 py-1.5 rounded-xl text-xs font-medium transition-colors border',
              membership === m
                ? 'bg-brand-500/10 text-brand-400 border-brand-500/30'
                : isDark
                  ? 'bg-zinc-800/50 text-zinc-400 border-zinc-700/50 hover:text-zinc-200'
                  : 'bg-zinc-50 text-zinc-500 border-zinc-200 hover:text-zinc-700'
            )}
          >
            {m || 'All'}
          </button>
        ))}
      </div>

      {/* Table */}
      <DataTable
        data={data?.items ?? []}
        columns={columns}
        isLoading={isLoading}
        searchPlaceholder="Search customers..."
        searchKeys={['FullName', 'City', 'CustomerID']}
        totalItems={data?.total}
        page={page}
        pageSize={pageSize}
        onPageChange={setPage}
        onPageSizeChange={(s) => { setPageSize(s); setPage(1); }}
        actions={(item) => (
          <div className="flex items-center gap-1">
            <button
              onClick={() => setSelectedCustomer(item)}
              className="p-1.5 rounded-lg text-zinc-500 hover:text-brand-400 hover:bg-brand-500/10 transition-colors"
              title="View Details"
            >
              <Eye className="w-4 h-4" />
            </button>
            <button
              onClick={() => navigate(`/recommendations?customer=${item.CustomerID}`)}
              className="p-1.5 rounded-lg text-zinc-500 hover:text-violet-400 hover:bg-violet-500/10 transition-colors"
              title="Get Recommendations"
            >
              <Sparkles className="w-4 h-4" />
            </button>
            <button
              onClick={() => handleDelete(item)}
              className="p-1.5 rounded-lg text-zinc-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
              title="Delete Customer"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        )}
      />

      {/* ─── Add Customer Modal ─────────────────────────────────────────────── */}
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
                <h2 className={cn('text-lg font-bold', isDark ? 'text-zinc-100' : 'text-zinc-900')}>Add New Customer</h2>
                <p className="text-xs text-zinc-500 mt-0.5">Saved directly to the customers database</p>
              </div>
              <button onClick={() => setIsAddModalOpen(false)} className="text-zinc-500 hover:text-zinc-300 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleAddCustomer} className="space-y-4">
              {/* Row 1: ID + Full Name */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Customer ID</label>
                  <input
                    type="text"
                    name="CustomerID"
                    placeholder={`C${String((data?.total ?? 0) + 1).padStart(4, '0')}`}
                    defaultValue={`C${String((data?.total ?? 0) + 1).padStart(4, '0')}`}
                    className={fieldClass}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Full Name *</label>
                  <input
                    type="text"
                    name="FullName"
                    required
                    placeholder="e.g. Arjun Kumar"
                    className={fieldClass}
                  />
                </div>
              </div>

              {/* Row 2: Gender + Age */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Gender *</label>
                  <select name="Gender" required className={cn(fieldClass, 'cursor-pointer')}>
                    <option value="">Select gender</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Age *</label>
                  <input
                    type="number"
                    name="Age"
                    required
                    min={1}
                    max={120}
                    placeholder="e.g. 32"
                    className={fieldClass}
                  />
                </div>
              </div>

              {/* Row 3: City + State */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">City</label>
                  <input
                    type="text"
                    name="City"
                    placeholder="e.g. Chennai"
                    className={fieldClass}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">State</label>
                  <input
                    type="text"
                    name="State"
                    placeholder="e.g. Tamil Nadu"
                    className={fieldClass}
                  />
                </div>
              </div>

              {/* Row 4: Membership + Preferred Category */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Membership</label>
                  <select name="Membership" className={cn(fieldClass, 'cursor-pointer')}>
                    <option value="">Select tier</option>
                    <option value="Bronze">Bronze</option>
                    <option value="Silver">Silver</option>
                    <option value="Gold">Gold</option>
                    <option value="Platinum">Platinum</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Preferred Category</label>
                  <select name="PreferredCategory" className={cn(fieldClass, 'cursor-pointer')}>
                    <option value="">Select category</option>
                    {['Men', 'Women', 'Kids', 'Accessories', 'Home & Lifestyle'].map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Row 5: Preferred Fabric + Loyalty Points */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Preferred Fabric</label>
                  <select name="PreferredFabric" className={cn(fieldClass, 'cursor-pointer')}>
                    <option value="">Select fabric</option>
                    {['Cotton', 'Silk', 'Handloom', 'Polyester', 'Linen', 'Leather'].map((f) => (
                      <option key={f} value={f}>{f}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Loyalty Points</label>
                  <input
                    type="number"
                    name="LoyaltyPoints"
                    min={0}
                    defaultValue={0}
                    placeholder="0"
                    className={fieldClass}
                  />
                </div>
              </div>

              {/* Row 6: Join Date */}
              <div>
                <label className="block text-xs font-semibold text-zinc-400 mb-1">Join Date</label>
                <input
                  type="date"
                  name="JoinDate"
                  defaultValue={new Date().toISOString().split('T')[0]}
                  className={fieldClass}
                />
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
                  {isSubmitting ? 'Adding...' : 'Add Customer'}
                </motion.button>
              </div>
            </form>
          </motion.div>
        </motion.div>
      )}

      {/* ─── Customer Detail Modal ──────────────────────────────────────────── */}
      {selectedCustomer && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
          onClick={() => setSelectedCustomer(null)}
        >
          <motion.div
            initial={{ scale: 0.95 }}
            animate={{ scale: 1 }}
            onClick={(e) => e.stopPropagation()}
            className={cn(
              'w-full max-w-2xl rounded-2xl p-6 border max-h-[80vh] overflow-y-auto',
              isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200'
            )}
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className={cn('text-lg font-bold', isDark ? 'text-zinc-100' : 'text-zinc-900')}>
                {selectedCustomer.FullName}
              </h2>
              <button onClick={() => setSelectedCustomer(null)} className="text-zinc-500 hover:text-zinc-300 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 mb-6">
              {[
                ['Customer ID', selectedCustomer.CustomerID],
                ['Gender', selectedCustomer.Gender],
                ['Age', selectedCustomer.Age],
                ['City', selectedCustomer.City],
                ['Membership', selectedCustomer.Membership],
                ['Loyalty Points', formatNumber(selectedCustomer.LoyaltyPoints ?? 0)],
                ['Preferred Category', selectedCustomer.PreferredCategory],
                ['Preferred Fabric', selectedCustomer.PreferredFabric],
                ['Tenure', `${selectedCustomer.CustomerTenureDays ?? 0} days`],
                ['Joined', formatDate(selectedCustomer.JoinDate)],
              ].map(([label, value]) => (
                <div key={String(label)} className="text-sm">
                  <span className="text-zinc-500 block text-xs">{String(label)}</span>
                  <span className={isDark ? 'text-zinc-200' : 'text-zinc-800'}>{String(value ?? '—')}</span>
                </div>
              ))}
            </div>

            {/* Purchase History */}
            <h3 className={cn('text-sm font-semibold mb-3', isDark ? 'text-zinc-300' : 'text-zinc-700')}>
              Recent Purchases ({salesData?.total ?? 0})
            </h3>
            <div className="space-y-2">
              {(salesData?.items ?? []).slice(0, 10).map((sale) => (
                <div
                  key={sale.SaleID}
                  className={cn(
                    'flex items-center justify-between px-3 py-2 rounded-xl text-sm',
                    isDark ? 'bg-zinc-800/50' : 'bg-zinc-50'
                  )}
                >
                  <div>
                    <span className="font-mono text-xs text-zinc-500">{sale.ProductID}</span>
                    <span className="mx-2 text-zinc-600">•</span>
                    <span className={isDark ? 'text-zinc-300' : 'text-zinc-700'}>{sale.SubCategory}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-emerald-500 font-medium">{formatCurrency(sale.FinalPrice)}</span>
                    <span className="text-zinc-500 text-xs ml-2">{formatDate(sale.SaleDate)}</span>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        </motion.div>
      )}
    </motion.div>
  );
}
