/**
 * Customers Page — Retail AI Frontend
 * ======================================
 * Customer management with membership badges, loyalty points,
 * search/filter, and recommendation navigation.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sparkles, Eye, X } from 'lucide-react';
import { useCustomers, useSales } from '../hooks';
import DataTable, { type Column } from '../components/shared/DataTable';
import StatusBadge from '../components/shared/StatusBadge';
import { useTheme } from '../contexts/ThemeContext';
import { cn, formatNumber, formatDate, formatCurrency } from '../utils';
import { fadeIn } from '../animations/variants';
import type { Customer } from '../types';

export default function CustomersPage() {
  const { isDark } = useTheme();
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [membership, setMembership] = useState('');
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);

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
      </div>

      {/* Membership Filter */}
      <div className="flex gap-2">
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
          </div>
        )}
      />

      {/* Customer Detail Modal */}
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
              <button onClick={() => setSelectedCustomer(null)} className="text-zinc-500 hover:text-zinc-300">
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
