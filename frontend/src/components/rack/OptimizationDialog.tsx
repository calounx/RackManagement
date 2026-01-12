import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Button } from '../ui/button';
import { Label } from '../ui/label';
import { Checkbox } from '../ui/checkbox';
import { Card } from '../ui/card';
import { Badge } from '../ui/badge';
import { api } from '../../lib/api';
import { useStore } from '../../store/useStore';
import { Sparkles, Loader2, CheckCircle, Info, Sliders } from 'lucide-react';
import type { Rack } from '../../types';

interface OptimizationDialogProps {
  rack: Rack;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface OptimizationResult {
  positions: any[];
  score: {
    cable_management: number;
    weight_distribution: number;
    thermal_management: number;
    access_frequency: number;
    total: number;
  };
  improvements: string[];
  metadata: {
    algorithm: string;
    alternatives_evaluated: number;
    devices_placed: number;
    total_devices: number;
    improvement_percentage?: number;
  };
}

export function OptimizationDialog({ rack, open, onOpenChange }: OptimizationDialogProps) {
  const [result, setResult] = useState<OptimizationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [customWeights, setCustomWeights] = useState(false);
  const [weights, setWeights] = useState({
    cable: 0.30,
    weight: 0.25,
    thermal: 0.25,
    access: 0.20
  });

  const addToast = useStore((state) => state.addToast);

  const runOptimization = async () => {
    setLoading(true);
    try {
      const optimizationResult = await api.optimizeRack(
        rack.id,
        [],
        customWeights ? weights : undefined
      );
      setResult(optimizationResult);
      addToast({
        title: 'Optimization Complete',
        description: `Generated optimized layout using ${optimizationResult.metadata.algorithm}`,
        type: 'success',
      });
    } catch (error: any) {
      const message = error.response?.data?.detail || error.message || 'Optimization failed';
      addToast({
        title: 'Optimization Failed',
        description: message,
        type: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  const applyOptimization = async () => {
    // TODO: Implement applying optimization (update rack positions)
    addToast({
      title: 'Apply Optimization',
      description: 'Applying optimization suggestions to rack...',
      type: 'info',
    });
    onOpenChange(false);
  };

  const handleClose = () => {
    setResult(null);
    setCustomWeights(false);
    setWeights({
      cable: 0.30,
      weight: 0.25,
      thermal: 0.25,
      access: 0.20
    });
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-electric" />
            Optimize Rack Layout
          </DialogTitle>
          <DialogDescription>
            Generate intelligent device placement suggestions based on thermal, power, cable, and access optimization
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Custom Weights Section */}
          {!result && (
            <>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="custom-weights"
                  checked={customWeights}
                  onCheckedChange={(checked) => setCustomWeights(checked as boolean)}
                />
                <Label htmlFor="custom-weights" className="cursor-pointer">
                  Customize optimization weights
                </Label>
              </div>

              {customWeights && (
                <Card className="p-4 space-y-4 bg-secondary/30">
                  <div className="flex items-center gap-2 mb-2">
                    <Sliders className="w-4 h-4 text-electric" />
                    <h4 className="font-medium text-foreground">Objective Weights</h4>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between mb-1">
                        <Label className="text-sm">Cable Management</Label>
                        <span className="text-sm text-muted-foreground">{(weights.cable * 100).toFixed(0)}%</span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={weights.cable * 100}
                        onChange={(e) => setWeights({...weights, cable: parseInt(e.target.value) / 100})}
                        className="w-full h-2 bg-secondary rounded-lg appearance-none cursor-pointer"
                      />
                    </div>

                    <div>
                      <div className="flex justify-between mb-1">
                        <Label className="text-sm">Weight Distribution</Label>
                        <span className="text-sm text-muted-foreground">{(weights.weight * 100).toFixed(0)}%</span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={weights.weight * 100}
                        onChange={(e) => setWeights({...weights, weight: parseInt(e.target.value) / 100})}
                        className="w-full h-2 bg-secondary rounded-lg appearance-none cursor-pointer"
                      />
                    </div>

                    <div>
                      <div className="flex justify-between mb-1">
                        <Label className="text-sm">Thermal Management</Label>
                        <span className="text-sm text-muted-foreground">{(weights.thermal * 100).toFixed(0)}%</span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={weights.thermal * 100}
                        onChange={(e) => setWeights({...weights, thermal: parseInt(e.target.value) / 100})}
                        className="w-full h-2 bg-secondary rounded-lg appearance-none cursor-pointer"
                      />
                    </div>

                    <div>
                      <div className="flex justify-between mb-1">
                        <Label className="text-sm">Access Frequency</Label>
                        <span className="text-sm text-muted-foreground">{(weights.access * 100).toFixed(0)}%</span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={weights.access * 100}
                        onChange={(e) => setWeights({...weights, access: parseInt(e.target.value) / 100})}
                        className="w-full h-2 bg-secondary rounded-lg appearance-none cursor-pointer"
                      />
                    </div>
                  </div>

                  <div className="text-xs text-muted-foreground">
                    <Info className="w-3 h-3 inline mr-1" />
                    Adjust weights to prioritize different optimization objectives
                  </div>
                </Card>
              )}
            </>
          )}

          {/* Results Display */}
          {result && (
            <div className="space-y-4">
              {/* Optimization Score Card */}
              <Card className="p-4 bg-electric/5 border-electric/30">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-foreground">Optimization Score</h3>
                  <Badge variant="success" className="text-base px-3 py-1">
                    {(result.score.total * 100).toFixed(0)}%
                  </Badge>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-secondary/30 rounded-lg">
                    <div className="text-xs text-muted-foreground mb-1">Cable Management</div>
                    <div className="text-lg font-semibold text-electric">
                      {(result.score.cable_management * 100).toFixed(0)}%
                    </div>
                  </div>
                  <div className="p-3 bg-secondary/30 rounded-lg">
                    <div className="text-xs text-muted-foreground mb-1">Weight Distribution</div>
                    <div className="text-lg font-semibold text-electric">
                      {(result.score.weight_distribution * 100).toFixed(0)}%
                    </div>
                  </div>
                  <div className="p-3 bg-secondary/30 rounded-lg">
                    <div className="text-xs text-muted-foreground mb-1">Thermal Management</div>
                    <div className="text-lg font-semibold text-electric">
                      {(result.score.thermal_management * 100).toFixed(0)}%
                    </div>
                  </div>
                  <div className="p-3 bg-secondary/30 rounded-lg">
                    <div className="text-xs text-muted-foreground mb-1">Access Frequency</div>
                    <div className="text-lg font-semibold text-electric">
                      {(result.score.access_frequency * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>
              </Card>

              {/* Improvements Card */}
              <Card className="p-4">
                <h3 className="text-lg font-semibold text-foreground mb-3">Improvements</h3>
                <ul className="space-y-2">
                  {result.improvements.map((improvement, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-sm">
                      <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                      <span className="text-muted-foreground">{improvement}</span>
                    </li>
                  ))}
                </ul>
              </Card>

              {/* Metadata Card */}
              <Card className="p-4 bg-secondary/30">
                <h3 className="text-lg font-semibold text-foreground mb-3">Optimization Details</h3>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-muted-foreground">Algorithm:</span>
                    <span className="ml-2 font-medium text-foreground">{result.metadata.algorithm}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Alternatives:</span>
                    <span className="ml-2 font-medium text-foreground">{result.metadata.alternatives_evaluated}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Devices Placed:</span>
                    <span className="ml-2 font-medium text-foreground">
                      {result.metadata.devices_placed} / {result.metadata.total_devices}
                    </span>
                  </div>
                  {result.metadata.improvement_percentage !== null && result.metadata.improvement_percentage !== undefined && (
                    <div>
                      <span className="text-muted-foreground">Improvement:</span>
                      <span className="ml-2 font-medium text-green-400">
                        +{result.metadata.improvement_percentage}%
                      </span>
                    </div>
                  )}
                </div>
              </Card>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={handleClose}
          >
            {result ? 'Close' : 'Cancel'}
          </Button>
          {!result && (
            <Button
              onClick={runOptimization}
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Optimizing...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" />
                  Run Optimization
                </>
              )}
            </Button>
          )}
          {result && (
            <Button onClick={applyOptimization}>
              Apply Suggestions
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
