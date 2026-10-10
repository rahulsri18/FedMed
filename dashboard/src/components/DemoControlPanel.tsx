import React, { useState } from 'react';
import { Lock, Unlock, UserX, UserCheck, Play, ShieldAlert, Cpu, Terminal, CheckCircle2, AlertCircle } from 'lucide-react';
import { NodeTelemetry } from '../types';

interface DemoControlPanelProps {
  nodes: NodeTelemetry[];
  encrypted: boolean;
  currentRound: number;
  onDropout: (nodeId: number) => Promise<boolean>;
  onReconnect: (nodeId: number) => Promise<boolean>;
  onToggleEncryption: () => Promise<boolean>;
  onStepRound: () => Promise<boolean>;
  onTriggerAudit: () => void;
}

export default function DemoControlPanel({
  nodes,
  encrypted,
  currentRound,
  onDropout,
  onReconnect,
  onToggleEncryption,
  onStepRound,
  onTriggerAudit,
}: DemoControlPanelProps) {
  const [actionFeedback, setActionFeedback] = useState<{ text: string; type: 'success' | 'warn' } | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);

  const showFeedback = (text: string, type: 'success' | 'warn' = 'success') => {
    setActionFeedback({ text, type });
    setTimeout(() => setActionFeedback(null), 4000);
  };

  const handleToggleNode = async (node: NodeTelemetry) => {
    setIsProcessing(true);
    if (node.status === 'offline' || node.status === 'dropped') {
      const ok = await onReconnect(node.id);
      showFeedback(ok ? `Hospital Node ${node.id} reconnected to Flower consortium.` : 'Failed to reconnect node.', 'success');
    } else {
      const ok = await onDropout(node.id);
      showFeedback(ok ? `Node ${node.id} dropped out. Quorum surviving with remaining active silos.` : 'Dropout trigger failed.', 'warn');
    }
    setIsProcessing(false);
  };

  const handleToggleEnc = async () => {
    setIsProcessing(true);
    const ok = await onToggleEncryption();
    showFeedback(ok ? `Switched encryption mode to: ${!encrypted ? 'TenSEAL CKKS Homomorphic' : 'Plaintext Baseline'}` : 'Toggle failed', 'success');
    setIsProcessing(false);
  };

  const handleStep = async () => {
    setIsProcessing(true);
    const ok = await onStepRound();
    showFeedback(ok ? `Advanced federated training to Round ${currentRound + 1}` : 'Step round failed', 'success');
    setIsProcessing(false);
  };

  return (
    <div className="glass-panel rounded-2xl p-5 space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-xl bg-sky-50 text-sky-600 border border-sky-200">
              <Terminal className="w-4 h-4" />
            </div>
            <h2 className="text-base font-bold font-display text-slate-900 tracking-tight">
              Interactive Consortium Chaos & Control Deck
            </h2>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Simulate real-world mid-round dropouts, toggle homomorphic encryption, and audit privacy bounds
          </p>
        </div>

        <span className="text-xs font-mono text-sky-700 font-bold px-2.5 py-1 rounded-lg bg-sky-50 border border-sky-200">
          Live gRPC Telemetry
        </span>
      </div>

      {/* Action Feedback Banner */}
      {actionFeedback && (
        <div className={`p-3 rounded-xl border text-xs font-mono flex items-center gap-2.5 transition-all shadow-sm ${
          actionFeedback.type === 'warn'
            ? 'bg-amber-50 border-amber-300 text-amber-900'
            : 'bg-emerald-50 border-emerald-300 text-emerald-900'
        }`}>
          {actionFeedback.type === 'warn' ? (
            <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0" />
          ) : (
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          )}
          <span>{actionFeedback.text}</span>
        </div>
      )}

      {/* Control Actions Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        
        {/* Toggle Encryption */}
        <button
          onClick={handleToggleEnc}
          disabled={isProcessing}
          className={`p-3.5 rounded-xl border font-mono text-xs font-semibold flex flex-col items-start justify-between gap-2 transition-all shadow-sm ${
            encrypted
              ? 'bg-purple-50 hover:bg-purple-100 border-purple-200 text-purple-900'
              : 'bg-slate-50 hover:bg-slate-100 border-slate-200 text-slate-700'
          }`}
        >
          <div className="flex items-center justify-between w-full">
            <span className="text-[10px] text-slate-500 uppercase tracking-wider font-bold">Privacy Engine</span>
            {encrypted ? <Lock className="w-4 h-4 text-purple-600" /> : <Unlock className="w-4 h-4 text-amber-600" />}
          </div>
          <div>
            <div className="font-bold text-slate-900 text-sm">
              {encrypted ? 'CKKS Encrypted' : 'Plaintext Mode'}
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">
              {encrypted ? 'TenSEAL homomorphic vectors' : 'NumPy array weights'}
            </div>
          </div>
        </button>

        {/* Step FL Round */}
        <button
          onClick={handleStep}
          disabled={isProcessing}
          className="p-3.5 rounded-xl border border-sky-300 hover:border-sky-400 bg-sky-50 hover:bg-sky-100 text-sky-900 font-mono text-xs font-semibold flex flex-col items-start justify-between gap-2 transition-all group shadow-sm"
        >
          <div className="flex items-center justify-between w-full">
            <span className="text-[10px] text-sky-600 uppercase tracking-wider font-bold">Orchestrator</span>
            <Play className="w-4 h-4 text-sky-600 group-hover:translate-x-0.5 transition-transform" />
          </div>
          <div>
            <div className="font-bold text-slate-900 text-sm">
              Advance FL Round
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">
              Step aggregation & evaluation
            </div>
          </div>
        </button>

        {/* Audit Privacy */}
        <button
          onClick={onTriggerAudit}
          className="p-3.5 rounded-xl border border-emerald-300 hover:border-emerald-400 bg-emerald-50 hover:bg-emerald-100 text-emerald-900 font-mono text-xs font-semibold flex flex-col items-start justify-between gap-2 transition-all shadow-sm"
        >
          <div className="flex items-center justify-between w-full">
            <span className="text-[10px] text-emerald-600 uppercase tracking-wider font-bold">Verification</span>
            <ShieldAlert className="w-4 h-4 text-emerald-600" />
          </div>
          <div>
            <div className="font-bold text-slate-900 text-sm">
              Audit Privacy (ε, δ)
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">
              RDP accountant & HIPAA report
            </div>
          </div>
        </button>

      </div>

      {/* Mid-Round Chaos Dropouts */}
      <div className="pt-2">
        <label className="text-[11px] font-mono uppercase tracking-wider text-slate-500 font-bold block mb-2">
          Mid-Round Dropout Simulator (Quorum: min 2 of 3)
        </label>
        <div className="grid grid-cols-3 gap-2">
          {[1, 2, 3].map((nodeId) => {
            const node = nodes.find((n) => n.id === nodeId);
            const isDropped = node?.status === 'dropped' || node?.status === 'offline';

            return (
              <button
                key={nodeId}
                onClick={() => node && handleToggleNode(node)}
                disabled={isProcessing}
                className={`py-2 px-3 rounded-xl text-xs font-mono font-semibold border flex items-center justify-between transition-all shadow-sm ${
                  isDropped
                    ? 'bg-rose-50 border-rose-300 text-rose-800'
                    : 'bg-white hover:bg-slate-50 border-slate-200 text-slate-700'
                }`}
              >
                <span>Node 0{nodeId}</span>
                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                  isDropped ? 'bg-rose-100 text-rose-700' : 'bg-emerald-100 text-emerald-800'
                }`}>
                  {isDropped ? 'DROPPED' : 'ONLINE'}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
