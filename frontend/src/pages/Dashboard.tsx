import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { useStore } from '../store/useStore';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { formatPower, formatTemperature } from '../lib/utils';

export const Dashboard: React.FC = () => {
  const { racks, devices, connections, fetchRacks, fetchDevices, fetchConnections } = useStore();

  useEffect(() => {
    fetchRacks();
    fetchDevices();
    fetchConnections();
  }, []);

  const totalPower = devices.reduce((sum, d) => sum + d.power_consumption_watts, 0);
  const avgTemp = devices.length > 0
    ? devices.reduce((sum, d) => sum + d.temperature_celsius, 0) / devices.length
    : 0;
  const activeDevices = devices.filter((d) => d.status === 'active').length;

  const stats = [
    {
      title: 'Total Racks',
      value: racks.length,
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
      ),
      color: 'text-electric',
      link: '/racks',
    },
    {
      title: 'Total Devices',
      value: devices.length,
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
        </svg>
      ),
      color: 'text-amber',
      link: '/devices',
    },
    {
      title: 'Active Devices',
      value: activeDevices,
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
      color: 'text-lime',
      link: '/devices',
    },
    {
      title: 'Connections',
      value: connections.length,
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
        </svg>
      ),
      color: 'text-purple-400',
      link: '/connections',
    },
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Welcome Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <h1 className="text-3xl font-bold text-foreground">
          Welcome to <span className="text-electric neon-text">HomeRack</span>
        </h1>
        <p className="text-muted-foreground mt-2">
          Precision engineering for your data center infrastructure
        </p>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, index) => (
          <Link key={stat.title} to={stat.link}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: index * 0.1 }}
            >
              <Card interactive className="h-full">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground font-mono">
                        {stat.title}
                      </p>
                      <p className={`text-4xl font-bold mt-2 ${stat.color}`}>
                        {stat.value}
                      </p>
                    </div>
                    <div className={`${stat.color} opacity-20`}>{stat.icon}</div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </Link>
        ))}
      </div>

      {/* Power & Thermal Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4, delay: 0.4 }}
        >
          <Card>
            <CardHeader>
              <CardTitle>Power Consumption</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-end gap-2">
                  <span className="text-5xl font-bold text-amber">
                    {formatPower(totalPower)}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-4 pt-4 border-t border-border">
                  <div>
                    <p className="text-xs text-muted-foreground">Peak</p>
                    <p className="text-lg font-mono text-foreground mt-1">
                      {formatPower(totalPower * 1.2)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Avg per Device</p>
                    <p className="text-lg font-mono text-foreground mt-1">
                      {devices.length > 0 ? formatPower(totalPower / devices.length) : '0 W'}
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4, delay: 0.5 }}
        >
          <Card>
            <CardHeader>
              <CardTitle>Thermal Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-end gap-2">
                  <span className="text-5xl font-bold text-lime">
                    {formatTemperature(avgTemp)}
                  </span>
                  <span className="text-muted-foreground mb-2">average</span>
                </div>
                <div className="grid grid-cols-2 gap-4 pt-4 border-t border-border">
                  <div>
                    <p className="text-xs text-muted-foreground">Hottest</p>
                    <p className="text-lg font-mono text-red-400 mt-1">
                      {devices.length > 0
                        ? formatTemperature(Math.max(...devices.map((d) => d.temperature_celsius)))
                        : '0°C'}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Coolest</p>
                    <p className="text-lg font-mono text-blue-400 mt-1">
                      {devices.length > 0
                        ? formatTemperature(Math.min(...devices.map((d) => d.temperature_celsius)))
                        : '0°C'}
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Recent Activity */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.6 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>Recent Devices</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {devices.slice(0, 5).map((device) => (
                <Link key={device.id} to={`/devices/${device.id}`}>
                  <div className="flex items-center justify-between p-3 rounded-lg hover:bg-secondary/50 transition-colors">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-electric/10 border border-electric/30 flex items-center justify-center">
                        <svg className="w-5 h-5 text-electric" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                        </svg>
                      </div>
                      <div>
                        <p className="font-medium text-foreground">{device.name}</p>
                        <p className="text-xs text-muted-foreground font-mono">
                          {device.manufacturer} {device.model}
                        </p>
                      </div>
                    </div>
                    <Badge
                      variant={device.status === 'active' ? 'success' : 'default'}
                      pulse={device.status === 'active'}
                    >
                      {device.status}
                    </Badge>
                  </div>
                </Link>
              ))}
              {devices.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  <p>No devices found</p>
                  <Link to="/devices" className="text-electric hover:underline text-sm mt-2 inline-block">
                    Add your first device
                  </Link>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};
