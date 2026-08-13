/**
 * Sidebar Navigation — Retail AI Frontend
 * ==========================================
 * Collapsible sidebar with animated route links, active highlighting,
 * user avatar, and branding. Collapses to an icon-only rail on toggle.
 * On mobile (<lg), it renders as a Sheet overlay.
 */

import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChevronLeft,
  ChevronRight,
  LogOut,
  Sparkles,
  Menu,
  Lock,
} from 'lucide-react';
import { NAV_ITEMS, APP_NAME } from '../../constants';
import { useAuth } from '../../contexts/AuthContext';
import { cn, getInitials } from '../../utils';
import { useMediaQuery } from '../../hooks';

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [isRestrictedModalOpen, setIsRestrictedModalOpen] = useState(false);
  const { user, logout } = useAuth();
  const location = useLocation();
  const isMobile = useMediaQuery('(max-width: 1023px)');

  const sidebarContent = (
    <div className="flex flex-col h-full">
      {/* ─── Brand ──────────────────────────────────────────────── */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-zinc-800 dark:border-zinc-800">
        <div className="w-9 h-9 rounded-xl gradient-brand flex items-center justify-center shrink-0">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: 'auto' }}
              exit={{ opacity: 0, width: 0 }}
              className="overflow-hidden whitespace-nowrap"
            >
              <h1 className="text-lg font-bold gradient-brand-text">{APP_NAME}</h1>
              <p className="text-[10px] text-zinc-500 -mt-0.5">Intelligence Suite</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ─── Navigation Links ───────────────────────────────────── */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          let label = item.label as string;
          if (item.path === '/admin') {
            if (user?.Role === 'Manager') {
              label = 'Manager Section';
            } else if (user?.Role === 'Employee') {
              label = 'Employee Section';
            } else {
              label = 'Admin Section';
            }
          }

          const isActive = location.pathname === item.path ||
            (item.path !== '/dashboard' && location.pathname.startsWith(item.path));

          const isModelManagement = item.path === '/model-management';
          const isEmployee = user?.Role === 'Employee';

          const handleClick = (e: React.MouseEvent) => {
            if (isModelManagement && isEmployee) {
              e.preventDefault();
              setIsRestrictedModalOpen(true);
              return;
            }
            if (isMobile) {
              setMobileOpen(false);
            }
          };

          return (
            <NavLink
              key={item.path}
              to={isModelManagement && isEmployee ? '#' : item.path}
              onClick={handleClick}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group',
                isActive
                  ? 'bg-brand-500/10 text-brand-400'
                  : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/50'
              )}
            >
              <item.icon className={cn(
                'w-5 h-5 shrink-0 transition-colors',
                isActive ? 'text-brand-400' : 'text-zinc-500 group-hover:text-zinc-300'
              )} />
              <AnimatePresence>
                {!collapsed && (
                  <motion.span
                    initial={{ opacity: 0, width: 0 }}
                    animate={{ opacity: 1, width: 'auto' }}
                    exit={{ opacity: 0, width: 0 }}
                    className="overflow-hidden whitespace-nowrap"
                  >
                    {label}
                  </motion.span>
                )}
              </AnimatePresence>
              {isActive && (
                <motion.div
                  layoutId="sidebar-active"
                  className="absolute left-0 w-[3px] h-6 rounded-r-full bg-brand-500"
                  transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                />
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* ─── User Section ───────────────────────────────────────── */}
      {user && (
        <div className="px-3 py-4 border-t border-zinc-800">
          <div className="flex items-center gap-3 px-3 py-2">
            <div className="w-8 h-8 rounded-full bg-brand-500/20 flex items-center justify-center text-brand-400 text-xs font-bold shrink-0">
              {getInitials(user.FullName || user.Username)}
            </div>
            <AnimatePresence>
              {!collapsed && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex-1 min-w-0"
                >
                  <p className="text-sm font-medium text-zinc-200 truncate">{user.FullName || user.Username}</p>
                  <p className="text-xs text-zinc-500 truncate">{user.Role}</p>
                </motion.div>
              )}
            </AnimatePresence>
            {!collapsed && (
              <button
                onClick={logout}
                className="p-1.5 rounded-lg text-zinc-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                title="Logout"
              >
                <LogOut className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      )}

      {/* ─── Collapse Toggle (desktop only) ─────────────────────── */}
      {!isMobile && (
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="absolute -right-3 top-20 w-6 h-6 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center text-zinc-400 hover:text-zinc-100 hover:bg-zinc-700 transition-colors z-50"
        >
          {collapsed ? <ChevronRight className="w-3.5 h-3.5" /> : <ChevronLeft className="w-3.5 h-3.5" />}
        </button>
      )}
    </div>
  );

  // ─── Mobile: Overlay Sheet ────────────────────────────────────────────────
  if (isMobile) {
    return (
      <>
        <button
          onClick={() => setMobileOpen(true)}
          className="fixed top-4 left-4 z-50 p-2 rounded-xl bg-zinc-800/80 backdrop-blur-sm text-zinc-300 hover:text-white lg:hidden"
        >
          <Menu className="w-5 h-5" />
        </button>

        <AnimatePresence>
          {mobileOpen && (
            <>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setMobileOpen(false)}
                className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
              />
              <motion.aside
                initial={{ x: -280 }}
                animate={{ x: 0 }}
                exit={{ x: -280 }}
                transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                className="fixed left-0 top-0 bottom-0 w-[260px] bg-zinc-900/95 backdrop-blur-xl border-r border-zinc-800 z-50 overflow-hidden"
              >
                {sidebarContent}
              </motion.aside>
            </>
          )}
        </AnimatePresence>
      </>
    );
  }

  // ─── Desktop: Fixed Sidebar ───────────────────────────────────────────────
  return (
    <>
      <motion.aside
        animate={{ width: collapsed ? 72 : 260 }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        className="relative hidden lg:flex flex-col h-screen bg-zinc-900/80 backdrop-blur-xl border-r border-zinc-800 shrink-0 overflow-hidden"
      >
        {sidebarContent}
      </motion.aside>

      <AnimatePresence>
        {isRestrictedModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsRestrictedModalOpen(false)}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            />
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              transition={{ type: 'spring', duration: 0.3 }}
              className="relative w-full max-w-md p-6 overflow-hidden text-left align-middle transition-all transform bg-zinc-900 border border-zinc-800 shadow-2xl rounded-3xl z-10"
            >
              <div className="flex flex-col items-center text-center space-y-4">
                <div className="w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center text-red-500">
                  <Lock className="w-6 h-6" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-lg font-bold text-zinc-100">Access Restricted</h3>
                  <p className="text-sm text-zinc-400">
                    AI Model Management is available only to Administrators and Store Managers.
                  </p>
                </div>
                <div className="w-full p-3 rounded-xl bg-zinc-800/40 border border-zinc-800/85 text-xs text-zinc-400 space-y-1">
                  <div>Your current role: <span className="font-semibold text-zinc-200">Employee</span></div>
                </div>
                <button
                  onClick={() => setIsRestrictedModalOpen(false)}
                  className="w-full py-2.5 rounded-xl text-sm font-semibold text-zinc-200 bg-zinc-800 hover:bg-zinc-700 active:bg-zinc-800 border border-zinc-750 transition-colors cursor-pointer"
                >
                  Close
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}
