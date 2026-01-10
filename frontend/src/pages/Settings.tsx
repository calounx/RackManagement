import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { useDebugStore } from '../lib/debug-store';
import { Bug, Terminal, Info } from 'lucide-react';

export const Settings: React.FC = () => {
  const { enabled, toggleDebug, togglePanel, panelOpen, logs } = useDebugStore();

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-foreground">Settings</h1>

      {/* Debug Settings */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Bug className="w-5 h-5" />
            <CardTitle>Debug Mode</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg border border-border">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="font-medium text-foreground">Enable Debug Mode</h3>
                {enabled && (
                  <Badge variant="success">
                    Active
                  </Badge>
                )}
              </div>
              <p className="text-sm text-muted-foreground">
                Log API requests, responses, and errors for debugging
              </p>
            </div>
            <button
              onClick={toggleDebug}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                enabled ? 'bg-primary' : 'bg-muted'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  enabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {enabled && (
            <>
              <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg border border-border">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-medium text-foreground">Debug Console</h3>
                    {panelOpen && (
                      <Badge variant="info">
                        Open
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">
                    View detailed debug logs in the bottom panel
                  </p>
                </div>
                <button
                  onClick={togglePanel}
                  className={`px-4 py-2 rounded-md font-medium transition-colors ${
                    panelOpen
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted text-foreground hover:bg-muted/80'
                  }`}
                >
                  <Terminal className="w-4 h-4" />
                </button>
              </div>

              <div className="p-4 bg-blue-500/5 border border-blue-500/20 rounded-lg">
                <div className="flex items-start gap-3">
                  <Info className="w-5 h-5 text-blue-500 mt-0.5" />
                  <div className="flex-1 space-y-2">
                    <h4 className="font-medium text-foreground">Debug Console Info</h4>
                    <ul className="text-sm text-muted-foreground space-y-1">
                      <li>• Current logs: <strong className="text-foreground">{logs.length}</strong></li>
                      <li>• Press <kbd className="px-2 py-1 bg-muted rounded border border-border font-mono text-xs">Ctrl</kbd> + <kbd className="px-2 py-1 bg-muted rounded border border-border font-mono text-xs">D</kbd> to toggle console</li>
                      <li>• API calls are logged automatically when debug is enabled</li>
                      <li>• Export logs as JSON for sharing or analysis</li>
                    </ul>
                  </div>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Application Info */}
      <Card>
        <CardHeader>
          <CardTitle>Application Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Version</span>
            <span className="font-mono text-foreground">1.0.1</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Environment</span>
            <span className="font-mono text-foreground">
              {import.meta.env.MODE}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">API Endpoint</span>
            <span className="font-mono text-foreground text-xs">
              {import.meta.env.VITE_API_URL || 'http://localhost:8000'}
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
