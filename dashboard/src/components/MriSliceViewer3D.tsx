import React, { useState, useEffect, useRef } from 'react';
import { Eye, Layers, Sliders, ChevronLeft, ChevronRight, Maximize2, ShieldCheck, Crosshair, Sparkles, Activity } from 'lucide-react';
import { FedMedService } from '../services/apiService';
import { ScanMetadata } from '../types';

interface MriSliceViewer3DProps {
  activeScan: ScanMetadata;
  availableScans: ScanMetadata[];
  onSelectScan: (scanId: string) => void;
}

export default function MriSliceViewer3D({
  activeScan,
  availableScans,
  onSelectScan,
}: MriSliceViewer3DProps) {
  const [sliceIndex, setSliceIndex] = useState<number>(32);
  const [axis, setAxis] = useState<'axial' | 'sagittal' | 'coronal'>('axial');
  const [modality, setModality] = useState<string>('FLAIR');
  const [blendOpacity, setBlendOpacity] = useState<number>(0.75);
  const [windowLevel, setWindowLevel] = useState<number>(0.5);
  const [windowWidth, setWindowWidth] = useState<number>(1.0);

  // Sub-region toggles
  const [showWT, setShowWT] = useState<boolean>(true); // Whole Tumor (Bio-Emerald)
  const [showTC, setShowTC] = useState<boolean>(true); // Tumor Core (Amber)
  const [showET, setShowET] = useState<boolean>(true); // Enhancing Tumor (Coral)

  // Hover voxel inspection
  const [hoverCoord, setHoverCoord] = useState<{ x: number; y: number; val: number } | null>(null);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rawImgRef = useRef<HTMLImageElement | null>(null);
  const maskImgRef = useRef<HTMLImageElement | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Construct URLs
  const rawSliceUrl = FedMedService.getSliceUrl(
    activeScan.id,
    axis,
    sliceIndex,
    modality,
    windowLevel,
    windowWidth
  );

  const maskSliceUrl = FedMedService.getMaskUrl(
    activeScan.id,
    axis,
    sliceIndex,
    showWT,
    showTC,
    showET,
    blendOpacity
  );

  // Load and composite onto HTML5 Canvas
  useEffect(() => {
    let isCancelled = false;
    setIsLoading(true);

    const rawImg = new Image();
    const maskImg = new Image();

    let loadedCount = 0;
    const checkDraw = () => {
      loadedCount++;
      if (loadedCount >= 2 && !isCancelled) {
        setIsLoading(false);
        drawComposite(rawImg, maskImg);
      }
    };

    rawImg.crossOrigin = 'anonymous';
    maskImg.crossOrigin = 'anonymous';

    rawImg.onload = checkDraw;
    rawImg.onerror = () => {
      loadedCount++;
      if (loadedCount >= 2 && !isCancelled) {
        setIsLoading(false);
        drawFallback();
      }
    };

    maskImg.onload = checkDraw;
    maskImg.onerror = () => {
      loadedCount++;
      if (loadedCount >= 2 && !isCancelled) {
        setIsLoading(false);
        drawFallback();
      }
    };

    rawImg.src = rawSliceUrl;
    maskImg.src = maskSliceUrl;

    rawImgRef.current = rawImg;
    maskImgRef.current = maskImg;

    return () => {
      isCancelled = true;
    };
  }, [rawSliceUrl, maskSliceUrl]);

  const drawComposite = (raw: HTMLImageElement, mask: HTMLImageElement) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.imageSmoothingEnabled = false;

    // Draw raw MRI scan slice
    ctx.drawImage(raw, 0, 0, canvas.width, canvas.height);

    // Composite segmentation mask with blend opacity
    if (blendOpacity > 0.05) {
      ctx.globalAlpha = blendOpacity;
      ctx.drawImage(mask, 0, 0, canvas.width, canvas.height);
      ctx.globalAlpha = 1.0;
    }
  };

  const drawFallback = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.fillStyle = '#050a16';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    const rx = canvas.width * 0.38;
    const ry = canvas.height * 0.44;

    const grad = ctx.createRadialGradient(cx, cy, 10, cx, cy, rx);
    grad.addColorStop(0, '#475569');
    grad.addColorStop(0.7, '#1e293b');
    grad.addColorStop(1, '#090d16');

    ctx.beginPath();
    ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
    ctx.fillStyle = grad;
    ctx.fill();
    ctx.strokeStyle = '#64748b';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    if (showWT) {
      ctx.beginPath();
      ctx.arc(cx + 25, cy - 20, 32, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(5, 150, 105, 0.5)';
      ctx.fill();
    }
    if (showTC) {
      ctx.beginPath();
      ctx.arc(cx + 25, cy - 20, 20, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(217, 119, 6, 0.7)';
      ctx.fill();
    }
    if (showET) {
      ctx.beginPath();
      ctx.arc(cx + 25, cy - 20, 10, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(225, 29, 72, 0.85)';
      ctx.fill();
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = Math.floor(((e.clientX - rect.left) / rect.width) * canvas.width);
    const y = Math.floor(((e.clientY - rect.top) / rect.height) * canvas.height);

    const ctx = canvas.getContext('2d');
    if (ctx && x >= 0 && x < canvas.width && y >= 0 && y < canvas.height) {
      try {
        const pixel = ctx.getImageData(x, y, 1, 1).data;
        const brightness = Math.round((pixel[0] + pixel[1] + pixel[2]) / 3);
        setHoverCoord({ x, y, val: brightness });
      } catch (_) {
        setHoverCoord({ x, y, val: 0 });
      }
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-5 space-y-5">
      {/* Header & Anatomical Plane Tabs (Light Theme) */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-xl bg-sky-50 text-sky-600 border border-sky-200">
              <Eye className="w-4 h-4" />
            </div>
            <h2 className="text-base font-bold font-display text-slate-900 tracking-tight">
              3D BraTS Volumetric PACS Viewer
            </h2>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">
              LIVE REST
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Orthogonal multi-channel MRI slices with synchronized federated tumor masks
          </p>
        </div>

        {/* Anatomical Plane Buttons */}
        <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs font-mono">
          {(['axial', 'sagittal', 'coronal'] as const).map((plane) => (
            <button
              key={plane}
              onClick={() => setAxis(plane)}
              className={`px-3 py-1.5 rounded-lg capitalize font-bold transition-all ${
                axis === plane
                  ? 'bg-white text-sky-700 shadow-sm border border-slate-200'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {plane}
            </button>
          ))}
        </div>
      </div>

      {/* Main 2-Column Viewer Layout */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-5 items-center">
        
        {/* Left: Slice Viewport */}
        <div className="md:col-span-6 flex flex-col items-center justify-center bg-slate-100 rounded-2xl p-4 border border-slate-200 relative shadow-inner">
          
          {/* Viewport Top Bar */}
          <div className="w-full flex items-center justify-between text-xs font-mono text-slate-600 mb-2.5 px-1">
            <span className="text-sky-700 font-bold uppercase tracking-wider flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-sky-600 animate-pulse" />
              {axis} VIEW • {modality}
            </span>
            <span className="text-slate-600 font-medium">
              {hoverCoord ? (
                <span className="text-emerald-700 font-bold">
                  VOXEL ({hoverCoord.x}, {hoverCoord.y}) | VAL {hoverCoord.val}
                </span>
              ) : (
                `SLICE ${sliceIndex}/64`
              )}
            </span>
          </div>

          {/* Canvas Display in Radiology Bezel */}
          <div className="relative group cursor-crosshair rounded-xl overflow-hidden border border-slate-300 shadow-md bg-black">
            <canvas
              ref={canvasRef}
              width={256}
              height={256}
              onMouseMove={handleMouseMove}
              onMouseLeave={() => setHoverCoord(null)}
              className="w-[280px] h-[280px] max-w-full object-contain block"
            />

            {/* Subtle Crosshair Center Mark */}
            <div className="absolute inset-0 pointer-events-none opacity-20 group-hover:opacity-40 transition-opacity">
              <div className="absolute top-1/2 left-0 right-0 h-px bg-cyan-400" />
              <div className="absolute top-0 bottom-0 left-1/2 w-px bg-cyan-400" />
            </div>

            {/* Loading indicator */}
            {isLoading && (
              <div className="absolute top-2 right-2 bg-black/75 px-2 py-0.5 rounded text-[10px] font-mono text-cyan-300 animate-pulse border border-cyan-500/40">
                STREAMING...
              </div>
            )}
          </div>

          {/* Slice Navigation Controls */}
          <div className="w-full max-w-xs mt-4 flex items-center gap-2">
            <button
              onClick={() => setSliceIndex((s) => Math.max(1, s - 5))}
              className="px-2 py-1 rounded-lg bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 text-[11px] font-mono shadow-sm"
              title="Jump -5"
            >
              -5
            </button>
            <button
              onClick={() => setSliceIndex((s) => Math.max(1, s - 1))}
              className="p-1.5 rounded-lg bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 shadow-sm"
              title="Previous slice"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>

            <span className="text-xs font-mono text-sky-700 w-10 text-right font-bold">
              #{sliceIndex}
            </span>

            <input
              type="range"
              min={1}
              max={64}
              value={sliceIndex}
              onChange={(e) => setSliceIndex(Number(e.target.value))}
              className="w-full accent-sky-600 h-1.5 bg-slate-200 rounded-lg cursor-pointer"
            />

            <span className="text-xs font-mono text-slate-400">/64</span>

            <button
              onClick={() => setSliceIndex((s) => Math.min(64, s + 1))}
              className="p-1.5 rounded-lg bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 shadow-sm"
              title="Next slice"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => setSliceIndex((s) => Math.min(64, s + 5))}
              className="px-2 py-1 rounded-lg bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 text-[11px] font-mono shadow-sm"
              title="Jump +5"
            >
              +5
            </button>
          </div>
        </div>

        {/* Right: Modality & Mask Controls */}
        <div className="md:col-span-6 space-y-4">
          
          {/* Active Patient Scan Selector */}
          <div>
            <label className="text-[11px] font-mono uppercase tracking-wider text-slate-500 font-bold block mb-1.5">
              Active Patient Scan Cohort
            </label>
            <select
              value={activeScan.id}
              onChange={(e) => onSelectScan(e.target.value)}
              className="w-full bg-white border border-slate-200 rounded-xl px-3 py-2 text-xs font-mono text-slate-800 focus:outline-none focus:border-sky-500 transition-all cursor-pointer shadow-sm"
            >
              {availableScans.map((scan) => (
                <option key={scan.id} value={scan.id}>
                  {scan.id}: {scan.name}
                </option>
              ))}
            </select>
            <div className="mt-1 flex items-center justify-between text-[11px] text-slate-500">
              <span className="italic">{activeScan.diagnosis || 'Glioblastoma Multiforme'}</span>
              <span className="font-mono text-sky-700 font-bold">Vol: {activeScan.tumor_volume_cm3 ?? 18.4} cm³</span>
            </div>
          </div>

          {/* MRI Acquisition Modalities */}
          <div>
            <label className="text-[11px] font-mono uppercase tracking-wider text-slate-500 font-bold block mb-1.5">
              MRI Channel Modality
            </label>
            <div className="grid grid-cols-4 gap-2">
              {['FLAIR', 'T1ce', 'T2', 'T1'].map((m) => (
                <button
                  key={m}
                  onClick={() => setModality(m)}
                  className={`py-1.5 rounded-xl text-xs font-mono font-bold border transition-all text-center shadow-sm ${
                    modality === m
                      ? 'bg-sky-50 border-sky-400 text-sky-700 shadow-sm'
                      : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>

          {/* Multi-Region Segmentation Sub-Class Toggles */}
          <div>
            <label className="text-[11px] font-mono uppercase tracking-wider text-slate-500 font-bold block mb-1.5">
              Tumor Sub-Region Masks
            </label>
            <div className="grid grid-cols-3 gap-2">
              {/* Whole Tumor (WT) */}
              <button
                onClick={() => setShowWT((prev) => !prev)}
                className={`px-2.5 py-1.5 rounded-xl text-xs font-mono font-semibold border flex items-center justify-between transition-all shadow-sm ${
                  showWT
                    ? 'bg-emerald-50 border-emerald-300 text-emerald-800'
                    : 'bg-white border-slate-200 text-slate-400'
                }`}
              >
                <div className="flex items-center gap-1.5">
                  <span className={`w-2 h-2 rounded-full ${showWT ? 'bg-emerald-500' : 'bg-slate-300'}`} />
                  <span>WT</span>
                </div>
                <span className="text-[10px] font-bold">{showWT ? 'ON' : 'OFF'}</span>
              </button>

              {/* Tumor Core (TC) */}
              <button
                onClick={() => setShowTC((prev) => !prev)}
                className={`px-2.5 py-1.5 rounded-xl text-xs font-mono font-semibold border flex items-center justify-between transition-all shadow-sm ${
                  showTC
                    ? 'bg-amber-50 border-amber-300 text-amber-800'
                    : 'bg-white border-slate-200 text-slate-400'
                }`}
              >
                <div className="flex items-center gap-1.5">
                  <span className={`w-2 h-2 rounded-full ${showTC ? 'bg-amber-500' : 'bg-slate-300'}`} />
                  <span>TC</span>
                </div>
                <span className="text-[10px] font-bold">{showTC ? 'ON' : 'OFF'}</span>
              </button>

              {/* Enhancing Tumor (ET) */}
              <button
                onClick={() => setShowET((prev) => !prev)}
                className={`px-2.5 py-1.5 rounded-xl text-xs font-mono font-semibold border flex items-center justify-between transition-all shadow-sm ${
                  showET
                    ? 'bg-rose-50 border-rose-300 text-rose-800'
                    : 'bg-white border-slate-200 text-slate-400'
                }`}
              >
                <div className="flex items-center gap-1.5">
                  <span className={`w-2 h-2 rounded-full ${showET ? 'bg-rose-500' : 'bg-slate-300'}`} />
                  <span>ET</span>
                </div>
                <span className="text-[10px] font-bold">{showET ? 'ON' : 'OFF'}</span>
              </button>
            </div>
          </div>

          {/* Mask Blend Opacity Slider */}
          <div>
            <div className="flex items-center justify-between text-[11px] font-mono text-slate-500 mb-1">
              <span>Mask Overlay Blend:</span>
              <strong className="text-sky-700 font-bold">{Math.round(blendOpacity * 100)}%</strong>
            </div>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={blendOpacity}
              onChange={(e) => setBlendOpacity(Number(e.target.value))}
              className="w-full accent-sky-600 h-1.5 bg-slate-200 rounded-lg cursor-pointer"
            />
          </div>

        </div>

      </div>
    </div>
  );
}
