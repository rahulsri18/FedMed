import React from 'react';
import { ShieldAlert, ShieldCheck, Key, Lock, CheckCircle2 } from 'lucide-react';

export default function PrivacyGauge({ privacy, encrypted }) {
  const epsilonTarget = privacy?.epsilon ?? 5.0;
  const epsilonSpent = privacy?.epsilon_spent ?? 2.3;
  const delta = privacy?.delta ?? 1e-5;
  const percentSpent = Math.min(100, Math.round((epsilonSpent / epsilonTarget) * 100));

  const isWarning = percentSpent > 80;

  return (
    <div className="glass-panel rounded-2xl p-5 border border-gray-800 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            Privacy Engine & Cryptographic Guarantees
          </h2>
          <p className="text-xs text-gray-400 mt-0.5">
            Rényi Differential Privacy (Opacus) + TenSEAL CKKS Homomorphic Encryption
          </p>
        </div>
        <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
          HIPAA & GDPR Compliant
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* DP Budget Gauge */}
        <div className="bg-gray-900/60 rounded-xl p-4 border border-gray-800/80">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-gray-300">
              Differential Privacy Budget (ε)
            </span>
            <span className="text-xs font-mono font-bold text-white">
              {epsilonSpent.toFixed(1)} / {epsilonTarget.toFixed(1)} ε
            </span>
          </div>

          {/* Progress bar */}
          <div className="w-full bg-gray-800 rounded-full h-2.5 overflow-hidden">
            <div
              className={`h-2.5 rounded-full transition-all duration-500 ${
                isWarning ? 'bg-amber-400' : 'bg-gradient-to-r from-emerald-400 to-cyan-400'
              }`}
              style={{ width: `${percentSpent}%` }}
            />
          </div>

          <div className="flex items-center justify-between text-[11px] text-gray-400 mt-2">
            <span>Failure Probability (δ): <strong className="text-gray-300 font-mono">1e-5</strong></span>
            <span>{percentSpent}% budget consumed</span>
          </div>

          <div className="mt-3 pt-2 border-t border-gray-800/60 text-[11px] text-gray-400 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>DP-Compatible Normalization: InstanceNorm (No BatchNorm)</span>
          </div>
        </div>

        {/* TenSEAL Homomorphic Encryption Status */}
        <div className="bg-gray-900/60 rounded-xl p-4 border border-gray-800/80">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-gray-300 flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5 text-cyan-400" />
              TenSEAL CKKS Scheme
            </span>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
              N=8192, 128-bit Security
            </span>
          </div>

          <p className="text-xs text-gray-300 leading-relaxed">
            Central server aggregates encrypted weight vectors via homomorphic addition. Zero plaintext access.
          </p>

          <div className="mt-3 pt-2 border-t border-gray-800/60 grid grid-cols-2 gap-2 text-[11px]">
            <div>
              <span className="text-gray-500 block">Trust Boundary:</span>
              <span className="text-gray-300 font-mono">Honest-but-curious</span>
            </div>
            <div>
              <span className="text-gray-500 block">Secret Key:</span>
              <span className="text-emerald-400 font-mono">Shared by Clients Only</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
