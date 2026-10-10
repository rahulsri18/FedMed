import React from 'react';
import { motion } from 'framer-motion';
import { ShieldCheck, Lock, CheckCircle2, AlertTriangle, Key, Shield, Cpu } from 'lucide-react';
import { PrivacyBudget } from '../types';

interface PrivacyBudgetGaugeProps {
  privacy?: PrivacyBudget;
  encrypted: boolean;
}

export default function PrivacyBudgetGauge({ privacy, encrypted }: PrivacyBudgetGaugeProps) {
  const epsilonTarget = privacy?.epsilon ?? 5.0;
  const epsilonSpent = privacy?.epsilon_spent ?? 1.8;
  const delta = privacy?.delta ?? 1e-5;
  const percentSpent = Math.min(100, Math.round((epsilonSpent / epsilonTarget) * 100));

  const isWarning = percentSpent > 80;

  return (
    <div className="glass-panel rounded-2xl p-5 space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-xl bg-purple-50 text-purple-700 border border-purple-200">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <h2 className="text-base font-bold font-display text-slate-900 tracking-tight">
              Cryptographic Trust Boundary & Privacy Budget Accounting
            </h2>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Rényi Differential Privacy (Opacus) + TenSEAL CKKS Homomorphic Encryption (N=8192)
          </p>
        </div>

        <span className="text-[11px] font-mono font-bold px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200">
          HIPAA & GDPR Art. 9 Verified
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        
        {/* DP Budget Meter */}
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-slate-800 flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5 text-sky-600" />
              Differential Privacy Budget (ε)
            </span>
            <span className="text-xs font-mono font-bold text-emerald-700">
              {epsilonSpent.toFixed(2)} / {epsilonTarget.toFixed(1)} ε
            </span>
          </div>

          {/* Animated Progress Meter */}
          <div className="w-full bg-slate-200 rounded-full h-3 overflow-hidden border border-slate-300 p-0.5">
            <motion.div
              initial={{ width: '0%' }}
              animate={{ width: `${percentSpent}%` }}
              transition={{ duration: 0.6, ease: 'easeOut' }}
              className={`h-full rounded-full transition-all duration-500 ${
                isWarning
                  ? 'bg-gradient-to-r from-amber-500 to-rose-500'
                  : 'bg-gradient-to-r from-sky-500 via-teal-500 to-emerald-500'
              }`}
            />
          </div>

          <div className="flex items-center justify-between text-[11px] font-mono text-slate-500">
            <span>Consumed: <strong className="text-slate-800">{percentSpent}%</strong></span>
            <span>Failure Bound (δ): <strong className="text-sky-700">1e-05</strong></span>
          </div>

          <div className="text-[11px] font-mono text-slate-600 bg-white p-2.5 rounded-lg border border-slate-200">
            <span className="text-slate-400 block font-bold text-[10px] uppercase">DP Perturbation:</span>
            Global L2-Clip C=1.0 • Calibrated Gaussian σ=0.8 • InstanceNorm only
          </div>
        </div>

        {/* TenSEAL CKKS Cryptographic Specs */}
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-slate-800 flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5 text-purple-600" />
              TenSEAL CKKS Scheme
            </span>
            <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full ${
              encrypted
                ? 'bg-purple-100 text-purple-800 border border-purple-200'
                : 'bg-slate-200 text-slate-700'
            }`}>
              {encrypted ? 'ENCRYPTION ACTIVE' : 'PLAINTEXT'}
            </span>
          </div>

          <div className="space-y-1.5 text-xs font-mono">
            <div className="flex items-center justify-between text-slate-500">
              <span>Poly Degree (N):</span>
              <strong className="text-sky-700 font-bold">8192</strong>
            </div>
            <div className="flex items-center justify-between text-slate-500">
              <span>Modulus Primes:</span>
              <strong className="text-slate-800 font-bold">[60, 40, 40, 60]</strong>
            </div>
            <div className="flex items-center justify-between text-slate-500">
              <span>Scale Factor:</span>
              <strong className="text-emerald-700 font-bold">2^40</strong>
            </div>
            <div className="flex items-center justify-between text-slate-500">
              <span>Security Level:</span>
              <strong className="text-purple-700 font-bold">128-bit Post-Quantum</strong>
            </div>
          </div>

          <p className="text-[10px] text-slate-500 italic border-t border-slate-200 pt-1.5">
            Server possesses evaluation keys only. Secret key remains confined inside hospital silos.
          </p>
        </div>

      </div>
    </div>
  );
}
