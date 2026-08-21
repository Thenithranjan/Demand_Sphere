/**
 * Aceternity UI — Sidebar Primitive Component
 * ===========================================
 * Smooth animated expandable/collapsible sidebar component built with
 * Framer Motion and Tailwind CSS. Supports desktop hover/state expand
 * and mobile overlay drawers.
 */

import React, { useState, createContext, useContext } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Menu, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { NavLink, useLocation } from "react-router-dom";

interface Links {
  label: string;
  href: string;
  icon: React.JSX.Element | React.ReactNode;
  onClick?: (e: React.MouseEvent) => void;
  badge?: string;
  isRestricted?: boolean;
}

interface SidebarContextProps {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  animate: boolean;
}

const SidebarContext = createContext<SidebarContextProps | undefined>(
  undefined
);

export const useSidebar = () => {
  const context = useContext(SidebarContext);
  if (!context) {
    throw new Error("useSidebar must be used within a SidebarProvider");
  }
  return context;
};

export const SidebarProvider = ({
  children,
  open: openProp,
  setOpen: setOpenProp,
  animate = true,
}: {
  children: React.ReactNode;
  open?: boolean;
  setOpen?: React.Dispatch<React.SetStateAction<boolean>>;
  animate?: boolean;
}) => {
  const [openState, setOpenState] = useState(false);

  const open = openProp !== undefined ? openProp : openState;
  const setOpen = setOpenProp !== undefined ? setOpenProp : setOpenState;

  return (
    <SidebarContext.Provider value={{ open, setOpen, animate }}>
      {children}
    </SidebarContext.Provider>
  );
};

export const Sidebar = ({
  children,
  open,
  setOpen,
  animate = true,
}: {
  children: React.ReactNode;
  open?: boolean;
  setOpen?: React.Dispatch<React.SetStateAction<boolean>>;
  animate?: boolean;
}) => {
  return (
    <SidebarProvider open={open} setOpen={setOpen} animate={animate}>
      {children}
    </SidebarProvider>
  );
};

export const SidebarBody = (props: React.ComponentProps<typeof motion.div>) => {
  return (
    <>
      <DesktopSidebar {...props} />
      <MobileSidebar {...(props as React.ComponentProps<"div">)} />
    </>
  );
};

export const DesktopSidebar = ({
  className,
  children,
  ...props
}: React.ComponentProps<typeof motion.div>) => {
  const { open, setOpen, animate } = useSidebar();
  return (
    <motion.div
      className={cn(
        "h-screen px-4 py-4 hidden lg:flex lg:flex-col bg-zinc-900/90 dark:bg-zinc-900/90 border-r border-zinc-800 text-zinc-100 w-[260px] flex-shrink-0 relative z-30 backdrop-blur-xl shadow-2xl overflow-hidden",
        className
      )}
      animate={{
        width: animate ? (open ? "260px" : "76px") : "260px",
      }}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      transition={{
        type: "spring",
        stiffness: 300,
        damping: 30,
      }}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export const MobileSidebar = ({
  className,
  children,
  ...props
}: React.ComponentProps<"div">) => {
  const { open, setOpen } = useSidebar();
  return (
    <div
      className={cn(
        "h-14 px-4 py-3 flex flex-row lg:hidden items-center justify-between bg-zinc-900 border-b border-zinc-800 w-full z-40 relative",
        className
      )}
      {...props}
    >
      <div className="flex items-center justify-between w-full">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 flex items-center justify-center font-bold text-white text-xs">
            DS
          </div>
          <span className="font-bold text-white text-sm">Demand Sphere</span>
        </div>
        <button
          onClick={() => setOpen(!open)}
          className="p-2 rounded-xl bg-zinc-800 text-zinc-200 hover:text-white transition-colors cursor-pointer"
          aria-label="Toggle menu"
        >
          <Menu className="w-5 h-5" />
        </button>
      </div>

      <AnimatePresence>
        {open && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setOpen(false)}
              className="fixed inset-0 bg-black/70 backdrop-blur-md z-40"
            />
            <motion.div
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{
                type: "spring",
                stiffness: 300,
                damping: 30,
              }}
              className={cn(
                "fixed h-full w-[280px] left-0 top-0 bg-zinc-900 border-r border-zinc-800 p-6 z-50 flex flex-col justify-between overflow-y-auto no-scrollbar shadow-2xl",
                className
              )}
            >
              <div
                className="absolute right-5 top-5 p-2 rounded-xl bg-zinc-800/80 text-zinc-400 hover:text-white transition-colors cursor-pointer"
                onClick={() => setOpen(false)}
              >
                <X className="w-5 h-5" />
              </div>
              {children}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};

export const SidebarLink = ({
  link,
  className,
  ...props
}: {
  link: Links;
  className?: string;
}) => {
  const { open, animate } = useSidebar();
  const location = useLocation();

  const isHrefActive =
    link.href !== "#" &&
    link.href !== "" &&
    (location.pathname === link.href ||
      (link.href !== "/dashboard" && location.pathname.startsWith(link.href)));

  const linkContent = (
    <>
      <div className="shrink-0 flex items-center justify-center w-6 h-6">
        {link.icon}
      </div>

      <motion.span
        animate={{
          display: animate ? (open ? "inline-block" : "none") : "inline-block",
          opacity: animate ? (open ? 1 : 0) : 1,
        }}
        transition={{ duration: 0.15 }}
        className="text-sm font-medium whitespace-pre group-hover/sidebar:translate-x-1 transition duration-150 inline-block !p-0 !m-0 overflow-hidden text-ellipsis flex-1"
      >
        {link.label}
      </motion.span>

      {isHrefActive && (
        <motion.div
          layoutId="active-indicator"
          className="absolute left-0 w-1 h-6 bg-indigo-500 rounded-r-full"
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
        />
      )}
    </>
  );

  const containerClasses = cn(
    "relative flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group/sidebar cursor-pointer",
    isHrefActive
      ? "bg-indigo-500/15 text-indigo-400 font-semibold"
      : "text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/60",
    className
  );

  if (link.href === "#" || !link.href) {
    return (
      <button
        onClick={link.onClick}
        className={cn(containerClasses, "w-full text-left")}
        {...props}
      >
        {linkContent}
      </button>
    );
  }

  return (
    <NavLink
      to={link.href}
      onClick={link.onClick}
      className={containerClasses}
      {...props}
    >
      {linkContent}
    </NavLink>
  );
};
