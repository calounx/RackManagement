import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { useStore } from '../store/useStore';
import { api } from '../lib/api';
import { AlertTriangle, Thermometer, Wind, Activity } from 'lucide-react';

export const ThermalAnalysis: React.FC = () => {
  const { racks, selectedRackId, selectRack } = useStore();
  const [thermalData, setThermalData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const currentRack = racks.find((r) => r.id === selectedRackId) || racks[0];

  useEffect(() => {
    if (currentRack) {
      loadThermalData(currentRack.id);
    }
  }, [currentRack]);

  const loadThermalData = async (rackId: number) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getRackThermal(rackId);
      setThermalData(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load thermal data');
      setThermalData(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Thermal Analysis</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Monitor temperature and cooling efficiency
          </p>
        </div>
        {racks.length > 1 && (
          <select
            value={currentRack?.id || ''}
            onChange={(e) => selectRack(parseInt(e.target.value))}
            className="px-4 py-2 bg-secondary border border-border rounded-lg text-foreground"
          >
            {racks.map((rack) => (
              <option key={rack.id} value={rack.id}>
                {rack.name}
              </option>
            ))}
          </select>
        )}
      </div>

      {loading && (
        <Card>
          <CardContent className="p-12 text-center">
            <Activity className="w-12 h-12 mx-auto text-muted-foreground animate-spin" />
            <p className="text-muted-foreground mt-4">Loading thermal data...</p>
          </CardContent>
        </Card>
      )}

      {error && (
        <Card>
          <CardContent className="p-8">
            <div className="flex items-center gap-3 text-amber-500">
              <AlertTriangle className="w-6 h-6" />
              <div>
                <h3 className="font-semibold">Thermal Analysis Not Available</h3>
                <p className="text-sm text-muted-foreground mt-1">{error}</p>
                <p className="text-sm text-muted-foreground mt-2">
                  The backend thermal analysis endpoint may not be fully implemented yet.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {!loading && !error && thermalData && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Thermometer className="w-5 h-5 text-amber-500" />
                <CardTitle>Average Temperature</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-foreground">
                {thermalData.average_temperature || 'N/A'}°C
              </div>
              <Badge variant={
                (thermalData.average_temperature || 0) > 30 ? 'error' :
                (thermalData.average_temperature || 0) > 25 ? 'warning' :
                'success'
              } className="mt-2">
                {(thermalData.average_temperature || 0) > 30 ? 'Hot' :
                 (thermalData.average_temperature || 0) > 25 ? 'Warm' : 'Cool'}
              </Badge>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-red-500" />
                <CardTitle>Max Temperature</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-foreground">
                {thermalData.max_temperature || 'N/A'}°C
              </div>
              <p className="text-sm text-muted-foreground mt-2">
                Hottest point in rack
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Wind className="w-5 h-5 text-blue-500" />
                <CardTitle>Cooling Efficiency</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-foreground">
                {thermalData.cooling_efficiency ? `${Math.round(thermalData.cooling_efficiency * 100)}%` : 'N/A'}
              </div>
              <p className="text-sm text-muted-foreground mt-2">
                {thermalData.airflow_direction || 'Unknown airflow'}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {!loading && !error && thermalData?.hotspots && thermalData.hotspots.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Thermal Hotspots</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {thermalData.hotspots.map((hotspot: any, index: number) => (
                <div key={index} className="flex items-center justify-between p-3 bg-secondary/50 rounded-lg">
                  <div>
                    <p className="font-medium text-foreground">{hotspot.device_name}</p>
                    <p className="text-sm text-muted-foreground">Unit {hotspot.start_unit}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-semibold text-amber-500">{hotspot.temperature}°C</p>
                    <Badge variant={
                      hotspot.severity === 'critical' ? 'error' :
                      hotspot.severity === 'high' ? 'warning' :
                      'default'
                    }>
                      {hotspot.severity}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {!loading && !error && !thermalData && (
        <Card>
          <CardContent className="p-12 text-center">
            <Thermometer className="w-16 h-16 mx-auto text-muted-foreground opacity-50" />
            <h3 className="text-xl font-semibold text-foreground mt-4">No Thermal Data</h3>
            <p className="text-muted-foreground mt-2">
              {currentRack ? `No thermal analysis data available for ${currentRack.name}` : 'Select a rack to view thermal analysis'}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
