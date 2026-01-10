import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';

export const CableValidator: React.FC = () => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Cable Validation</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex items-center justify-between p-2 bg-secondary/50 rounded">
            <span className="text-sm">Port compatibility</span>
            <Badge variant="success">Valid</Badge>
          </div>
          <div className="flex items-center justify-between p-2 bg-secondary/50 rounded">
            <span className="text-sm">Cable length</span>
            <Badge variant="success">Within limits</Badge>
          </div>
          <div className="flex items-center justify-between p-2 bg-secondary/50 rounded">
            <span className="text-sm">Speed matching</span>
            <Badge variant="warning">Mismatch</Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
