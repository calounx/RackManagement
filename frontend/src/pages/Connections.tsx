import React, { useEffect } from 'react';
import { useStore } from '../store/useStore';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';

export const Connections: React.FC = () => {
  const { connections, fetchConnections } = useStore();

  useEffect(() => {
    fetchConnections();
  }, []);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Cable Management</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Track network and power connections
          </p>
        </div>
        <Button variant="primary">Add Connection</Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Connections</CardTitle>
        </CardHeader>
        <CardContent>
          <table className="data-table">
            <thead>
              <tr>
                <th>Source</th>
                <th>Target</th>
                <th>Type</th>
                <th>Length</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {connections.map((conn) => (
                <tr key={conn.id}>
                  <td className="font-mono text-sm">
                    {conn.source_device?.name} : {conn.source_port}
                  </td>
                  <td className="font-mono text-sm">
                    {conn.target_device?.name} : {conn.target_port}
                  </td>
                  <td>
                    <Badge variant="default">{conn.cable_type}</Badge>
                  </td>
                  <td className="font-mono">{conn.cable_length_meters}m</td>
                  <td>
                    <Badge variant={conn.status === 'active' ? 'success' : 'default'}>
                      {conn.status}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
};
