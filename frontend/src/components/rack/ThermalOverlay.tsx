import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { Device, ThermalData } from '../../types';
import { api } from '../../lib/api';
import { getThermalStatus, formatTemperature } from '../../lib/utils';

interface ThermalOverlayProps {
  rackId: number;
  devices: Device[];
}

export const ThermalOverlay: React.FC<ThermalOverlayProps> = ({ rackId, devices }) => {
  const [thermalData, setThermalData] = useState<ThermalData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchThermalData = async () => {
      try {
        setLoading(true);
        const data = await api.getRackThermal(rackId);
        setThermalData(data);
      } catch (error) {
        console.error('Failed to fetch thermal data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchThermalData();
    const interval = setInterval(fetchThermalData, 10000); // Refresh every 10 seconds

    return () => clearInterval(interval);
  }, [rackId]);

  if (loading || !thermalData) {
    return (
      <motion.div
        className="absolute inset-0 bg-blue-500/5 backdrop-blur-sm flex items-center justify-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      >
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-electric border-t-transparent rounded-full mx-auto" />
          <p className="text-xs text-muted-foreground mt-2 font-mono">Loading thermal data...</p>
        </div>
      </motion.div>
    );
  }

  return (
    <AnimatePresence>
      <motion.div
        className="absolute inset-0 pointer-events-none"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      >
        {/* Thermal Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-blue-500/10 via-transparent to-red-500/10" />

        {/* Device Thermal Highlights */}
        {devices.map((device) => {
          if (!device.start_unit || !device.rack_id || device.rack_id !== rackId) return null;

          const thermalStatus = getThermalStatus(device.temperature_celsius);
          const heightPx = device.height_units * 44.45;

          // Calculate position from bottom
          const totalUnits = 42;
          const unitFromBottom = totalUnits - device.start_unit - device.height_units + 1;
          const topPx = unitFromBottom * 44.45;

          return (
            <motion.div
              key={device.id}
              className={`absolute left-8 right-8 rounded-lg pointer-events-auto cursor-pointer`}
              style={{
                height: `${heightPx}px`,
                top: `${topPx}px`,
              }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.6 }}
              whileHover={{ opacity: 1, scale: 1.02 }}
            >
              {/* Thermal Color Overlay */}
              <div className={`h-full rounded-lg thermal-${thermalStatus.status}`}>
                <div className="h-full flex items-center justify-center">
                  <div className="glass rounded px-3 py-1 border border-white/10">
                    <p className={`text-xs font-mono font-semibold ${thermalStatus.color}`}>
                      {formatTemperature(device.temperature_celsius)}
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>
          );
        })}

        {/* Thermal Legend */}
        <div className="absolute top-4 right-4 glass rounded-lg p-3 border border-border pointer-events-auto">
          <h4 className="text-xs font-mono font-semibold text-foreground mb-2">
            Thermal Map
          </h4>
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded thermal-cold" />
              <span className="text-xs text-blue-400 font-mono">&lt; 20°C</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded thermal-cool" />
              <span className="text-xs text-green-400 font-mono">20-30°C</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded thermal-warm" />
              <span className="text-xs text-amber font-mono">30-40°C</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded thermal-hot" />
              <span className="text-xs text-orange-500 font-mono">40-50°C</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded thermal-critical" />
              <span className="text-xs text-red-500 font-mono">&gt; 50°C</span>
            </div>
          </div>

          <div className="mt-3 pt-3 border-t border-border">
            <div className="text-xs space-y-1">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Avg Temp:</span>
                <span className="text-electric font-mono">
                  {formatTemperature(thermalData.average_temperature)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Max Temp:</span>
                <span className="text-red-400 font-mono">
                  {formatTemperature(thermalData.max_temperature)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Efficiency:</span>
                <span className="text-lime font-mono">
                  {(thermalData.cooling_efficiency * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Airflow Direction Indicator */}
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 glass rounded-lg px-4 py-2 border border-border pointer-events-auto">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-electric" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
            </svg>
            <span className="text-xs text-muted-foreground font-mono">
              Airflow: {thermalData.airflow_direction.replace('-', ' → ')}
            </span>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};
