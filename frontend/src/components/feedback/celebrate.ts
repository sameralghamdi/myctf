/**
 * A short confetti burst from a point on screen (default: the centre).
 * Pure DOM + Web Animations, cleaned up when it finishes. Skipped when the
 * visitor prefers reduced motion.
 */
const COLORS = ["#f87171", "#fb923c", "#facc15", "#4ade80", "#60a5fa", "#e879f9"];

export function celebrate(origin?: { x: number; y: number }) {
  if (typeof window === "undefined") return;
  if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
  if (!("animate" in Element.prototype)) return;

  const x = origin?.x ?? window.innerWidth / 2;
  const y = origin?.y ?? window.innerHeight / 3;
  const layer = document.createElement("div");
  layer.setAttribute("aria-hidden", "true");
  layer.style.cssText = "position:fixed;inset:0;pointer-events:none;z-index:60;overflow:hidden";
  document.body.appendChild(layer);

  const pieces = 90;
  let finished = 0;
  for (let i = 0; i < pieces; i += 1) {
    const piece = document.createElement("span");
    const size = 6 + Math.random() * 6;
    piece.style.cssText = `position:absolute;left:${x}px;top:${y}px;width:${size}px;height:${size * 0.45}px;background:${COLORS[i % COLORS.length]};border-radius:2px`;
    layer.appendChild(piece);
    const angle = Math.random() * Math.PI * 2;
    const velocity = 160 + Math.random() * 280;
    const dx = Math.cos(angle) * velocity;
    const dy = Math.sin(angle) * velocity - 180;
    const spin = (Math.random() - 0.5) * 1080;
    const animation = piece.animate(
      [
        { transform: "translate(0,0) rotate(0deg)", opacity: 1 },
        { transform: `translate(${dx}px, ${dy + 420}px) rotate(${spin}deg)`, opacity: 0 },
      ],
      { duration: 1400 + Math.random() * 900, easing: "cubic-bezier(0.2, 0.6, 0.4, 1)", fill: "forwards" },
    );
    animation.onfinish = () => {
      finished += 1;
      if (finished === pieces) layer.remove();
    };
  }
}
