import { cn } from "../../lib/cn";

interface AvatarProps {
  name: string;
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
}

/** Each name gets its own stable gradient so players are easy to tell apart. */
const GRADIENTS = [
  "from-brand-500 to-orange-500",
  "from-sky-500 to-indigo-500",
  "from-emerald-500 to-teal-600",
  "from-fuchsia-500 to-pink-600",
  "from-amber-500 to-orange-600",
  "from-violet-500 to-purple-700",
  "from-cyan-500 to-blue-600",
  "from-rose-500 to-red-700",
];

function hash(value: string): number {
  let h = 0;
  for (let i = 0; i < value.length; i += 1) h = (h * 31 + value.charCodeAt(i)) >>> 0;
  return h;
}

const sizes = {
  sm: "h-6 w-6 text-xs",
  md: "h-8 w-8 text-sm",
  lg: "h-16 w-16 text-2xl",
  xl: "h-20 w-20 text-3xl",
} as const;

export function Avatar({ name, size = "md", className }: AvatarProps) {
  const initial = (name.trim()[0] ?? "?").toUpperCase();
  return (
    <span
      aria-hidden="true"
      className={cn(
        "grid shrink-0 place-items-center rounded-full bg-gradient-to-br font-semibold text-white shadow-sm",
        GRADIENTS[hash(name) % GRADIENTS.length],
        sizes[size],
        className,
      )}
    >
      {initial}
    </span>
  );
}
