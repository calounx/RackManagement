import React, { useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { useStore } from '../../store/useStore';

export const SpecFetcher: React.FC = () => {
  const [url, setUrl] = useState('');
  const { fetchSpecsFromUrl, loading } = useStore();

  const handleFetch = async () => {
    if (!url) return;
    await fetchSpecsFromUrl(url);
    setUrl('');
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Auto-Fetch Device Specs</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex gap-2">
          <Input
            placeholder="Enter manufacturer URL or model number..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
          <Button onClick={handleFetch} loading={loading}>
            Fetch Specs
          </Button>
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          Automatically fetch device specifications from manufacturer websites
        </p>
      </CardContent>
    </Card>
  );
};
