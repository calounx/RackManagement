import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useEffect } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { ToastContainer } from './components/ui/toast';
import { DebugPanel } from './components/debug/DebugPanel';
import { useDebugStore } from './lib/debug-store';

// Pages
import { Dashboard } from './pages/Dashboard';
import { Racks } from './pages/Racks';
import { Devices } from './pages/Devices';
import { Connections } from './pages/Connections';
import { ThermalAnalysis } from './pages/ThermalAnalysis';
import { Settings } from './pages/Settings';

function App() {
  const { togglePanel, enabled, setEnabled } = useDebugStore();

  // Keyboard shortcut: Ctrl+D to toggle debug panel
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === 'd') {
        e.preventDefault();
        // Enable debug mode if not already enabled
        if (!enabled) {
          setEnabled(true);
        }
        togglePanel();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [togglePanel, enabled, setEnabled]);

  return (
    <Router>
      <div className="flex h-screen bg-background dot-grid overflow-hidden">
        {/* Sidebar */}
        <Sidebar />

        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header />

          {/* Page Content */}
          <main className="flex-1 overflow-y-auto">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/racks" element={<Racks />} />
              <Route path="/devices" element={<Devices />} />
              <Route path="/connections" element={<Connections />} />
              <Route path="/thermal" element={<ThermalAnalysis />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </main>
        </div>

        {/* Toast Notifications */}
        <ToastContainer />

        {/* Debug Panel */}
        <DebugPanel />
      </div>
    </Router>
  );
}

export default App;
