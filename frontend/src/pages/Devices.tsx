import React, { useEffect } from 'react';
import { useStore } from '../store/useStore';
import { DeviceCard } from '../components/devices/DeviceCard';
import { Button } from '../components/ui/button';

export const Devices: React.FC = () => {
  const { devices, fetchDevices } = useStore();

  useEffect(() => {
    fetchDevices();
  }, []);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Device Library</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Manage your hardware inventory
          </p>
        </div>
        <Button variant="primary">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add Device
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {devices.map((device) => (
          <DeviceCard key={device.id} device={device} />
        ))}
      </div>
    </div>
  );
};
