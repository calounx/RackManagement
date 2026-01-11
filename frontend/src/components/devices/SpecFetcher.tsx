import React, { useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { useStore } from '../../store/useStore';

export const SpecFetcher: React.FC = () => {
  const [brand, setBrand] = useState('');
  const [model, setModel] = useState('');
  const { fetchSpecsFromUrl, loading } = useStore();

  const handleFetch = async () => {
    if (!brand || !model) return;
    await fetchSpecsFromUrl(brand, model);
    setBrand('');
    setModel('');
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Auto-Fetch Device Specs</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex gap-2">
            <Input
              placeholder="Brand (e.g., Cisco, Dell)"
              value={brand}
              onChange={(e) => setBrand(e.target.value)}
            />
            <Input
              placeholder="Model (e.g., Catalyst 2960)"
              value={model}
              onChange={(e) => setModel(e.target.value)}
            />
          </div>
          <Button onClick={handleFetch} loading={loading} className="w-full">
            Fetch Specs
          </Button>
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          Automatically fetch device specifications from manufacturer databases
        </p>
      </CardContent>
    </Card>
  );
};
