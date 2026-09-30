import React from 'react';
import { Building2, Wifi, Upload, HardDrive, ShieldCheck } from 'lucide-react';

const HOSPITAL_PROFILES = {
  1: {
    name: "St. Jude Medical Silo",
    role: "Pediatric & High-Grade Glioma",
    port: 8081,
    cases: 14,
  },
  2: {
    name: "Charité Berlin Silo",
    role: "Multicentric Adult Glioblastoma",
    port: 8082,
    cases: 12,
  },
  3: {
    name: "Mayo Clinic Oncology",
    role: "Low-Grade & Oligodendroglioma",
    port: 8083,
    cases: 10,
  },
};

export default function NodeCards({ nodes = [] }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <Building2 className="w-4 h-4 text-emerald-400" />
          Cross-Silo Hospital Nodes (Flower Clients)
        </h2>
        <span className="text-xs text-gray-400">3 of 3 Nodes Synchronized</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {nodes.map((node) => {
          const profile = HOSPITAL_PROFILES[node.id] || {
            name: `Hospital Silo ${node.id}`,
            role: "Simulated Node",
            port: 8080 + node.id,
            cases: 10,
          };
          const isActive = node.status === 'active';
          const payloadMb = (node.bytes / (1024 * 1024)).toFixed(1);

          return (
            <div
              key={node.id}
              className="glass-panel glass-card-hover rounded-2xl p-4.5 border border-gray-800 relative overflow-hidden"
            >
              {/* Top Accent line */}
              <div
                className={`absolute top-0 left-0 right-0 h-1 ${
                  isActive ? 'bg-gradient-to-r from-emerald-500 to-cyan-500' : 'bg-red-500'
                }`}
              />

              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-gray-800 text-cyan-400 font-semibold">
                      Node {node.id}
                    </span>
                    <h3 className="text-sm font-bold text-white tracking-tight">
                      {profile.name}
                    </h3>
                  </div>
                  <p className="text-[11px] text-gray-400 mt-0.5">{profile.role}</p>
                </div>

                <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[11px] text-emerald-400 font-medium">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  {node.status}
                </div>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 gap-2 mt-4 pt-3 border-t border-gray-800/80">
                <div className="bg-gray-900/60 rounded-xl p-2.5 border border-gray-800/50">
                  <span className="text-[10px] uppercase tracking-wider text-gray-400 font-medium block">
                    Local Dice
                  </span>
                  <span className="text-lg font-bold text-white font-mono">
                    {node.dice?.toFixed(2) ?? '0.00'}
                  </span>
                </div>

                <div className="bg-gray-900/60 rounded-xl p-2.5 border border-gray-800/50">
                  <span className="text-[10px] uppercase tracking-wider text-gray-400 font-medium block">
                    Upload Time
                  </span>
                  <div className="flex items-baseline gap-1">
                    <span className="text-lg font-bold text-cyan-300 font-mono">
                      {node.upload_ms}
                    </span>
                    <span className="text-[10px] text-gray-500">ms</span>
                  </div>
                </div>
              </div>

              {/* Footer info */}
              <div className="mt-3 flex items-center justify-between text-[11px] text-gray-400 pt-2 border-t border-gray-800/40">
                <span className="flex items-center gap-1 font-mono">
                  <HardDrive className="w-3 h-3 text-gray-500" />
                  {payloadMb} MB (CKKS)
                </span>
                <span className="font-mono text-gray-500">
                  Aux Port: :{profile.port}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
