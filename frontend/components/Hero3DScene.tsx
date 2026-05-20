"use client";

import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Float, MeshDistortMaterial } from "@react-three/drei";
import type { Mesh } from "three";
import * as THREE from "three";

function CrystalCore({ scrollProgress }: { scrollProgress: number }) {
  const meshRef = useRef<Mesh>(null);

  const geometry = useMemo(() => new THREE.IcosahedronGeometry(1.45, 2), []);

  useFrame((state) => {
    const mesh = meshRef.current;
    if (!mesh) return;
    mesh.rotation.x = state.pointer.y * 0.52;
    mesh.rotation.y = state.pointer.x * 0.72 + scrollProgress * Math.PI * 1.4;
    const scale = 0.94 + scrollProgress * 0.26;
    mesh.scale.setScalar(scale);
  });

  return (
    <Float speed={1.4} rotationIntensity={0.25} floatIntensity={0.45}>
      <mesh ref={meshRef} geometry={geometry}>
        <MeshDistortMaterial
          color="#D4AF37"
          emissive="#0A0F1E"
          roughness={0.18}
          metalness={0.82}
          distort={0.28}
          speed={1.85}
        />
      </mesh>
    </Float>
  );
}

export function Hero3DScene({ scrollProgress }: { scrollProgress: number }) {
  return (
    <div className="pointer-events-none absolute inset-0 z-0">
      <Canvas
        aria-hidden
        dpr={[1, 2]}
        gl={{ alpha: true, antialias: true }}
        camera={{ position: [0, 0, 6.2], fov: 38 }}
      >
        <ambientLight intensity={0.35} />
        <pointLight position={[8, 6, 12]} intensity={1.05} color="#D4AF37" />
        <pointLight position={[-10, -8, -6]} intensity={0.45} color="#3b63ff" />
        <CrystalCore scrollProgress={scrollProgress} />
      </Canvas>
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_30%_-10%,rgba(212,175,55,0.08),transparent_52%),linear-gradient(to_bottom,rgba(5,9,20,0.3),rgba(10,15,30,0.94))]" />
    </div>
  );
}
