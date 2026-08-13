/**
 * Admin Page — Retail AI Frontend
 * =====================================
 * Modern user management board allowing Admins and Managers
 * to view, add, and remove staff members, and inspect passwords.
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Trash2, Eye, EyeOff, X, Shield, Users } from 'lucide-react';
import { useUsers } from '../hooks';
import { useAuth } from '../contexts/AuthContext';
import { userApi as userService } from '../services/userApi';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { useTheme } from '../contexts/ThemeContext';
import { cn } from '../utils';
import { fadeIn, staggerContainer } from '../animations/variants';

export default function AdminPage() {
  const { isDark } = useTheme();
  const { user: currentUser } = useAuth();
  const queryClient = useQueryClient();
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [visiblePasswords, setVisiblePasswords] = useState<Record<string, boolean>>({});

  // Fetch all users
  const { data: usersData, isLoading } = useUsers({ limit: 500 });

  const users = usersData?.items ?? [];

  // Filter users based on logged-in user's role
  // Admin can manage Managers and Employees.
  // Manager can only manage Employees.
  const managersList = users.filter((u) => u.Role === 'Manager');
  const employeesList = users.filter((u) => u.Role === 'Employee');

  const togglePasswordVisibility = (userId: string) => {
    setVisiblePasswords((prev) => ({
      ...prev,
      [userId]: !prev[userId],
    }));
  };

  const handleAddSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    
    const roleValue = formData.get('Role') as string;
    
    const newUser = {
      UserID: formData.get('UserID') as string,
      Username: formData.get('Username') as string,
      FullName: formData.get('FullName') as string,
      Email: formData.get('Email') as string,
      Password: formData.get('Password') as string,
      Role: roleValue,
    };

    try {
      await userService.create(newUser);
      toast.success(`${roleValue} added successfully`);
      setIsAddModalOpen(false);
      queryClient.invalidateQueries({ queryKey: ['users'] });
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to add user';
      toast.error(errorMsg);
    }
  };

  const handleDelete = async (userId: string, fullName: string) => {
    if (userId === currentUser?.UserID) {
      toast.error('You cannot delete yourself!');
      return;
    }
    if (!confirm(`Are you sure you want to remove "${fullName}"?`)) return;
    
    try {
      await userService.delete(userId);
      toast.success('Staff member removed successfully');
      queryClient.invalidateQueries({ queryKey: ['users'] });
    } catch {
      toast.error('Failed to remove staff member');
    }
  };

  const isEmployee = currentUser?.Role === 'Employee';

  const renderUserTable = (title: string, list: typeof users, showRole = false) => (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Users className="w-5 h-5 text-brand-400" />
        <h2 className={cn('text-lg font-semibold', isDark ? 'text-zinc-200' : 'text-zinc-800')}>{title}</h2>
      </div>
      <div className={cn(
        'rounded-2xl border overflow-hidden transition-colors',
        isDark ? 'border-zinc-800 bg-zinc-900/40 backdrop-blur-xl' : 'border-zinc-200 bg-white shadow-sm'
      )}>
        <table className="w-full text-sm text-left">
          <thead>
            <tr className={cn('border-b text-xs font-semibold uppercase tracking-wider', isDark ? 'border-zinc-800 bg-zinc-900/80 text-zinc-400' : 'border-zinc-200 bg-zinc-50 text-zinc-500')}>
              <th className="px-6 py-4">User ID</th>
              <th className="px-6 py-4">Full Name</th>
              <th className="px-6 py-4">Username</th>
              <th className="px-6 py-4">Email</th>
              {showRole && <th className="px-6 py-4">Role</th>}
              {!isEmployee && <th className="px-6 py-4">Password</th>}
              {!isEmployee && <th className="px-6 py-4 text-right">Actions</th>}
            </tr>
          </thead>
          <tbody>
            <AnimatePresence mode="popLayout">
              {list.length === 0 ? (
                <tr>
                  <td colSpan={showRole ? (isEmployee ? 5 : 7) : (isEmployee ? 4 : 6)} className="px-6 py-10 text-center text-zinc-500">
                    No staff members found.
                  </td>
                </tr>
              ) : (
                list.map((u) => (
                  <motion.tr
                    key={u.UserID}
                    layout
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className={cn('border-b last:border-0 hover:bg-zinc-800/10 transition-colors', isDark ? 'border-zinc-800/50' : 'border-zinc-100')}
                  >
                    <td className="px-6 py-4 font-mono text-xs text-brand-400">{u.UserID}</td>
                    <td className="px-6 py-4 font-medium text-zinc-200">{u.FullName}</td>
                    <td className="px-6 py-4 text-zinc-400">{u.Username}</td>
                    <td className="px-6 py-4 text-zinc-400">{u.Email}</td>
                    {showRole && <td className="px-6 py-4 text-zinc-400 capitalize">{u.Role}</td>}
                    {!isEmployee && (
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-zinc-300">
                            {visiblePasswords[u.UserID] ? (u.Password || '—') : '••••••••'}
                          </span>
                          <button
                            onClick={() => togglePasswordVisibility(u.UserID)}
                            className="text-zinc-500 hover:text-zinc-300 transition-colors p-1"
                          >
                            {visiblePasswords[u.UserID] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                          </button>
                        </div>
                      </td>
                    )}
                    {!isEmployee && (
                      <td className="px-6 py-4 text-right">
                        {u.UserID !== currentUser?.UserID && (
                          <button
                            onClick={() => handleDelete(u.UserID, u.FullName || '')}
                            className="p-2 rounded-xl text-zinc-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </td>
                    )}
                  </motion.tr>
                ))
              )}
            </AnimatePresence>
          </tbody>
        </table>
      </div>
    </div>
  );

  return (
    <motion.div variants={fadeIn} initial="hidden" animate="visible" className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className={cn('text-2xl font-bold tracking-tight', isDark ? 'text-zinc-100' : 'text-zinc-900')}>
            {isEmployee ? 'Staff Directory' : 'Staff Management'}
          </h1>
          <p className="text-sm text-zinc-500 mt-1">
            {isEmployee ? 'View store staff details and contact info' : 'Manage store logins, user roles, and staff credentials'}
          </p>
        </div>
        {!isEmployee && (
          <motion.button
            onClick={() => setIsAddModalOpen(true)}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-white gradient-brand hover:opacity-90 transition-opacity"
          >
            <Plus className="w-4 h-4" /> Add Staff Member
          </motion.button>
        )}
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-brand-500" />
        </div>
      ) : (
        <motion.div variants={staggerContainer} className="space-y-8">
          {/* Managers List (Only Admin can see/manage) */}
          {currentUser?.Role === 'Admin' && renderUserTable('Managers', managersList)}
          
          {/* Employees List (Both Admin and Manager can manage) */}
          {renderUserTable('Store Employees', employeesList)}
        </motion.div>
      )}

      {/* Add Staff Modal */}
      {isAddModalOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto"
          onClick={() => setIsAddModalOpen(false)}
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            onClick={(e) => e.stopPropagation()}
            className={cn(
              'w-full max-w-md rounded-2xl p-6 border my-8',
              isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200'
            )}
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className={cn('text-lg font-bold', isDark ? 'text-zinc-100' : 'text-zinc-900')}>Add New Staff</h2>
              <button onClick={() => setIsAddModalOpen(false)} className="text-zinc-500 hover:text-zinc-300">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <form onSubmit={handleAddSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-zinc-400 mb-1">User ID</label>
                <input
                  type="text"
                  name="UserID"
                  required
                  placeholder="e.g. U0011"
                  defaultValue={`U${String(users.length + 1).padStart(4, '0')}`}
                  className={cn(
                    'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors',
                    isDark
                      ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                      : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                  )}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-400 mb-1">Full Name</label>
                <input
                  type="text"
                  name="FullName"
                  required
                  placeholder="e.g. Rajesh Kumar"
                  className={cn(
                    'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors',
                    isDark
                      ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                      : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                  )}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-400 mb-1">Username</label>
                <input
                  type="text"
                  name="Username"
                  required
                  placeholder="e.g. rajesh"
                  className={cn(
                    'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors',
                    isDark
                      ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                      : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                  )}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-400 mb-1">Email</label>
                <input
                  type="email"
                  name="Email"
                  required
                  placeholder="e.g. rajesh@retailai.com"
                  className={cn(
                    'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors',
                    isDark
                      ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                      : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                  )}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-400 mb-1">Password</label>
                <input
                  type="text"
                  name="Password"
                  required
                  placeholder="Plain-text password"
                  className={cn(
                    'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors',
                    isDark
                      ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                      : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                  )}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-400 mb-1">Role</label>
                {currentUser?.Role === 'Admin' ? (
                  <select
                    name="Role"
                    required
                    className={cn(
                      'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors cursor-pointer',
                      isDark
                        ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                        : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                    )}
                  >
                    <option value="Manager">Manager</option>
                    <option value="Employee">Employee</option>
                  </select>
                ) : (
                  <input
                    type="text"
                    name="Role"
                    value="Employee"
                    readOnly
                    className={cn(
                      'w-full px-3 py-2 rounded-xl text-sm outline-none border opacity-60 bg-zinc-800 border-zinc-700 text-zinc-400'
                    )}
                  />
                )}
              </div>

              <div className="flex gap-3 justify-end pt-4">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className={cn(
                    'px-4 py-2 rounded-xl text-sm font-medium transition-colors border',
                    isDark
                      ? 'border-zinc-800 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
                      : 'border-zinc-200 text-zinc-500 hover:bg-zinc-50'
                  )}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl text-sm font-medium text-white gradient-brand hover:opacity-90 transition-opacity"
                >
                  Save Staff Member
                </button>
              </div>
            </form>
          </motion.div>
        </motion.div>
      )}
    </motion.div>
  );
}
