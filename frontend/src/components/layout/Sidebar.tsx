/**
 * Aceternity UI Sidebar — Retail AI Frontend Layout
 * ===================================================
 * Integrated Aceternity UI Sidebar component with expand/collapse animations,
 * active route highlighting, user profile menu, and role-based access popups.
 */

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { LogOut, Lock, Sparkles } from "lucide-react";
import { NAV_ITEMS, APP_NAME } from "../../constants";
import { useAuth } from "../../contexts/AuthContext";
import { getInitials } from "../../utils";
import { Sidebar, SidebarBody, SidebarLink, useSidebar } from "../ui/sidebar";

export default function AppSidebar() {
  const [open, setOpen] = useState(false);
  const [isRestrictedModalOpen, setIsRestrictedModalOpen] = useState(false);
  const { user, logout } = useAuth();

  return (
    <>
      <Sidebar open={open} setOpen={setOpen}>
        <SidebarBody className="justify-between gap-6">
          {/* ─── Top Section: Logo & Nav Links ─────────────────── */}
          <div className="flex flex-1 flex-col overflow-x-hidden overflow-y-auto no-scrollbar">
            <Logo />
            <div className="mt-6 flex flex-col gap-1">
              {NAV_ITEMS.map((item) => {
                let label = item.label as string;
                if (item.path === "/admin") {
                  if (user?.Role === "Manager") {
                    label = "Manager Section";
                  } else if (user?.Role === "Employee") {
                    label = "Employee Section";
                  } else {
                    label = "Admin Section";
                  }
                }

                const isModelManagement = item.path === "/model-management";
                const isEmployee = user?.Role === "Employee";

                const handleClick = (e: React.MouseEvent) => {
                  if (isModelManagement && isEmployee) {
                    e.preventDefault();
                    setIsRestrictedModalOpen(true);
                    return;
                  }
                };

                return (
                  <SidebarLink
                    key={item.path}
                    link={{
                      label: label,
                      href: isModelManagement && isEmployee ? "#" : item.path,
                      icon: (
                        <item.icon className="h-5 w-5 shrink-0 text-zinc-400 group-hover/sidebar:text-indigo-400 transition-colors" />
                      ),
                      onClick: handleClick,
                    }}
                  />
                );
              })}
            </div>
          </div>

          {/* ─── Bottom Section: User Profile & Logout ────────── */}
          {user && <UserFooter user={user} logout={logout} />}
        </SidebarBody>
      </Sidebar>

      {/* ─── Role Restricted Modal ────────────────────────────── */}
      <AnimatePresence>
        {isRestrictedModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsRestrictedModalOpen(false)}
              className="absolute inset-0 bg-black/70 backdrop-blur-sm"
            />
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              transition={{ type: "spring", duration: 0.3 }}
              className="relative w-full max-w-md p-6 overflow-hidden text-left align-middle transition-all transform bg-zinc-900 border border-zinc-800 shadow-2xl rounded-3xl z-50"
            >
              <div className="flex flex-col items-center text-center space-y-4">
                <div className="w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center text-red-500">
                  <Lock className="w-6 h-6" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-lg font-bold text-zinc-100">
                    Access Restricted
                  </h3>
                  <p className="text-sm text-zinc-400">
                    AI Model Management is available only to Administrators and Store Managers.
                  </p>
                </div>
                <div className="w-full p-3 rounded-xl bg-zinc-800/40 border border-zinc-800/85 text-xs text-zinc-400 space-y-1">
                  <div>
                    Your current role:{" "}
                    <span className="font-semibold text-zinc-200">
                      {user?.Role || "Employee"}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => setIsRestrictedModalOpen(false)}
                  className="w-full py-2.5 rounded-xl text-sm font-semibold text-zinc-200 bg-zinc-800 hover:bg-zinc-700 active:bg-zinc-800 border border-zinc-700 transition-colors cursor-pointer"
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

export const Logo = () => {
  const { open } = useSidebar();
  return (
    <a
      href="#"
      className="relative z-20 flex items-center space-x-3 py-2 px-1 text-sm font-normal text-black dark:text-white"
    >
      <div className="h-9 w-9 shrink-0 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
        <Sparkles className="h-5 w-5 text-white" />
      </div>
      <motion.div
        animate={{
          display: open ? "block" : "none",
          opacity: open ? 1 : 0,
        }}
        transition={{ duration: 0.15 }}
        className="font-bold whitespace-pre text-white overflow-hidden text-ellipsis"
      >
        <span className="text-lg bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
          {APP_NAME}
        </span>
        <p className="text-[10px] text-zinc-400 font-normal -mt-1">
          Intelligence Suite
        </p>
      </motion.div>
    </a>
  );
};

export const UserFooter = ({ user, logout }: { user: any; logout: () => void }) => {
  const { open } = useSidebar();
  return (
    <div className="pt-4 border-t border-zinc-800/80">
      <div className="flex items-center gap-3 px-1 py-2">
        <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white text-xs font-bold shrink-0 shadow-md">
          {getInitials(user.FullName || user.Username)}
        </div>
        <motion.div
          animate={{
            display: open ? "block" : "none",
            opacity: open ? 1 : 0,
          }}
          transition={{ duration: 0.15 }}
          className="flex-1 min-w-0 overflow-hidden"
        >
          <p className="text-sm font-semibold text-zinc-200 truncate">
            {user.FullName || user.Username}
          </p>
          <p className="text-xs text-indigo-400 truncate font-medium">
            {user.Role}
          </p>
        </motion.div>
        <motion.div
          animate={{
            display: open ? "block" : "none",
            opacity: open ? 1 : 0,
          }}
        >
          <button
            onClick={logout}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-red-400 hover:bg-red-500/10 transition-colors cursor-pointer"
            title="Logout"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </motion.div>
      </div>
    </div>
  );
};
