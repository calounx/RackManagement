import React from 'react';
import { motion } from 'framer-motion';
import { useLocation } from 'react-router-dom';
import { useStore } from '../../store/useStore';
import { Button } from '../ui/button';

const pageTitles: Record<string, { title: string; subtitle: string }> = {
  '/': { title: 'Dashboard', subtitle: 'System overview and monitoring' },
  '/racks': { title: 'Rack Management', subtitle: 'Manage your server racks' },
  '/devices': { title: 'Device Library', subtitle: 'Hardware inventory and specifications' },
  '/connections': { title: 'Cable Management', subtitle: 'Network and power connections' },
  '/thermal': { title: 'Thermal Analysis', subtitle: 'Temperature monitoring and airflow' },
  '/settings': { title: 'Settings', subtitle: 'Application preferences' },
};

export const Header: React.FC = () => {
  const location = useLocation();
  const refreshAll = useStore((state) => state.refreshAll);
  const loading = useStore((state) => state.loading);

  const currentPage = pageTitles[location.pathname] || {
    title: 'HomeRack',
    subtitle: 'Precision rack management',
  };

  return (
    <header className="h-16 border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-40">
      <div className="h-full px-6 flex items-center justify-between">
        {/* Breadcrumb / Title */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          <h1 className="text-xl font-semibold text-foreground">
            {currentPage.title}
          </h1>
          <p className="text-xs text-muted-foreground font-mono">
            {currentPage.subtitle}
          </p>
        </motion.div>

        {/* Actions */}
        <div className="flex items-center gap-3">
          {/* Search */}
          <div className="relative">
            <input
              type="text"
              placeholder="Search..."
              className="w-64 pl-10 pr-4 py-2 rounded-md bg-input border border-border text-sm focus:outline-none focus:ring-2 focus:ring-electric-blue/50 focus:border-electric transition-all"
            />
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>

          {/* Refresh Button */}
          <Button
            variant="ghost"
            size="sm"
            onClick={refreshAll}
            loading={loading}
            leftIcon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
            }
          >
            Refresh
          </Button>

          {/* Notifications */}
          <button className="relative p-2 text-muted-foreground hover:text-foreground transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
              />
            </svg>
            <span className="absolute top-1 right-1 w-2 h-2 bg-amber rounded-full animate-pulse-glow" />
          </button>

          {/* User Menu */}
          <div className="flex items-center gap-3 pl-3 border-l border-border">
            <div className="text-right">
              <p className="text-sm font-medium text-foreground">Admin</p>
              <p className="text-xs text-muted-foreground font-mono">admin@homerack.local</p>
            </div>
            <div className="w-9 h-9 rounded-lg bg-electric/10 border border-electric/30 flex items-center justify-center glow-electric">
              <span className="text-electric font-semibold text-sm">A</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
