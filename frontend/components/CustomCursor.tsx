"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";

export function CustomCursor() {
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isHovering, setIsHovering] = useState(false);
  const [hideNativeCursor, setHideNativeCursor] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const mq = window.matchMedia("(pointer: fine)");
    const sync = () => setHideNativeCursor(mq.matches);
    sync();
    mq.addEventListener?.("change", sync);

    document.body.classList.add("cursor-elite");

    const handleMove = (e: MouseEvent) => setPosition({ x: e.clientX, y: e.clientY });

    const handleHover = (e: MouseEvent) => {
      const target = e.target as HTMLElement | null;
      if (!target) {
        setIsHovering(false);
        return;
      }
      setIsHovering(Boolean(target.closest("a, button, [data-cursor-hover], input, textarea, select")));
    };

    window.addEventListener("mousemove", handleMove);
    window.addEventListener("mouseover", handleHover);

    return () => {
      mq.removeEventListener?.("change", sync);
      document.body.classList.remove("cursor-elite");
      window.removeEventListener("mousemove", handleMove);
      window.removeEventListener("mouseover", handleHover);
    };
  }, []);

  if (!hideNativeCursor) {
    return null;
  }

  return (
    <>
      <motion.div
        className="pointer-events-none fixed left-0 top-0 z-[9999] h-4 w-4 rounded-full border border-gold-500 mix-blend-difference"
        animate={{
          x: position.x - 8,
          y: position.y - 8,
          scale: isHovering ? 2 : 1,
        }}
        transition={{ type: "spring", stiffness: 500, damping: 28, mass: 0.5 }}
      />
      <motion.div
        className="pointer-events-none fixed left-0 top-0 z-[9999] h-1.5 w-1.5 rounded-full bg-gold-500"
        animate={{ x: position.x - 3, y: position.y - 3 }}
        transition={{ type: "spring", stiffness: 900, damping: 45, mass: 0.2 }}
      />
    </>
  );
}
