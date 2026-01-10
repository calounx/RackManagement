import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';

export const ThermalAnalysis: React.FC = () => {
  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-foreground">Thermal Analysis</h1>
      <Card>
        <CardHeader>
          <CardTitle>Temperature Monitoring</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Thermal analysis visualization coming soon...
          </p>
        </CardContent>
      </Card>
    </div>
  );
};
