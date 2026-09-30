import React, { useState, useEffect, useRef } from 'react';
import { Eye, Layers, Sliders, Maximize2, RefreshCw } from 'lucide-react';

export default function CanvasMRIViewer() {
  const canvasRef = useRef(null);
  const [sliceIndex, setSliceIndex] = useState(32);
  const [axis, setAxis] = useState('axial'); // axial, sagittal, coronal
  const [modality, setModality] = useState('FLAIR');
  const [maskOpacity, setMaskOpacity] = useState(0.7);
  
  // Segmentation region toggles
  const [showWT, setShowWT] = useState(true); // Whole Tumor (Green)
  const [showTC, setShowTC] = useState(true); // Tumor Core (Yellow)
  const [showET, setShowET] = useState(true); // Enhancing Tumor (Red)

  // Draw MRI slice and tumor segmentation mask onto HTML5 Canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;

    // Clear background
    ctx.fillStyle = '#05070f';
    ctx.fillRect(0, 0, width, height);

    const centerX = width / 2;
    const centerY = height / 2;
    
    // Scale brain size according to slice position (curved sphere volume)
    const normalizedPos = Math.abs(sliceIndex - 32) / 32; // 0 at center, 1 at poles
    const sliceFactor = Math.sqrt(Math.max(0.1, 1 - normalizedPos * normalizedPos));
    const brainRadiusX = (width * 0.38) * sliceFactor;
    const brainRadiusY = (height * 0.42) * sliceFactor;

    if (brainRadiusX > 10) {
      // 1. Draw Simulated Brain Phantom Tissue
      const grad = ctx.createRadialGradient(
        centerX, centerY, 10,
        centerX, centerY, brainRadiusX
      );

      // Contrast adjustments based on modality
      if (modality === 'FLAIR') {
        grad.addColorStop(0, '#3a3a44');
        grad.addColorStop(0.7, '#2f2f38');
        grad.addColorStop(1.0, '#1a1a22');
      } else if (modality === 'T1ce') {
        grad.addColorStop(0, '#555562');
        grad.addColorStop(0.7, '#42424e');
        grad.addColorStop(1.0, '#1c1c24');
      } else if (modality === 'T2') {
        grad.addColorStop(0, '#4a4a58');
        grad.addColorStop(0.8, '#626274');
        grad.addColorStop(1.0, '#1f1f2a');
      } else {
        // T1
        grad.addColorStop(0, '#444450');
        grad.addColorStop(0.8, '#363640');
        grad.addColorStop(1.0, '#181820');
      }

      ctx.beginPath();
      ctx.ellipse(centerX, centerY, brainRadiusX, brainRadiusY, 0, 0, Math.PI * 2);
      ctx.fillStyle = grad;
      ctx.fill();

      // Brain cortex edge glow / skull boundary
      ctx.strokeStyle = '#2d3748';
      ctx.lineWidth = 3;
      ctx.stroke();

      // Ventricles (simulated fluid cavities)
      if (sliceFactor > 0.4) {
        ctx.fillStyle = '#070913';
        ctx.beginPath();
        // Left ventricle
        ctx.ellipse(centerX - 18, centerY - 6, 8 * sliceFactor, 22 * sliceFactor, -0.15, 0, Math.PI * 2);
        // Right ventricle
        ctx.ellipse(centerX + 18, centerY - 6, 8 * sliceFactor, 22 * sliceFactor, 0.15, 0, Math.PI * 2);
        ctx.fill();
      }

      // 2. Draw Multi-Region Tumor Segmentation Mask
      // Only visible in slices 18 to 46 (where tumor is located)
      if (sliceIndex >= 18 && sliceIndex <= 46) {
        const tumorSliceWeight = 1 - Math.abs(sliceIndex - 32) / 14;
        const tumorBaseX = centerX + 45;
        const tumorBaseY = centerY - 35;
        const baseRadius = 38 * tumorSliceWeight;

        ctx.save();
        ctx.globalAlpha = maskOpacity;

        // Whole Tumor (WT) - Green (#22c55e)
        if (showWT && baseRadius > 5) {
          ctx.beginPath();
          ctx.ellipse(tumorBaseX, tumorBaseY, baseRadius, baseRadius * 0.85, 0.3, 0, Math.PI * 2);
          ctx.fillStyle = 'rgba(34, 197, 94, 0.65)';
          ctx.fill();
          ctx.strokeStyle = '#22c55e';
          ctx.lineWidth = 1.5;
          ctx.stroke();
        }

        // Tumor Core (TC) - Yellow (#eab308)
        if (showTC && baseRadius * 0.65 > 4) {
          ctx.beginPath();
          ctx.ellipse(tumorBaseX - 3, tumorBaseY + 2, baseRadius * 0.65, baseRadius * 0.55, 0.2, 0, Math.PI * 2);
          ctx.fillStyle = 'rgba(234, 179, 8, 0.75)';
          ctx.fill();
          ctx.strokeStyle = '#eab308';
          ctx.lineWidth = 1.5;
          ctx.stroke();
        }

        // Enhancing Tumor (ET) - Red (#ef4444)
        if (showET && baseRadius * 0.35 > 2) {
          ctx.beginPath();
          ctx.ellipse(tumorBaseX + 4, tumorBaseY - 3, baseRadius * 0.35, baseRadius * 0.3, 0.4, 0, Math.PI * 2);
          ctx.fillStyle = 'rgba(239, 68, 68, 0.85)';
          ctx.fill();
          ctx.strokeStyle = '#ef4444';
          ctx.lineWidth = 1.5;
          ctx.stroke();
        }

        ctx.restore();
      }
    }

    // Grid crosshairs and medical orientation labels
    ctx.fillStyle = '#64748b';
    ctx.font = '10px monospace';
    ctx.fillText('A (Anterior)', centerX - 30, 18);
    ctx.fillText('P (Posterior)', centerX - 30, height - 10);
    ctx.fillText('R', 12, centerY + 4);
    ctx.fillText('L', width - 20, centerY + 4);
    ctx.fillText(`Slice: ${sliceIndex}/64 [${axis.toUpperCase()}]`, 12, height - 10);
  }, [sliceIndex, axis, modality, maskOpacity, showWT, showTC, showET]);

  return (
    <div className="glass-panel rounded-2xl p-5 border border-gray-800 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <Eye className="w-4 h-4 text-cyan-400" />
            Interactive 3D BraTS Volume & Tumor Mask Viewer
          </h2>
          <p className="text-xs text-gray-400 mt-0.5">
            HTML5 Canvas rendering synchronized with local hospital predictions
          </p>
        </div>

        {/* View Plane Selector */}
        <div className="flex items-center bg-gray-900 rounded-lg p-1 border border-gray-800 text-xs">
          {['axial', 'sagittal', 'coronal'].map((plane) => (
            <button
              key={plane}
              onClick={() => setAxis(plane)}
              className={`px-2.5 py-1 rounded-md capitalize font-medium transition-all ${
                axis === plane
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              {plane}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Canvas Display Viewport */}
        <div className="lg:col-span-7 flex flex-col items-center justify-center bg-black/60 rounded-xl p-3 border border-gray-800/80">
          <canvas
            ref={canvasRef}
            width={340}
            height={340}
            className="rounded-lg shadow-2xl border border-gray-800 max-w-full h-auto"
          />

          {/* Slice Navigation Slider */}
          <div className="w-full max-w-xs mt-4 flex items-center gap-3">
            <span className="text-xs font-mono text-gray-400 w-12">Z: {sliceIndex}</span>
            <input
              type="range"
              min={1}
              max={64}
              value={sliceIndex}
              onChange={(e) => setSliceIndex(Number(e.target.value))}
              className="w-full accent-cyan-400 h-1.5 bg-gray-800 rounded-lg cursor-pointer"
            />
            <span className="text-xs font-mono text-gray-400">/64</span>
          </div>
        </div>

        {/* Controls and Segmentation Layer Toggles */}
        <div className="lg:col-span-5 flex flex-col justify-between space-y-4">
          
          {/* Modality Selector */}
          <div>
            <label className="text-xs uppercase tracking-wider font-semibold text-gray-400 mb-2 block">
              MRI Acquisition Modality
            </label>
            <div className="grid grid-cols-2 gap-2">
              {['FLAIR', 'T1ce', 'T2', 'T1'].map((m) => (
                <button
                  key={m}
                  onClick={() => setModality(m)}
                  className={`py-1.5 px-3 rounded-xl text-xs font-mono font-medium border text-center transition-all ${
                    modality === m
                      ? 'bg-cyan-500/10 border-cyan-500/50 text-cyan-300 shadow-sm'
                      : 'bg-gray-900/60 border-gray-800 text-gray-400 hover:border-gray-700'
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>

          {/* Sub-Region Mask Toggles */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs uppercase tracking-wider font-semibold text-gray-400">
                Predicted Tumor Sub-Regions
              </label>
              <span className="text-[11px] text-gray-500">BraTS 2021 Multi-Class</span>
            </div>

            <div className="space-y-2">
              {/* WT */}
              <button
                onClick={() => setShowWT(!showWT)}
                className={`w-full flex items-center justify-between p-2.5 rounded-xl border text-xs transition-all ${
                  showWT
                    ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-300'
                    : 'bg-gray-900/40 border-gray-800 text-gray-500'
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500/50"></span>
                  <span className="font-semibold">Whole Tumor (WT)</span>
                </div>
                <span className="font-mono text-[11px]">Dice: 0.88</span>
              </button>

              {/* TC */}
              <button
                onClick={() => setShowTC(!showTC)}
                className={`w-full flex items-center justify-between p-2.5 rounded-xl border text-xs transition-all ${
                  showTC
                    ? 'bg-yellow-500/10 border-yellow-500/40 text-yellow-300'
                    : 'bg-gray-900/40 border-gray-800 text-gray-500'
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-yellow-400 shadow-sm shadow-yellow-400/50"></span>
                  <span className="font-semibold">Tumor Core (TC)</span>
                </div>
                <span className="font-mono text-[11px]">Dice: 0.82</span>
              </button>

              {/* ET */}
              <button
                onClick={() => setShowET(!showET)}
                className={`w-full flex items-center justify-between p-2.5 rounded-xl border text-xs transition-all ${
                  showET
                    ? 'bg-red-500/10 border-red-500/40 text-red-300'
                    : 'bg-gray-900/40 border-gray-800 text-gray-500'
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-red-500 shadow-sm shadow-red-500/50"></span>
                  <span className="font-semibold">Enhancing Tumor (ET)</span>
                </div>
                <span className="font-mono text-[11px]">Dice: 0.79</span>
              </button>
            </div>
          </div>

          {/* Mask Opacity Slider */}
          <div className="bg-gray-900/60 rounded-xl p-3 border border-gray-800/80">
            <div className="flex items-center justify-between text-xs mb-1.5">
              <span className="text-gray-400 flex items-center gap-1.5">
                <Sliders className="w-3 h-3 text-cyan-400" />
                Overlay Opacity
              </span>
              <span className="font-mono text-gray-300">{Math.round(maskOpacity * 100)}%</span>
            </div>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={maskOpacity}
              onChange={(e) => setMaskOpacity(Number(e.target.value))}
              className="w-full accent-emerald-400 h-1.5 bg-gray-800 rounded-lg cursor-pointer"
            />
          </div>

        </div>
      </div>
    </div>
  );
}
