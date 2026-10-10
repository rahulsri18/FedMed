import React from 'react';
import { motion } from 'framer-motion';
import { Building2, HardDrive, Wifi, ShieldAlert, CheckCircle2, UserX, UserCheck, Activity, Cpu } from 'lucide-react';
import { NodeTelemetry } from '../types';

interface HospitalNodeCardsProps {
  nodes: NodeTelemetry[];
  encrypted: boolean;
  onToggleDropout?: (nodeId: number) => void;
}

const HOSPITAL_PROFILES: Record<number, { name: string; location: string; specialty: string; cases: number; port: number }> = {
  1: {
    name: "St. Jude Medical Silo",
    location: "Memphis, USA",
    specialty: "Pediatric & High-Grade Glioma",
    cases: 14,
    port: 8081,
  },
  2: {
    name: "Charité Berlin Silo",
    location: "Berlin, Germany",
    specialty: "Adult Glioblastoma Multiforme",
    cases: 12,
    port: 8082,
  },
  3: {
    name: "Mayo Clinic Oncology",
    location: "Rochester, USA",
    specialty: "Low-Grade & Oligodendroglioma",
    cases: 10,
    port: 8083,
  },
};

export default function HospitalNodeCards({ nodes = [], encrypted, onToggleDropout }: HospitalNodeCardsProps) {
  return (
    <div className="space-y-3">
      {/* Deck Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-xl bg-sky-50 text-sky-600 border border-sky-200">
            <Building2 className="w-4 h-4" />
          </div>
          <h2 className="text-sm font-bold font-display uppercase tracking-wider text-slate-900">
            Hospital Silo Nodes (Flower gRPC Clients)
          </h2>
        </div>
        <span className="text-xs font-mono text-slate-500">
          Dirichlet Non-IID Partition (α=0.5)
        </span>
      </div>

      {/* 3 Hospital Cards Grid (Light Mode) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[1, 2, 3].map((nodeId) => {
          const node = nodes.find((n) => n.id === nodeId) || {
            id: nodeId,
            status: 'active',
            dice: 0.78 + nodeId * 0.02,
            upload_ms: 650 + nodeId * 50,
            bytes: encrypted ? 5242880 : 1048576,
          };

          const profile = HOSPITAL_PROFILES[nodeId];
          const isDropped = node.status === 'dropped' || node.status === 'offline';
          const dicePct = Math.min(100, Math.round(node.dice * 100));

          return (
            <motion.div
              key={nodeId}
              layout
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`glass-panel rounded-2xl p-5 border transition-all ${
                isDropped
                  ? 'border-rose-200 bg-rose-50/60 shadow-sm'
                  : 'border-slate-200 bg-white/95 shadow-sm hover:border-sky-300'
              }`}
            >
              {/* Card Header: Node ID & Live Status */}
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-bold px-2 py-0.5 rounded-md bg-sky-50 text-sky-700 border border-sky-200">
                    SILO 0{nodeId}
                  </span>
                  <span className="text-xs font-mono text-slate-400">:808{nodeId}</span>
                </div>

                <div className="flex items-center gap-1.5">
                  <span className={`w-2 h-2 rounded-full ${isDropped ? 'bg-rose-500' : 'bg-emerald-500 animate-pulse'}`} />
                  <span
                    className={`text-[10px] font-mono uppercase font-bold tracking-wider px-2 py-0.5 rounded-full ${
                      isDropped
                        ? 'bg-rose-100 text-rose-700 border border-rose-200'
                        : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                    }`}
                  >
                    {isDropped ? 'DROPPED' : 'ACTIVE'}
                  </span>
                </div>
              </div>

              {/* Hospital Profile Info */}
              <div className="mt-3">
                <h3 className="text-sm font-bold font-display text-slate-900 tracking-tight">
                  {profile.name}
                </h3>
                <p className="text-xs text-slate-500">{profile.location}</p>
                <p className="text-[11px] font-mono text-sky-700 mt-0.5">{profile.specialty}</p>
              </div>

              {/* Real-time Telemetry Metrics */}
              <div className="mt-4 space-y-2.5 pt-3 border-t border-slate-100">
                {/* Dice Score Bar */}
                <div>
                  <div className="flex items-center justify-between text-xs font-mono mb-1">
                    <span className="text-slate-500">Local Dice:</span>
                    <strong className={isDropped ? 'text-rose-600 font-bold' : 'text-emerald-700 font-bold'}>
                      {(node.dice * 100).toFixed(1)}%
                    </strong>
                  </div>
                  <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        isDropped ? 'bg-rose-500' : 'bg-emerald-500'
                      }`}
                      style={{ width: `${dicePct}%` }}
                    />
                  </div>
                </div>

                {/* Latency & Payload */}
                <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-1">
                  <div className="bg-slate-50 p-2 rounded-xl border border-slate-200">
                    <span className="text-[10px] text-slate-400 block uppercase font-semibold">Uplink Ping</span>
                    <span className="font-bold text-slate-800">{node.upload_ms}ms</span>
                  </div>
                  <div className="bg-slate-50 p-2 rounded-xl border border-slate-200">
                    <span className="text-[10px] text-slate-400 block uppercase font-semibold">Payload</span>
                    <span className="font-bold text-sky-700">
                      {(node.bytes / (1024 * 1024)).toFixed(1)} MB
                    </span>
                  </div>
                </div>
              </div>

              {/* Quick Chaos Dropout Trigger */}
              <div className="mt-4">
                <button
                  onClick={() => onToggleDropout?.(nodeId)}
                  className={`w-full py-2 px-3 rounded-xl text-xs font-mono font-semibold transition-all flex items-center justify-center gap-1.5 border shadow-sm ${
                    isDropped
                      ? 'bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border-emerald-300'
                      : 'bg-rose-50 hover:bg-rose-100 text-rose-700 border-rose-200'
                  }`}
                >
                  {isDropped ? (
                    <>
                      <UserCheck className="w-3.5 h-3.5" />
                      <span>Reconnect Silo 0{nodeId}</span>
                    </>
                  ) : (
                    <>
                      <UserX className="w-3.5 h-3.5" />
                      <span>Simulate Node Failure</span>
                    </>
                  )}
                </button>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
