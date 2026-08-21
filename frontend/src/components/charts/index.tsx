/**
 * Reusable Chart Components — Demand Sphere Frontend
 * =================================================
 * All chart wrappers use Recharts with consistent theming,
 * custom tooltips, and Framer Motion reveal animations.
 */

import { motion } from 'framer-motion';
import {
  AreaChart, Area, LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import { chartReveal } from '../../animations/variants';
import { useTheme } from '../../contexts/ThemeContext';
import { cn, formatCurrency, formatNumber } from '../../utils';
import { CHART_COLORS } from '../../constants';

// ─── Shared Chart Card Wrapper ───────────────────────────────────────────────
interface ChartCardProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  className?: string;
}

export function ChartCard({ title, subtitle, children, className }: ChartCardProps) {
  const { isDark } = useTheme();

  return (
    <motion.div
      variants={chartReveal}
      initial="hidden"
      animate="visible"
      className={cn(
        'rounded-2xl p-5 border transition-colors',
        isDark
          ? 'bg-zinc-900/60 border-zinc-800/60 backdrop-blur-xl'
          : 'bg-white border-zinc-200 shadow-sm',
        className
      )}
    >
      <div className="mb-4">
        <h3 className={cn('text-sm font-semibold', isDark ? 'text-zinc-200' : 'text-zinc-800')}>{title}</h3>
        {subtitle && <p className="text-xs text-zinc-500 mt-0.5">{subtitle}</p>}
      </div>
      {children}
    </motion.div>
  );
}

// ─── Custom Tooltip ──────────────────────────────────────────────────────────
function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-zinc-900/95 backdrop-blur-lg border border-zinc-700 rounded-xl px-3 py-2 shadow-xl">
      <p className="text-xs text-zinc-400 mb-1">{label}</p>
      {payload.map((p: any, i: number) => (
        <p key={i} className="text-sm font-medium" style={{ color: p.color }}>
          {p.name}: {typeof p.value === 'number' && p.value > 1000 ? formatNumber(p.value) : p.value}
        </p>
      ))}
    </div>
  );
}

// ─── Sales Area Chart ────────────────────────────────────────────────────────
interface SalesAreaChartProps {
  data: Array<{ month: string; total_quantity: number; total_revenue: number }>;
}

export function SalesAreaChart({ data }: SalesAreaChartProps) {
  return (
    <ChartCard title="Monthly Sales Trend" subtitle="Quantity sold over time">
      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="salesGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={CHART_COLORS[0]} stopOpacity={0.3} />
              <stop offset="100%" stopColor={CHART_COLORS[0]} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
          <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#71717a' }} tickLine={false} axisLine={false} />
          <YAxis tick={{ fontSize: 11, fill: '#71717a' }} tickLine={false} axisLine={false} />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey="total_quantity"
            stroke={CHART_COLORS[0]}
            fill="url(#salesGradient)"
            strokeWidth={2}
            name="Quantity"
          />
        </AreaChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

// ─── Revenue Trend Line Chart ────────────────────────────────────────────────
interface RevenueTrendChartProps {
  data: Array<{ month: string; total_revenue: number; total_quantity: number }>;
}

export function RevenueTrendChart({ data }: RevenueTrendChartProps) {
  return (
    <ChartCard title="Revenue Trend" subtitle="Monthly revenue performance">
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
          <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#71717a' }} tickLine={false} axisLine={false} />
          <YAxis tick={{ fontSize: 11, fill: '#71717a' }} tickLine={false} axisLine={false} tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}K`} />
          <Tooltip content={<CustomTooltip />} />
          <Line type="monotone" dataKey="total_revenue" stroke={CHART_COLORS[1]} strokeWidth={2.5} dot={false} name="Revenue" />
        </LineChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

// ─── Category Pie Chart ──────────────────────────────────────────────────────
interface CategoryPieChartProps {
  data: Array<{ SubCategory: string; total_revenue: number }>;
}

export function CategoryPieChart({ data }: CategoryPieChartProps) {
  const top8 = data.slice(0, 8);

  return (
    <ChartCard title="Category Distribution" subtitle="Revenue by sub-category">
      <ResponsiveContainer width="100%" height={280}>
        <PieChart>
          <Pie
            data={top8}
            dataKey="total_revenue"
            nameKey="SubCategory"
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            paddingAngle={3}
            strokeWidth={0}
          >
            {top8.map((_, idx) => (
              <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend
            verticalAlign="bottom"
            height={36}
            formatter={(value: string) => (
              <span className="text-xs text-zinc-400">{value}</span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

// ─── Top Products Bar Chart ──────────────────────────────────────────────────
interface TopProductsBarChartProps {
  data: Array<{ ProductName: string; revenue: number }>;
}

export function TopProductsBarChart({ data }: TopProductsBarChartProps) {
  const trimmed = data.map((d) => ({
    ...d,
    name: d.ProductName.length > 25 ? d.ProductName.slice(0, 25) + '…' : d.ProductName,
  }));

  return (
    <ChartCard title="Top Products" subtitle="By total revenue">
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={trimmed} layout="vertical" margin={{ left: 80 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" horizontal={false} />
          <XAxis type="number" tick={{ fontSize: 11, fill: '#71717a' }} tickLine={false} axisLine={false} tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}K`} />
          <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: '#71717a' }} tickLine={false} axisLine={false} width={80} />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="revenue" fill={CHART_COLORS[2]} radius={[0, 6, 6, 0]} barSize={16} name="Revenue" />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

// ─── Inventory Status Chart ──────────────────────────────────────────────────
interface InventoryStatusChartProps {
  data: Array<{ Warehouse: string; total_stock: number; product_count: number }>;
}

export function InventoryStatusChart({ data }: InventoryStatusChartProps) {
  return (
    <ChartCard title="Warehouse Stock" subtitle="Stock levels across warehouses">
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
          <XAxis dataKey="Warehouse" tick={{ fontSize: 10, fill: '#71717a' }} tickLine={false} axisLine={false} />
          <YAxis tick={{ fontSize: 11, fill: '#71717a' }} tickLine={false} axisLine={false} />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="total_stock" fill={CHART_COLORS[3]} radius={[6, 6, 0, 0]} barSize={32} name="Total Stock" />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

// ─── Forecast Line Chart ─────────────────────────────────────────────────────
interface ForecastLineChartProps {
  data: Array<{ YearMonth: string; Quantity: number | null; TargetQuantity: number | null }>;
}

export function ForecastLineChart({ data }: ForecastLineChartProps) {
  return (
    <ChartCard title="Forecast vs Actual" subtitle="Quantity comparison over time">
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
          <XAxis dataKey="YearMonth" tick={{ fontSize: 10, fill: '#71717a' }} tickLine={false} axisLine={false} />
          <YAxis tick={{ fontSize: 11, fill: '#71717a' }} tickLine={false} axisLine={false} />
          <Tooltip content={<CustomTooltip />} />
          <Line type="monotone" dataKey="Quantity" stroke={CHART_COLORS[0]} strokeWidth={2} dot={false} name="Actual" />
          <Line type="monotone" dataKey="TargetQuantity" stroke={CHART_COLORS[4]} strokeWidth={2} strokeDasharray="5 5" dot={false} name="Target" />
          <Legend formatter={(value: string) => <span className="text-xs text-zinc-400">{value}</span>} />
        </LineChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}
