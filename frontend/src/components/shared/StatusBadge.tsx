/**
 * StatusBadge — Demand Sphere Frontend
 * ===================================
 * Color-coded badge for inventory status, membership tiers, etc.
 */

import { cn } from '../../utils';

interface StatusBadgeProps {
  status: string;
  colorMap?: Record<string, { bg: string; text: string; dot?: string }>;
  className?: string;
}

const DEFAULT_COLORS: Record<string, { bg: string; text: string; dot: string }> = {
  'Active': { bg: 'bg-emerald-500/10', text: 'text-emerald-500', dot: 'bg-emerald-500' },
  'Inactive': { bg: 'bg-zinc-500/10', text: 'text-zinc-400', dot: 'bg-zinc-500' },
  'Discontinued': { bg: 'bg-red-500/10', text: 'text-red-500', dot: 'bg-red-500' },
  'Healthy': { bg: 'bg-emerald-500/10', text: 'text-emerald-500', dot: 'bg-emerald-500' },
  'Low Stock': { bg: 'bg-amber-500/10', text: 'text-amber-500', dot: 'bg-amber-500' },
  'Critical': { bg: 'bg-red-500/10', text: 'text-red-500', dot: 'bg-red-500' },
  'Overstock': { bg: 'bg-blue-500/10', text: 'text-blue-500', dot: 'bg-blue-500' },
  'Out of Stock': { bg: 'bg-gray-500/10', text: 'text-gray-500', dot: 'bg-gray-500' },
  'Bronze': { bg: 'bg-orange-500/10', text: 'text-orange-400', dot: 'bg-orange-500' },
  'Silver': { bg: 'bg-slate-400/10', text: 'text-slate-300', dot: 'bg-slate-400' },
  'Gold': { bg: 'bg-yellow-500/10', text: 'text-yellow-400', dot: 'bg-yellow-500' },
  'Platinum': { bg: 'bg-violet-500/10', text: 'text-violet-400', dot: 'bg-violet-500' },
};

export default function StatusBadge({ status, colorMap, className }: StatusBadgeProps) {
  const colors = colorMap || DEFAULT_COLORS;
  const style = colors[status] || { bg: 'bg-zinc-500/10', text: 'text-zinc-400', dot: 'bg-zinc-500' };

  return (
    <span className={cn(
      'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium',
      style.bg,
      style.text,
      className
    )}>
      {style.dot && <span className={cn('w-1.5 h-1.5 rounded-full', style.dot)} />}
      {status}
    </span>
  );
}
