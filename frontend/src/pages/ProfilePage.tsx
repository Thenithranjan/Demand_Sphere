/**
 * Profile Page — Retail AI Frontend
 * ===================================
 * Manages user metadata, theme toggle, and credentials.
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { UserCircle, Key, Laptop, Sparkles, LogOut, CheckCircle } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { cn, getInitials } from '../utils';
import { fadeIn } from '../animations/variants';
import { toast } from 'sonner';

const passwordSchema = z.object({
  current: z.string().min(1, 'Current password is required'),
  newPassword: z.string().min(6, 'Password must be at least 6 characters'),
  confirm: z.string(),
}).refine((data) => data.newPassword === data.confirm, {
  message: "Passwords don't match",
  path: ['confirm'],
});

type PasswordFormData = z.infer<typeof passwordSchema>;

export default function ProfilePage() {
  const { isDark, toggleTheme, theme } = useTheme();
  const { user, logout } = useAuth();
  const [success, setSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<PasswordFormData>({
    resolver: zodResolver(passwordSchema),
  });

  const onSubmit = async (data: PasswordFormData) => {
    try {
      // Fake credentials update for demo
      await new Promise((resolve) => setTimeout(resolve, 800));
      setSuccess(true);
      reset();
      toast.success('Password updated successfully');
    } catch {
      toast.error('Failed to change password');
    }
  };

  return (
    <motion.div variants={fadeIn} initial="hidden" animate="visible" className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1 className={cn('text-2xl font-bold', isDark ? 'text-zinc-100' : 'text-zinc-900')}>
          User Profile
        </h1>
        <p className="text-sm text-zinc-500 mt-1">
          Review your credentials, credentials roles, and preference controls
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Profile Card */}
        <div className={cn(
          'rounded-2xl p-6 border flex flex-col items-center justify-between text-center',
          isDark ? 'bg-zinc-900/60 border-zinc-800/60 backdrop-blur-xl' : 'bg-white border-zinc-200 shadow-sm'
        )}>
          {user && (
            <div className="space-y-4 flex-1 flex flex-col items-center justify-center">
              <div className="w-20 h-20 rounded-full bg-brand-500/20 flex items-center justify-center text-brand-400 text-2xl font-bold border-2 border-brand-500/30">
                {getInitials(user.FullName || user.Username)}
              </div>
              <div>
                <h2 className={cn('font-bold text-lg', isDark ? 'text-zinc-200' : 'text-zinc-800')}>
                  {user.FullName || user.Username}
                </h2>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-brand-500/10 text-brand-400 border border-brand-500/30 mt-1">
                  {user.Role}
                </span>
              </div>
              <p className="text-xs text-zinc-500">{user.Email}</p>
            </div>
          )}

          <button
            onClick={logout}
            className="mt-6 flex items-center justify-center gap-2 px-4 py-2 w-full rounded-xl text-sm font-medium border border-red-500/30 text-red-400 hover:bg-red-500/10 transition-colors"
          >
            <LogOut className="w-4 h-4" /> Sign Out
          </button>
        </div>

        {/* Change Password & Preferences */}
        <div className="md:col-span-2 space-y-6">
          {/* Preferences */}
          <div className={cn(
            'rounded-2xl p-6 border space-y-4',
            isDark ? 'bg-zinc-900/60 border-zinc-800/60' : 'bg-white border-zinc-200 shadow-sm'
          )}>
            <h3 className={cn('text-sm font-semibold flex items-center gap-2', isDark ? 'text-zinc-200' : 'text-zinc-800')}>
              <Laptop className="w-4 h-4 text-brand-400" /> Preferences
            </h3>
            <div className="flex items-center justify-between py-2">
              <div>
                <span className="text-sm font-medium block">Application Theme</span>
                <span className="text-xs text-zinc-500">Toggle dark mode first look</span>
              </div>
              <button
                onClick={toggleTheme}
                className={cn(
                  'px-3 py-1.5 rounded-xl text-xs font-medium border transition-colors capitalize',
                  isDark
                    ? 'bg-zinc-800 border-zinc-700 text-zinc-300'
                    : 'bg-zinc-50 border-zinc-200 text-zinc-600'
                )}
              >
                {theme} Mode
              </button>
            </div>
          </div>

          {/* Password Reset */}
          <div className={cn(
            'rounded-2xl p-6 border space-y-4',
            isDark ? 'bg-zinc-900/60 border-zinc-800/60' : 'bg-white border-zinc-200 shadow-sm'
          )}>
            <h3 className={cn('text-sm font-semibold flex items-center gap-2', isDark ? 'text-zinc-200' : 'text-zinc-800')}>
              <Key className="w-4 h-4 text-brand-400" /> Change Password
            </h3>

            {success && (
              <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-4 py-3 rounded-xl text-sm flex items-center gap-2">
                <CheckCircle className="w-4 h-4" /> Password changed successfully
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">Current Password</label>
                <input
                  {...register('current')}
                  type="password"
                  className={cn(
                    'w-full px-3 py-2 rounded-xl bg-zinc-800/20 border text-sm outline-none transition-colors placeholder:text-zinc-600',
                    errors.current ? 'border-red-500/50' : 'border-zinc-700/50',
                    isDark ? 'text-zinc-200 focus:border-brand-500' : 'text-zinc-800 focus:border-brand-500'
                  )}
                  placeholder="Enter current password"
                />
                {errors.current && <p className="text-xs text-red-400 mt-1">{errors.current.message}</p>}
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">New Password</label>
                <input
                  {...register('newPassword')}
                  type="password"
                  className={cn(
                    'w-full px-3 py-2 rounded-xl bg-zinc-800/20 border text-sm outline-none transition-colors placeholder:text-zinc-600',
                    errors.newPassword ? 'border-red-500/50' : 'border-zinc-700/50',
                    isDark ? 'text-zinc-200 focus:border-brand-500' : 'text-zinc-800 focus:border-brand-500'
                  )}
                  placeholder="Enter new password"
                />
                {errors.newPassword && <p className="text-xs text-red-400 mt-1">{errors.newPassword.message}</p>}
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-400 mb-1.5">Confirm New Password</label>
                <input
                  {...register('confirm')}
                  type="password"
                  className={cn(
                    'w-full px-3 py-2 rounded-xl bg-zinc-800/20 border text-sm outline-none transition-colors placeholder:text-zinc-600',
                    errors.confirm ? 'border-red-500/50' : 'border-zinc-700/50',
                    isDark ? 'text-zinc-200 focus:border-brand-500' : 'text-zinc-800 focus:border-brand-500'
                  )}
                  placeholder="Confirm new password"
                />
                {errors.confirm && <p className="text-xs text-red-400 mt-1">{errors.confirm.message}</p>}
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="flex items-center justify-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-white gradient-brand hover:opacity-90 transition-opacity disabled:opacity-50"
              >
                Update Password
              </button>
            </form>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
