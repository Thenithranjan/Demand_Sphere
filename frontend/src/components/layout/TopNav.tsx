/**
 * Top Navigation Bar — Demand Sphere Frontend
 * ==========================================
 * Sticky header with breadcrumbs, search, notifications, theme toggle,
 * and profile dropdown.
 */

import { useLocation, useNavigate } from 'react-router-dom';
import { Moon, Sun, Bell, Search, ChevronRight, Home } from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';
import { cn, getInitials } from '../../utils';
import { NAV_ITEMS } from '../../constants';

export default function TopNav() {
  const { theme, toggleTheme, isDark } = useTheme();
  const { user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  // Build breadcrumb from current path
  const pathSegments = location.pathname.split('/').filter(Boolean);
  const currentPage = NAV_ITEMS.find((item) =>
    location.pathname === item.path ||
    (item.path !== '/dashboard' && location.pathname.startsWith(item.path))
  );

  return (
    <header className={cn(
      'sticky top-0 z-30 flex items-center justify-between px-6 py-3 border-b backdrop-blur-xl transition-colors',
      isDark
        ? 'bg-zinc-950/80 border-zinc-800'
        : 'bg-white/80 border-zinc-200'
    )}>
      {/* ─── Left: Breadcrumbs ────────────────────────────────── */}
      <div className="flex items-center gap-2 text-sm">
        <Home className="w-4 h-4 text-zinc-500" />
        <ChevronRight className="w-3 h-3 text-zinc-600" />
        {pathSegments.map((segment, idx) => (
          <div key={segment} className="flex items-center gap-2">
            <span className={cn(
              'capitalize',
              idx === pathSegments.length - 1
                ? isDark ? 'text-zinc-100 font-medium' : 'text-zinc-900 font-medium'
                : 'text-zinc-500'
            )}>
              {segment}
            </span>
            {idx < pathSegments.length - 1 && (
              <ChevronRight className="w-3 h-3 text-zinc-600" />
            )}
          </div>
        ))}
      </div>

      {/* ─── Right: Actions ───────────────────────────────────── */}
      <div className="flex items-center gap-2">
        {/* Search */}
        <div className={cn(
          'hidden md:flex items-center gap-2 px-3 py-1.5 rounded-xl text-sm transition-colors',
          isDark
            ? 'bg-zinc-800/50 text-zinc-400 border border-zinc-700/50'
            : 'bg-zinc-100 text-zinc-500 border border-zinc-200'
        )}>
          <Search className="w-4 h-4" />
          <span className="text-xs">Search...</span>
          <kbd className={cn(
            'ml-4 px-1.5 py-0.5 rounded text-[10px] font-mono',
            isDark ? 'bg-zinc-700 text-zinc-400' : 'bg-zinc-200 text-zinc-500'
          )}>⌘K</kbd>
        </div>

        {/* Notifications */}
        <button
          onClick={() => navigate('/inventory?tab=alerts')}
          className={cn(
            'relative p-2 rounded-xl transition-colors',
            isDark ? 'hover:bg-zinc-800 text-zinc-400' : 'hover:bg-zinc-100 text-zinc-500'
          )}
        >
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-brand-500 ring-2 ring-zinc-950" />
        </button>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className={cn(
            'p-2 rounded-xl transition-colors',
            isDark ? 'hover:bg-zinc-800 text-zinc-400' : 'hover:bg-zinc-100 text-zinc-500'
          )}
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
          {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>

        {/* Profile Avatar */}
        {user && (
          <div
            onClick={() => navigate('/profile')}
            className={cn(
              'flex items-center gap-2 pl-2 ml-1 border-l cursor-pointer hover:opacity-85 transition-opacity',
              isDark ? 'border-zinc-800' : 'border-zinc-200'
            )}
          >
            <div className="w-8 h-8 rounded-full bg-brand-500/20 flex items-center justify-center text-brand-400 text-xs font-bold">
              {getInitials(user.FullName || user.Username)}
            </div>
            <div className="hidden sm:block">
              <p className={cn('text-sm font-medium', isDark ? 'text-zinc-200' : 'text-zinc-800')}>
                {user.FullName || user.Username}
              </p>
              <p className="text-xs text-zinc-500">{user.Role}</p>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
