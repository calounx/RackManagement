import React, { useState } from 'react';
import { X, Trash2, ChevronDown, ChevronRight, Download } from 'lucide-react';
import { useDebugStore } from '../../lib/debug-store';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { format } from 'date-fns';

export const DebugPanel: React.FC = () => {
  const { panelOpen, togglePanel, logs, clearLogs, enabled, setEnabled } = useDebugStore();
  const [expandedLogs, setExpandedLogs] = useState<Set<string>>(new Set());

  if (!panelOpen) return null;

  const toggleExpand = (id: string) => {
    setExpandedLogs((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const exportLogs = () => {
    const data = JSON.stringify(logs, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `homerack-debug-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'request':
        return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
      case 'response':
        return 'bg-green-500/10 text-green-500 border-green-500/20';
      case 'error':
        return 'bg-red-500/10 text-red-500 border-red-500/20';
      case 'info':
        return 'bg-gray-500/10 text-gray-500 border-gray-500/20';
      default:
        return 'bg-gray-500/10 text-gray-500 border-gray-500/20';
    }
  };

  const getStatusColor = (status?: number) => {
    if (!status) return '';
    if (status >= 200 && status < 300) return 'text-green-500';
    if (status >= 300 && status < 400) return 'text-yellow-500';
    if (status >= 400 && status < 500) return 'text-orange-500';
    if (status >= 500) return 'text-red-500';
    return '';
  };

  return (
    <div className="fixed bottom-0 right-0 w-full md:w-2/3 lg:w-1/2 h-96 bg-background/95 backdrop-blur-sm border-t border-l border-border shadow-2xl z-50 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="flex items-center gap-3">
          <h3 className="font-semibold text-foreground">Debug Console</h3>
          <Badge variant="info" className="text-xs">
            {logs.length} logs
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="ghost"
            onClick={exportLogs}
            disabled={logs.length === 0}
          >
            <Download className="w-4 h-4" />
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={clearLogs}
            disabled={logs.length === 0}
          >
            <Trash2 className="w-4 h-4" />
          </Button>
          <Button size="sm" variant="ghost" onClick={togglePanel}>
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Logs */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1 font-mono text-xs">
        {!enabled ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-4 space-y-3">
            <div className="text-muted-foreground">
              Debug mode is disabled
            </div>
            <button
              onClick={() => setEnabled(true)}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md font-medium hover:bg-primary/90 transition-colors text-sm"
            >
              Enable Debug Mode
            </button>
            <div className="text-xs text-muted-foreground">
              Or enable it in Settings
            </div>
          </div>
        ) : logs.length === 0 ? (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            No debug logs yet - make some API requests to see logs
          </div>
        ) : (
          logs.map((log) => {
            const isExpanded = expandedLogs.has(log.id);
            return (
              <div
                key={log.id}
                className="bg-card/50 border border-border rounded p-2 hover:bg-card/80 transition-colors"
              >
                <div
                  className="flex items-start gap-2 cursor-pointer"
                  onClick={() => toggleExpand(log.id)}
                >
                  <button className="mt-0.5">
                    {isExpanded ? (
                      <ChevronDown className="w-3 h-3" />
                    ) : (
                      <ChevronRight className="w-3 h-3" />
                    )}
                  </button>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-muted-foreground text-[10px]">
                        {format(log.timestamp, 'HH:mm:ss.SSS')}
                      </span>
                      <Badge
                        variant="default"
                        className={`text-[10px] px-1 py-0 ${getTypeColor(log.type)}`}
                      >
                        {log.type.toUpperCase()}
                      </Badge>
                      {log.method && (
                        <Badge variant="default" className="text-[10px] px-1 py-0">
                          {log.method}
                        </Badge>
                      )}
                      {log.status && (
                        <Badge
                          variant="default"
                          className={`text-[10px] px-1 py-0 ${getStatusColor(log.status)}`}
                        >
                          {log.status}
                        </Badge>
                      )}
                      {log.duration && (
                        <span className="text-muted-foreground text-[10px]">
                          {log.duration}ms
                        </span>
                      )}
                    </div>
                    {log.url && (
                      <div className="text-foreground mt-1 truncate">{log.url}</div>
                    )}
                    {log.error && (
                      <div className="text-red-500 mt-1">{log.error}</div>
                    )}
                  </div>
                </div>

                {isExpanded && (log.data || log.error) && (
                  <div className="mt-2 ml-5 p-2 bg-background/50 rounded border border-border overflow-x-auto">
                    <pre className="text-[10px] text-muted-foreground whitespace-pre-wrap">
                      {JSON.stringify(log.data || log.error, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
