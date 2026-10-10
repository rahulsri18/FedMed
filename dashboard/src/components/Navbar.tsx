import React from 'react';
import { Lock, Radio, Activity, Cpu, ShieldCheck, Terminal, Sparkles } from 'lucide-react';
import { TelemetryPayload, ConnectionStatus } from '../types';

interface NavbarProps {
  telemetry: TelemetryPayload | null;
  connectionStatus: ConnectionStatus;
  onOpenAudit?: () => void;
}

export default function Navbar({ telemetry, connectionStatus, onOpenAudit }: NavbarProps) {
  const currentRound = telemetry?.round ?? 1;
  const totalRounds = telemetry?.global?.rounds_total ?? 5;
  const phase = telemetry?.phase ?? 'idle';
  const isEncrypted = telemetry?.encrypted ?? true;

  return (
    <header className="border-b border-slate-200/90 bg-white/90 backdrop-blur-xl sticky top-0 z-50 px-4 sm:px-8 py-3.5 shadow-sm">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
        
        {/* Brand & Identity */}
        <div className="flex items-center gap-3.5">
          <div className="relative group cursor-pointer">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sky-50 to-sky-100 border border-sky-200 flex items-center justify-center text-sky-600 shadow-sm">
              {/* Custom SVG Neural Crest */}
              <svg className="w-5 h-5 text-sky-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8z" opacity="0.3" />
                <path d="M12 6v6l4 2" />
                <circle cx="12" cy="12" r="3" fill="#0284c7" fillOpacity="0.25" />
              </svg>
            </div>
          </div>

          <div>
            <div className="flex items-center gap-2.5">
              <span className="text-lg font-extrabold font-display tracking-tight text-slate-900 flex items-center gap-1.5">
                FED<span className="text-sky-600">MED</span>
              </span>
              <span className="text-[10px] font-mono tracking-wider px-2 py-0.5 rounded-full bg-sky-50 text-sky-700 border border-sky-200 font-bold uppercase">
                CLINICAL OPS
              </span>
            </div>
            <p className="text-[11px] font-medium text-slate-500 tracking-normal hidden sm:block">
              Cross-Silo Federated Learning • 3D Brain Tumor Segmentation
            </p>
          </div>
        </div>

        {/* Tactical Telemetry Badges (Light Mode) */}
        <div className="flex flex-wrap items-center gap-2.5 text-xs font-mono">
          
          {/* Round Counter */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-700 shadow-sm">
            <span className="text-slate-400 text-[11px] font-semibold tracking-wider">ROUND</span>
            <strong className="text-slate-900 font-bold font-mono text-sm">
              {currentRound < 10 ? `0${currentRound}` : currentRound}
              <span className="text-slate-400 font-normal text-xs">/{totalRounds < 10 ? `0${totalRounds}` : totalRounds}</span>
            </strong>
          </div>

          {/* Phase Badge */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-sky-50/80 border border-sky-200 text-sky-900 shadow-sm">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-sky-500 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-sky-600" />
            </span>
            <span className="text-sky-700 text-[11px]">PHASE:</span>
            <span className="uppercase font-bold text-sky-700 tracking-wide text-xs">
              {phase}
            </span>
          </div>

          {/* Encryption Indicator */}
          <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-semibold shadow-sm transition-all ${
            isEncrypted
              ? 'bg-purple-50 border-purple-200 text-purple-700'
              : 'bg-amber-50 border-amber-200 text-amber-700'
          }`}>
            <Lock className="w-3.5 h-3.5" />
            <span className="tracking-wide">
              {isEncrypted ? 'CKKS HE' : 'PLAINTEXT'}
            </span>
          </div>

          {/* WebSocket Status */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-50 border border-slate-200 text-xs shadow-sm">
            <span
              className={`w-2 h-2 rounded-full ${
                connectionStatus.connected
                  ? connectionStatus.isMock
                    ? 'bg-amber-500 animate-pulse'
                    : 'bg-emerald-500 animate-pulse'
                  : 'bg-rose-500'
              }`}
            />
            <span className="text-slate-700 font-medium">
              {connectionStatus.connected
                ? connectionStatus.isMock
                  ? 'Standalone'
                  : 'Live gRPC / WS'
                : 'Offline'}
            </span>
          </div>

          {/* Privacy Audit Action Button */}
          {onOpenAudit && (
            <button
              onClick={onOpenAudit}
              className="px-3 py-1.5 rounded-xl bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 text-emerald-700 font-mono text-xs font-semibold flex items-center gap-1.5 transition-all shadow-sm"
            >
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              <span>AUDIT (ε, δ)</span>
            </button>
          )}

        </div>

      </div>
    </header>
  );
}
