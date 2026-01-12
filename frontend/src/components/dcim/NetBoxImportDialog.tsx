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
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Checkbox } from '../ui/checkbox';
import { api } from '../../lib/api';
import { useStore } from '../../store/useStore';
import { Download, Loader2 } from 'lucide-react';

interface NetBoxImportDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function NetBoxImportDialog({ open, onOpenChange }: NetBoxImportDialogProps) {
  const [rackName, setRackName] = useState('');
  const [importDevices, setImportDevices] = useState(true);
  const [overwriteExisting, setOverwriteExisting] = useState(false);
  const [importing, setImporting] = useState(false);

  const addToast = useStore((state) => state.addToast);
  const fetchRacks = useStore((state) => state.fetchRacks);

  const handleImport = async () => {
    if (!rackName.trim()) {
      addToast({
        title: 'Validation Error',
        description: 'Please enter a rack name',
        type: 'error',
      });
      return;
    }

    setImporting(true);
    try {
      const result = await api.importRackFromNetBox(
        rackName.trim(),
        importDevices,
        overwriteExisting
      );

      addToast({
        title: 'Import Successful',
        description: result.message,
        type: 'success',
        duration: 5000,
      });

      // Refresh racks list
      await fetchRacks();

      // Close dialog
      onOpenChange(false);

      // Reset form
      setRackName('');
      setImportDevices(true);
      setOverwriteExisting(false);
    } catch (error: any) {
      const message = error.response?.data?.detail || error.message || 'Import failed';
      addToast({
        title: 'Import Failed',
        description: message,
        type: 'error',
        duration: 7000,
      });
    } finally {
      setImporting(false);
    }
  };

  const handleCancel = () => {
    if (!importing) {
      setRackName('');
      setImportDevices(true);
      setOverwriteExisting(false);
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleCancel}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Download className="h-5 w-5" />
            Import Rack from NetBox
          </DialogTitle>
          <DialogDescription>
            Enter the NetBox rack name to import the rack layout and devices into HomeRack
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="rack-name">Rack Name *</Label>
            <Input
              id="rack-name"
              placeholder="e.g., DC1-R01, Server-Rack-A"
              value={rackName}
              onChange={(e) => setRackName(e.target.value)}
              disabled={importing}
              autoFocus
            />
            <p className="text-sm text-muted-foreground">
              The exact rack name as it appears in NetBox
            </p>
          </div>

          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="import-devices"
                checked={importDevices}
                onCheckedChange={(checked) => setImportDevices(checked as boolean)}
                disabled={importing}
              />
              <Label
                htmlFor="import-devices"
                className="text-sm font-normal cursor-pointer"
              >
                Import devices positioned in this rack
              </Label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="overwrite-existing"
                checked={overwriteExisting}
                onCheckedChange={(checked) => setOverwriteExisting(checked as boolean)}
                disabled={importing}
              />
              <Label
                htmlFor="overwrite-existing"
                className="text-sm font-normal cursor-pointer"
              >
                Overwrite if rack already exists
              </Label>
            </div>
          </div>

          {overwriteExisting && (
            <div className="rounded-md bg-yellow-50 dark:bg-yellow-900/20 p-3 border border-yellow-200 dark:border-yellow-800">
              <p className="text-sm text-yellow-800 dark:text-yellow-200">
                <strong>Warning:</strong> Existing rack data will be replaced with data from NetBox.
              </p>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={handleCancel}
            disabled={importing}
          >
            Cancel
          </Button>
          <Button
            onClick={handleImport}
            disabled={!rackName.trim() || importing}
          >
            {importing ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Importing...
              </>
            ) : (
              <>
                <Download className="mr-2 h-4 w-4" />
                Import Rack
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
