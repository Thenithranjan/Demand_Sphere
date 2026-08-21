/**
 * Application Constants — Retail AI Frontend
 * =============================================
 * Centralized configuration for navigation, chart colors, status maps, and labels.
 */

import {
  LayoutDashboard,
  Package,
  Users,
  Warehouse,
  TrendingUp,
  Sparkles,
  BarChart3,
  FileText,
  UserCircle,
  ShoppingCart,
  Shield,
  Brain,
} from 'lucide-react';

// ─── Sidebar Navigation Items ────────────────────────────────────────────────
export const NAV_ITEMS = [
  { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { label: 'Products', path: '/products', icon: Package },
  { label: 'Customers', path: '/customers', icon: Users },
  { label: 'Sales', path: '/sales', icon: ShoppingCart },
  { label: 'Inventory', path: '/inventory', icon: Warehouse },
  { label: 'Forecast', path: '/forecast', icon: TrendingUp },
  { label: 'Recommendations', path: '/recommendations', icon: Sparkles },
  { label: 'Analytics', path: '/analytics', icon: BarChart3 },
  { label: 'Reports', path: '/reports', icon: FileText },
  { label: 'AI Model Management', path: '/model-management', icon: Brain },
  { label: 'Admin Section', path: '/admin', icon: Shield },
  { label: 'Profile', path: '/profile', icon: UserCircle },
] as const;

// ─── Chart Color Palette ─────────────────────────────────────────────────────
export const CHART_COLORS = [
  '#6366f1', // indigo
  '#8b5cf6', // violet
  '#06b6d4', // cyan
  '#10b981', // emerald
  '#f59e0b', // amber
  '#ef4444', // red
  '#ec4899', // pink
  '#14b8a6', // teal
  '#f97316', // orange
  '#3b82f6', // blue
];

export const CHART_GRADIENT = {
  primary: { start: '#6366f1', end: '#8b5cf6' },
  success: { start: '#10b981', end: '#14b8a6' },
  warning: { start: '#f59e0b', end: '#f97316' },
  danger: { start: '#ef4444', end: '#f97316' },
};

// ─── Inventory Status Color Map ──────────────────────────────────────────────
export const INVENTORY_STATUS_COLORS: Record<string, { bg: string; text: string; dot: string }> = {
  'Healthy': { bg: 'bg-emerald-500/10', text: 'text-emerald-500', dot: 'bg-emerald-500' },
  'Low Stock': { bg: 'bg-amber-500/10', text: 'text-amber-500', dot: 'bg-amber-500' },
  'Critical': { bg: 'bg-red-500/10', text: 'text-red-500', dot: 'bg-red-500' },
  'Overstock': { bg: 'bg-blue-500/10', text: 'text-blue-500', dot: 'bg-blue-500' },
  'Out of Stock': { bg: 'bg-gray-500/10', text: 'text-gray-500', dot: 'bg-gray-500' },
};

// ─── Membership Tier Colors ──────────────────────────────────────────────────
export const MEMBERSHIP_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  'Bronze': { bg: 'bg-orange-500/10', text: 'text-orange-500', border: 'border-orange-500/30' },
  'Silver': { bg: 'bg-slate-400/10', text: 'text-slate-400', border: 'border-slate-400/30' },
  'Gold': { bg: 'bg-yellow-500/10', text: 'text-yellow-500', border: 'border-yellow-500/30' },
  'Platinum': { bg: 'bg-violet-500/10', text: 'text-violet-500', border: 'border-violet-500/30' },
};

// ─── Recommendation Action Labels ────────────────────────────────────────────
export const RECOMMENDATION_LABELS: Record<string, { color: string; label: string }> = {
  'Reorder Immediately': { color: 'text-red-500', label: '🔴 Reorder Immediately' },
  'Plan Reorder': { color: 'text-amber-500', label: '🟡 Plan Reorder' },
  'Stock OK': { color: 'text-emerald-500', label: '🟢 Stock OK' },
  'Promote/Discount': { color: 'text-blue-500', label: '🔵 Promote / Discount' },
};

// ─── API Base URL ────────────────────────────────────────────────────────────
const rawApiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
const cleanedUrl = rawApiUrl.replace(/\/+$/, '');
export const API_BASE_URL = cleanedUrl.endsWith('/api/v1')
  ? cleanedUrl
  : `${cleanedUrl}/api/v1`;

// ─── Application Info ────────────────────────────────────────────────────────
export const APP_NAME = 'RetailAI';
export const APP_VERSION = '1.0.0';
export const APP_DESCRIPTION = 'AI-Powered Retail Intelligence System';
