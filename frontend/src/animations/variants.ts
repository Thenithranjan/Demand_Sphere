/**
 * Framer Motion Animation Variants — Demand Sphere Frontend
 * ======================================================
 * Reusable animation presets for consistent micro-interactions.
 *
 * Strategy:
 * - Every page transition uses `pageTransition` for smooth route changes.
 * - Cards and list items use `staggerContainer` + `staggerItem` for sequential reveals.
 * - Individual elements use `fadeIn`, `slideUp`, `scaleIn` as needed.
 */

import type { Variants } from 'framer-motion';

/** Simple fade from transparent to opaque */
export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { duration: 0.5, ease: 'easeOut' },
  },
};

/** Slide up from below with fade */
export const slideUp: Variants = {
  hidden: { opacity: 0, y: 24 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] },
  },
};

/** Slide in from the left */
export const slideInLeft: Variants = {
  hidden: { opacity: 0, x: -24 },
  visible: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.4, ease: 'easeOut' },
  },
};

/** Scale up from 95% with fade */
export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { duration: 0.3, ease: 'easeOut' },
  },
};

/** Parent container that staggers its children's entry animations */
export const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.1,
    },
  },
};

/** Child item used inside a staggerContainer */
export const staggerItem: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] },
  },
};

/** Full-page transition for React Router route changes */
export const pageTransition: Variants = {
  initial: { opacity: 0, y: 12 },
  animate: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.35, ease: 'easeOut' },
  },
  exit: {
    opacity: 0,
    y: -8,
    transition: { duration: 0.2, ease: 'easeIn' },
  },
};

/** Sidebar link hover/tap animation */
export const sidebarLink = {
  rest: { scale: 1 },
  hover: { scale: 1.02, x: 4 },
  tap: { scale: 0.98 },
};

/** Chart container reveal */
export const chartReveal: Variants = {
  hidden: { opacity: 0, scale: 0.96 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94], delay: 0.2 },
  },
};
