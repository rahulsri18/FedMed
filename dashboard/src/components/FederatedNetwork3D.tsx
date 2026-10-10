import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { TelemetryPayload, NodeTelemetry } from '../types';
import { Lock, ShieldAlert, Cpu, Activity, RefreshCw, Eye, EyeOff } from 'lucide-react';

interface FederatedNetwork3DProps {
  telemetry: TelemetryPayload | null;
  onNodeClick?: (nodeId: number) => void;
}

const NODE_POSITIONS: Record<number, [number, number, number]> = {
  1: [-3.8, 0.5, 1.5],  // St. Jude (Left-Forward)
  2: [3.8, -0.4, 1.8],   // Charité Berlin (Right-Forward)
  3: [0.3, 3.0, -2.6],   // Mayo Clinic (Top-Rear)
};

const HOSPITAL_INFO: Record<number, { name: string; city: string; role: string }> = {
  1: { name: "St. Jude Medical", city: "Memphis, USA", role: "Pediatric & High-Grade Glioma" },
  2: { name: "Charité Berlin", city: "Berlin, DE", role: "Adult Glioblastoma Multiforme" },
  3: { name: "Mayo Clinic Oncology", city: "Rochester, USA", role: "Low-Grade & Oligodendroglioma" },
};

interface ScreenPosition {
  x: number;
  y: number;
  visible: boolean;
}

