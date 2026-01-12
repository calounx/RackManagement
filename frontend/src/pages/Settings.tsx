import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Settings as SettingsIcon,
  Database,
  Package,
  Tag,
  Sliders,
  AlertCircle,
  Layers,
  Bug,
  Copy,
  Trash2,
  ChevronDown,
  ChevronUp,
  Monitor,
  Server,
  Activity,
  AlertTriangle,
  CheckCircle,
  Info,
  Cloud,
  Download,
} from 'lucide-react';
import { Card } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Collapsible } from '../components/ui/collapsible';
import { useStore } from '../store/useStore';
import { useCatalogStore } from '../store/useCatalogStore';
import { useDebugStore } from '../lib/debug-store';
import { DeviceTypesManagement } from '../components/catalog/DeviceTypesManagement';
import { BrandsManagement } from '../components/catalog/BrandsManagement';
import { ModelsManagement } from '../components/catalog/ModelsManagement';
import { NetBoxImportDialog } from '../components/dcim/NetBoxImportDialog';
import type { DeviceType, NetBoxHealthResponse } from '../types';
import { cn } from '../lib/utils';
import { api } from '../lib/api';

type TabType = 'device-types' | 'types' | 'brands' | 'models' | 'dcim' | 'app';

const DEVICE_TYPE_ICONS: Record<DeviceType, string> = {
  server: '🖥️',
  switch: '🔀',
  router: '📡',
  firewall: '🛡️',
  storage: '💾',
  pdu: '⚡',
  ups: '🔋',
  patch_panel: '🔌',
  other: '📦',
};

const DEVICE_TYPE_COLORS: Record<DeviceType, string> = {
  server: 'text-blue-400',
  switch: 'text-green-400',
  router: 'text-purple-400',
  firewall: 'text-red-400',
  storage: 'text-yellow-400',
  pdu: 'text-orange-400',
  ups: 'text-cyan-400',
  patch_panel: 'text-pink-400',
  other: 'text-gray-400',
};

export const Settings: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('device-types');
  const { deviceSpecs, fetchDeviceSpecs } = useStore();

  useEffect(() => {
    fetchDeviceSpecs();
  }, [fetchDeviceSpecs]);

  // Device type statistics (for legacy types tab only)
  const deviceTypeStats = useMemo(() => {
    const stats = new Map<DeviceType, { brands: Set<string>; models: number }>();

    deviceSpecs.forEach(spec => {
      const type = spec.device_type as DeviceType;
      if (!stats.has(type)) {
        stats.set(type, { brands: new Set(), models: 0 });
      }
      stats.get(type)!.brands.add(spec.manufacturer);
      stats.get(type)!.models++;
    });

    return stats;
  }, [deviceSpecs]);

  const tabs = [
    { id: 'device-types' as TabType, label: 'Device Types', icon: Layers },
    { id: 'types' as TabType, label: 'Legacy Types', icon: Database },
    { id: 'brands' as TabType, label: 'Brands', icon: Tag },
    { id: 'models' as TabType, label: 'Models', icon: Package },
    { id: 'dcim' as TabType, label: 'DCIM Integration', icon: Cloud },
    { id: 'app' as TabType, label: 'Application', icon: Sliders },
  ];

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Header */}
      <div className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-electric/10 border border-electric/30 flex items-center justify-center">
              <SettingsIcon className="w-5 h-5 text-electric" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-foreground">Settings</h1>
              <p className="text-sm text-muted-foreground">Manage device catalog and application preferences</p>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-2">
            {tabs.map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    'relative px-4 py-2.5 rounded-lg font-medium text-sm transition-all',
                    'flex items-center gap-2',
                    activeTab === tab.id
                      ? 'text-electric bg-electric/10 border border-electric/30'
                      : 'text-muted-foreground hover:text-foreground hover:bg-secondary/50'
                  )}
                >
                  {activeTab === tab.id && (
                    <motion.div
                      layoutId="activeTab"
                      className="absolute inset-0 bg-electric/5 rounded-lg"
                      transition={{ type: 'spring', duration: 0.4 }}
                    />
                  )}
                  <Icon className="w-4 h-4 relative z-10" />
                  <span className="relative z-10">{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <AnimatePresence mode="wait">
          {activeTab === 'device-types' && (
            <motion.div
              key="device-types"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <DeviceTypesManagement />
            </motion.div>
          )}
          {activeTab === 'types' && (
            <DeviceTypesTab key="types" deviceTypeStats={deviceTypeStats} />
          )}
          {activeTab === 'brands' && (
            <motion.div
              key="brands"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <BrandsManagement />
            </motion.div>
          )}
          {activeTab === 'models' && (
            <motion.div
              key="models"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <ModelsManagement />
            </motion.div>
          )}
          {activeTab === 'dcim' && <DCIMTab key="dcim" />}
          {activeTab === 'app' && <AppSettingsTab key="app" />}
        </AnimatePresence>
      </div>
    </div>
  );
};

