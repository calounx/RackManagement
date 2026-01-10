import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useStore } from '../store/useStore';
import { RackVisualizer } from '../components/rack/RackVisualizer';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import type { Device } from '../types';

export const Racks: React.FC = () => {
  const { racks, devices, fetchRacks, fetchDevices, selectedRackId, selectRack } = useStore();
  const [, setSelectedDevice] = useState<Device | null>(null);

  useEffect(() => {
    fetchRacks();
    fetchDevices();
  }, []);

  const currentRack = racks.find((r) => r.id === selectedRackId) || racks[0];
  const rackDevices = devices.filter((d) => d.rack_id === currentRack?.id);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Rack Management</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Visualize and manage your server racks
          </p>
        </div>
        <Button variant="primary">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add Rack
        </Button>
      </div>

      {racks.length === 0 ? (
        <Card className="p-12 text-center">
          <svg className="w-16 h-16 mx-auto text-muted-foreground opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
          <h3 className="text-xl font-semibold text-foreground mt-4">No racks yet</h3>
          <p className="text-muted-foreground mt-2">Get started by adding your first rack</p>
          <Button variant="primary" className="mt-6">Create Rack</Button>
        </Card>
      ) : (
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-3">
            <Card className="p-4">
              <h3 className="font-semibold text-foreground mb-4">Available Racks</h3>
              <div className="space-y-2">
                {racks.map((rack) => (
                  <motion.button
                    key={rack.id}
                    onClick={() => selectRack(rack.id)}
                    className={`w-full p-3 rounded-lg text-left transition-all ${
                      currentRack?.id === rack.id
                        ? 'bg-electric/10 border-2 border-electric text-electric'
                        : 'bg-secondary/50 border-2 border-transparent hover:border-border'
                    }`}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <p className="font-medium">{rack.name}</p>
                    <p className="text-xs text-muted-foreground font-mono mt-1">
                      {rack.location}
                    </p>
                  </motion.button>
                ))}
              </div>
            </Card>
          </div>

          <div className="col-span-9">
            {currentRack && (
              <RackVisualizer
                rack={currentRack}
                devices={rackDevices}
                onDeviceClick={setSelectedDevice}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
};
