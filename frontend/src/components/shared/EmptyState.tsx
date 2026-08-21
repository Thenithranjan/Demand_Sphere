/**
 * EmptyState — Demand Sphere Frontend
 * ==================================
 * Illustrated empty state with icon, message, and optional action button.
 */

import { type LucideIcon, Inbox } from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';
import { cn } from '../../utils';

interface EmptyStateProps {
  icon?: LucideIcon;
  title?: string;
  description?: string;
  action?: { label: string; onClick: () => void };
}

export default function EmptyState({
  icon: Icon = Inbox,
  title = 'No data found',
  description = 'There are no records to display at the moment.',
  action,
}: EmptyStateProps) {
  const { isDark } = useTheme();

  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <div className={cn(
        'w-16 h-16 rounded-2xl flex items-center justify-center mb-4',
        isDark ? 'bg-zinc-800' : 'bg-zinc-100'
      )}>
        <Icon className={cn('w-8 h-8', isDark ? 'text-zinc-600' : 'text-zinc-400')} />
      </div>
      <h3 className={cn(
        'text-lg font-semibold mb-1',
        isDark ? 'text-zinc-300' : 'text-zinc-700'
      )}>
        {title}
      </h3>
      <p className={cn(
        'text-sm text-center max-w-sm',
        isDark ? 'text-zinc-500' : 'text-zinc-400'
      )}>
        {description}
      </p>
      {action && (
        <button
          onClick={action.onClick}
          className="mt-4 px-4 py-2 rounded-xl text-sm font-medium gradient-brand text-white hover:opacity-90 transition-opacity"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