// Device Types Tab Component
const DeviceTypesTab: React.FC<{
  deviceTypeStats: Map<DeviceType, { brands: Set<string>; models: number }>;
}> = ({ deviceTypeStats }) => {
  const deviceTypes: DeviceType[] = [
    'server',
    'switch',
    'router',
    'firewall',
    'storage',
    'pdu',
    'ups',
    'patch_panel',
    'other',
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="space-y-4"
    >
      <div className="flex items-center justify-between mb-6">
        <p className="text-sm text-muted-foreground">
          Manage device categories and their properties
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {deviceTypes.map(type => {
          const stats = deviceTypeStats.get(type) || { brands: new Set(), models: 0 };
          return (
            <Card key={type} className="p-6 hover:border-electric/30 transition-colors">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="text-3xl">{DEVICE_TYPE_ICONS[type]}</div>
                  <div>
                    <h3 className={cn('font-semibold capitalize', DEVICE_TYPE_COLORS[type])}>
                      {type.replace('_', ' ')}
                    </h3>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {type === 'pdu' ? 'Power Distribution' : type === 'ups' ? 'Power Backup' : 'Network Device'}
                    </p>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-secondary/50 rounded-lg">
                  <div className="text-xs text-muted-foreground mb-1">Brands</div>
                  <div className="text-lg font-mono font-bold text-electric">
                    {stats.brands.size}
                  </div>
                </div>
                <div className="p-3 bg-secondary/50 rounded-lg">
                  <div className="text-xs text-muted-foreground mb-1">Models</div>
                  <div className="text-lg font-mono font-bold text-electric">
                    {stats.models}
                  </div>
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      <div className="mt-6 p-4 bg-muted/30 border border-border rounded-lg flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-muted-foreground mt-0.5" />
        <div>
          <h4 className="font-medium text-foreground mb-1">Device Type Management</h4>
          <p className="text-sm text-muted-foreground">
            Device types are predefined categories. To organize your inventory, use the Brands and Models tabs
            to manage specific manufacturers and their product lines.
          </p>
        </div>
      </div>
    </motion.div>
  );
};

// DCIM Integration Tab Component
const DCIMTab: React.FC = () => {
  const [netboxHealth, setNetboxHealth] = useState<NetBoxHealthResponse | null>(null);
  const [checking, setChecking] = useState(false);
  const [showImportDialog, setShowImportDialog] = useState(false);
  const addToast = useStore((state) => state.addToast);

  // Check health on mount
  useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    setChecking(true);
    try {
      const health = await api.checkNetBoxHealth();
      setNetboxHealth(health);

      if (health.connected) {
        addToast({
          title: 'NetBox Connection Successful',
          description: `Connected to ${health.url}`,
          type: 'success',
        });
      } else {
        addToast({
          title: 'NetBox Connection Failed',
          description: health.message,
          type: 'warning',
        });
      }
    } catch (error: any) {
      const message = error.response?.data?.detail || error.message || 'Failed to check NetBox connection';
      addToast({
        title: 'NetBox Connection Error',
        description: message,
        type: 'error',
      });
      setNetboxHealth({
        connected: false,
        url: null,
        message: message,
      });
    } finally {
      setChecking(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground mb-2">DCIM Integration</h2>
          <p className="text-sm text-muted-foreground">
            Connect to NetBox for device specification and rack layout synchronization
          </p>
        </div>
      </div>

      {/* NetBox Connection Status Card */}
      <Card className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-electric/10 border border-electric/30 flex items-center justify-center">
            <Cloud className="w-5 h-5 text-electric" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-foreground">NetBox Connection</h3>
            <p className="text-xs text-muted-foreground">
              View connection status and test connectivity
            </p>
          </div>
        </div>

        <div className="space-y-4">
          {/* Connection Status */}
          <div className="flex items-center justify-between p-4 bg-secondary/30 rounded-lg">
            <div className="flex items-center gap-3">
              <div>
                <h4 className="font-medium text-foreground mb-1">Connection Status</h4>
                <p className="text-xs text-muted-foreground">
                  {netboxHealth?.connected
                    ? 'Successfully connected to NetBox instance'
                    : 'Not connected to NetBox'
                  }
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {netboxHealth && (
                <Badge
                  variant={netboxHealth.connected ? 'success' : 'error'}
                  pulse={netboxHealth.connected}
                >
                  {netboxHealth.connected ? 'Connected' : 'Disconnected'}
                </Badge>
              )}
            </div>
          </div>

          {/* NetBox URL */}
          {netboxHealth?.url && (
            <div className="flex items-center justify-between p-4 bg-secondary/30 rounded-lg">
              <div>
                <h4 className="font-medium text-foreground mb-1">NetBox URL</h4>
                <p className="text-xs text-muted-foreground font-mono">
                  {netboxHealth.url}
                </p>
              </div>
            </div>
          )}

          {/* Status Message */}
          {netboxHealth && (
            <div className={cn(
              'p-4 rounded-lg border',
              netboxHealth.connected
                ? 'bg-green-500/10 border-green-500/30'
                : 'bg-red-500/10 border-red-500/30'
            )}>
              <div className="flex items-start gap-3">
                {netboxHealth.connected ? (
                  <CheckCircle className="w-5 h-5 text-green-400 mt-0.5" />
                ) : (
                  <AlertTriangle className="w-5 h-5 text-red-400 mt-0.5" />
                )}
                <div>
                  <h4 className="font-medium text-foreground mb-1">
                    {netboxHealth.connected ? 'Connection Active' : 'Connection Issue'}
                  </h4>
                  <p className="text-sm text-muted-foreground">
                    {netboxHealth.message}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Test Connection Button */}
          <Button
            onClick={checkHealth}
            disabled={checking}
            className="w-full"
          >
            {checking ? (
              <>
                <Activity className="w-4 h-4 mr-2 animate-spin" />
                Testing Connection...
              </>
            ) : (
              <>
                <Activity className="w-4 h-4 mr-2" />
                Test Connection
              </>
            )}
          </Button>
        </div>
      </Card>

      {/* Import Rack Card */}
      <Card className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-electric/10 border border-electric/30 flex items-center justify-center">
            <Download className="w-5 h-5 text-electric" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-foreground">Import from NetBox</h3>
            <p className="text-xs text-muted-foreground">
              Pull rack layouts and device specifications
            </p>
          </div>
        </div>

        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Import rack configurations, device positions, and specifications directly from your NetBox instance.
            This will create or update racks in HomeRack with data from NetBox.
          </p>

          <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
            <div className="flex items-start gap-3">
              <Info className="w-5 h-5 text-blue-400 mt-0.5" />
              <div>
                <h4 className="font-medium text-foreground mb-1">Import Options</h4>
                <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
                  <li>Import rack with all specifications</li>
                  <li>Optionally import devices positioned in the rack</li>
                  <li>Choose to overwrite existing racks or skip</li>
                  <li>Device specifications will be fetched automatically</li>
                </ul>
              </div>
            </div>
          </div>

          <Button
            onClick={() => setShowImportDialog(true)}
            disabled={!netboxHealth?.connected}
            className="w-full"
          >
            <Download className="w-4 h-4 mr-2" />
            Import Rack from NetBox
          </Button>

          {!netboxHealth?.connected && (
            <p className="text-xs text-center text-muted-foreground">
              NetBox connection required to import racks
            </p>
          )}
        </div>
      </Card>

      {/* Configuration Info Card */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-foreground mb-4">Configuration</h3>
        <div className="space-y-4">
          <div className="p-4 bg-secondary/30 rounded-lg">
            <h4 className="font-medium text-foreground mb-2">Environment Variables</h4>
            <p className="text-sm text-muted-foreground mb-3">
              NetBox integration is configured via environment variables on the backend.
            </p>
            <div className="space-y-2 text-xs font-mono">
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground">NETBOX_ENABLED:</span>
                <code className="px-2 py-1 bg-black/30 rounded text-foreground">true/false</code>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground">NETBOX_URL:</span>
                <code className="px-2 py-1 bg-black/30 rounded text-foreground">https://netbox.example.com</code>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground">NETBOX_TOKEN:</span>
                <code className="px-2 py-1 bg-black/30 rounded text-foreground">Token nbt_***</code>
              </div>
            </div>
          </div>

          <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-amber-400 mt-0.5" />
              <div>
                <h4 className="font-medium text-foreground mb-1">Read-Only Integration</h4>
                <p className="text-sm text-muted-foreground">
                  HomeRack imports data from NetBox but does not write back changes.
                  NetBox remains the authoritative source for infrastructure data.
                </p>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* NetBox Import Dialog */}
      <NetBoxImportDialog
        open={showImportDialog}
        onOpenChange={setShowImportDialog}
      />
    </motion.div>
  );
};

// Application Settings Tab Component
const AppSettingsTab: React.FC = () => {
  const { preferences, setPreferences } = useStore();
  const { enabled: debugEnabled, setEnabled: setDebugEnabled } = useDebugStore();

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="space-y-6"
    >
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-foreground mb-4">Display Preferences</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-secondary/30 rounded-lg">
            <div>
              <h4 className="font-medium text-foreground">Temperature Unit</h4>
              <p className="text-sm text-muted-foreground">Choose your preferred temperature scale</p>
            </div>
            <select
              value={preferences.temperatureUnit}
              onChange={e => setPreferences({ temperatureUnit: e.target.value as 'celsius' | 'fahrenheit' })}
              className="px-4 py-2 bg-card border border-border rounded-lg text-foreground"
            >
              <option value="celsius">Celsius (°C)</option>
              <option value="fahrenheit">Fahrenheit (°F)</option>
            </select>
          </div>

          <div className="flex items-center justify-between p-4 bg-secondary/30 rounded-lg">
            <div>
              <h4 className="font-medium text-foreground">Power Unit</h4>
              <p className="text-sm text-muted-foreground">Choose your preferred power measurement</p>
            </div>
            <select
              value={preferences.powerUnit}
              onChange={e => setPreferences({ powerUnit: e.target.value as 'watts' | 'kilowatts' })}
              className="px-4 py-2 bg-card border border-border rounded-lg text-foreground"
            >
              <option value="watts">Watts (W)</option>
              <option value="kilowatts">Kilowatts (kW)</option>
            </select>
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <h3 className="text-lg font-semibold text-foreground mb-4">Application Info</h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between py-2 border-b border-border">
            <span className="text-muted-foreground">Version</span>
            <span className="font-mono text-foreground">1.0.1</span>
          </div>
          <div className="flex justify-between py-2 border-b border-border">
            <span className="text-muted-foreground">Environment</span>
            <span className="font-mono text-foreground">{import.meta.env.MODE}</span>
          </div>
          <div className="flex justify-between py-2">
            <span className="text-muted-foreground">API Endpoint</span>
            <span className="font-mono text-xs text-foreground">
              {import.meta.env.VITE_API_URL || 'http://localhost:8000'}
            </span>
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
          <Bug className="w-5 h-5 text-electric" />
          Debug Mode
        </h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-secondary/30 rounded-lg">
            <div>
              <h4 className="font-medium text-foreground">Enable Debug Mode</h4>
              <p className="text-sm text-muted-foreground">
                Show detailed API logs, store state, and performance metrics
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={debugEnabled}
                onChange={(e) => setDebugEnabled(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-secondary peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-electric/50 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-electric"></div>
            </label>
          </div>

          {debugEnabled && (
            <div className="flex items-center gap-2 p-3 bg-electric/10 border border-electric/30 rounded-lg">
              <CheckCircle className="w-4 h-4 text-electric" />
              <span className="text-sm text-foreground">
                Debug mode is enabled. Logging API requests and responses.
              </span>
            </div>
          )}
        </div>
      </Card>

      {debugEnabled && <DebugConsole />}
    </motion.div>
  );
};

// Debug Console Component
const DebugConsole: React.FC = () => {
  const { logs, clearLogs } = useDebugStore();
  const mainStore = useStore();
  const catalogStore = useCatalogStore();
  const [expandedLog, setExpandedLog] = useState<string | null>(null);
  const [copySuccess, setCopySuccess] = useState<string | null>(null);

  // Browser info
  const browserInfo = useMemo(() => ({
    userAgent: navigator.userAgent,
    viewport: `${window.innerWidth} x ${window.innerHeight}`,
    devicePixelRatio: window.devicePixelRatio,
    language: navigator.language,
    platform: navigator.platform,
    cookieEnabled: navigator.cookieEnabled,
    onLine: navigator.onLine,
  }), []);

  // Environment info
  const envInfo = useMemo(() => ({
    mode: import.meta.env.MODE,
    apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    dev: import.meta.env.DEV,
    prod: import.meta.env.PROD,
  }), []);

  // API Stats
  const apiStats = useMemo(() => {
    const requests = logs.filter(l => l.type === 'request').length;
    const responses = logs.filter(l => l.type === 'response').length;
    const errors = logs.filter(l => l.type === 'error').length;
    const avgResponseTime = logs
      .filter(l => l.type === 'response' && l.duration)
      .reduce((acc, l) => acc + (l.duration || 0), 0) / (responses || 1);

    return { requests, responses, errors, avgResponseTime };
  }, [logs]);

  // Error logs (last 50)
  const errorLogs = useMemo(() => {
    return logs.filter(l => l.type === 'error').slice(0, 50);
  }, [logs]);

  const copyToClipboard = async (text: string, id: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopySuccess(id);
      setTimeout(() => setCopySuccess(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const formatDate = (date: Date) => {
    return new Date(date).toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 3,
    });
  };

  const getLogTypeIcon = (type: string) => {
    switch (type) {
      case 'request': return <Activity className="w-4 h-4 text-blue-400" />;
      case 'response': return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'error': return <AlertTriangle className="w-4 h-4 text-red-400" />;
      default: return <Info className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status?: number) => {
    if (!status) return 'text-gray-400';
    if (status >= 200 && status < 300) return 'text-green-400';
    if (status >= 400 && status < 500) return 'text-orange-400';
    if (status >= 500) return 'text-red-400';
    return 'text-gray-400';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
    >
      <Card className="p-6 bg-slate-900/50 border-electric/30">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-electric/10 border border-electric/30 flex items-center justify-center">
              <Bug className="w-5 h-5 text-electric" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-foreground">Debug Console</h3>
              <p className="text-xs text-muted-foreground">
                System diagnostics and API monitoring
              </p>
            </div>
          </div>
          <Badge variant="info" pulse>
            LIVE
          </Badge>
        </div>

        <div className="space-y-4">
          {/* System Info */}
          <Collapsible title="System Information" defaultOpen>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm">
                  <Monitor className="w-4 h-4 text-electric" />
                  <span className="font-medium text-foreground">Environment</span>
                </div>
                <div className="pl-6 space-y-1 text-xs font-mono">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Mode:</span>
                    <span className="text-foreground">{envInfo.mode}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Dev:</span>
                    <span className="text-foreground">{envInfo.dev.toString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">API URL:</span>
                    <span className="text-foreground truncate ml-2">{envInfo.apiUrl}</span>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm">
                  <Server className="w-4 h-4 text-electric" />
                  <span className="font-medium text-foreground">Application</span>
                </div>
                <div className="pl-6 space-y-1 text-xs font-mono">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Version:</span>
                    <span className="text-foreground">1.0.1</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Viewport:</span>
                    <span className="text-foreground">{browserInfo.viewport}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Online:</span>
                    <span className={browserInfo.onLine ? 'text-green-400' : 'text-red-400'}>
                      {browserInfo.onLine.toString()}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </Collapsible>

          {/* API Performance */}
          <Collapsible title="API Performance" defaultOpen>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 bg-secondary/30 rounded-lg">
                <div className="text-xs text-muted-foreground mb-1">Total Requests</div>
                <div className="text-2xl font-mono font-bold text-electric">
                  {apiStats.requests}
                </div>
              </div>
              <div className="p-4 bg-secondary/30 rounded-lg">
                <div className="text-xs text-muted-foreground mb-1">Responses</div>
                <div className="text-2xl font-mono font-bold text-green-400">
                  {apiStats.responses}
                </div>
              </div>
              <div className="p-4 bg-secondary/30 rounded-lg">
                <div className="text-xs text-muted-foreground mb-1">Errors</div>
                <div className="text-2xl font-mono font-bold text-red-400">
                  {apiStats.errors}
                </div>
              </div>
              <div className="p-4 bg-secondary/30 rounded-lg">
                <div className="text-xs text-muted-foreground mb-1">Avg Response</div>
                <div className="text-2xl font-mono font-bold text-amber">
                  {Math.round(apiStats.avgResponseTime)}
                  <span className="text-xs ml-1">ms</span>
                </div>
              </div>
            </div>
          </Collapsible>

          {/* Store State Inspector */}
          <Collapsible title="Store State Inspector">
            <div className="space-y-4">
              <div className="relative">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-foreground">Main Store</span>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => copyToClipboard(JSON.stringify(mainStore, null, 2), 'main-store')}
                  >
                    <Copy className="w-4 h-4 mr-2" />
                    {copySuccess === 'main-store' ? 'Copied!' : 'Copy'}
                  </Button>
                </div>
                <pre className="p-4 bg-black/50 rounded-lg overflow-x-auto text-xs font-mono text-foreground max-h-64 overflow-y-auto">
                  {JSON.stringify({
                    racks: mainStore.racks.length,
                    devices: mainStore.devices.length,
                    deviceSpecs: mainStore.deviceSpecs.length,
                    connections: mainStore.connections.length,
                    selectedRackId: mainStore.selectedRackId,
                    selectedDeviceId: mainStore.selectedDeviceId,
                    loading: mainStore.loading,
                    error: mainStore.error,
                    preferences: mainStore.preferences,
                  }, null, 2)}
                </pre>
              </div>

              <div className="relative">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-foreground">Catalog Store</span>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => copyToClipboard(JSON.stringify(catalogStore, null, 2), 'catalog-store')}
                  >
                    <Copy className="w-4 h-4 mr-2" />
                    {copySuccess === 'catalog-store' ? 'Copied!' : 'Copy'}
                  </Button>
                </div>
                <pre className="p-4 bg-black/50 rounded-lg overflow-x-auto text-xs font-mono text-foreground max-h-64 overflow-y-auto">
                  {JSON.stringify({
                    deviceTypes: catalogStore.deviceTypes.length,
                    brands: catalogStore.brands.length,
                    models: catalogStore.models.length,
                    dcimConnections: catalogStore.dcimConnections.length,
                    loading: {
                      deviceTypes: catalogStore.deviceTypesLoading,
                      brands: catalogStore.brandsLoading,
                      models: catalogStore.modelsLoading,
                    },
                  }, null, 2)}
                </pre>
              </div>
            </div>
          </Collapsible>

          {/* Error Log Viewer */}
          <Collapsible title={`Error Logs (${errorLogs.length})`}>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">
                  Showing last {Math.min(50, errorLogs.length)} errors
                </span>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => copyToClipboard(JSON.stringify(errorLogs, null, 2), 'error-logs')}
                  >
                    <Copy className="w-4 h-4 mr-2" />
                    {copySuccess === 'error-logs' ? 'Copied!' : 'Export'}
                  </Button>
                  <Button
                    size="sm"
                    variant="danger"
                    onClick={clearLogs}
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Clear
                  </Button>
                </div>
              </div>

              {errorLogs.length === 0 ? (
                <div className="p-8 text-center">
                  <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground">No errors logged</p>
                </div>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {errorLogs.map((log) => (
                    <div
                      key={log.id}
                      className="p-3 bg-black/50 rounded-lg border border-red-500/30 hover:border-red-500/50 transition-colors"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          {getLogTypeIcon(log.type)}
                          <span className="text-xs font-mono text-muted-foreground">
                            {formatDate(log.timestamp)}
                          </span>
                          {log.method && (
                            <Badge variant="error" className="text-xs">
                              {log.method}
                            </Badge>
                          )}
                          {log.status && (
                            <span className={cn('text-xs font-mono font-bold', getStatusColor(log.status))}>
                              {log.status}
                            </span>
                          )}
                        </div>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setExpandedLog(expandedLog === log.id ? null : log.id)}
                        >
                          {expandedLog === log.id ? (
                            <ChevronUp className="w-4 h-4" />
                          ) : (
                            <ChevronDown className="w-4 h-4" />
                          )}
                        </Button>
                      </div>
                      <div className="text-sm font-mono text-red-400 mb-1">
                        {log.error}
                      </div>
                      {log.url && (
                        <div className="text-xs font-mono text-muted-foreground truncate">
                          {log.url}
                        </div>
                      )}
                      {expandedLog === log.id && log.data && (
                        <pre className="mt-2 p-2 bg-black/30 rounded text-xs font-mono text-foreground overflow-x-auto">
                          {JSON.stringify(log.data, null, 2)}
                        </pre>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </Collapsible>

          {/* Recent API Activity */}
          <Collapsible title={`Recent API Activity (${Math.min(20, logs.length)})`}>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {logs.slice(0, 20).map((log) => (
                <div
                  key={log.id}
                  className={cn(
                    'p-3 rounded-lg border transition-colors',
                    log.type === 'error' ? 'bg-red-500/10 border-red-500/30' :
                    log.type === 'response' ? 'bg-green-500/10 border-green-500/30' :
                    'bg-blue-500/10 border-blue-500/30'
                  )}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      {getLogTypeIcon(log.type)}
                      <span className="text-xs font-mono text-muted-foreground">
                        {formatDate(log.timestamp)}
                      </span>
                      {log.method && (
                        <Badge variant={log.type === 'error' ? 'error' : 'info'} className="text-xs">
                          {log.method}
                        </Badge>
                      )}
                      {log.status && (
                        <span className={cn('text-xs font-mono font-bold', getStatusColor(log.status))}>
                          {log.status}
                        </span>
                      )}
                      {log.duration !== undefined && (
                        <span className="text-xs font-mono text-amber">
                          {log.duration}ms
                        </span>
                      )}
                    </div>
                  </div>
                  {log.url && (
                    <div className="text-xs font-mono text-muted-foreground truncate mt-1 ml-6">
                      {log.url}
                    </div>
                  )}
                </div>
              ))}
              {logs.length === 0 && (
                <div className="p-8 text-center">
                  <Activity className="w-12 h-12 text-muted-foreground mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground">No API activity yet</p>
                </div>
              )}
            </div>
          </Collapsible>

          {/* Browser Info */}
          <Collapsible title="Browser Information">
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between py-2 border-b border-border">
                <span className="text-muted-foreground">User Agent:</span>
                <span className="text-foreground text-right ml-4 max-w-md truncate">
                  {browserInfo.userAgent}
                </span>
              </div>
              <div className="flex justify-between py-2 border-b border-border">
                <span className="text-muted-foreground">Viewport:</span>
                <span className="text-foreground">{browserInfo.viewport}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-border">
                <span className="text-muted-foreground">Device Pixel Ratio:</span>
                <span className="text-foreground">{browserInfo.devicePixelRatio}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-border">
                <span className="text-muted-foreground">Language:</span>
                <span className="text-foreground">{browserInfo.language}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-border">
                <span className="text-muted-foreground">Platform:</span>
                <span className="text-foreground">{browserInfo.platform}</span>
              </div>
              <div className="flex justify-between py-2">
                <span className="text-muted-foreground">Cookies Enabled:</span>
                <span className="text-foreground">{browserInfo.cookieEnabled.toString()}</span>
              </div>
            </div>
          </Collapsible>
        </div>
      </Card>
    </motion.div>
  );
};
