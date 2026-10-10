import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
} from 'recharts';
import { TrendingUp, Award, Activity, Target } from 'lucide-react';
import { ConvergenceRecord } from '../types';

interface ConvergenceChartProps {
  history: ConvergenceRecord[];
}

export default function ConvergenceChart({ history }: ConvergenceChartProps) {
  const latest = history[history.length - 1] || { round: 1, dice: 0.75, loss: 0.35 };
  const peakDice = history.reduce((max, h) => Math.max(max, h.dice), 0);

  return (
    <div className="glass-panel rounded-2xl p-5 space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-xl bg-emerald-50 text-emerald-600 border border-emerald-200">
              <TrendingUp className="w-4 h-4" />
            </div>
            <h2 className="text-base font-bold font-display text-slate-900 tracking-tight">
              Federated Convergence Telemetry (3D U-Net)
            </h2>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Synchronized Dice Similarity Coefficient & Cross-Entropy Loss across rounds
          </p>
        </div>

        {/* Badges */}
        <div className="flex items-center gap-2.5 text-xs font-mono">
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 shadow-sm">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span>Peak Dice: <strong className="text-slate-900 font-bold">{(peakDice * 100).toFixed(1)}%</strong></span>
          </div>

          <div className="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-sky-50 border border-sky-200 text-sky-800 shadow-sm">
            <span className="w-2 h-2 rounded-full bg-sky-500" />
            <span>Loss: <strong className="text-slate-900 font-bold">{latest.loss.toFixed(4)}</strong></span>
          </div>
        </div>
      </div>

      {/* Area / Line Chart with Soft Light Gradients */}
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={history} margin={{ top: 12, right: 16, left: -22, bottom: 0 }}>
            <defs>
              <linearGradient id="diceGlow" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#059669" stopOpacity={0.18} />
                <stop offset="95%" stopColor="#059669" stopOpacity={0.0} />
              </linearGradient>
              <linearGradient id="lossGlow" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0284c7" stopOpacity={0.15} />
                <stop offset="95%" stopColor="#0284c7" stopOpacity={0.0} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            
            <XAxis
              dataKey="round"
              stroke="#64748b"
              fontSize={11}
              fontFamily="JetBrains Mono"
              tickLine={false}
              tickFormatter={(r) => `R0${r}`}
            />
            
            <YAxis
              stroke="#64748b"
              fontSize={11}
              fontFamily="JetBrains Mono"
              domain={[0, 1.0]}
              tickLine={false}
              ticks={[0.2, 0.4, 0.6, 0.8, 1.0]}
            />

            {/* Clinical Target Benchmark Reference Line at 0.85 */}
            <ReferenceLine
              y={0.85}
              stroke="#d97706"
              strokeDasharray="4 4"
              strokeWidth={1.5}
              label={{
                value: 'Clinical Target (Dice ≥ 0.85)',
                position: 'insideTopRight',
                fill: '#d97706',
                fontSize: 10,
                fontFamily: 'JetBrains Mono',
              }}
            />

            <Tooltip
              content={({ active, payload, label }) => {
                if (active && payload && payload.length) {
                  const diceVal = payload.find((p) => p.dataKey === 'dice')?.value as number;
                  const lossVal = payload.find((p) => p.dataKey === 'loss')?.value as number;
                  const targetMet = diceVal >= 0.85;

                  return (
                    <div className="bg-white/95 border border-slate-200 p-3 rounded-xl shadow-xl backdrop-blur-md text-xs font-mono min-w-[210px]">
                      <div className="text-slate-500 font-bold border-b border-slate-100 pb-1.5 mb-2 flex items-center justify-between">
                        <span>Communication Round {label}</span>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${targetMet ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'}`}>
                          {targetMet ? 'TARGET MET' : 'CONVERGING'}
                        </span>
                      </div>
                      <div className="space-y-1.5">
                        <div className="flex items-center justify-between text-emerald-700">
                          <span>Global Dice Score:</span>
                          <span className="font-bold">{(diceVal * 100).toFixed(2)}%</span>
                        </div>
                        <div className="flex items-center justify-between text-sky-700">
                          <span>Cross-Entropy Loss:</span>
                          <span className="font-bold">{lossVal?.toFixed(4)}</span>
                        </div>
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />

            {/* Global Dice Area & Line */}
            <Area
              type="monotone"
              dataKey="dice"
              stroke="#059669"
              strokeWidth={2.5}
              fill="url(#diceGlow)"
              activeDot={{ r: 6, fill: '#059669', stroke: '#ffffff', strokeWidth: 2 }}
            />

            {/* Loss Area & Line */}
            <Area
              type="monotone"
              dataKey="loss"
              stroke="#0284c7"
              strokeWidth={2}
              fill="url(#lossGlow)"
              activeDot={{ r: 5, fill: '#0284c7' }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