export const FederatedNetwork3D: React.FC<FederatedNetwork3DProps> = ({
  telemetry,
  onNodeClick,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const [selectedNodeId, setSelectedNodeId] = useState<number | null>(null);
  const [autoRotate, setAutoRotate] = useState<boolean>(true);
  const [showHudOverlays, setShowHudOverlays] = useState<boolean>(true);
  const [nodeScreenPositions, setNodeScreenPositions] = useState<Record<number, ScreenPosition>>({});
  const [coreScreenPosition, setCoreScreenPosition] = useState<ScreenPosition>({ x: 0, y: 0, visible: false });

  // Refs for Three.js instance objects across renders
  const controlsRef = useRef<OrbitControls | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const nodeMeshesRef = useRef<Record<number, THREE.Group>>({});
  const coreGroupRef = useRef<THREE.Group | null>(null);
  const innerCoreMeshRef = useRef<THREE.Mesh | null>(null);
  const gyroRingOuterRef = useRef<THREE.Mesh | null>(null);
  const gyroRingMidRef = useRef<THREE.Mesh | null>(null);
  const particleSystemsRef = useRef<{ points: THREE.Points; curve: THREE.CatmullRomCurve3; speed: number; progress: Float32Array }[]>([]);

  const phase = telemetry?.phase || 'idle';
  const encrypted = telemetry?.encrypted ?? true;
  const roundNum = telemetry?.round || 1;

  // Initialize Three.js Scene (Light Clinical Aesthetic)
  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    const width = container.clientWidth;
    const height = container.clientHeight;

    // 1. Scene
    const scene = new THREE.Scene();
    sceneRef.current = scene;

    // Luminous floor grid (Sky blue + Soft slate lines)
    const gridHelper = new THREE.GridHelper(18, 36, 0x0284c7, 0xcbd5e1);
    gridHelper.position.y = -2.8;
    (gridHelper.material as THREE.Material).transparent = true;
    (gridHelper.material as THREE.Material).opacity = 0.5;
    scene.add(gridHelper);

    // 2. Camera
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 1000);
    camera.position.set(0, 4.5, 9.5);
    cameraRef.current = camera;

    // 3. Renderer with Light Medical Clear Color
    const renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance',
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0xf1f5f9, 1.0); // Slate-100 Light Canvas
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.1;
    rendererRef.current = renderer;

    // 4. OrbitControls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxDistance = 18;
    controls.minDistance = 3.5;
    controls.maxPolarAngle = Math.PI / 2 + 0.15;
    controls.autoRotate = autoRotate;
    controls.autoRotateSpeed = 0.8;
    controlsRef.current = controls;

    // 5. Lighting (Bright Clinical Lighting)
    const ambientLight = new THREE.AmbientLight(0xffffff, 2.2);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 1.6);
    dirLight.position.set(6, 12, 8);
    scene.add(dirLight);

    const skyPointLight = new THREE.PointLight(0x0284c7, 2.8, 16);
    skyPointLight.position.set(0, 0, 0);
    scene.add(skyPointLight);

    const emeraldPointLight = new THREE.PointLight(0x059669, 2.2, 14);
    emeraldPointLight.position.set(-4, 2, 2);
    scene.add(emeraldPointLight);

    const violetPointLight = new THREE.PointLight(0x7c3aed, 2.2, 14);
    violetPointLight.position.set(4, -1, 2);
    scene.add(violetPointLight);

    // 6. Central Aggregation Core
    const coreGroup = new THREE.Group();
    coreGroupRef.current = coreGroup;
    scene.add(coreGroup);

    // Inner Core (Icosahedron)
    const coreGeo = new THREE.IcosahedronGeometry(0.72, 2);
    const coreMat = new THREE.MeshStandardMaterial({
      color: 0x0284c7,
      emissive: 0x0284c7,
      emissiveIntensity: 0.35,
      roughness: 0.2,
      metalness: 0.5,
      wireframe: false,
    });
    const innerCoreMesh = new THREE.Mesh(coreGeo, coreMat);
    innerCoreMeshRef.current = innerCoreMesh;
    coreGroup.add(innerCoreMesh);

    // Wireframe Shield Sphere
    const shieldGeo = new THREE.SphereGeometry(0.95, 18, 18);
    const shieldMat = new THREE.MeshBasicMaterial({
      color: 0x0284c7,
      wireframe: true,
      transparent: true,
      opacity: 0.3,
    });
    const shieldMesh = new THREE.Mesh(shieldGeo, shieldMat);
    coreGroup.add(shieldMesh);

    // Gyro Ring Outer
    const ringOuterGeo = new THREE.TorusGeometry(1.65, 0.03, 16, 64);
    const ringOuterMat = new THREE.MeshBasicMaterial({
      color: 0x0284c7,
      transparent: true,
      opacity: 0.6,
      wireframe: true,
    });
    const gyroRingOuter = new THREE.Mesh(ringOuterGeo, ringOuterMat);
    gyroRingOuterRef.current = gyroRingOuter;
    coreGroup.add(gyroRingOuter);

    // Gyro Ring Mid
    const ringMidGeo = new THREE.TorusGeometry(1.35, 0.025, 16, 64);
    const ringMidMat = new THREE.MeshBasicMaterial({
      color: 0x7c3aed,
      transparent: true,
      opacity: 0.5,
    });
    const gyroRingMid = new THREE.Mesh(ringMidGeo, ringMidMat);
    gyroRingMidRef.current = gyroRingMid;
    coreGroup.add(gyroRingMid);

    // 7. Hospital Silo Nodes
    const nodeGroups: Record<number, THREE.Group> = {};
    const particleSystems: { points: THREE.Points; curve: THREE.CatmullRomCurve3; speed: number; progress: Float32Array }[] = [];

    [1, 2, 3].forEach((nodeId) => {
      const pos = NODE_POSITIONS[nodeId];
      const nodeGroup = new THREE.Group();
      nodeGroup.position.set(pos[0], pos[1], pos[2]);
      nodeGroup.userData = { nodeId };

      // Outer Wireframe Cage (Octahedron)
      const cageGeo = new THREE.OctahedronGeometry(0.55, 0);
      const cageMat = new THREE.MeshBasicMaterial({
        color: 0x059669,
        wireframe: true,
        transparent: true,
        opacity: 0.75,
      });
      const cageMesh = new THREE.Mesh(cageGeo, cageMat);
      cageMesh.name = `cage-${nodeId}`;
      nodeGroup.add(cageMesh);

      // Inner Solid Sphere Core
      const nodeCoreGeo = new THREE.SphereGeometry(0.32, 16, 16);
      const nodeCoreMat = new THREE.MeshStandardMaterial({
        color: 0x059669,
        emissive: 0x059669,
        emissiveIntensity: 0.35,
        roughness: 0.3,
        metalness: 0.5,
      });
      const nodeCoreMesh = new THREE.Mesh(nodeCoreGeo, nodeCoreMat);
      nodeCoreMesh.name = `core-${nodeId}`;
      nodeGroup.add(nodeCoreMesh);

      // Ground Radar Halo Ring
      const haloGeo = new THREE.RingGeometry(0.5, 0.7, 32);
      const haloMat = new THREE.MeshBasicMaterial({
        color: 0x059669,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.35,
      });
      const haloMesh = new THREE.Mesh(haloGeo, haloMat);
      haloMesh.rotation.x = Math.PI / 2;
      haloMesh.position.y = -0.6;
      nodeGroup.add(haloMesh);

      scene.add(nodeGroup);
      nodeGroups[nodeId] = nodeGroup;

      // Connecting Spline Curve to Central Core (0, 0, 0)
      const start = new THREE.Vector3(pos[0], pos[1], pos[2]);
      const end = new THREE.Vector3(0, 0, 0);
      const mid = new THREE.Vector3(
        (start.x + end.x) * 0.5,
        (start.y + end.y) * 0.5 + 0.6,
        (start.z + end.z) * 0.5
      );
      const curve = new THREE.CatmullRomCurve3([start, mid, end]);

      // Subtle Spline Guide Tube
      const curvePoints = curve.getPoints(50);
      const lineGeo = new THREE.BufferGeometry().setFromPoints(curvePoints);
      const lineMat = new THREE.LineBasicMaterial({
        color: 0x0284c7,
        transparent: true,
        opacity: 0.35,
      });
      const splineLine = new THREE.Line(lineGeo, lineMat);
      scene.add(splineLine);

      // Spline Particle Stream
      const PARTICLE_COUNT = 24;
      const progress = new Float32Array(PARTICLE_COUNT);
      const positions = new Float32Array(PARTICLE_COUNT * 3);
      for (let i = 0; i < PARTICLE_COUNT; i++) {
        progress[i] = i / PARTICLE_COUNT;
        const pt = curve.getPoint(progress[i]);
        positions[i * 3] = pt.x;
        positions[i * 3 + 1] = pt.y;
        positions[i * 3 + 2] = pt.z;
      }

      const particleGeo = new THREE.BufferGeometry();
      particleGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      const particleMat = new THREE.PointsMaterial({
        color: 0x0284c7,
        size: 0.1,
        transparent: true,
        opacity: 0.9,
      });
      const particlePoints = new THREE.Points(particleGeo, particleMat);
      scene.add(particlePoints);

      particleSystems.push({
        points: particlePoints,
        curve,
        speed: 0.18 + nodeId * 0.04,
        progress,
      });
    });

    nodeMeshesRef.current = nodeGroups;
    particleSystemsRef.current = particleSystems;

    // 8. Raycaster for clicking
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    const handleCanvasClick = (event: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      const targetMeshes: THREE.Object3D[] = [];
      Object.values(nodeGroups).forEach((group) => {
        group.children.forEach((child) => targetMeshes.push(child));
      });

      const intersects = raycaster.intersectObjects(targetMeshes);
      if (intersects.length > 0) {
        const hit = intersects[0].object;
        const parentGroup = hit.parent;
        if (parentGroup && parentGroup.userData.nodeId) {
          const clickedId = parentGroup.userData.nodeId;
          setSelectedNodeId(clickedId);
          onNodeClick?.(clickedId);
        }
      }
    };

    canvas.addEventListener('click', handleCanvasClick);

    // 9. Resize Observer
    const handleResize = () => {
      if (!container || !renderer || !camera) return;
      const newW = container.clientWidth;
      const newH = container.clientHeight;
      camera.aspect = newW / newH;
      camera.updateProjectionMatrix();
      renderer.setSize(newW, newH);
    };

    window.addEventListener('resize', handleResize);

    // 10. Animation Loop
    let animationFrameId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const delta = clock.getDelta();
      const elapsed = clock.getElapsedTime();

      controls.update();

      if (gyroRingOuterRef.current) {
        gyroRingOuterRef.current.rotation.y += delta * 0.6;
        gyroRingOuterRef.current.rotation.x += delta * 0.3;
      }
      if (gyroRingMidRef.current) {
        gyroRingMidRef.current.rotation.z -= delta * 0.8;
        gyroRingMidRef.current.rotation.y += delta * 0.4;
      }

      if (innerCoreMeshRef.current) {
        const pulse = 1.0 + Math.sin(elapsed * 3.5) * 0.08;
        innerCoreMeshRef.current.scale.set(pulse, pulse, pulse);
        innerCoreMeshRef.current.rotation.y += delta * 0.5;
      }

      Object.values(nodeGroups).forEach((group, idx) => {
        const cage = group.getObjectByName(`cage-${idx + 1}`);
        if (cage) {
          cage.rotation.y += delta * (0.8 + idx * 0.2);
          cage.rotation.x += delta * 0.4;
        }
        group.position.y = NODE_POSITIONS[idx + 1][1] + Math.sin(elapsed * 2 + idx) * 0.08;
      });

      particleSystems.forEach((sys) => {
        const positions = sys.points.geometry.attributes.position.array as Float32Array;
        for (let i = 0; i < sys.progress.length; i++) {
          sys.progress[i] = (sys.progress[i] + delta * sys.speed) % 1.0;
          const pt = sys.curve.getPoint(sys.progress[i]);
          positions[i * 3] = pt.x;
          positions[i * 3 + 1] = pt.y;
          positions[i * 3 + 2] = pt.z;
        }
        sys.points.geometry.attributes.position.needsUpdate = true;
      });

      // Project 3D points to 2D for HUD badges
      const newScreenPositions: Record<number, ScreenPosition> = {};
      const tempVec = new THREE.Vector3();

      [1, 2, 3].forEach((nodeId) => {
        const group = nodeGroups[nodeId];
        if (group) {
          tempVec.copy(group.position);
          tempVec.y += 0.75;
          tempVec.project(camera);

          const isBehind = tempVec.z > 1;
          const sx = ((tempVec.x + 1) * width) / 2;
          const sy = ((-tempVec.y + 1) * height) / 2;

          newScreenPositions[nodeId] = {
            x: sx,
            y: sy,
            visible: !isBehind && sx >= 0 && sx <= width && sy >= 0 && sy <= height,
          };
        }
      });
      setNodeScreenPositions(newScreenPositions);

      tempVec.set(0, 1.2, 0);
      tempVec.project(camera);
      setCoreScreenPosition({
        x: ((tempVec.x + 1) * width) / 2,
        y: ((-tempVec.y + 1) * height) / 2,
        visible: tempVec.z <= 1,
      });

      renderer.render(scene, camera);
    };

    animate();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      canvas.removeEventListener('click', handleCanvasClick);
      controls.dispose();
      renderer.dispose();
    };
  }, []);

  // Update Three.js materials dynamically
  useEffect(() => {
    if (!telemetry || !sceneRef.current) return;

    const isAggregating = phase === 'aggregating';
    const isEncrypting = phase === 'encrypting';

    if (innerCoreMeshRef.current) {
      const mat = innerCoreMeshRef.current.material as THREE.MeshStandardMaterial;
      if (isAggregating) {
        mat.color.setHex(0x0284c7); // Sky blue
        mat.emissive.setHex(0x0284c7);
        mat.emissiveIntensity = 0.6;
      } else if (isEncrypting) {
        mat.color.setHex(0x7c3aed); // Violet
        mat.emissive.setHex(0x7c3aed);
        mat.emissiveIntensity = 0.5;
      } else {
        mat.color.setHex(0x059669); // Emerald
        mat.emissive.setHex(0x059669);
        mat.emissiveIntensity = 0.35;
      }
    }

    telemetry.nodes.forEach((node) => {
      const group = nodeMeshesRef.current[node.id];
      if (group) {
        const coreMesh = group.getObjectByName(`core-${node.id}`) as THREE.Mesh;
        const cageMesh = group.getObjectByName(`cage-${node.id}`) as THREE.Mesh;
        const isDropped = node.status === 'dropped' || node.status === 'offline';

        const colorHex = isDropped ? 0xe11d48 : (node.id === selectedNodeId ? 0x0284c7 : 0x059669);

        if (coreMesh) {
          const cMat = coreMesh.material as THREE.MeshStandardMaterial;
          cMat.color.setHex(colorHex);
          cMat.emissive.setHex(colorHex);
          cMat.emissiveIntensity = isDropped ? 0.2 : 0.45;
        }
        if (cageMesh) {
          const wMat = cageMesh.material as THREE.MeshBasicMaterial;
          wMat.color.setHex(colorHex);
        }
      }
    });
  }, [telemetry, phase, selectedNodeId]);

  const toggleAutoRotate = useCallback(() => {
    setAutoRotate((prev) => {
      const next = !prev;
      if (controlsRef.current) {
        controlsRef.current.autoRotate = next;
      }
      return next;
    });
  }, []);

  const handleResetCamera = useCallback(() => {
    if (cameraRef.current && controlsRef.current) {
      cameraRef.current.position.set(0, 4.5, 9.5);
      controlsRef.current.target.set(0, 0, 0);
      controlsRef.current.update();
    }
  }, []);

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full min-h-[460px] bg-gradient-to-b from-[#f8fafc] via-[#f1f5f9] to-[#e2e8f0] rounded-2xl overflow-hidden border border-slate-200 shadow-sm"
    >
      {/* 3D WebGL Canvas */}
      <canvas ref={canvasRef} className="w-full h-full block cursor-grab active:cursor-grabbing" />

      {/* Control Toolbar (Top Right) */}
      <div className="absolute top-3.5 right-3.5 flex items-center space-x-2 z-20">
        <button
          onClick={() => setShowHudOverlays((prev) => !prev)}
          title="Toggle HUD Labels"
          className="p-1.5 rounded-xl bg-white/90 hover:bg-white text-slate-700 hover:text-sky-600 border border-slate-200/90 backdrop-blur-md transition-all text-xs flex items-center space-x-1 shadow-sm"
        >
          {showHudOverlays ? <Eye size={14} /> : <EyeOff size={14} />}
          <span className="hidden sm:inline font-mono font-semibold">{showHudOverlays ? 'HUD ON' : 'HUD OFF'}</span>
        </button>

        <button
          onClick={toggleAutoRotate}
          title="Toggle Rotation"
          className={`p-1.5 rounded-xl border backdrop-blur-md transition-all text-xs font-mono font-semibold flex items-center space-x-1 shadow-sm ${
            autoRotate
              ? 'bg-sky-50 text-sky-700 border-sky-300'
              : 'bg-white/90 text-slate-600 border-slate-200'
          }`}
        >
          <Activity size={14} className={autoRotate ? 'animate-spin' : ''} />
          <span className="hidden sm:inline">{autoRotate ? 'ORBITING' : 'STATIC'}</span>
        </button>

        <button
          onClick={handleResetCamera}
          title="Reset Camera View"
          className="p-1.5 rounded-xl bg-white/90 hover:bg-white text-slate-700 hover:text-sky-600 border border-slate-200 backdrop-blur-md transition-all text-xs flex items-center space-x-1 font-mono font-semibold shadow-sm"
        >
          <RefreshCw size={14} />
          <span className="hidden sm:inline">RESET</span>
        </button>
      </div>

      {/* Telemetry Status Bar (Top Left) */}
      <div className="absolute top-3.5 left-3.5 z-20 flex flex-wrap items-center gap-2">
        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-white/95 backdrop-blur-md border border-slate-200 shadow-sm">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-sky-500 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-sky-600" />
          </span>
          <span className="font-mono text-xs font-bold text-slate-800">
            ROUND {roundNum} / {telemetry?.global?.rounds_total || 5}
          </span>
          <span className="text-slate-300 font-mono">|</span>
          <span className="font-mono text-xs text-sky-700 uppercase tracking-wider font-bold">
            {phase}
          </span>
        </div>

        <div className="hidden sm:flex items-center space-x-1.5 px-2.5 py-1.5 rounded-xl bg-white/95 backdrop-blur-md border border-slate-200 text-xs font-mono text-slate-700 shadow-sm">
          <Lock size={12} className={encrypted ? 'text-purple-600' : 'text-slate-400'} />
          <span className={encrypted ? 'text-purple-700 font-bold' : 'text-slate-600'}>
            {encrypted ? 'CKKS ENCRYPTION' : 'PLAINTEXT'}
          </span>
        </div>
      </div>

      {/* Floating 2D HUD Badges Projected Over 3D Nodes */}
      {showHudOverlays && (
        <div className="pointer-events-none absolute inset-0 z-10 overflow-hidden">
          {/* Central Aggregation Core Badge */}
          {coreScreenPosition.visible && (
            <div
              style={{
                transform: `translate(${coreScreenPosition.x}px, ${coreScreenPosition.y}px) translate(-50%, -100%)`,
              }}
              className="absolute pointer-events-auto transition-transform duration-75"
            >
              <div className="px-3.5 py-2 rounded-xl bg-white/95 border border-sky-300 backdrop-blur-md shadow-lg text-center">
                <div className="flex items-center justify-center space-x-1.5 text-xs font-mono text-sky-700 font-bold tracking-wider">
                  <Cpu size={13} className="text-sky-600" />
                  <span>AGGREGATION CORE</span>
                </div>
                <div className="text-[11px] font-mono text-slate-500 mt-0.5">
                  FedAvg Quorum (min 2 of 3)
                </div>
              </div>
            </div>
          )}

          {/* Hospital Silo Badges */}
          {[1, 2, 3].map((nodeId) => {
            const screen = nodeScreenPositions[nodeId];
            if (!screen || !screen.visible) return null;

            const nodeData = telemetry?.nodes.find((n) => n.id === nodeId);
            const info = HOSPITAL_INFO[nodeId];
            const isDropped = nodeData?.status === 'dropped' || nodeData?.status === 'offline';
            const isSelected = selectedNodeId === nodeId;

            return (
              <div
                key={nodeId}
                style={{
                  transform: `translate(${screen.x}px, ${screen.y}px) translate(-50%, -100%)`,
                }}
                className="absolute pointer-events-auto transition-transform duration-75"
              >
                <div
                  onClick={() => {
                    setSelectedNodeId(nodeId);
                    onNodeClick?.(nodeId);
                  }}
                  className={`cursor-pointer px-3.5 py-2.5 rounded-2xl backdrop-blur-md transition-all shadow-md border ${
                    isSelected
                      ? 'bg-sky-50/95 border-sky-400 ring-2 ring-sky-300'
                      : isDropped
                      ? 'bg-rose-50/95 border-rose-300 text-rose-900'
                      : 'bg-white/95 border-emerald-200 hover:border-emerald-400'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <span
                      className={`h-2 w-2 rounded-full ${
                        isDropped ? 'bg-rose-500' : 'bg-emerald-500 animate-pulse'
                      }`}
                    />
                    <span className="font-mono text-xs font-bold text-slate-900">
                      NODE 0{nodeId}
                    </span>
                    <span
                      className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded-full font-bold ${
                        isDropped
                          ? 'bg-rose-100 text-rose-700'
                          : 'bg-emerald-100 text-emerald-800'
                      }`}
                    >
                      {isDropped ? 'DROPPED' : 'ACTIVE'}
                    </span>
                  </div>

                  <div className="text-xs font-bold text-slate-800 mt-1">
                    {info.name}
                  </div>
                  <div className="text-[11px] font-mono text-slate-500">
                    {info.city}
                  </div>

                  <div className="mt-2 pt-1.5 border-t border-slate-100 flex items-center justify-between space-x-3 text-[11px] font-mono">
                    <span className="text-slate-500">
                      Dice:{' '}
                      <strong className={isDropped ? 'text-rose-600' : 'text-emerald-700 font-bold'}>
                        {nodeData ? (nodeData.dice * 100).toFixed(1) + '%' : '--'}
                      </strong>
                    </span>
                    <span className="text-slate-500">
                      Latency:{' '}
                      <strong className="text-sky-700 font-bold">
                        {nodeData ? `${nodeData.upload_ms}ms` : '--'}
                      </strong>
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Bottom Hint Banner */}
      <div className="absolute bottom-3 left-3 right-3 z-20 flex items-center justify-between text-xs font-mono text-slate-600 bg-white/90 backdrop-blur-md px-3.5 py-1.5 rounded-xl border border-slate-200 shadow-sm pointer-events-none">
        <div className="flex items-center space-x-2">
          <Activity size={13} className="text-sky-600" />
          <span>Interactive 3D WebGL • Left-drag to rotate • Right-drag to pan • Scroll to zoom</span>
        </div>
        <div className="hidden sm:flex items-center space-x-2 text-slate-500">
          <span>Click any hospital node to inspect</span>
        </div>
      </div>
    </div>
  );
};

export default FederatedNetwork3D;
