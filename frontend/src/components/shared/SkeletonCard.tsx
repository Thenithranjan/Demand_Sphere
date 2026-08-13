/**
 * SkeletonCard — Retail AI Frontend
 * ====================================
 * Shimmer loading skeleton for stats cards and chart containers.
 */

import { cn } from '../../utils';
import { useTheme } from '../../contexts/ThemeContext';

interface SkeletonCardProps {
  className?: string;
  lines?: number;
}

export default function SkeletonCard({ className, lines = 3 }: SkeletonCardProps) {
  const { isDark } = useTheme();

  return (
    <div className={cn(
      'rounded-2xl p-5 space-y-4',
      isDark ? 'bg-zinc-900/60 border border-zinc-800/60' : 'bg-white border border-zinc-200',
      className
    )}>
      <div className={cn(
        'h-3 w-24 rounded-full',
        isDark ? 'animate-shimmer' : 'bg-zinc-200 animate-pulse'
      )} />
      <div className={cn(
        'h-8 w-32 rounded-lg',
        isDark ? 'animate-shimmer' : 'bg-zinc-200 animate-pulse'
      )} />
      {Array.from({ length: lines - 2 }).map((_, i) => (
        <div
          key={i}
          className={cn(
            'h-3 rounded-full',
            isDark ? 'animate-shimmer' : 'bg-zinc-200 animate-pulse'
          )}
          style={{ width: `${60 + Math.random() * 30}%` }}
        />
      ))}
    </div>
  );
}

export function SkeletonTable({ rows = 5 }: { rows?: number }) {
  const { isDark } = useTheme();

  return (
    <div className={cn(
      'rounded-2xl overflow-hidden',
      isDark ? 'bg-zinc-900/60 border border-zinc-800/60' : 'bg-white border border-zinc-200'
    )}>
      {/* Header */}
      <div className={cn(
        'flex gap-4 px-4 py-3 border-b',
        isDark ? 'border-zinc-800' : 'border-zinc-200'
      )}>
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className={cn(
              'h-3 rounded-full flex-1',
              isDark ? 'animate-shimmer' : 'bg-zinc-200 animate-pulse'
            )}
          />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className={cn(
            'flex gap-4 px-4 py-3 border-b last:border-0',
            isDark ? 'border-zinc-800/50' : 'border-zinc-100'
          )}
        >
          {Array.from({ length: 5 }).map((_, j) => (
            <div
              key={j}
              className={cn(
                'h-3 rounded-full flex-1',
                isDark ? 'animate-shimmer' : 'bg-zinc-100 animate-pulse'
              )}
              style={{ animationDelay: `${(i * 5 + j) * 0.05}s` }}
            />
          ))}
        </div>
      ))}
    </div>
  );
}
