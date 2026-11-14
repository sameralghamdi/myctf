import { cn } from "../../lib/cn";

interface AvatarProps {
  name: string;
  size?: "md" | "lg";
}

export function Avatar({ name, size = "md" }: AvatarProps) {
  const initial = (name.trim()[0] ?? "?").toUpperCase();
  return (
    <span
      aria-hidden="true"
      className={cn(
        "grid shrink-0 place-items-center rounded-full bg-brand-600 font-semibold text-white",
        size === "md" ? "h-8 w-8 text-sm" : "h-16 w-16 text-2xl",
      )}
    >
      {initial}
    </span>
  );
}
