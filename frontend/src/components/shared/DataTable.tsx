/**
 * DataTable — Demand Sphere Frontend
 * =================================
 * Reusable sortable/filterable table with pagination, search,
 * and loading skeleton support.
 */

import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Search, ChevronLeft, ChevronRight, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';
import { cn } from '../../utils';
import { useDebounce } from '../../hooks';
import { SkeletonTable } from './SkeletonCard';
import EmptyState from './EmptyState';

export interface Column<T> {
  key: string;
  label: string;
  sortable?: boolean;
  render?: (item: T) => React.ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  isLoading?: boolean;
  searchPlaceholder?: string;
  searchKeys?: string[];
  totalItems?: number;
  page?: number;
  pageSize?: number;
  onPageChange?: (page: number) => void;
  onPageSizeChange?: (size: number) => void;
  actions?: (item: T) => React.ReactNode;
}

export default function DataTable<T>({
  data,
  columns,
  isLoading,
  searchPlaceholder = 'Search...',
  searchKeys = [],
  totalItems,
  page = 1,
  pageSize = 20,
  onPageChange,
  onPageSizeChange,
  actions,
}: DataTableProps<T>) {
  const { isDark } = useTheme();
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const debouncedSearch = useDebounce(search, 300);

  // Client-side filtering
  const filteredData = useMemo(() => {
    if (!debouncedSearch || searchKeys.length === 0) return data;
    const q = debouncedSearch.toLowerCase();
    return data.filter((item) =>
      searchKeys.some((key) => {
        const val = (item as any)[key];
        return val != null && String(val).toLowerCase().includes(q);
      })
    );
  }, [data, debouncedSearch, searchKeys]);

  // Client-side sorting
  const sortedData = useMemo(() => {
    if (!sortKey) return filteredData;
    return [...filteredData].sort((a, b) => {
      const aVal = (a as any)[sortKey];
      const bVal = (b as any)[sortKey];
      if (aVal == null) return 1;
      if (bVal == null) return -1;
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortDir === 'asc' ? aVal - bVal : bVal - aVal;
      }
      const cmp = String(aVal).localeCompare(String(bVal));
      return sortDir === 'asc' ? cmp : -cmp;
    });
  }, [filteredData, sortKey, sortDir]);

  const totalPages = totalItems ? Math.ceil(totalItems / pageSize) : Math.ceil(sortedData.length / pageSize);

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  if (isLoading) return <SkeletonTable rows={8} />;

  return (
    <div className={cn(
      'rounded-2xl overflow-hidden border',
      isDark ? 'bg-zinc-900/60 border-zinc-800/60' : 'bg-white border-zinc-200'
    )}>
      {/* ─── Toolbar ──────────────────────────────────────────── */}
      <div className={cn(
        'flex flex-wrap items-center justify-between gap-3 px-4 py-3 border-b',
        isDark ? 'border-zinc-800' : 'border-zinc-200'
      )}>
        <div className={cn(
          'flex items-center gap-2 px-3 py-1.5 rounded-xl text-sm flex-1 max-w-xs',
          isDark
            ? 'bg-zinc-800/50 text-zinc-400 border border-zinc-700/50'
            : 'bg-zinc-50 text-zinc-500 border border-zinc-200'
        )}>
          <Search className="w-4 h-4 shrink-0" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={searchPlaceholder}
            className="bg-transparent outline-none text-sm w-full placeholder:text-zinc-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-zinc-500">Rows:</span>
          <select
            value={pageSize}
            onChange={(e) => onPageSizeChange?.(Number(e.target.value))}
            className={cn(
              'text-xs rounded-lg px-2 py-1 outline-none',
              isDark ? 'bg-zinc-800 text-zinc-300 border-zinc-700' : 'bg-zinc-50 text-zinc-700 border-zinc-200',
              'border'
            )}
          >
            {[10, 20, 50, 100].map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </div>
      </div>

      {/* ─── Table ────────────────────────────────────────────── */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className={cn(
              'border-b',
              isDark ? 'border-zinc-800 bg-zinc-900/30' : 'border-zinc-200 bg-zinc-50'
            )}>
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={cn(
                    'px-4 py-3 text-left text-xs font-medium uppercase tracking-wider',
                    isDark ? 'text-zinc-500' : 'text-zinc-400',
                    col.sortable && 'cursor-pointer select-none hover:text-zinc-300',
                    col.className
                  )}
                  onClick={() => col.sortable && handleSort(col.key)}
                >
                  <span className="flex items-center gap-1">
                    {col.label}
                    {col.sortable && (
                      sortKey === col.key
                        ? sortDir === 'asc'
                          ? <ArrowUp className="w-3 h-3" />
                          : <ArrowDown className="w-3 h-3" />
                        : <ArrowUpDown className="w-3 h-3 opacity-30" />
                    )}
                  </span>
                </th>
              ))}
              {actions && <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-zinc-500">Actions</th>}
            </tr>
          </thead>
          <tbody>
            {sortedData.length === 0 ? (
              <tr>
                <td colSpan={columns.length + (actions ? 1 : 0)}>
                  <EmptyState />
                </td>
              </tr>
            ) : (
              sortedData.map((item, idx) => (
                <motion.tr
                  key={idx}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: idx * 0.02 }}
                  className={cn(
                    'border-b last:border-0 transition-colors',
                    isDark
                      ? 'border-zinc-800/50 hover:bg-zinc-800/30'
                      : 'border-zinc-100 hover:bg-zinc-50'
                  )}
                >
                  {columns.map((col) => (
                    <td key={col.key} className={cn('px-4 py-3', col.className)}>
                      {col.render ? col.render(item) : String((item as any)[col.key] ?? '—')}
                    </td>
                  ))}
                  {actions && (
                    <td className="px-4 py-3 text-right">
                      {actions(item)}
                    </td>
                  )}
                </motion.tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* ─── Pagination ───────────────────────────────────────── */}
      <div className={cn(
        'flex items-center justify-between px-4 py-3 border-t',
        isDark ? 'border-zinc-800' : 'border-zinc-200'
      )}>
        <span className="text-xs text-zinc-500">
          Showing {sortedData.length} of {totalItems ?? sortedData.length} records
        </span>
        <div className="flex items-center gap-1">
          <button
            onClick={() => onPageChange?.(page - 1)}
            disabled={page <= 1}
            className={cn(
              'p-1.5 rounded-lg disabled:opacity-30 transition-colors',
              isDark ? 'hover:bg-zinc-800 text-zinc-400' : 'hover:bg-zinc-100 text-zinc-500'
            )}
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="text-xs text-zinc-400 px-2">
            Page {page} of {totalPages || 1}
          </span>
          <button
            onClick={() => onPageChange?.(page + 1)}
            disabled={page >= totalPages}
            className={cn(
              'p-1.5 rounded-lg disabled:opacity-30 transition-colors',
              isDark ? 'hover:bg-zinc-800 text-zinc-400' : 'hover:bg-zinc-100 text-zinc-500'
            )}
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
