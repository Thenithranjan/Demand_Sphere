/**
 * Login Page — Retail AI Frontend
 * ==================================
 * Modern login with animated gradient background, glassmorphic card,
 * Zod validation, and role-based authentication.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Eye, EyeOff, Sparkles, Loader2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { authApi } from '../services/authApi';
import { cn } from '../utils';

const loginSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
  remember: z.boolean().optional(),
});

type LoginFormData = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { remember: false },
  });

  const handleFillCredentials = (role: string) => {
    if (role === 'Admin') {
      setValue('username', 'admin');
      setValue('password', 'admin123');
    } else if (role === 'Manager') {
      setValue('username', 'manager');
      setValue('password', 'manager123');
    } else if (role === 'Employee') {
      setValue('username', 'employee1');
      setValue('password', 'employee123');
    }
  };

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    setError('');

    // Predefined seeded credentials list for offline fallback
    const MOCK_USERS = [
      { username: 'admin', password: 'admin123', UserID: 'U0001', FullName: 'System Administrator', Email: 'admin@retailai.com', Role: 'Admin' },
      { username: 'manager', password: 'manager123', UserID: 'U0002', FullName: 'Store Manager', Email: 'manager@retailai.com', Role: 'Manager' },
      { username: 'employee1', password: 'employee123', UserID: 'U0003', FullName: 'Sales Associate', Email: 'employee1@retailai.com', Role: 'Employee' },
    ];

    try {
      // 1. Try backend POST Login first
      const response = await authApi.login({
        Username: data.username,
        Password: data.password,
      });

      // Save token in localStorage
      localStorage.setItem('retailai_token', response.access_token);

      login({
        UserID: response.user.UserID,
        Username: response.user.Username || '',
        FullName: response.user.FullName || '',
        Email: response.user.Email || '',
        Role: response.user.Role || 'Employee',
      });

      navigate('/dashboard');
    } catch (apiError: any) {
      // 2. Offline fallback: check local mock credentials
      const matchedMock = MOCK_USERS.find(
        (u) => u.username.toLowerCase() === data.username.toLowerCase() && u.password === data.password
      );

      if (matchedMock) {
        localStorage.setItem('retailai_token', `mock-jwt-${matchedMock.UserID}`);
        login({
          UserID: matchedMock.UserID,
          Username: matchedMock.username,
          FullName: matchedMock.FullName,
          Email: matchedMock.Email,
          Role: matchedMock.Role,
        });
        navigate('/dashboard');
      } else {
        const errorDetail = apiError.response?.data?.detail || 'Invalid username or password';
        setError(errorDetail);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden bg-zinc-950">
      {/* ─── Animated Background ────────────────────────────────── */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-gradient-to-br from-brand-900/30 via-zinc-950 to-violet-900/20" />
        {/* Floating orbs */}
        <motion.div
          animate={{ y: [0, -20, 0], x: [0, 10, 0] }}
          transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }}
          className="absolute top-1/4 left-1/4 w-72 h-72 bg-brand-500/10 rounded-full blur-3xl"
        />
        <motion.div
          animate={{ y: [0, 15, 0], x: [0, -15, 0] }}
          transition={{ duration: 10, repeat: Infinity, ease: 'easeInOut' }}
          className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-violet-500/10 rounded-full blur-3xl"
        />
        <motion.div
          animate={{ y: [0, -10, 0] }}
          transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
          className="absolute top-1/2 right-1/3 w-48 h-48 bg-emerald-500/5 rounded-full blur-3xl"
        />
        {/* Grid pattern */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: 'linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.1) 1px, transparent 1px)',
            backgroundSize: '60px 60px',
          }}
        />
      </div>

      {/* ─── Login Card ─────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: [0.25, 0.46, 0.45, 0.94] }}
        className="relative z-10 w-full max-w-md mx-4"
      >
        <div className="bg-zinc-900/60 backdrop-blur-2xl border border-zinc-800/60 rounded-3xl p-8 shadow-2xl">
          {/* Brand */}
          <div className="text-center mb-8">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
              className="w-14 h-14 rounded-2xl gradient-brand flex items-center justify-center mx-auto mb-4"
            >
              <Sparkles className="w-7 h-7 text-white" />
            </motion.div>
            <h1 className="text-2xl font-bold text-zinc-100">Welcome back</h1>
            <p className="text-sm text-zinc-500 mt-1">Sign in to RetailAI Intelligence Suite</p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 text-sm text-red-400"
              >
                {error}
              </motion.div>
            )}

            {/* Username */}
            <div>
              <label className="block text-sm font-medium text-zinc-400 mb-1.5">Username</label>
              <input
                {...register('username')}
                type="text"
                className={cn(
                  'w-full px-4 py-2.5 rounded-xl bg-zinc-800/50 border text-zinc-100 text-sm outline-none transition-colors',
                  'placeholder:text-zinc-600 focus:border-brand-500 focus:ring-1 focus:ring-brand-500/20',
                  errors.username ? 'border-red-500/50' : 'border-zinc-700/50'
                )}
                placeholder="Enter your username"
              />
              {errors.username && <p className="text-xs text-red-400 mt-1">{errors.username.message}</p>}
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-medium text-zinc-400 mb-1.5">Password</label>
              <div className="relative">
                <input
                  {...register('password')}
                  type={showPassword ? 'text' : 'password'}
                  className={cn(
                    'w-full px-4 py-2.5 pr-10 rounded-xl bg-zinc-800/50 border text-zinc-100 text-sm outline-none transition-colors',
                    'placeholder:text-zinc-600 focus:border-brand-500 focus:ring-1 focus:ring-brand-500/20',
                    errors.password ? 'border-red-500/50' : 'border-zinc-700/50'
                  )}
                  placeholder="Enter your password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && <p className="text-xs text-red-400 mt-1">{errors.password.message}</p>}
            </div>

            {/* Remember Me & Forgot */}
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 text-sm text-zinc-400 cursor-pointer">
                <input
                  {...register('remember')}
                  type="checkbox"
                  className="w-4 h-4 rounded border-zinc-700 bg-zinc-800 text-brand-500 focus:ring-brand-500/20"
                />
                Remember me
              </label>
              <button type="button" className="text-sm text-brand-400 hover:text-brand-300 transition-colors">
                Forgot password?
              </button>
            </div>

            {/* Submit */}
            <motion.button
              type="submit"
              disabled={isLoading}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              className={cn(
                'w-full py-2.5 rounded-xl text-sm font-semibold text-white transition-all',
                'gradient-brand hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed',
                'flex items-center justify-center gap-2'
              )}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                'Sign in'
              )}
            </motion.button>
          </form>

          {/* Role hints */}
          <div className="mt-6 pt-6 border-t border-zinc-800">
            <p className="text-xs text-zinc-600 text-center mb-3">Demo accounts</p>
            <div className="grid grid-cols-3 gap-2">
              {['Admin', 'Manager', 'Employee'].map((role) => (
                <button
                  type="button"
                  key={role}
                  onClick={() => handleFillCredentials(role)}
                  className="text-center py-1.5 px-2 rounded-lg bg-zinc-800/30 border border-zinc-800 text-xs text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/80 transition-all cursor-pointer"
                >
                  {role}
                </button>
              ))}
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
