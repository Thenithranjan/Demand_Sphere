/**
 * Sales Page — Retail AI Frontend
 * ==================================
 * Transaction log displaying invoice list, seasonal tags,
 * and festival categories.
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import { useSales } from '../hooks';
import DataTable, { type Column } from '../components/shared/DataTable';
import StatusBadge from '../components/shared/StatusBadge';
import { useTheme } from '../contexts/ThemeContext';
import { cn, formatDate, formatCurrency } from '../utils';
import { fadeIn } from '../animations/variants';
import type { Sale } from '../types';

export default function SalesPage() {
  const { isDark } = useTheme();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  const { data, isLoading } = useSales({
    skip: (page - 1) * pageSize,
    limit: pageSize,
  });

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
      <div>
        <h1 className={cn('text-2xl font-bold', isDark ? 'text-zinc-100' : 'text-zinc-900')}>Sales Transactions</h1>
        <p className="text-sm text-zinc-500 mt-1">Review transaction logs, invoice mappings, and seasonal attributes • {data?.total ?? 0} sales records</p>
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
      />
    </motion.div>
  );
}
