import React from 'react';
import { ShieldCheck, Lock, Activity, Server, Radio } from 'lucide-react';

export default function Navbar({ telemetry, connectionStatus }) {
  const currentRound = telemetry?.round ?? 1;
  const phase = telemetry?.phase ?? "idle";
  const isEncrypted = telemetry?.encrypted ?? true;

  return (
    <header className="border-b border-gray-800 bg-[#0d1322]/90 backdrop-blur-md sticky top-0 z-50 px-6 py-3.5">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        
        {/* Brand & Title */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 to-emerald-500 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <span className="text-xl">🧠</span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-white">FedMed</h1>
              <span className="text-[10px] uppercase tracking-wider font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                v0.1-Scaffold
              </span>
            </div>
            <p className="text-xs text-gray-400">
              Cross-Silo FL Brain Tumor Segmentation (BraTS)
            </p>
          </div>
        </div>

        {/* Status Indicators */}
        <div className="flex items-center gap-3">
          {/* Phase Badge */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-900 border border-gray-800 text-xs">
            <Activity className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
            <span className="text-gray-400">Round <strong className="text-white">{currentRound}</strong></span>
            <span className="text-gray-600">•</span>
            <span className="uppercase text-[11px] font-semibold tracking-wider text-cyan-300">
              {phase}
            </span>
          </div>

          {/* Encryption Badge */}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-950/40 border border-emerald-800/50 text-xs text-emerald-400">
            <Lock className="w-3.5 h-3.5" />
            <span className="font-medium">CKKS Homomorphic {isEncrypted ? "Active" : "Off"}</span>
          </div>

          {/* Connection Status */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-900 border border-gray-800 text-xs">
            <span className={`w-2 h-2 rounded-full ${connectionStatus?.connected ? 'bg-emerald-400 animate-pulse' : 'bg-red-500'}`} />
            <span className="text-gray-300">
              {connectionStatus?.isMock ? "Mock Stream" : "Live WebSocket"}
            </span>
          </div>
        </div>

      </div>
    </header>
  );
}
