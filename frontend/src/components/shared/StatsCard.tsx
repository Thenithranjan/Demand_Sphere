/**
 * StatsCard — Demand Sphere Frontend
 * =================================
 * Animated glassmorphic metric card with icon, title, value,
 * optional trend indicator, and gradient accent stripe.
 */

import { motion } from 'framer-motion';
import { type LucideIcon, TrendingUp, TrendingDown } from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';
import { cn } from '../../utils';
import { staggerItem } from '../../animations/variants';

interface StatsCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  trend?: { value: number; label: string };
  gradient?: string;
  className?: string;
}

export default function StatsCard({ title, value, icon: Icon, trend, gradient, className }: StatsCardProps) {
  const { isDark } = useTheme();

  return (
    <motion.div
      variants={staggerItem}
      className={cn(
        'relative overflow-hidden rounded-2xl p-5 transition-all duration-300 hover-lift group',
        isDark
          ? 'bg-zinc-900/60 border border-zinc-800/60 backdrop-blur-xl'
          : 'bg-white border border-zinc-200/60 shadow-sm',
        className
      )}
    >
      {/* Gradient accent stripe */}
      <div className={cn(
        'absolute top-0 left-0 right-0 h-[2px]',
        gradient || 'bg-gradient-to-r from-brand-500 to-violet-500'
      )} />

      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <p className={cn(
            'text-xs font-medium uppercase tracking-wider',
            isDark ? 'text-zinc-500' : 'text-zinc-400'
          )}>
            {title}
          </p>
          <p className={cn(
            'text-2xl font-bold tracking-tight',
            isDark ? 'text-zinc-100' : 'text-zinc-900'
          )}>
            {value}
          </p>
          {trend && (
            <div className="flex items-center gap-1.5">
              {trend.value >= 0 ? (
                <TrendingUp className="w-3.5 h-3.5 text-emerald-500" />
              ) : (
                <TrendingDown className="w-3.5 h-3.5 text-red-500" />
              )}
              <span className={cn(
                'text-xs font-medium',
                trend.value >= 0 ? 'text-emerald-500' : 'text-red-500'
              )}>
                {trend.value >= 0 ? '+' : ''}{trend.value}%
              </span>
              <span className="text-xs text-zinc-500">{trend.label}</span>
            </div>
          )}
        </div>

        <div className={cn(
          'p-2.5 rounded-xl transition-colors',
          isDark ? 'bg-zinc-800/80 group-hover:bg-brand-500/10' : 'bg-zinc-100 group-hover:bg-brand-50'
        )}>
          <Icon className={cn(
            'w-5 h-5 transition-colors',
            isDark ? 'text-zinc-400 group-hover:text-brand-400' : 'text-zinc-500 group-hover:text-brand-600'
          )} />
        </div>
      </div>
    </motion.div>
  );
}
