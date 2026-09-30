import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';
import { TrendingUp, Award } from 'lucide-react';

export default function MetricsChart({ history }) {
  return (
    <div className="glass-panel rounded-2xl p-5 border border-gray-800 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-cyan-400" />
            Global Model Convergence (BraTS 3D U-Net)
          </h2>
          <p className="text-xs text-gray-400 mt-0.5">
            Synchronized Dice Similarity Coefficient & Cross-Entropy Loss across rounds
          </p>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-1 bg-emerald-400 rounded-full inline-block"></span>
            <span className="text-gray-300">Global Dice (Target: &gt;0.85)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-1 bg-cyan-400 rounded-full inline-block"></span>
            <span className="text-gray-300">Loss</span>
          </div>
        </div>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={history} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
            <XAxis
              dataKey="round"
              stroke="#6b7280"
              fontSize={11}
              tickLine={false}
              tickFormatter={(r) => `R${r}`}
            />
            <YAxis
              stroke="#6b7280"
              fontSize={11}
              domain={[0, 1]}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#111827',
                borderColor: '#374151',
                borderRadius: '0.75rem',
                fontSize: '12px',
                boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)',
              }}
              labelFormatter={(label) => `Communication Round ${label}`}
            />
            <Line
              type="monotone"
              dataKey="dice"
              name="Dice Score"
              stroke="#34d399"
              strokeWidth={2.5}
              dot={{ r: 3, fill: '#10b981', strokeWidth: 0 }}
              activeDot={{ r: 6, fill: '#34d399' }}
            />
            <Line
              type="monotone"
              dataKey="loss"
              name="Loss"
              stroke="#38bdf8"
              strokeWidth={2}
              dot={{ r: 3, fill: '#0284c7', strokeWidth: 0 }}
              activeDot={{ r: 5, fill: '#38bdf8' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
