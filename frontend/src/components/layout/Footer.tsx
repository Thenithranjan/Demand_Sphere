/**
 * Footer — Retail AI Frontend
 * ==============================
 * Minimal footer with project name, version, and copyright.
 */

import { useTheme } from '../../contexts/ThemeContext';
import { cn } from '../../utils';
import { APP_NAME, APP_VERSION } from '../../constants';

export default function Footer() {
  const { isDark } = useTheme();

  return (
    <footer className={cn(
      'px-6 py-4 border-t text-center text-xs transition-colors',
      isDark
        ? 'bg-zinc-950/50 border-zinc-800 text-zinc-500'
        : 'bg-white/50 border-zinc-200 text-zinc-400'
    )}>
      <p>
        © {new Date().getFullYear()} {APP_NAME} — AI-Powered Retail Intelligence System · v{APP_VERSION}
      </p>
    </footer>
  );
}
