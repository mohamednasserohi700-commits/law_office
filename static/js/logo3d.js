import React, { useMemo, useRef, useState } from "https://esm.sh/react@18.3.1";
import { createRoot } from "https://esm.sh/react-dom@18.3.1/client";
import { Canvas, useFrame } from "https://esm.sh/@react-three/fiber@8.16.8";
import { Environment, Float } from "https://esm.sh/@react-three/drei@9.110.6";
import * as THREE from "https://esm.sh/three@0.164.1";

function LegalMark({ mode }) {
  const group = useRef();
  const [hovered, setHovered] = useState(false);
  const pulse = mode === "login";
  const metalGold = useMemo(
    () => new THREE.MeshStandardMaterial({ color: "#C9A54C", metalness: 0.95, roughness: 0.2 }),
    []
  );
  const metalSilver = useMemo(
    () => new THREE.MeshStandardMaterial({ color: "#c8d4f0", metalness: 0.9, roughness: 0.25 }),
    []
  );

  useFrame((state) => {
    if (!group.current) return;
    const t = state.clock.elapsedTime;
    group.current.position.y = Math.sin(t * 0.7) * 0.07;
    group.current.rotation.y += 0.003;
    group.current.rotation.x = Math.sin(t * 0.35) * 0.05;
    const target = hovered ? 1.08 : 1;
    const pulseScale = pulse ? 1 + Math.sin(t * 2.4) * 0.03 : 1;
    const finalScale = target * pulseScale;
    group.current.scale.lerp(new THREE.Vector3(finalScale, finalScale, finalScale), 0.08);
  });

  return React.createElement(
    Float,
    { speed: 1.1, rotationIntensity: 0.2, floatIntensity: 0.4 },
    React.createElement(
      "group",
      {
        ref: group,
        onPointerOver: () => setHovered(true),
        onPointerOut: () => setHovered(false),
      },
      React.createElement("mesh", { position: [0, 0.32, 0], material: metalGold }, React.createElement("cylinderGeometry", { args: [0.06, 0.06, 0.88, 28] })),
      React.createElement("mesh", { position: [0, 0.72, 0], material: metalSilver }, React.createElement("sphereGeometry", { args: [0.1, 24, 24] })),
      React.createElement("mesh", { position: [-0.45, 0.52, 0], material: metalSilver }, React.createElement("boxGeometry", { args: [0.7, 0.06, 0.05] })),
      React.createElement("mesh", { position: [0.45, 0.52, 0], material: metalSilver }, React.createElement("boxGeometry", { args: [0.7, 0.06, 0.05] })),
      React.createElement("mesh", { position: [-0.8, 0.2, 0], material: metalGold }, React.createElement("coneGeometry", { args: [0.2, 0.35, 22] })),
      React.createElement("mesh", { position: [0.8, 0.2, 0], material: metalGold }, React.createElement("coneGeometry", { args: [0.2, 0.35, 22] })),
      React.createElement("mesh", { position: [0, -0.03, 0], material: metalGold }, React.createElement("cylinderGeometry", { args: [0.72, 0.75, 0.08, 36] })),
      React.createElement("mesh", { position: [0.12, -0.28, 0], rotation: [0, 0, -0.68], material: metalSilver }, React.createElement("boxGeometry", { args: [1, 0.08, 0.08] })),
      React.createElement("mesh", { position: [0.57, -0.61, 0], material: metalGold }, React.createElement("cylinderGeometry", { args: [0.12, 0.14, 0.26, 22] }))
    )
  );
}

function Scene({ mode }) {
  return React.createElement(
    Canvas,
    { shadows: true, camera: { position: [0, 0.6, 2.6], fov: 42 } },
    React.createElement("ambientLight", { intensity: 0.6 }),
    React.createElement("pointLight", { position: [1.8, 2.2, 2], intensity: 1.3, color: "#f5d07b", castShadow: true }),
    React.createElement("pointLight", { position: [-2, -0.3, 1.5], intensity: 0.9, color: "#6ea9ff" }),
    React.createElement("directionalLight", { position: [0, 1, -2], intensity: 0.7, color: "#d3b4ff" }),
    React.createElement("mesh", { position: [0, -1.05, 0], rotation: [-Math.PI / 2, 0, 0], receiveShadow: true },
      React.createElement("planeGeometry", { args: [8, 8] }),
      React.createElement("shadowMaterial", { opacity: 0.25 })
    ),
    React.createElement(LegalMark, { mode }),
    React.createElement(Environment, { preset: "city" })
  );
}

document.querySelectorAll("[data-logo-3d]").forEach((mountNode) => {
  const mode = mountNode.getAttribute("data-logo-mode") || "app";
  try {
    const root = createRoot(mountNode);
    root.render(React.createElement(Scene, { mode }));
    mountNode.classList.add("logo-ready");
  } catch (error) {
    console.error("3D logo mount failed:", error);
  }
});
