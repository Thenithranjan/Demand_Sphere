/**
 * AI Model Management Page — Retail AI Frontend
 * ===============================================
 * Premium modern dashboard for managing recommendation and demand forecasting models.
 */

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  Brain,
  Cpu,
  RefreshCw,
  Play,
  Settings,
  Database,
  History,
  TrendingUp,
  Sparkles,
  ShieldCheck,
  CheckCircle,
  AlertTriangle,
  Clock,
  ArrowUpDown,
  Search,
  Unlock,
  Check,
  X,
  GitCompare,
  BarChart2,
  AlertCircle
} from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend
} from 'recharts';

import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';
import { cn, formatNumber, formatPercent } from '../utils';
import { fadeIn, scaleIn } from '../animations/variants';
import SkeletonCard, { SkeletonTable } from '../components/shared/SkeletonCard';

import { modelManagementApi } from '../services/modelManagementApi';
import type { ModelStatus, TrainingProgress, TrainingSettings, ModelVersionEntry, ModelDetails } from '../services/modelManagementApi';
import { productApi } from '../services/productApi';
import { customerApi } from '../services/customerApi';
import { salesApi } from '../services/salesApi';
import { inventoryApi } from '../services/inventoryApi';

export default function ModelManagementPage() {
  const { isDark } = useTheme();
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // ─── Authorization State ──────────────────────────────────────────────────
  const [isAuthorized, setIsAuthorized] = useState(() => {
    return sessionStorage.getItem('retailai_model_authorized') === 'true';
  });
  const [password, setPassword] = useState('');
  const [authError, setAuthError] = useState('');

  // ─── Page Tabs State ──────────────────────────────────────────────────────
  const [activeTab, setActiveTab] = useState<'overview' | 'registry' | 'trends'>('overview');

  // ─── Page Modals State ─────────────────────────────────────────────────────
  const [confirmTrainOpen, setConfirmTrainOpen] = useState(false);
  const [successAlertOpen, setSuccessAlertOpen] = useState(false);
  const [failureAlertOpen, setFailureAlertOpen] = useState(false);

  // MLOps Action Modals
  const [rejectionModalOpen, setRejectionModalOpen] = useState(false);
  const [selectedVersionToReject, setSelectedVersionToReject] = useState<{ modelType: string; version: string } | null>(null);
  const [rejectionReason, setRejectionReason] = useState('');

  const [rollbackModalOpen, setRollbackModalOpen] = useState(false);
  const [selectedVersionToRollback, setSelectedVersionToRollback] = useState<{ modelType: string; version: string } | null>(null);

  // Model Comparison State
  const [compareModelType, setCompareModelType] = useState<'recommendation' | 'forecast'>('recommendation');
  const [compareModelA, setCompareModelA] = useState<string>('');
  const [compareModelB, setCompareModelB] = useState<string>('');

  // Settings edit state
  const [salesThreshold, setSalesThreshold] = useState(1000);
  const [customersThreshold, setCustomersThreshold] = useState(500);
  const [timeThreshold, setTimeThreshold] = useState(1);
  const [minPrecision, setMinPrecision] = useState(0.0);
  const [maxRmse, setMaxRmse] = useState(100.0);
  const [approvalMode, setApprovalMode] = useState<'automatic' | 'manual'>('automatic');

  // History table state
  const [historySearch, setHistorySearch] = useState('');
  const [historyFilterStatus, setHistoryFilterStatus] = useState<string>('all');
  const [historySortField, setHistorySortField] = useState<string>('training_start_time');
  const [historySortOrder, setHistorySortOrder] = useState<'asc' | 'desc'>('desc');
  const [historyPage, setHistoryPage] = useState(1);
  const itemsPerPage = 5;

  // Local timer for running training
  const [trainingElapsed, setTrainingElapsed] = useState(0);
  const timerRef = useRef<any>(null);

  // Redirect if employee
  const isEmployee = user?.Role === 'Employee';
  useEffect(() => {
    if (isEmployee) {
      toast.error('Access denied. You do not have permission to view AI Model Management.');
      navigate('/dashboard');
    }
  }, [isEmployee, navigate]);

  // ─── TanStack Queries ─────────────────────────────────────────────────────
  // Fetch overall status
  const { data: status, isLoading: statusLoading, refetch: refetchStatus } = useQuery<ModelStatus>({
    queryKey: ['model-status'],
    queryFn: modelManagementApi.getModelStatus,
    enabled: isAuthorized && !isEmployee,
  });

  // Fetch training settings
  const { data: settings, isLoading: settingsLoading, refetch: refetchSettings } = useQuery<TrainingSettings>({
    queryKey: ['model-settings'],
    queryFn: modelManagementApi.getTrainingSettings,
    enabled: isAuthorized && !isEmployee,
  });

  // Fetch active database counts
  const productsCount = useQuery({ queryKey: ['products-count'], queryFn: () => productApi.getAll({ limit: 1 }), enabled: isAuthorized });
  const customersCount = useQuery({ queryKey: ['customers-count'], queryFn: () => customerApi.getAll({ limit: 1 }), enabled: isAuthorized });
  const salesCount = useQuery({ queryKey: ['sales-count'], queryFn: () => salesApi.getAll({ limit: 1 }), enabled: isAuthorized });
  const inventoryCount = useQuery({ queryKey: ['inventory-count'], queryFn: () => inventoryApi.getAll({ limit: 1 }), enabled: isAuthorized });

  // Fetch training progress
  const { data: progress, refetch: refetchProgress } = useQuery<TrainingProgress>({
    queryKey: ['model-progress'],
    queryFn: modelManagementApi.getTrainingProgress,
    enabled: isAuthorized && !isEmployee,
    refetchInterval: (query) => {
      const data = query.state.data;
      return (data && data.status === 'running') ? 2000 : false;
    }
  });

  // Fetch history
  const { data: historyData, isLoading: historyLoading, refetch: refetchHistory } = useQuery({
    queryKey: ['model-history'],
    queryFn: modelManagementApi.getTrainingHistory,
    enabled: isAuthorized && !isEmployee,
  });

  // Fetch model versions
  const { data: recVersions, refetch: refetchRecVersions } = useQuery<ModelVersionEntry[]>({
    queryKey: ['model-versions', 'recommendation'],
    queryFn: () => modelManagementApi.getModelVersions('recommendation'),
    enabled: isAuthorized && !isEmployee
  });

  const { data: forecastVersions, refetch: refetchForecastVersions } = useQuery<ModelVersionEntry[]>({
    queryKey: ['model-versions', 'forecast'],
    queryFn: () => modelManagementApi.getModelVersions('forecast'),
    enabled: isAuthorized && !isEmployee
  });

  // Fetch model comparison details
  const modelADetails = useQuery<ModelDetails>({
    queryKey: ['model-details', compareModelType, compareModelA],
    queryFn: () => modelManagementApi.getModelDetails(compareModelType, compareModelA),
    enabled: !!compareModelA && isAuthorized
  });

  const modelBDetails = useQuery<ModelDetails>({
    queryKey: ['model-details', compareModelType, compareModelB],
    queryFn: () => modelManagementApi.getModelDetails(compareModelType, compareModelB),
    enabled: !!compareModelB && isAuthorized
  });

  // ─── Set Comparisons Defaults ─────────────────────────────────────────────
  useEffect(() => {
    if (compareModelType === 'recommendation' && recVersions && recVersions.length > 0) {
      setCompareModelA(recVersions[recVersions.length - 1]?.version || '');
      setCompareModelB(recVersions[recVersions.length - 2 >= 0 ? recVersions.length - 2 : 0]?.version || '');
    } else if (compareModelType === 'forecast' && forecastVersions && forecastVersions.length > 0) {
      setCompareModelA(forecastVersions[forecastVersions.length - 1]?.version || '');
      setCompareModelB(forecastVersions[forecastVersions.length - 2 >= 0 ? forecastVersions.length - 2 : 0]?.version || '');
    }
  }, [compareModelType, recVersions, forecastVersions]);

  // Update Settings fields when loaded
  useEffect(() => {
    if (settings) {
      setSalesThreshold(settings.sales_threshold);
      setCustomersThreshold(settings.customers_threshold);
      setTimeThreshold(settings.time_threshold_months);
      setMinPrecision(settings.min_precision || 0.0);
      setMaxRmse(settings.max_rmse || 100.0);
      setApprovalMode(settings.approval_mode || 'automatic');
    }
  }, [settings]);

  // Handle training timer
  const isTraining = progress?.status === 'running';
  const startedAt = progress?.started_at;

  useEffect(() => {
    if (isTraining && startedAt) {
      const startMs = new Date(startedAt).getTime();
      const updateTimer = () => {
        const elapsed = Math.round((Date.now() - startMs) / 1000);
        setTrainingElapsed(elapsed > 0 ? elapsed : 0);
      };
      updateTimer();
      timerRef.current = setInterval(updateTimer, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      setTrainingElapsed(0);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isTraining, startedAt]);

  // Handle retraining alerts on status transition
  const prevProgressStatusRef = useRef<string | null>(null);
  useEffect(() => {
    if (progress) {
      const prevStatus = prevProgressStatusRef.current;
      const currentStatus = progress.status;
      
      if (prevStatus === 'running' && currentStatus === 'completed') {
        setSuccessAlertOpen(true);
        queryClient.invalidateQueries();
        toast.success('AI Models retrained successfully!');
      } else if (prevStatus === 'running' && currentStatus === 'failed') {
        setFailureAlertOpen(true);
        queryClient.invalidateQueries();
        toast.error('Model training run failed.');
      }
      prevProgressStatusRef.current = currentStatus;
    }
  }, [progress, queryClient]);

  // ─── Mutations ────────────────────────────────────────────────────────────
  // Verify training password
  const verifyMutation = useMutation({
    mutationFn: (pwd: string) => modelManagementApi.verifyTrainingPassword(pwd),
    onSuccess: () => {
      sessionStorage.setItem('retailai_model_authorized', 'true');
      setIsAuthorized(true);
      setAuthError('');
      toast.success('Authorized successfully');
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail || 'Incorrect training password';
      setAuthError(detail);
      toast.error('Authorization failed');
    }
  });

  // Start manual retraining
  const startManualRetraining = useMutation({
    mutationFn: modelManagementApi.startManualTraining,
    onSuccess: () => {
      setConfirmTrainOpen(false);
      setSuccessAlertOpen(false);
      setFailureAlertOpen(false);
      queryClient.invalidateQueries({ queryKey: ['model-progress'] });
      toast.info('Manual retraining sequence initiated');
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail || 'Failed to start retraining';
      toast.error(detail);
    }
  });

  // Update settings
  const updateSettingsMutation = useMutation({
    mutationFn: (newSettings: TrainingSettings) => modelManagementApi.updateTrainingSettings(newSettings),
    onSuccess: () => {
      toast.success('Retraining settings updated successfully');
      queryClient.invalidateQueries({ queryKey: ['model-settings'] });
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail || 'Failed to update settings';
      toast.error(detail);
    }
  });

  // Approve model mutation
  const approveModelMutation = useMutation({
    mutationFn: ({ modelType, version }: { modelType: string; version: string }) =>
      modelManagementApi.approveModel(modelType, version),
    onSuccess: () => {
      toast.success('Model approved and set active successfully');
      queryClient.invalidateQueries();
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail || 'Failed to approve model';
      toast.error(detail);
    }
  });

  // Reject model mutation
  const rejectModelMutation = useMutation({
    mutationFn: ({ modelType, version, reason }: { modelType: string; version: string; reason: string }) =>
      modelManagementApi.rejectModel(modelType, version, reason),
    onSuccess: () => {
      toast.success('Model rejected successfully');
      setRejectionModalOpen(false);
      setRejectionReason('');
      queryClient.invalidateQueries();
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail || 'Failed to reject model';
      toast.error(detail);
    }
  });

  // Rollback model mutation
  const rollbackModelMutation = useMutation({
    mutationFn: ({ modelType, version }: { modelType: string; version: string }) =>
      modelManagementApi.rollbackModel(modelType, version),
    onSuccess: () => {
      toast.success('Model rollback completed successfully');
      setRollbackModalOpen(false);
      queryClient.invalidateQueries();
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail || 'Failed to perform rollback';
      toast.error(detail);
    }
  });

  // ─── Action Handlers ──────────────────────────────────────────────────────
  const handleAuthSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!password.trim()) {
      setAuthError('Password cannot be empty');
      return;
    }
    verifyMutation.mutate(password);
  };

  const handleRefreshAll = () => {
    refetchStatus();
    refetchSettings();
    refetchProgress();
    refetchHistory();
    refetchRecVersions();
    refetchForecastVersions();
    productsCount.refetch();
    customersCount.refetch();
    salesCount.refetch();
    inventoryCount.refetch();
    toast.success('Dashboard status refreshed');
  };

  const handleSaveSettings = (e: React.FormEvent) => {
    e.preventDefault();
    updateSettingsMutation.mutate({
      sales_threshold: salesThreshold,
      customers_threshold: customersThreshold,
      time_threshold_months: timeThreshold,
      min_precision: minPrecision,
      max_rmse: maxRmse,
      approval_mode: approvalMode
    });
  };

  const formatTimer = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  const getSyncStatus = (dbVal?: number, trVal?: number) => {
    if (dbVal === undefined || trVal === undefined) return 'Checking';
    return dbVal === trVal ? 'Synchronized' : 'Sync Required';
  };

  const getStatusBadgeClass = (statusStr: string) => {
    switch (statusStr.toUpperCase()) {
      case 'ACTIVE':
        return 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20';
      case 'PENDING_APPROVAL':
        return 'bg-amber-500/10 text-amber-500 border border-amber-500/20 animate-pulse';
      case 'TRAINING':
      case 'EVALUATING':
        return 'bg-blue-500/10 text-blue-500 border border-blue-500/20';
      case 'REJECTED':
      case 'FAILED':
        return 'bg-red-500/10 text-red-500 border border-red-500/20';
      case 'ROLLED_BACK':
      case 'ARCHIVED':
      default:
        return 'bg-zinc-500/10 text-zinc-400 border border-zinc-500/20';
    }
  };

  // ─── Render: Authorization Overlay ────────────────────────────────────────
  if (!isAuthorized) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-zinc-950/80 backdrop-blur-xl">
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: 'spring', duration: 0.4 }}
          className={cn(
            'relative w-full max-w-md p-8 rounded-3xl border shadow-2xl transition-colors',
            isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200'
          )}
        >
          <div className="flex flex-col items-center text-center space-y-4 mb-6">
            <div className="w-14 h-14 rounded-2xl bg-brand-500/10 flex items-center justify-center text-brand-400">
              <Unlock className="w-7 h-7 animate-pulse" />
            </div>
            <h1 className={cn('text-2xl font-bold', isDark ? 'text-zinc-100' : 'text-zinc-900')}>
              AI Model Management
            </h1>
            <p className="text-sm text-zinc-500 max-w-xs">
              Enter the training authorization password to continue.
            </p>
          </div>

          {/* ── Password Quick-Access Banner ─────────────────────────── */}
          <motion.button
            type="button"
            onClick={() => setPassword('trainmodel')}
            whileHover={{ scale: 1.015, y: -1 }}
            whileTap={{ scale: 0.98 }}
            title="Click to auto-fill the authorization password"
            className={cn(
              'w-full mb-4 px-4 py-3 rounded-2xl border-2 border-dashed text-left flex items-center gap-3 transition-all cursor-pointer group',
              isDark
                ? 'border-amber-500/40 bg-amber-500/5 hover:bg-amber-500/10 hover:border-amber-500/60'
                : 'border-amber-400/50 bg-amber-50 hover:bg-amber-100 hover:border-amber-500'
            )}
          >
            <div className="w-8 h-8 rounded-xl bg-amber-500/20 flex items-center justify-center shrink-0">
              <span className="text-base">🔑</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-[10px] font-bold uppercase tracking-widest text-amber-500 mb-0.5">Quick Access — Click to Auto-Fill</p>
              <p className={cn('text-sm font-mono font-semibold tracking-widest', isDark ? 'text-amber-300' : 'text-amber-700')}>
                ••••••••••
              </p>
              <p className={cn('text-[10px] mt-0.5', isDark ? 'text-zinc-500' : 'text-zinc-400')}>trainmodel</p>
            </div>
            <span className={cn(
              'text-[10px] font-semibold px-2 py-1 rounded-lg transition-colors shrink-0',
              isDark
                ? 'bg-amber-500/20 text-amber-400 group-hover:bg-amber-500/30'
                : 'bg-amber-200 text-amber-700 group-hover:bg-amber-300'
            )}>
              Auto-fill
            </span>
          </motion.button>

          <form onSubmit={handleAuthSubmit} className="space-y-4">
            <div className="space-y-2">
              <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                Authorization Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className={cn(
                  'w-full px-4 py-3 rounded-xl text-sm outline-none border transition-all text-center tracking-widest',
                  isDark ? 'bg-zinc-950 border-zinc-800 text-zinc-100 focus:border-brand-500' : 'bg-zinc-50 border-zinc-200 text-zinc-900 focus:border-brand-500'
                )}
                autoFocus
              />
              {authError && <p className="text-xs text-red-500 font-medium text-center">{authError}</p>}
            </div>

            <button
              type="submit"
              disabled={verifyMutation.isPending}
              className="w-full py-3 rounded-xl text-sm font-semibold text-white gradient-brand hover:opacity-90 active:opacity-100 transition-opacity cursor-pointer flex justify-center"
            >
              {verifyMutation.isPending ? 'Verifying...' : 'Continue'}
            </button>
          </form>
        </motion.div>
      </div>
    );
  }

  // ─── Main Render ──────────────────────────────────────────────────────────
  return (
    <motion.div
      variants={fadeIn}
      initial="hidden"
      animate="visible"
      className="space-y-6 max-w-7xl mx-auto px-1.5"
    >
      {/* ─── Header Section ─────────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-zinc-800/40 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl gradient-brand flex items-center justify-center text-white shrink-0">
              <Brain className="w-5.5 h-5.5" />
            </div>
            <div>
              <h1 className={cn('text-2xl font-bold tracking-tight', isDark ? 'text-zinc-100' : 'text-zinc-900')}>
                AI Model Management & MLOps
              </h1>
              <p className="text-sm text-zinc-500 mt-0.5">
                Monitor performance, review lineage report logs, approve candidate builds, and rollback serving models.
              </p>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Quick status indicators */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-zinc-900/60 border border-zinc-800 text-xs">
            <span className="text-zinc-500">Pipeline:</span>
            {isTraining ? (
              <span className="text-amber-400 font-semibold animate-pulse flex items-center gap-1">
                ● Retraining
              </span>
            ) : (
              <span className="text-emerald-500 font-semibold flex items-center gap-1">
                ● Serving Active
              </span>
            )}
          </div>

          <button
            onClick={handleRefreshAll}
            className={cn(
              'px-4 py-2 rounded-xl text-sm font-semibold border flex items-center gap-2 transition-all cursor-pointer shadow-sm',
              isDark
                ? 'border-zinc-800 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
                : 'border-zinc-200 text-zinc-600 hover:bg-zinc-50 hover:text-zinc-800'
            )}
            title="Refresh Status"
          >
            <RefreshCw className={cn('w-4 h-4', statusLoading && 'animate-spin')} />
            Refresh Status
          </button>
        </div>
      </div>

      {/* ─── Navigation Tabs ────────────────────────────────────────────────── */}
      <div className="flex border-b border-zinc-800/40 gap-1 pb-px">
        {[
          { id: 'overview', label: 'Overview & Controls', icon: Cpu },
          { id: 'registry', label: 'Model Registry & Comparison', icon: GitCompare },
          { id: 'trends', label: 'Performance Trends', icon: BarChart2 }
        ].map((tab) => {
          const Icon = tab.icon;
          const active = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={cn(
                'flex items-center gap-2 px-5 py-3 text-xs font-semibold relative transition-colors cursor-pointer',
                active ? 'text-brand-400' : 'text-zinc-500 hover:text-zinc-300'
              )}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
              {active && (
                <motion.div
                  layoutId="activeTabUnderline"
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-brand-500"
                />
              )}
            </button>
          );
        })}
      </div>

      {/* ─── Training Progress Panel ─────────────────────────────────────────── */}
      <AnimatePresence>
        {isTraining && progress && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className={cn(
              'p-6 rounded-3xl border overflow-hidden transition-all',
              isDark ? 'bg-amber-500/5 border-amber-500/20' : 'bg-amber-500/2 border-amber-500/10'
            )}
          >
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
              <div>
                <h3 className="text-lg font-bold text-amber-500 flex items-center gap-2">
                  <Cpu className="w-5 h-5 animate-spin" />
                  Model Training In Progress
                </h3>
                <p className="text-sm text-zinc-400 mt-0.5">
                  Current Stage: <span className="font-semibold text-zinc-200">{progress.current_stage}</span>
                </p>
              </div>
              <div className="flex items-center gap-3 text-sm text-zinc-400 bg-zinc-900/60 border border-zinc-800 px-3 py-1.5 rounded-xl shrink-0 self-start md:self-auto">
                <Clock className="w-4 h-4 text-amber-500" />
                Elapsed time: <span className="font-semibold text-zinc-200">{formatTimer(trainingElapsed)}</span>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-xs font-semibold text-zinc-400">
                <span>{progress.current_stage}</span>
                <span className="text-amber-500">{progress.percentage}%</span>
              </div>
              <div className="w-full h-3 rounded-full bg-zinc-800 border border-zinc-800 overflow-hidden">
                <motion.div
                  className="h-full rounded-full gradient-brand"
                  initial={{ width: 0 }}
                  animate={{ width: `${progress.percentage}%` }}
                  transition={{ duration: 0.35 }}
                />
              </div>
              <p className="text-xs text-zinc-500 italic">
                Please do not close this window. Active pipelines continue in the background.
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ─── Alerts: Success / Failure ────────────────────────────────────────── */}
      <AnimatePresence>
        {successAlertOpen && status && (
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            className="p-6 rounded-3xl border bg-emerald-500/5 border-emerald-500/25 flex flex-col sm:flex-row gap-4 items-start relative"
          >
            <div className="w-10 h-10 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-500 shrink-0">
              <CheckCircle className="w-5.5 h-5.5" />
            </div>
            <div className="space-y-2 flex-1">
              <h4 className="text-base font-bold text-emerald-400">AI Models Updated Successfully</h4>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm pt-1">
                <div>
                  <div className="text-zinc-500 text-xs uppercase tracking-wider font-semibold">Recommendation</div>
                  <div className={cn('font-semibold', isDark ? 'text-zinc-200' : 'text-zinc-800')}>{status.recommendation_model_version}</div>
                </div>
                <div>
                  <div className="text-zinc-500 text-xs uppercase tracking-wider font-semibold">Demand Forecast</div>
                  <div className={cn('font-semibold', isDark ? 'text-zinc-200' : 'text-zinc-800')}>{status.forecast_model_version}</div>
                </div>
                <div>
                  <div className="text-zinc-500 text-xs uppercase tracking-wider font-semibold">Latest Accuracy</div>
                  <div className={cn('font-semibold', isDark ? 'text-zinc-200' : 'text-zinc-800')}>{formatPercent(status.recommendation_accuracy / 100)}</div>
                </div>
              </div>
            </div>
            <button
              onClick={() => setSuccessAlertOpen(false)}
              className="absolute right-4 top-4 text-zinc-500 hover:text-zinc-300 text-xs font-semibold p-1"
            >
              ✕
            </button>
          </motion.div>
        )}

        {failureAlertOpen && progress && (
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            className="p-6 rounded-3xl border bg-red-500/5 border-red-500/25 flex flex-col sm:flex-row gap-4 items-start relative"
          >
            <div className="w-10 h-10 rounded-full bg-red-500/10 flex items-center justify-center text-red-500 shrink-0">
              <AlertTriangle className="w-5.5 h-5.5" />
            </div>
            <div className="space-y-2 flex-1 min-w-0">
              <h4 className="text-base font-bold text-red-400">Model Training Failed</h4>
              <p className="text-sm text-zinc-400 truncate max-w-2xl font-mono bg-zinc-950/40 p-2.5 rounded-lg border border-zinc-900">
                {progress.error_message || 'An unknown error occurred during execution.'}
              </p>
              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => {
                    setFailureAlertOpen(false);
                    setConfirmTrainOpen(true);
                  }}
                  className="px-3.5 py-1.5 bg-red-500 text-white rounded-lg text-xs font-semibold hover:opacity-90 active:opacity-100 transition-opacity cursor-pointer"
                >
                  Retry
                </button>
                <button
                  onClick={() => setFailureAlertOpen(false)}
                  className="px-3.5 py-1.5 border border-zinc-800 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200 rounded-lg text-xs font-semibold transition-colors cursor-pointer"
                >
                  Close
                </button>
              </div>
            </div>
            <button
              onClick={() => setFailureAlertOpen(false)}
              className="absolute right-4 top-4 text-zinc-500 hover:text-zinc-300 text-xs font-semibold p-1"
            >
              ✕
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ─── TAB 1: OVERVIEW & CONTROLS ─────────────────────────────────────── */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Model Status Cards */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Recommendation Model Card */}
            {statusLoading ? (
              <SkeletonCard className="h-60" />
            ) : status ? (
              <motion.div
                variants={scaleIn}
                initial="hidden"
                animate="visible"
                className={cn(
                  'p-6 rounded-3xl border hover-lift transition-all flex flex-col justify-between relative overflow-hidden',
                  isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200 shadow-sm'
                )}
              >
                <div className="absolute -top-10 -right-10 w-40 h-40 bg-brand-500/5 rounded-full blur-3xl" />
                <div className="flex justify-between items-start gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 text-brand-400">
                      <Sparkles className="w-4 h-4" />
                      <span className="text-xs font-bold uppercase tracking-wider">Recommendation System</span>
                    </div>
                    <h3 className={cn('text-lg font-bold', isDark ? 'text-zinc-100' : 'text-zinc-900')}>
                      Hybrid Engine Model
                    </h3>
                  </div>
                  <span className="px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-500 text-[10px] font-bold uppercase border border-emerald-500/20">
                    Serving Active
                  </span>
                </div>

                <div className={cn('grid grid-cols-2 gap-6 py-6 border-y my-4', isDark ? 'border-zinc-800/40' : 'border-zinc-200')}>
                  <div>
                    <span className="text-xs text-zinc-500 font-medium">Model Version</span>
                    <p className={cn('text-3xl font-extrabold tracking-tight mt-0.5', isDark ? 'text-zinc-100' : 'text-zinc-900')}>
                      {status.recommendation_model_version}
                    </p>
                  </div>
                  <div>
                    <span className="text-xs text-zinc-500 font-medium">Precision@10</span>
                    <p className="text-3xl font-extrabold text-brand-400 mt-0.5">
                      {formatPercent(status.recommendation_accuracy / 100)}
                    </p>
                  </div>
                </div>

                <div className="flex justify-between items-center text-xs text-zinc-500">
                  <div>
                    Last trained:{' '}
                    <span className={cn('font-semibold', isDark ? 'text-zinc-300' : 'text-zinc-700')}>{status.last_training_date}</span>
                  </div>
                  <div>
                    Records:{' '}
                    <span className={cn('font-semibold', isDark ? 'text-zinc-300' : 'text-zinc-700')}>
                      {formatNumber(status.training_dataset_size.sales)} sales
                    </span>
                  </div>
                </div>
              </motion.div>
            ) : null}

            {/* Forecasting Model Card */}
            {statusLoading ? (
              <SkeletonCard className="h-60" />
            ) : status ? (
              <motion.div
                variants={scaleIn}
                initial="hidden"
                animate="visible"
                className={cn(
                  'p-6 rounded-3xl border hover-lift transition-all flex flex-col justify-between relative overflow-hidden',
                  isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200 shadow-sm'
                )}
              >
                <div className="absolute -top-10 -right-10 w-40 h-40 bg-indigo-500/5 rounded-full blur-3xl" />
                <div className="flex justify-between items-start gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 text-indigo-400">
                      <TrendingUp className="w-4 h-4" />
                      <span className="text-xs font-bold uppercase tracking-wider">Demand Forecasting</span>
                    </div>
                    <h3 className={cn('text-lg font-bold', isDark ? 'text-zinc-100' : 'text-zinc-900')}>
                      XGBoost Regressor Model
                    </h3>
                  </div>
                  <span className="px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-500 text-[10px] font-bold uppercase border border-emerald-500/20">
                    Serving Active
                  </span>
                </div>

                <div className={cn('grid grid-cols-3 gap-4 py-6 border-y my-4', isDark ? 'border-zinc-800/40' : 'border-zinc-200')}>
                  <div>
                    <span className="text-xs text-zinc-500 font-medium">Model Version</span>
                    <p className={cn('text-3xl font-extrabold tracking-tight mt-0.5', isDark ? 'text-zinc-100' : 'text-zinc-900')}>
                      {status.forecast_model_version}
                    </p>
                  </div>
                  <div>
                    <span className="text-xs text-zinc-500 font-medium">RMSE</span>
                    <p className="text-3xl font-extrabold text-indigo-400 mt-0.5">
                      {status.forecast_accuracy.rmse}
                    </p>
                  </div>
                  <div>
                    <span className="text-xs text-zinc-500 font-medium">MAE</span>
                    <p className="text-3xl font-extrabold text-violet-400 mt-0.5">
                      {status.forecast_accuracy.mae}
                    </p>
                  </div>
                </div>

                <div className="flex justify-between items-center text-xs text-zinc-500">
                  <div>
                    Last trained:{' '}
                    <span className={cn('font-semibold', isDark ? 'text-zinc-300' : 'text-zinc-700')}>{status.last_training_date}</span>
                  </div>
                  <div>
                    Records:{' '}
                    <span className={cn('font-semibold', isDark ? 'text-zinc-300' : 'text-zinc-700')}>
                      {formatNumber(status.training_dataset_size.sales)} sales
                    </span>
                  </div>
                </div>
              </motion.div>
            ) : null}
          </div>

          {/* Dataset Sync Status */}
          <div className="space-y-4">
            <h2 className={cn('text-lg font-bold flex items-center gap-2 border-l-4 border-brand-500 pl-3', isDark ? 'text-zinc-200' : 'text-zinc-800')}>
              <Database className="w-5 h-5 text-brand-400" />
              Dataset Synchronization Status
            </h2>

            {statusLoading || productsCount.isLoading || salesCount.isLoading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <SkeletonCard lines={2} />
                <SkeletonCard lines={2} />
                <SkeletonCard lines={2} />
                <SkeletonCard lines={2} />
              </div>
            ) : status ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                  {
                    title: 'Products Catalog',
                    dbVal: productsCount.data?.total,
                    trVal: status.training_dataset_size.products,
                  },
                  {
                    title: 'Customers Register',
                    dbVal: customersCount.data?.total,
                    trVal: status.training_dataset_size.customers,
                  },
                  {
                    title: 'Sales Transactions',
                    dbVal: salesCount.data?.total,
                    trVal: status.training_dataset_size.sales,
                  },
                  {
                    title: 'Inventory Records',
                    dbVal: inventoryCount.data?.total,
                    trVal: status.training_dataset_size.inventory || 500,
                  },
                ].map((d, index) => {
                  const syncStatus = getSyncStatus(d.dbVal, d.trVal);
                  return (
                    <div
                      key={index}
                      className={cn(
                        'p-5 rounded-2xl border transition-colors',
                        isDark ? 'bg-zinc-900/60 border-zinc-800' : 'bg-white border-zinc-200 shadow-sm'
                      )}
                    >
                      <div className="flex justify-between items-start gap-2">
                        <span className="text-xs text-zinc-500 font-semibold">{d.title}</span>
                        <span
                          className={cn(
                            'px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider',
                            syncStatus === 'Synchronized'
                              ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20'
                              : 'bg-amber-500/10 text-amber-500 border border-amber-500/20'
                          )}
                        >
                          {syncStatus}
                        </span>
                      </div>

                      <div className={cn('grid grid-cols-2 gap-4 pt-4 mt-2 border-t', isDark ? 'border-zinc-800/30' : 'border-zinc-100')}>
                        <div>
                          <span className="text-[10px] text-zinc-500 block">Database Records</span>
                          <span className={cn('text-lg font-bold mt-0.5', isDark ? 'text-zinc-200' : 'text-zinc-800')}>
                            {d.dbVal !== undefined ? formatNumber(d.dbVal) : '...'}
                          </span>
                        </div>
                        <div>
                          <span className="text-[10px] text-zinc-500 block">Training Snapshot</span>
                          <span className="text-lg font-bold text-brand-400 mt-0.5">
                            {formatNumber(d.trVal)}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : null}
          </div>

          {/* Controls & Retraining settings */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Manual Training Controls */}
            <div
              className={cn(
                'p-6 rounded-3xl border lg:col-span-2 flex flex-col justify-between transition-colors',
                isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200 shadow-sm'
              )}
            >
              <div className="space-y-4">
                <h2 className={cn('text-lg font-bold flex items-center gap-2', isDark ? 'text-zinc-200' : 'text-zinc-800')}>
                  <Play className="w-5 h-5 text-brand-400" />
                  Model Training Control
                </h2>
                <div className="space-y-2 text-sm text-zinc-400">
                  <p>
                    Triggering a training sequence immediately synchronizes database transactions, generates clean feature sets, constructs XGBoost / collaborative models, and loads them dynamically in-memory.
                  </p>
              <div className={cn(
                'p-4 border rounded-2xl space-y-1.5 text-xs font-mono',
                isDark ? 'bg-zinc-950/40 border-zinc-850 text-zinc-500' : 'bg-zinc-50 border-zinc-200 text-zinc-500'
              )}>
                    <div className="flex gap-2">● <span>Synchronizes MySQL data structures → CSV snapshots</span></div>
                    <div className="flex gap-2">● <span>Computes Content and Item-Item Collab similarities</span></div>
                    <div className="flex gap-2">● <span>Trains and tunes XGBoost forecasting algorithms</span></div>
                    <div className="flex gap-2">● <span>Loads models using configured MLOps automatic/manual approval flows</span></div>
                  </div>
                </div>
              </div>

              <div className="pt-6 border-t border-zinc-800/30 mt-6 flex justify-end">
                <button
                  onClick={() => setConfirmTrainOpen(true)}
                  disabled={isTraining}
                  className="px-6 py-3 rounded-xl text-sm font-semibold text-white gradient-brand hover:opacity-90 active:opacity-100 transition-opacity flex items-center gap-2 cursor-pointer shadow-lg shadow-brand-500/25 disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
                >
                  <Cpu className="w-4 h-4" />
                  Train Models Now
                </button>
              </div>
            </div>

            {/* MLOps Retraining Configuration Settings */}
            <div
              className={cn(
                'p-6 rounded-3xl border transition-colors',
                isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200 shadow-sm'
              )}
            >
              <form onSubmit={handleSaveSettings} className="h-full flex flex-col justify-between">
                <div className="space-y-4">
                  <h2 className={cn('text-lg font-bold flex items-center gap-2', isDark ? 'text-zinc-200' : 'text-zinc-800')}>
                    <Settings className="w-5 h-5 text-brand-400" />
                    MLOps & Condition Settings
                  </h2>
                  <p className="text-xs text-zinc-500">
                    Configure thresholds, approval modes, and model acceptance evaluation triggers.
                  </p>

                  {settingsLoading ? (
                    <div className="space-y-3">
                      <div className="h-10 bg-zinc-800/50 animate-pulse rounded-xl" />
                      <div className="h-10 bg-zinc-800/50 animate-pulse rounded-xl" />
                    </div>
                  ) : (
                    <div className="space-y-3 pt-2 text-xs">
                      {/* Grid parameters */}
                      <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1">
                          <label className="text-zinc-500 font-semibold">Sales Delta Limit</label>
                          <input
                            type="number"
                            value={salesThreshold}
                            onChange={(e) => setSalesThreshold(Number(e.target.value))}
                            className={cn(
                              'w-full px-3 py-2 rounded-xl text-xs outline-none border transition-colors',
                              isDark ? 'bg-zinc-950 border-zinc-800 text-zinc-200' : 'bg-zinc-50 border-zinc-200 text-zinc-900'
                            )}
                            required
                          />
                        </div>
                        <div className="space-y-1">
                          <label className="text-zinc-500 font-semibold">Customer Delta</label>
                          <input
                            type="number"
                            value={customersThreshold}
                            onChange={(e) => setCustomersThreshold(Number(e.target.value))}
                            className={cn(
                              'w-full px-3 py-2 rounded-xl text-xs outline-none border transition-colors',
                              isDark ? 'bg-zinc-950 border-zinc-800 text-zinc-200' : 'bg-zinc-50 border-zinc-200 text-zinc-900'
                            )}
                            required
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1">
                          <label className="text-zinc-500 font-semibold">Timeline Limit (Mo)</label>
                          <input
                            type="number"
                            value={timeThreshold}
                            onChange={(e) => setTimeThreshold(Number(e.target.value))}
                            className={cn(
                              'w-full px-3 py-2 rounded-xl text-xs outline-none border transition-colors',
                              isDark ? 'bg-zinc-950 border-zinc-800 text-zinc-200' : 'bg-zinc-50 border-zinc-200 text-zinc-900'
                            )}
                            required
                          />
                        </div>
                        <div className="space-y-1">
                          <label className="text-zinc-500 font-semibold">Min Precision (%)</label>
                          <input
                            type="number"
                            step="0.01"
                            value={minPrecision}
                            onChange={(e) => setMinPrecision(Number(e.target.value))}
                            className={cn(
                              'w-full px-3 py-2 rounded-xl text-xs outline-none border transition-colors',
                              isDark ? 'bg-zinc-950 border-zinc-800 text-zinc-200' : 'bg-zinc-50 border-zinc-200 text-zinc-900'
                            )}
                            required
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1">
                          <label className="text-zinc-500 font-semibold">Max Forecast RMSE</label>
                          <input
                            type="number"
                            step="0.01"
                            value={maxRmse}
                            onChange={(e) => setMaxRmse(Number(e.target.value))}
                            className={cn(
                              'w-full px-3 py-2 rounded-xl text-xs outline-none border transition-colors',
                              isDark ? 'bg-zinc-950 border-zinc-800 text-zinc-200' : 'bg-zinc-50 border-zinc-200 text-zinc-900'
                            )}
                            required
                          />
                        </div>
                        <div className="space-y-1">
                          <label className="text-zinc-500 font-semibold">Approval Strategy</label>
                          <select
                            value={approvalMode}
                            onChange={(e) => setApprovalMode(e.target.value as any)}
                            className={cn(
                              'w-full px-3 py-2 rounded-xl text-xs outline-none border transition-colors cursor-pointer',
                              isDark ? 'bg-zinc-950 border-zinc-800 text-zinc-200' : 'bg-zinc-50 border-zinc-250 text-zinc-800'
                            )}
                          >
                            <option value="automatic">Automatic Approval</option>
                            <option value="manual">Manual Approval</option>
                          </select>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                <div className={cn('pt-6 border-t mt-6 flex justify-end', isDark ? 'border-zinc-800/30' : 'border-zinc-200')}>
                  <button
                    type="submit"
                    disabled={updateSettingsMutation.isPending}
                    className="px-5 py-2.5 bg-brand-500 hover:bg-brand-600 text-white rounded-xl text-xs font-bold transition-all shadow-md shadow-brand-500/10 cursor-pointer"
                  >
                    {updateSettingsMutation.isPending ? 'Saving...' : 'Save Settings'}
                  </button>
                </div>
              </form>
            </div>
          </div>

          {/* Training History Log */}
          <div className="space-y-4">
            <h2 className={cn('text-lg font-bold flex items-center gap-2 border-l-4 border-brand-500 pl-3', isDark ? 'text-zinc-200' : 'text-zinc-800')}>
              <History className="w-5 h-5 text-brand-400" />
              Retraining Audit History Logs
            </h2>

            <div className={cn(
              'p-5 rounded-3xl border space-y-4 transition-colors',
              isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200 shadow-sm'
            )}>
              {/* Table controls */}
              <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
                <div className="relative w-full sm:max-w-xs">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                  <input
                    type="text"
                    placeholder="Search logs (e.g. TRN-, admin)..."
                    value={historySearch}
                    onChange={(e) => {
                      setHistorySearch(e.target.value);
                      setHistoryPage(1);
                    }}
                    className={cn(
                      'w-full pl-9 pr-4 py-2 rounded-xl text-xs outline-none border transition-colors',
                      isDark ? 'bg-zinc-950 border-zinc-800 text-zinc-200 focus:border-brand-500' : 'bg-zinc-50 border-zinc-250 text-zinc-900 focus:border-brand-500'
                    )}
                  />
                </div>

                <div className="flex items-center gap-2 self-end sm:self-auto text-xs">
                  <span className="text-zinc-500 font-semibold">Status:</span>
                  <select
                    value={historyFilterStatus}
                    onChange={(e) => {
                      setHistoryFilterStatus(e.target.value);
                      setHistoryPage(1);
                    }}
                    className={cn(
                      'px-3 py-1.5 rounded-xl border outline-none cursor-pointer',
                      isDark ? 'bg-zinc-950 border-zinc-800 text-zinc-300' : 'bg-zinc-50 border-zinc-250 text-zinc-800'
                    )}
                  >
                    <option value="all">All Logs</option>
                    <option value="success">Success</option>
                    <option value="model_rejected">Model Rejected</option>
                    <option value="failed">Failed</option>
                  </select>
                </div>
              </div>

              {/* History Table */}
              <div className="overflow-x-auto">
                {historyLoading ? (
                  <SkeletonTable rows={3} />
                ) : historyData ? (
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className={cn('border-b font-semibold uppercase tracking-wider', isDark ? 'border-zinc-800 text-zinc-500' : 'border-zinc-200 text-zinc-400')}>
                        <th className="pb-3 pr-4">Training ID</th>
                        <th className="pb-3 px-4">Date & Time</th>
                        <th className="pb-3 px-4">Trigger / User</th>
                        <th className="pb-3 px-4">Model Versions</th>
                        <th className="pb-3 px-4 text-center">Metrics</th>
                        <th className="pb-3 pl-4 text-right">Status</th>
                      </tr>
                    </thead>
                    <tbody className={cn('divide-y', isDark ? 'divide-zinc-800/40' : 'divide-zinc-100')}>
                      {(() => {
                        // Client-side filtering & sorting
                        const filtered = (historyData.history || []).filter((entry: any) => {
                          const query = historySearch.toLowerCase();
                          const matchesSearch =
                            entry.training_id?.toLowerCase().includes(query) ||
                            entry.user?.toLowerCase().includes(query) ||
                            entry.reason?.toLowerCase().includes(query);
                          const matchesStatus =
                            historyFilterStatus === 'all' || entry.status === historyFilterStatus;
                          return matchesSearch && matchesStatus;
                        });

                        const sorted = filtered.sort((a: any, b: any) => {
                          let fieldA = a[historySortField];
                          let fieldB = b[historySortField];
                          if (historySortField === 'training_start_time') {
                            fieldA = new Date(fieldA).getTime();
                            fieldB = new Date(fieldB).getTime();
                          }
                          if (fieldA < fieldB) return historySortOrder === 'asc' ? -1 : 1;
                          if (fieldA > fieldB) return historySortOrder === 'asc' ? 1 : -1;
                          return 0;
                        });

                        const pageStart = (historyPage - 1) * itemsPerPage;
                        const pageItems = sorted.slice(pageStart, pageStart + itemsPerPage);

                        if (pageItems.length === 0) {
                          return (
                            <tr>
                              <td colSpan={6} className="py-8 text-center text-zinc-500 italic">
                                No logs match the specified filters.
                              </td>
                            </tr>
                          );
                        }

                        return pageItems.map((entry: any) => (
                          <tr key={entry.training_id} className="hover:bg-zinc-850/10 transition-colors">
                            <td className={cn('py-4 pr-4 font-mono font-bold', isDark ? 'text-zinc-200' : 'text-zinc-800')}>
                              {entry.training_id}
                            </td>
                            <td className={cn('py-4 px-4', isDark ? 'text-zinc-400' : 'text-zinc-600')}>
                              <div>{entry.training_start_time}</div>
                              <div className={cn('text-[10px] mt-0.5', isDark ? 'text-zinc-600' : 'text-zinc-400')}>
                                Duration: {entry.duration_human}
                              </div>
                            </td>
                            <td className="py-4 px-4">
                              <div className={cn('font-semibold', isDark ? 'text-zinc-300' : 'text-zinc-700')}>{entry.reason}</div>
                              <div className="text-[10px] text-zinc-500 mt-0.5">
                                By: {entry.user} ({entry.role})
                              </div>
                            </td>
                            <td className={cn('py-4 px-4 font-mono', isDark ? 'text-zinc-400' : 'text-zinc-600')}>
                              <div>Rec: <span className="font-semibold text-brand-400">{entry.recommendation_version}</span></div>
                              <div className="mt-0.5">Fore: <span className="font-semibold text-indigo-400">{entry.forecast_version}</span></div>
                            </td>
                            <td className="py-4 px-4 text-center">
                              <div className="flex flex-col gap-0.5 items-center">
                                <span className="text-[10px] text-zinc-500">
                                  Rec Acc: {entry.metrics?.recommendation_accuracy ? `${entry.metrics.recommendation_accuracy}%` : 'N/A'}
                                </span>
                                <span className="text-[10px] text-zinc-500">
                                  Fore RMSE: {entry.metrics?.forecast_rmse || 'N/A'}
                                </span>
                              </div>
                            </td>
                            <td className="py-4 pl-4 text-right">
                              <span
                                className={cn(
                                  'px-2.5 py-1 rounded-full text-[9px] font-bold uppercase tracking-wider',
                                  entry.status === 'success'
                                    ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20'
                                    : entry.status === 'model_rejected'
                                    ? 'bg-amber-500/10 text-amber-500 border border-amber-500/20'
                                    : 'bg-red-500/10 text-red-500 border border-red-500/20'
                                )}
                              >
                                {entry.status === 'success' ? 'Success' : entry.status === 'model_rejected' ? 'Rejected' : 'Failed'}
                              </span>
                              {entry.error_message && (
                                <div className="text-[10px] text-red-400 mt-1.5 max-w-[200px] truncate ml-auto" title={entry.error_message}>
                                  {entry.error_message}
                                </div>
                              )}
                            </td>
                          </tr>
                        ));
                      })()}
                    </tbody>
                  </table>
                ) : null}
              </div>

              {/* Table pagination */}
              {historyData && (
                <div className={cn('flex items-center justify-between border-t pt-4 text-xs', isDark ? 'border-zinc-800/40' : 'border-zinc-200')}>
                  <span className="text-zinc-500">
                    Showing page {historyPage} of{' '}
                    {Math.ceil(
                      (historyData.history || []).filter((entry: any) => {
                        const query = historySearch.toLowerCase();
                        const matchesSearch =
                          entry.training_id?.toLowerCase().includes(query) ||
                          entry.user?.toLowerCase().includes(query) ||
                          entry.reason?.toLowerCase().includes(query);
                        const matchesStatus =
                          historyFilterStatus === 'all' || entry.status === historyFilterStatus;
                        return matchesSearch && matchesStatus;
                      }).length / itemsPerPage
                    ) || 1}
                  </span>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setHistoryPage((p) => Math.max(1, p - 1))}
                      disabled={historyPage === 1}
                      className={cn(
                        'px-3 py-1.5 rounded-lg border disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer',
                        isDark ? 'border-zinc-800 text-zinc-400 hover:bg-zinc-800' : 'border-zinc-200 text-zinc-600 hover:bg-zinc-50'
                      )}
                    >
                      Prev
                    </button>
                    <button
                      onClick={() => setHistoryPage((p) => p + 1)}
                      disabled={
                        historyPage >=
                        Math.ceil(
                          (historyData.history || []).filter((entry: any) => {
                            const query = historySearch.toLowerCase();
                            const matchesSearch =
                              entry.training_id?.toLowerCase().includes(query) ||
                              entry.user?.toLowerCase().includes(query) ||
                              entry.reason?.toLowerCase().includes(query);
                            const matchesStatus =
                              historyFilterStatus === 'all' || entry.status === historyFilterStatus;
                            return matchesSearch && matchesStatus;
                          }).length / itemsPerPage
                        )
                      }
                      className={cn(
                        'px-3 py-1.5 rounded-lg border disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer',
                        isDark ? 'border-zinc-800 text-zinc-400 hover:bg-zinc-800' : 'border-zinc-200 text-zinc-600 hover:bg-zinc-50'
                      )}
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ─── TAB 2: MODEL REGISTRY & COMPARISON ─────────────────────────────── */}
      {activeTab === 'registry' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Recommendation Model Registry List */}
            <div
              className={cn(
                'p-6 rounded-3xl border transition-colors',
                isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200 shadow-sm'
              )}
            >
              <h2 className={cn('text-lg font-bold flex items-center gap-2 mb-4 border-l-4 border-brand-500 pl-3', isDark ? 'text-zinc-200' : 'text-zinc-800')}>
                <Sparkles className="w-5 h-5 text-brand-400" />
                Recommendation Model Registry
              </h2>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className={cn('border-b font-semibold uppercase tracking-wider', isDark ? 'border-zinc-800 text-zinc-500' : 'border-zinc-200 text-zinc-400')}>
                      <th className="pb-3 pr-4">Version</th>
                      <th className="pb-3 px-4">Trained Date</th>
                      <th className="pb-3 px-4 text-center">Precision@10</th>
                      <th className="pb-3 px-4 text-center">Status</th>
                      <th className="pb-3 pl-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className={cn('divide-y', isDark ? 'divide-zinc-800/40' : 'divide-zinc-100')}>
                    {recVersions && recVersions.length > 0 ? (
                      [...recVersions].reverse().map((v) => {
                        const isVersionActive = v.status === 'ACTIVE';
                        const hasPrevious = recVersions.some(x => x.status === 'ARCHIVED' || x.status === 'ROLLED_BACK');
                        return (
                          <tr key={v.version} className="hover:bg-zinc-850/10 transition-colors">
                            <td className="py-4 pr-4 font-mono font-bold text-zinc-200">{v.version}</td>
                            <td className="py-4 px-4 text-zinc-400">{new Date(v.trained_on || Date.now()).toLocaleDateString()}</td>
                            <td className="py-4 px-4 text-center font-semibold text-brand-400">
                              {v.metrics?.precision_at_k !== undefined ? `${v.metrics.precision_at_k}%` : 'N/A'}
                            </td>
                            <td className="py-4 px-4 text-center">
                              <span className={cn('px-2.5 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider', getStatusBadgeClass(v.status))}>
                                {v.status}
                              </span>
                            </td>
                            <td className="py-4 pl-4 text-right">
                              <div className="flex gap-2 justify-end">
                                {v.status === 'PENDING_APPROVAL' && (
                                  <>
                                    <button
                                      onClick={() => approveModelMutation.mutate({ modelType: 'recommendation', version: v.version })}
                                      className="p-1.5 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 rounded-lg transition-colors cursor-pointer border border-emerald-500/20"
                                      title="Approve & Activate"
                                    >
                                      <Check className="w-3.5 h-3.5" />
                                    </button>
                                    <button
                                      onClick={() => {
                                        setSelectedVersionToReject({ modelType: 'recommendation', version: v.version });
                                        setRejectionModalOpen(true);
                                      }}
                                      className="p-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg transition-colors cursor-pointer border border-red-500/20"
                                      title="Reject Model Build"
                                    >
                                      <X className="w-3.5 h-3.5" />
                                    </button>
                                  </>
                                )}
                                {isVersionActive && hasPrevious && (
                                  <button
                                    onClick={() => {
                                      // Find previous archived/rollbackable version
                                      const prev = [...recVersions].reverse().find(x => x.version !== v.version && (x.status === 'ARCHIVED' || x.status === 'ROLLED_BACK'));
                                      if (prev) {
                                        setSelectedVersionToRollback({ modelType: 'recommendation', version: prev.version });
                                        setRollbackModalOpen(true);
                                      } else {
                                        toast.error('No valid historical model available for rollback.');
                                      }
                                    }}
                                    className={cn(
                                      'px-2.5 py-1.5 border rounded-lg text-[10px] font-bold uppercase transition-colors cursor-pointer',
                                      isDark
                                        ? 'border-zinc-800 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
                                        : 'border-zinc-300 text-zinc-500 hover:bg-zinc-100 hover:text-zinc-800'
                                    )}
                                  >
                                    Rollback
                                  </button>
                                )}
                              </div>
                            </td>
                          </tr>
                        );
                      })
                    ) : (
                      <tr>
                        <td colSpan={5} className="py-8 text-center text-zinc-500 italic">
                          No models registered. Run a training sequence.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Demand Forecast Model Registry List */}
            <div
              className={cn(
                'p-6 rounded-3xl border transition-colors',
                isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200 shadow-sm'
              )}
            >
              <h2 className={cn('text-lg font-bold flex items-center gap-2 mb-4 border-l-4 border-indigo-500 pl-3', isDark ? 'text-zinc-200' : 'text-zinc-800')}>
                <TrendingUp className="w-5 h-5 text-indigo-400" />
                Forecast Model Registry
              </h2>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className={cn('border-b font-semibold uppercase tracking-wider', isDark ? 'border-zinc-800 text-zinc-500' : 'border-zinc-200 text-zinc-400')}>
                      <th className="pb-3 pr-4">Version</th>
                      <th className="pb-3 px-4">Trained Date</th>
                      <th className="pb-3 px-4 text-center">RMSE</th>
                      <th className="pb-3 px-4 text-center">Status</th>
                      <th className="pb-3 pl-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className={cn('divide-y', isDark ? 'divide-zinc-800/40' : 'divide-zinc-100')}>
                    {forecastVersions && forecastVersions.length > 0 ? (
                      [...forecastVersions].reverse().map((v) => {
                        const isVersionActive = v.status === 'ACTIVE';
                        const hasPrevious = forecastVersions.some(x => x.status === 'ARCHIVED' || x.status === 'ROLLED_BACK');
                        return (
                          <tr key={v.version} className="hover:bg-zinc-850/10 transition-colors">
                            <td className="py-4 pr-4 font-mono font-bold text-zinc-200">{v.version}</td>
                            <td className="py-4 px-4 text-zinc-400">{new Date(v.trained_on || Date.now()).toLocaleDateString()}</td>
                            <td className="py-4 px-4 text-center font-semibold text-indigo-400">
                              {v.metrics?.rmse !== undefined ? v.metrics.rmse : 'N/A'}
                            </td>
                            <td className="py-4 px-4 text-center">
                              <span className={cn('px-2.5 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider', getStatusBadgeClass(v.status))}>
                                {v.status}
                              </span>
                            </td>
                            <td className="py-4 pl-4 text-right">
                              <div className="flex gap-2 justify-end">
                                {v.status === 'PENDING_APPROVAL' && (
                                  <>
                                    <button
                                      onClick={() => approveModelMutation.mutate({ modelType: 'forecast', version: v.version })}
                                      className="p-1.5 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 rounded-lg transition-colors cursor-pointer border border-emerald-500/20"
                                      title="Approve & Activate"
                                    >
                                      <Check className="w-3.5 h-3.5" />
                                    </button>
                                    <button
                                      onClick={() => {
                                        setSelectedVersionToReject({ modelType: 'forecast', version: v.version });
                                        setRejectionModalOpen(true);
                                      }}
                                      className="p-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg transition-colors cursor-pointer border border-red-500/20"
                                      title="Reject Model Build"
                                    >
                                      <X className="w-3.5 h-3.5" />
                                    </button>
                                  </>
                                )}
                                {isVersionActive && hasPrevious && (
                                  <button
                                    onClick={() => {
                                      const prev = [...forecastVersions].reverse().find(x => x.version !== v.version && (x.status === 'ARCHIVED' || x.status === 'ROLLED_BACK'));
                                      if (prev) {
                                        setSelectedVersionToRollback({ modelType: 'forecast', version: prev.version });
                                        setRollbackModalOpen(true);
                                      } else {
                                        toast.error('No valid historical model available for rollback.');
                                      }
                                    }}
                                    className={cn(
                                      'px-2.5 py-1.5 border rounded-lg text-[10px] font-bold uppercase transition-colors cursor-pointer',
                                      isDark
                                        ? 'border-zinc-800 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
                                        : 'border-zinc-300 text-zinc-500 hover:bg-zinc-100 hover:text-zinc-800'
                                    )}
                                  >
                                    Rollback
                                  </button>
                                )}
                              </div>
                            </td>
                          </tr>
                        );
                      })
                    ) : (
                      <tr>
                        <td colSpan={5} className="py-8 text-center text-zinc-500 italic">
                          No models registered. Run a training sequence.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Model Comparison Tool */}
          <div
            className={cn(
              'p-6 rounded-3xl border transition-colors',
              isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200 shadow-sm'
            )}
          >
            <div className={cn('flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6 pb-4 border-b', isDark ? 'border-zinc-800/40' : 'border-zinc-200')}>
              <h2 className={cn('text-lg font-bold flex items-center gap-2', isDark ? 'text-zinc-200' : 'text-zinc-800')}>
                <GitCompare className="w-5 h-5 text-brand-400 animate-pulse" />
                Side-by-Side Model Comparison
              </h2>

              <div className="flex items-center gap-3">
                <button
                  onClick={() => setCompareModelType('recommendation')}
                  className={cn(
                    'px-3 py-1.5 rounded-lg text-xs font-semibold border cursor-pointer transition-colors',
                    compareModelType === 'recommendation' ? 'border-brand-500/30 text-brand-400 bg-brand-500/5' : (isDark ? 'border-zinc-800 text-zinc-500 hover:text-zinc-300' : 'border-zinc-200 text-zinc-500 hover:text-zinc-700')
                  )}
                >
                  Recommendation Model
                </button>
                <button
                  onClick={() => setCompareModelType('forecast')}
                  className={cn(
                    'px-3 py-1.5 rounded-lg text-xs font-semibold border cursor-pointer transition-colors',
                    compareModelType === 'forecast' ? 'border-indigo-500/30 text-indigo-400 bg-indigo-500/5' : (isDark ? 'border-zinc-800 text-zinc-500 hover:text-zinc-300' : 'border-zinc-200 text-zinc-500 hover:text-zinc-700')
                  )}
                >
                  Demand Forecasting
                </button>
              </div>
            </div>

            {/* Version Selectors */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-6">
              <div className="space-y-1.5">
                <label className="text-xs text-zinc-500 font-semibold block">Select Model A (Newer Candidate)</label>
                <select
                  value={compareModelA}
                  onChange={(e) => setCompareModelA(e.target.value)}
                  className={cn(
                    'w-full px-3 py-2 rounded-xl text-xs outline-none border cursor-pointer',
                    isDark ? 'bg-zinc-950 border-zinc-800 text-zinc-200' : 'bg-zinc-50 border-zinc-250 text-zinc-800'
                  )}
                >
                  {(compareModelType === 'recommendation' ? recVersions : forecastVersions)?.map((v) => (
                    <option key={v.version} value={v.version}>{v.version} ({v.status})</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs text-zinc-500 font-semibold block">Select Model B (Older Reference)</label>
                <select
                  value={compareModelB}
                  onChange={(e) => setCompareModelB(e.target.value)}
                  className={cn(
                    'w-full px-3 py-2 rounded-xl text-xs outline-none border cursor-pointer',
                    isDark ? 'bg-zinc-950 border-zinc-800 text-zinc-200' : 'bg-zinc-50 border-zinc-250 text-zinc-800'
                  )}
                >
                  {(compareModelType === 'recommendation' ? recVersions : forecastVersions)?.map((v) => (
                    <option key={v.version} value={v.version}>{v.version} ({v.status})</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Comparison Grid */}
            {modelADetails.data && modelBDetails.data ? (
                  <div className={cn('overflow-x-auto border rounded-2xl', isDark ? 'border-zinc-800/40' : 'border-zinc-200')}>
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className={cn('border-b bg-zinc-950/20 font-semibold uppercase tracking-wider', isDark ? 'border-zinc-800 text-zinc-500' : 'border-zinc-200 text-zinc-400 bg-zinc-50')}>
                      <th className="py-3 px-4">Parameter</th>
                      <th className="py-3 px-4">Model A ({compareModelA})</th>
                      <th className="py-3 px-4">Model B ({compareModelB})</th>
                      <th className="py-3 px-4 text-right">Delta / Improvement</th>
                    </tr>
                  </thead>
                      <tbody className={cn('divide-y', isDark ? 'divide-zinc-800/30' : 'divide-zinc-100')}>
                        <tr className="hover:bg-zinc-850/5">
                          <td className={cn('py-3 px-4 font-semibold', isDark ? 'text-zinc-400' : 'text-zinc-600')}>MLOps serving status</td>
                      <td className="py-3 px-4">
                        <span className={cn('px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider', getStatusBadgeClass(modelADetails.data.status))}>
                          {modelADetails.data.status}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span className={cn('px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider', getStatusBadgeClass(modelBDetails.data.status))}>
                          {modelBDetails.data.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right text-zinc-500">—</td>
                    </tr>
                        <tr className="hover:bg-zinc-850/5">
                          <td className={cn('py-3 px-4 font-semibold', isDark ? 'text-zinc-400' : 'text-zinc-600')}>Training Date</td>
                          <td className={cn('py-3 px-4', isDark ? 'text-zinc-300' : 'text-zinc-700')}>{new Date(modelADetails.data.training_date).toLocaleString()}</td>
                          <td className={cn('py-3 px-4', isDark ? 'text-zinc-300' : 'text-zinc-700')}>{new Date(modelBDetails.data.training_date).toLocaleString()}</td>
                          <td className="py-3 px-4 text-right text-zinc-500">—</td>
                        </tr>
                        <tr className="hover:bg-zinc-850/5">
                          <td className={cn('py-3 px-4 font-semibold', isDark ? 'text-zinc-400' : 'text-zinc-600')}>Trained Dataset version</td>
                      <td className="py-3 px-4 font-mono text-brand-400">{modelADetails.data.dataset_version}</td>
                      <td className="py-3 px-4 font-mono text-zinc-500">{modelBDetails.data.dataset_version}</td>
                      <td className="py-3 px-4 text-right text-zinc-500">—</td>
                    </tr>
                        <tr className="hover:bg-zinc-850/5">
                          <td className={cn('py-3 px-4 font-semibold', isDark ? 'text-zinc-400' : 'text-zinc-600')}>Training duration</td>
                          <td className={cn('py-3 px-4', isDark ? 'text-zinc-300' : 'text-zinc-700')}>{modelADetails.data.training_duration}s</td>
                          <td className={cn('py-3 px-4', isDark ? 'text-zinc-300' : 'text-zinc-700')}>{modelBDetails.data.training_duration}s</td>
                          <td className={cn('py-3 px-4 text-right', isDark ? 'text-zinc-350' : 'text-zinc-500')}>
                        {modelADetails.data.training_duration - modelBDetails.data.training_duration > 0
                          ? `+${(modelADetails.data.training_duration - modelBDetails.data.training_duration).toFixed(1)}s`
                          : `${(modelADetails.data.training_duration - modelBDetails.data.training_duration).toFixed(1)}s`}
                      </td>
                    </tr>
                        <tr className="hover:bg-zinc-850/5">
                          <td className={cn('py-3 px-4 font-semibold', isDark ? 'text-zinc-400' : 'text-zinc-600')}>Training Algorithm</td>
                          <td className={cn('py-3 px-4', isDark ? 'text-zinc-300' : 'text-zinc-700')}>{modelADetails.data.algorithm}</td>
                          <td className={cn('py-3 px-4', isDark ? 'text-zinc-300' : 'text-zinc-700')}>{modelBDetails.data.algorithm}</td>
                          <td className="py-3 px-4 text-right text-zinc-500">—</td>
                        </tr>

                    {/* Render Model specific metrics */}
                    {compareModelType === 'recommendation' ? (
                      <>
                        <tr className="hover:bg-zinc-850/5">
                          <td className="py-3 px-4 font-semibold text-zinc-400">Precision@10 (higher is better)</td>
                          <td className="py-3 px-4 text-brand-400 font-bold">{modelADetails.data.metrics?.precision_at_k}%</td>
                          <td className="py-3 px-4 text-zinc-300">{modelBDetails.data.metrics?.precision_at_k}%</td>
                          <td className={cn('py-3 px-4 text-right font-bold',
                            (modelADetails.data.metrics?.precision_at_k || 0) >= (modelBDetails.data.metrics?.precision_at_k || 0) ? 'text-emerald-500' : 'text-red-500'
                          )}>
                            {(modelADetails.data.metrics?.precision_at_k || 0) - (modelBDetails.data.metrics?.precision_at_k || 0) >= 0 ? '+' : ''}
                            {((modelADetails.data.metrics?.precision_at_k || 0) - (modelBDetails.data.metrics?.precision_at_k || 0)).toFixed(2)}%
                          </td>
                        </tr>
                        <tr className="hover:bg-zinc-850/5">
                          <td className="py-3 px-4 font-semibold text-zinc-400">Recall@10</td>
                          <td className={cn('py-3 px-4', isDark ? 'text-zinc-200' : 'text-zinc-700')}>{modelADetails.data.metrics?.recall_at_k}%</td>
                          <td className={cn('py-3 px-4', isDark ? 'text-zinc-400' : 'text-zinc-600')}>{modelBDetails.data.metrics?.recall_at_k}%</td>
                          <td className={cn('py-3 px-4 text-right', isDark ? 'text-zinc-300' : 'text-zinc-600')}>
                            {((modelADetails.data.metrics?.recall_at_k || 0) - (modelBDetails.data.metrics?.recall_at_k || 0)).toFixed(2)}%
                          </td>
                        </tr>
                        <tr className="hover:bg-zinc-850/5">
                          <td className={cn('py-3 px-4 font-semibold', isDark ? 'text-zinc-400' : 'text-zinc-600')}>F1@10</td>
                          <td className={cn('py-3 px-4', isDark ? 'text-zinc-200' : 'text-zinc-700')}>{modelADetails.data.metrics?.f1_at_k}%</td>
                          <td className={cn('py-3 px-4', isDark ? 'text-zinc-400' : 'text-zinc-600')}>{modelBDetails.data.metrics?.f1_at_k}%</td>
                          <td className={cn('py-3 px-4 text-right', isDark ? 'text-zinc-300' : 'text-zinc-600')}>
                            {((modelADetails.data.metrics?.f1_at_k || 0) - (modelBDetails.data.metrics?.f1_at_k || 0)).toFixed(2)}%
                          </td>
                        </tr>
                        <tr className="hover:bg-zinc-850/5">
                          <td className={cn('py-3 px-4 font-semibold', isDark ? 'text-zinc-400' : 'text-zinc-600')}>Catalog Coverage</td>
                          <td className={cn('py-3 px-4', isDark ? 'text-zinc-200' : 'text-zinc-700')}>{modelADetails.data.metrics?.coverage}%</td>
                          <td className={cn('py-3 px-4', isDark ? 'text-zinc-400' : 'text-zinc-600')}>{modelBDetails.data.metrics?.coverage}%</td>
                          <td className={cn('py-3 px-4 text-right', isDark ? 'text-zinc-300' : 'text-zinc-600')}>
                            {((modelADetails.data.metrics?.coverage || 0) - (modelBDetails.data.metrics?.coverage || 0)).toFixed(2)}%
                          </td>
                        </tr>
                      </>
                    ) : (
                      <>
                        <tr className="hover:bg-zinc-850/5">
                          <td className="py-3 px-4 font-semibold text-zinc-400">RMSE (lower is better)</td>
                          <td className="py-3 px-4 text-indigo-400 font-bold">{modelADetails.data.metrics?.rmse}</td>
                          <td className={cn('py-3 px-4', isDark ? 'text-zinc-300' : 'text-zinc-700')}>{modelBDetails.data.metrics?.rmse}</td>
                          <td className={cn('py-3 px-4 text-right font-bold',
                            (modelADetails.data.metrics?.rmse || 0) <= (modelBDetails.data.metrics?.rmse || 0) ? 'text-emerald-500' : 'text-red-500'
                          )}>
                            {(modelADetails.data.metrics?.rmse || 0) - (modelBDetails.data.metrics?.rmse || 0) > 0 ? '+' : ''}
                            {((modelADetails.data.metrics?.rmse || 0) - (modelBDetails.data.metrics?.rmse || 0)).toFixed(4)}
                          </td>
                        </tr>
                        <tr className="hover:bg-zinc-850/5">
                          <td className={cn('py-3 px-4 font-semibold', isDark ? 'text-zinc-400' : 'text-zinc-600')}>MAE (lower is better)</td>
                          <td className={cn('py-3 px-4', isDark ? 'text-zinc-200' : 'text-zinc-700')}>{modelADetails.data.metrics?.mae}</td>
                          <td className={cn('py-3 px-4', isDark ? 'text-zinc-400' : 'text-zinc-600')}>{modelBDetails.data.metrics?.mae}</td>
                          <td className={cn('py-3 px-4 text-right font-bold',
                            (modelADetails.data.metrics?.mae || 0) <= (modelBDetails.data.metrics?.mae || 0) ? 'text-emerald-500' : 'text-red-500'
                          )}>
                            {(modelADetails.data.metrics?.mae || 0) - (modelBDetails.data.metrics?.mae || 0) > 0 ? '+' : ''}
                            {((modelADetails.data.metrics?.mae || 0) - (modelBDetails.data.metrics?.mae || 0)).toFixed(4)}
                          </td>
                        </tr>
                        <tr className="hover:bg-zinc-850/5">
                          <td className={cn('py-3 px-4 font-semibold', isDark ? 'text-zinc-400' : 'text-zinc-600')}>MAPE (%)</td>
                          <td className={cn('py-3 px-4', isDark ? 'text-zinc-200' : 'text-zinc-700')}>{((modelADetails.data.metrics?.mape || 0) * 100).toFixed(2)}%</td>
                          <td className={cn('py-3 px-4', isDark ? 'text-zinc-400' : 'text-zinc-600')}>{((modelBDetails.data.metrics?.mape || 0) * 100).toFixed(2)}%</td>
                          <td className={cn('py-3 px-4 text-right', isDark ? 'text-zinc-300' : 'text-zinc-600')}>
                            {(((modelADetails.data.metrics?.mape || 0) - (modelBDetails.data.metrics?.mape || 0)) * 100).toFixed(2)}%
                          </td>
                        </tr>
                        <tr className="hover:bg-zinc-850/5">
                          <td className={cn('py-3 px-4 font-semibold', isDark ? 'text-zinc-400' : 'text-zinc-600')}>R² Coefficient</td>
                          <td className={cn('py-3 px-4', isDark ? 'text-zinc-200' : 'text-zinc-700')}>{modelADetails.data.metrics?.r2}</td>
                          <td className={cn('py-3 px-4', isDark ? 'text-zinc-400' : 'text-zinc-600')}>{modelBDetails.data.metrics?.r2}</td>
                          <td className={cn('py-3 px-4 text-right', isDark ? 'text-zinc-300' : 'text-zinc-600')}>
                            {((modelADetails.data.metrics?.r2 || 0) - (modelBDetails.data.metrics?.r2 || 0)).toFixed(4)}
                          </td>
                        </tr>
                      </>
                    )}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="py-8 text-center text-zinc-500 italic">
                Select two model versions to see a side-by-side parameters and performance delta check.
              </div>
            )}
          </div>
        </div>
      )}

      {/* ─── TAB 3: PERFORMANCE TRENDS ──────────────────────────────────────── */}
      {activeTab === 'trends' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Recommendation Model Trend */}
            <div
              className={cn(
                'p-6 rounded-3xl border transition-colors',
                isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200 shadow-sm'
              )}
            >
              <h2 className={cn('text-lg font-bold flex items-center gap-2 mb-4 border-l-4 border-brand-500 pl-3', isDark ? 'text-zinc-200' : 'text-zinc-800')}>
                <BarChart2 className="w-5 h-5 text-brand-400" />
                Recommendation Precision Trend
              </h2>

              {recVersions && recVersions.length >= 2 ? (
                <div className="h-72 w-full pt-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={recVersions}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                      <XAxis dataKey="version" stroke="#71717a" />
                      <YAxis stroke="#71717a" unit="%" />
                      <RechartsTooltip contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', borderRadius: '12px' }} />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="metrics.precision_at_k"
                        name="Precision@10"
                        stroke="#e11d48"
                        strokeWidth={2.5}
                        activeDot={{ r: 6 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="h-72 flex flex-col items-center justify-center text-center p-6 border border-dashed border-zinc-800 rounded-2xl">
                  <AlertCircle className="w-8 h-8 text-zinc-600 mb-2" />
                  <p className="text-sm text-zinc-500">
                    Not enough historical training runs to display a performance trend.
                  </p>
                  <p className="text-xs text-zinc-650 mt-1 max-w-xs">
                    Please train at least 2 versions to plot the offline precision tracking line.
                  </p>
                </div>
              )}
            </div>

            {/* Forecast Model Metrics Trend */}
            <div
              className={cn(
                'p-6 rounded-3xl border transition-colors',
                isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200 shadow-sm'
              )}
            >
              <h2 className={cn('text-lg font-bold flex items-center gap-2 mb-4 border-l-4 border-indigo-500 pl-3', isDark ? 'text-zinc-200' : 'text-zinc-800')}>
                <TrendingUp className="w-5 h-5 text-indigo-400" />
                Forecast RMSE & MAE Trend
              </h2>

              {forecastVersions && forecastVersions.length >= 2 ? (
                <div className="h-72 w-full pt-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={forecastVersions}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                      <XAxis dataKey="version" stroke="#71717a" />
                      <YAxis stroke="#71717a" />
                      <RechartsTooltip contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', borderRadius: '12px' }} />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="metrics.rmse"
                        name="RMSE"
                        stroke="#6366f1"
                        strokeWidth={2.5}
                        activeDot={{ r: 6 }}
                      />
                      <Line
                        type="monotone"
                        dataKey="metrics.mae"
                        name="MAE"
                        stroke="#a78bfa"
                        strokeWidth={2}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="h-72 flex flex-col items-center justify-center text-center p-6 border border-dashed border-zinc-800 rounded-2xl">
                  <AlertCircle className="w-8 h-8 text-zinc-600 mb-2" />
                  <p className="text-sm text-zinc-500">
                    Not enough historical training runs to display a performance trend.
                  </p>
                  <p className="text-xs text-zinc-650 mt-1 max-w-xs">
                    Please train at least 2 versions to plot the offline RMSE / MAE tracking line.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ─── MODAL DIALOGS ──────────────────────────────────────────────────── */}
      <AnimatePresence>
        {/* Confirm Retraining Modal */}
        {confirmTrainOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-zinc-950/60 backdrop-blur-md">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-zinc-900 border border-zinc-800 w-full max-w-md p-6 rounded-3xl space-y-4 shadow-2xl"
            >
              <div className="flex gap-3 items-start">
                <div className="w-10 h-10 rounded-full bg-brand-500/10 flex items-center justify-center text-brand-400 shrink-0">
                  <Brain className="w-5.5 h-5.5" />
                </div>
                <div>
                  <h4 className="text-lg font-bold text-zinc-100">Initiate Retraining Run</h4>
                  <p className="text-xs text-zinc-400 mt-1 leading-relaxed">
                    This triggers a full training cycle: syncs core MySQL data, builds recommendation algorithms, tunes XGBoost parameters, and serves the new builds via zero-downtime hot reloading.
                  </p>
                </div>
              </div>
              <div className="flex gap-2 justify-end pt-2">
                <button
                  onClick={() => setConfirmTrainOpen(false)}
                  className="px-4 py-2 border border-zinc-800 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200 rounded-xl text-xs font-semibold cursor-pointer transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => startManualRetraining.mutate()}
                  className="px-4 py-2 bg-brand-500 text-white rounded-xl text-xs font-bold hover:bg-brand-600 cursor-pointer shadow-lg shadow-brand-500/15"
                >
                  Start Training
                </button>
              </div>
            </motion.div>
          </div>
        )}

        {/* Model Rejection Modal */}
        {rejectionModalOpen && selectedVersionToReject && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-zinc-950/60 backdrop-blur-md">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-zinc-900 border border-zinc-800 w-full max-w-md p-6 rounded-3xl space-y-4 shadow-2xl"
            >
              <div className="flex gap-3 items-start">
                <div className="w-10 h-10 rounded-full bg-red-500/10 flex items-center justify-center text-red-500 shrink-0">
                  <X className="w-5.5 h-5.5" />
                </div>
                <div>
                  <h4 className="text-lg font-bold text-zinc-100">Reject Model Build?</h4>
                  <p className="text-xs text-zinc-400 mt-1">
                    Provide a rejection reason. This version will be marked as REJECTED in the registries and will not be servable.
                  </p>
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[10px] text-zinc-500 font-bold uppercase block">Rejection Reason</label>
                <input
                  type="text"
                  placeholder="E.g., Forecast RMSE is worse than serving model."
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded-xl text-xs outline-none focus:border-red-500 text-zinc-200"
                  required
                />
              </div>

              <div className="flex gap-2 justify-end pt-2">
                <button
                  onClick={() => {
                    setRejectionModalOpen(false);
                    setRejectionReason('');
                  }}
                  className="px-4 py-2 border border-zinc-800 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200 rounded-xl text-xs font-semibold cursor-pointer transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    if (!rejectionReason.trim()) {
                      toast.error('Rejection reason is required.');
                      return;
                    }
                    rejectModelMutation.mutate({
                      modelType: selectedVersionToReject.modelType,
                      version: selectedVersionToReject.version,
                      reason: rejectionReason
                    });
                  }}
                  className="px-4 py-2 bg-red-500 text-white rounded-xl text-xs font-bold hover:bg-red-650 cursor-pointer shadow-lg shadow-red-500/15"
                >
                  Reject Model
                </button>
              </div>
            </motion.div>
          </div>
        )}

        {/* Model Rollback Modal */}
        {rollbackModalOpen && selectedVersionToRollback && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-zinc-950/60 backdrop-blur-md">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-zinc-900 border border-zinc-800 w-full max-w-md p-6 rounded-3xl space-y-4 shadow-2xl"
            >
              <div className="flex gap-3 items-start">
                <div className="w-10 h-10 rounded-full bg-amber-500/10 flex items-center justify-center text-amber-500 shrink-0">
                  <AlertTriangle className="w-5.5 h-5.5" />
                </div>
                <div>
                  <h4 className="text-lg font-bold text-zinc-100">Rollback Model Version?</h4>
                  <p className="text-xs text-zinc-400 mt-1 leading-relaxed">
                    You are rolling back the active model to version <span className="font-semibold text-brand-400">{selectedVersionToRollback.version}</span>. The serving code will instantly switch back to this build.
                  </p>
                  <p className="text-[10px] text-amber-500 bg-amber-500/5 border border-amber-500/10 p-2.5 rounded-lg mt-3">
                    Warning: The selected previous model will become serve-active immediately.
                  </p>
                </div>
              </div>

              <div className="flex gap-2 justify-end pt-2">
                <button
                  onClick={() => setRollbackModalOpen(false)}
                  className="px-4 py-2 border border-zinc-800 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200 rounded-xl text-xs font-semibold cursor-pointer transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => rollbackModelMutation.mutate({
                    modelType: selectedVersionToRollback.modelType,
                    version: selectedVersionToRollback.version
                  })}
                  className="px-4 py-2 bg-amber-500 text-zinc-950 font-bold rounded-xl text-xs hover:bg-amber-600 cursor-pointer shadow-lg shadow-amber-500/15"
                >
                  Confirm Rollback
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
