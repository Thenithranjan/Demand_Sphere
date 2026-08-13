/**
 * Dashboard Layout — Retail AI Frontend
 * ========================================
 * Root layout wrapping Sidebar + TopNav + <Outlet /> + Footer.
 * Uses Framer Motion for smooth page transitions on route changes.
 *
 * Component Architecture:
 * ┌──────────────────────────────────────┐
 * │ Sidebar │  TopNav                    │
 * │         │  ┌────────────────────┐    │
 * │         │  │  <Outlet />        │    │
 * │         │  │  (Page Content)    │    │
 * │         │  └────────────────────┘    │
 * │         │  Footer                    │
 * └──────────────────────────────────────┘
 */

import { Outlet, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import Sidebar from './Sidebar';
import TopNav from './TopNav';
import Footer from './Footer';
import { pageTransition } from '../../animations/variants';
import { useTheme } from '../../contexts/ThemeContext';
import { cn } from '../../utils';

export default function DashboardLayout() {
  const location = useLocation();
  const { isDark } = useTheme();

  return (
    <div className="flex h-screen overflow-hidden">
      {/* ─── Sidebar ──────────────────────────────────────────── */}
      <Sidebar />

      {/* ─── Main Content Area ────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <TopNav />

        <main className={cn(
          'flex-1 overflow-y-auto',
          isDark ? 'bg-zinc-950' : 'bg-gray-50'
        )}>
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              variants={pageTransition}
              initial="initial"
              animate="animate"
              exit="exit"
              className="p-6"
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>

        <Footer />
      </div>
    </div>
  );
}
