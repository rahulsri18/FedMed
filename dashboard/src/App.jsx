import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import MetricsChart from './components/MetricsChart';
import NodeCards from './components/NodeCards';
import PrivacyGauge from './components/PrivacyGauge';
import CanvasMRIViewer from './components/CanvasMRIViewer';
import { TelemetryService } from './services/mockTelemetry';
import { ShieldCheck, Activity, Users, Database } from 'lucide-react';

export default function App() {
  const [telemetry, setTelemetry] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState({ connected: false, isMock: true });
  const [history, setHistory] = useState([
    { round: 1, dice: 0.68, loss: 0.42 },
    { round: 2, dice: 0.72, loss: 0.38 },
    { round: 3, dice: 0.75, loss: 0.34 },
    { round: 4, dice: 0.78, loss: 0.31 },
  ]);

  useEffect(() => {
    const service = new TelemetryService(
      (data) => {
        setTelemetry(data);
        if (data.global && data.round) {
          setHistory((prev) => {
            // Keep unique by round
            const filtered = prev.filter((item) => item.round !== data.round);
            const updated = [...filtered, { round: data.round, dice: data.global.dice, loss: data.global.loss }];
            return updated.sort((a, b) => a.round - b.round);
          });
        }
      },
      (status) => {
        setConnectionStatus(status);
      }
    );

    service.connect();

    return () => {
      service.disconnect();
    };
  }, []);

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col font-sans">
      {/* Top Header */}
      <Navbar telemetry={telemetry} connectionStatus={connectionStatus} />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-6 space-y-6">
        
        {/* Top Summary Banner */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="glass-panel rounded-2xl p-4 border border-gray-800 flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11px] uppercase tracking-wider text-gray-400 block font-medium">Global Mean Dice</span>
              <span className="text-xl font-bold font-mono text-white">
                {telemetry?.global?.dice?.toFixed(2) ?? '0.78'}
              </span>
            </div>
          </div>

          <div className="glass-panel rounded-2xl p-4 border border-gray-800 flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11px] uppercase tracking-wider text-gray-400 block font-medium">Privacy Spent</span>
              <span className="text-xl font-bold font-mono text-white">
                {telemetry?.privacy?.epsilon_spent?.toFixed(1) ?? '2.3'} / 5.0 ε
              </span>
            </div>
          </div>

          <div className="glass-panel rounded-2xl p-4 border border-gray-800 flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11px] uppercase tracking-wider text-gray-400 block font-medium">Hospital Silos</span>
              <span className="text-xl font-bold font-mono text-white">
                3 Nodes Active
              </span>
            </div>
          </div>

          <div className="glass-panel rounded-2xl p-4 border border-gray-800 flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11px] uppercase tracking-wider text-gray-400 block font-medium">Cohort Volume</span>
              <span className="text-xl font-bold font-mono text-white">
                36 BraTS Scans
              </span>
            </div>
          </div>
        </div>

        {/* Hospital Silo Node Status Cards */}
        <NodeCards nodes={telemetry?.nodes || []} />

        {/* Charts & Interactive Viewer Row */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-6 space-y-6">
            <MetricsChart history={history} />
            <PrivacyGauge privacy={telemetry?.privacy} encrypted={telemetry?.encrypted} />
          </div>

          <div className="lg:col-span-6">
            <CanvasMRIViewer />
          </div>
        </div>

      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800/80 bg-[#0d1322]/60 py-4 px-6 mt-8">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-xs text-gray-500">
          <p>FedMed: Cross-Silo Privacy-Preserving Federated Brain Tumor Segmentation Engine</p>
          <p className="font-mono">Flower • TenSEAL CKKS • Opacus DP • MONAI 3D U-Net • FastAPI • Vite</p>
        </div>
      </footer>
    </div>
  );
}
