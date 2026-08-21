/**
 * Top Navigation Bar — Demand Sphere Frontend
 * ==========================================
 * Sticky header with breadcrumbs, interactive global page search,
 * notifications, theme toggle, and profile dropdown.
 */

import { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Moon, Sun, Bell, Search, ChevronRight, Home, X, ArrowRight, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';
import { cn, getInitials } from '../../utils';
import { NAV_ITEMS } from '../../constants';

const PAGE_METADATA: Record<string, { description: string; keywords: string[] }> = {
  '/dashboard': { description: 'Overview of key metrics, KPIs & quick stats', keywords: ['home', 'kpi', 'revenue', 'overview'] },
  '/products': { description: 'Product catalog, pricing, categories & inventory tags', keywords: ['textile', 'clothes', 'saree', 'shirt', 'price', 'catalog', 'stock'] },
  '/customers': { description: 'Customer directory, membership tiers & loyalty points', keywords: ['users', 'loyalty', 'clients', 'gold', 'silver', 'platinum'] },
  '/sales': { description: 'Invoice history, transaction logs & seasonal tags', keywords: ['invoices', 'billing', 'orders', 'transactions', 'festivals'] },
  '/inventory': { description: 'Stock levels, warehouse health, alerts & reorders', keywords: ['warehouse', 'low stock', 'overstock', 'reorder', 'alerts'] },
  '/forecast': { description: 'AI demand prediction, XGBoost trends & seasonality', keywords: ['predictions', 'ai', 'xgboost', 'demand', 'future'] },
  '/recommendations': { description: 'AI-powered collaborative & content product recs', keywords: ['cross sell', 'upsell', 'ai recs', 'suggestions'] },
  '/analytics': { description: 'Business intelligence, revenue trends & customer segments', keywords: ['charts', 'bi', 'reports', 'insights', 'ltv'] },
  '/reports': { description: 'Export PDF & CSV summary reports', keywords: ['download', 'pdf', 'csv', 'export', 'print'] },
  '/model-management': { description: 'MLOps model training lifecycle & version audit', keywords: ['ml', 'training', 'retrain', 'models', 'version'] },
  '/admin': { description: 'User management & staff permission board', keywords: ['staff', 'employee', 'roles', 'permissions', 'passwords'] },
  '/profile': { description: 'Account settings, credentials & theme preference', keywords: ['account', 'user', 'settings', 'theme', 'password'] },
};

export default function TopNav() {
  const { theme, toggleTheme, isDark } = useTheme();
  const { user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Build breadcrumb from current path
  const pathSegments = location.pathname.split('/').filter(Boolean);

  // Keyboard shortcut (⌘K / Ctrl+K) handler
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setIsSearchOpen(true);
        setTimeout(() => searchInputRef.current?.focus(), 50);
      } else if (e.key === 'Escape') {
        setIsSearchOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsSearchOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Filter items matching query
  const filteredItems = NAV_ITEMS.filter((item) => {
    if (!searchQuery.trim()) return true;
    const query = searchQuery.toLowerCase().trim();
    const meta = PAGE_METADATA[item.path];
    const matchTitle = item.label.toLowerCase().includes(query);
    const matchPath = item.path.toLowerCase().includes(query);
    const matchDesc = meta?.description.toLowerCase().includes(query);
    const matchKey = meta?.keywords.some((k) => k.toLowerCase().includes(query));
    return matchTitle || matchPath || matchDesc || matchKey;
  });

  const handleSelectPage = (path: string) => {
    navigate(path);
    setSearchQuery('');
    setIsSearchOpen(false);
  };

  const handleKeyDownInput = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && filteredItems.length > 0) {
      handleSelectPage(filteredItems[0].path);
    }
  };

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
        {/* Interactive Search Bar */}
        <div ref={containerRef} className="relative">
          <div
            onClick={() => {
              setIsSearchOpen(true);
              searchInputRef.current?.focus();
            }}
            className={cn(
              'flex items-center gap-2 px-3 py-1.5 rounded-xl text-sm transition-all cursor-pointer min-w-[200px] md:min-w-[260px]',
              isDark
                ? 'bg-zinc-800/50 hover:bg-zinc-800 text-zinc-300 border border-zinc-700/50 focus-within:border-brand-500/50'
                : 'bg-zinc-100 hover:bg-zinc-200/80 text-zinc-700 border border-zinc-200 focus-within:border-brand-500/50'
            )}
          >
            <Search className="w-4 h-4 text-zinc-400 shrink-0" />
            <input
              ref={searchInputRef}
              type="text"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                if (!isSearchOpen) setIsSearchOpen(true);
              }}
              onFocus={() => setIsSearchOpen(true)}
              onKeyDown={handleKeyDownInput}
              placeholder="Search pages & features..."
              className={cn(
                'bg-transparent border-none outline-none w-full text-xs placeholder:text-zinc-500',
                isDark ? 'text-zinc-100' : 'text-zinc-900'
              )}
            />
            {searchQuery ? (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setSearchQuery('');
                }}
                className="text-zinc-400 hover:text-zinc-200"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            ) : (
              <kbd className={cn(
                'hidden md:inline-flex px-1.5 py-0.5 rounded text-[10px] font-mono shrink-0',
                isDark ? 'bg-zinc-700 text-zinc-400' : 'bg-zinc-200 text-zinc-500'
              )}>⌘K</kbd>
            )}
          </div>

          {/* Search Results Dropdown Overlay */}
          <AnimatePresence>
            {isSearchOpen && (
              <motion.div
                initial={{ opacity: 0, y: 8, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 8, scale: 0.98 }}
                transition={{ duration: 0.15 }}
                className={cn(
                  'absolute right-0 mt-2 w-80 md:w-96 rounded-2xl border shadow-2xl overflow-hidden z-50 backdrop-blur-2xl',
                  isDark
                    ? 'bg-zinc-900/95 border-zinc-800 text-zinc-100'
                    : 'bg-white/95 border-zinc-200 text-zinc-900'
                )}
              >
                <div className="p-2 border-b border-zinc-800/40 text-[11px] font-semibold tracking-wider text-zinc-500 uppercase flex items-center justify-between px-3">
                  <span>Navigation & Pages</span>
                  <span>{filteredItems.length} result{filteredItems.length === 1 ? '' : 's'}</span>
                </div>

                <div className="max-h-80 overflow-y-auto p-1.5 space-y-1">
                  {filteredItems.length > 0 ? (
                    filteredItems.map((item) => {
                      const Icon = item.icon;
                      const meta = PAGE_METADATA[item.path];
                      const isCurrent = location.pathname === item.path;

                      return (
                        <div
                          key={item.path}
                          onClick={() => handleSelectPage(item.path)}
                          className={cn(
                            'group flex items-center justify-between p-2.5 rounded-xl cursor-pointer transition-all',
                            isCurrent
                              ? 'bg-brand-500/10 text-brand-400 font-medium'
                              : isDark
                                ? 'hover:bg-zinc-800/80 text-zinc-200'
                                : 'hover:bg-zinc-100 text-zinc-800'
                          )}
                        >
                          <div className="flex items-center gap-3 min-w-0">
                            <div className={cn(
                              'p-2 rounded-lg transition-colors',
                              isCurrent
                                ? 'bg-brand-500/20 text-brand-400'
                                : isDark
                                  ? 'bg-zinc-800 text-zinc-400 group-hover:text-brand-400 group-hover:bg-brand-500/10'
                                  : 'bg-zinc-100 text-zinc-500 group-hover:text-brand-600 group-hover:bg-brand-50'
                            )}>
                              <Icon className="w-4 h-4" />
                            </div>
                            <div className="min-w-0">
                              <p className="text-xs font-semibold truncate group-hover:text-brand-400 transition-colors">
                                {item.label}
                              </p>
                              {meta && (
                                <p className="text-[11px] text-zinc-500 truncate mt-0.5">
                                  {meta.description}
                                </p>
                              )}
                            </div>
                          </div>
                          <ArrowRight className="w-3.5 h-3.5 text-zinc-600 opacity-0 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all shrink-0 ml-2" />
                        </div>
                      );
                    })
                  ) : (
                    <div className="p-6 text-center text-zinc-500 text-xs">
                      No matching pages found for "{searchQuery}"
                    </div>
                  )}
                </div>

                <div className="p-2 border-t border-zinc-800/40 bg-zinc-950/40 text-[11px] text-zinc-500 flex items-center justify-between px-3">
                  <span className="flex items-center gap-1">
                    <Sparkles className="w-3 h-3 text-brand-400" />
                    Click to navigate instantly
                  </span>
                  <span>ESC to close</span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
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
