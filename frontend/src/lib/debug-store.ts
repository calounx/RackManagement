import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { generateId } from './utils';

export interface DebugLog {
  id: string;
  timestamp: Date;
  type: 'request' | 'response' | 'error' | 'info';
  method?: string;
  url?: string;
  status?: number;
  duration?: number;
  data?: any;
  error?: string;
}

interface DebugState {
  enabled: boolean;
  panelOpen: boolean;
  logs: DebugLog[];
  maxLogs: number;

  // Actions
  toggleDebug: () => void;
  togglePanel: () => void;
  addLog: (log: Omit<DebugLog, 'id' | 'timestamp'>) => void;
  clearLogs: () => void;
  setEnabled: (enabled: boolean) => void;
}

export const useDebugStore = create<DebugState>()(
  persist(
    (set, get) => ({
      enabled: import.meta.env.DEV || false,
      panelOpen: false,
      logs: [],
      maxLogs: 100,

      toggleDebug: () => {
        set((state) => ({ enabled: !state.enabled }));
      },

      togglePanel: () => {
        set((state) => ({ panelOpen: !state.panelOpen }));
      },

      setEnabled: (enabled: boolean) => {
        set({ enabled });
        if (!enabled) {
          set({ logs: [] });
        }
      },

      addLog: (log) => {
        if (!get().enabled) return;

        const newLog: DebugLog = {
          ...log,
          id: generateId(),
          timestamp: new Date(),
        };

        set((state) => ({
          logs: [newLog, ...state.logs].slice(0, state.maxLogs),
        }));
      },

      clearLogs: () => {
        set({ logs: [] });
      },
    }),
    {
      name: 'homerack-debug',
      partialize: (state) => ({ enabled: state.enabled }),
    }
  )
);
