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
} from 'lucide-react';
import { Card } from '../components/ui/card';
import { useStore } from '../store/useStore';
import { DeviceTypesManagement } from '../components/catalog/DeviceTypesManagement';
import { BrandsManagement } from '../components/catalog/BrandsManagement';
import { ModelsManagement } from '../components/catalog/ModelsManagement';
import type { DeviceType } from '../types';
import { cn } from '../lib/utils';

type TabType = 'device-types' | 'types' | 'brands' | 'models' | 'app';

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

// Application Settings Tab Component
const AppSettingsTab: React.FC = () => {
  const { preferences, setPreferences } = useStore();

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
    </motion.div>
  );
};
