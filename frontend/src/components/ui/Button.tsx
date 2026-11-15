import type { AnchorHTMLAttributes, ButtonHTMLAttributes, ReactNode } from "react";
import { Link } from "react-router-dom";
import { cn, focusRing } from "../../lib/cn";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md";

interface BaseProps {
  variant?: Variant;
  size?: Size;
  className?: string;
  children: ReactNode;
  /** Force a real <a> (full page load) even for "/..." hrefs, e.g. lab URLs served by Flask. */
  external?: boolean;
}

type ButtonAsButton = BaseProps &
  Omit<ButtonHTMLAttributes<HTMLButtonElement>, keyof BaseProps> & { href?: undefined };

type ButtonAsLink = BaseProps &
  Omit<AnchorHTMLAttributes<HTMLAnchorElement>, keyof BaseProps> & { href: string };

export type ButtonProps = ButtonAsButton | ButtonAsLink;

const variants: Record<Variant, string> = {
  primary: "bg-brand-600 text-white shadow-sm hover:bg-brand-700",
  secondary: "border border-gray-800 bg-gray-900 text-gray-200 shadow-sm hover:bg-gray-800",
  ghost: "text-gray-300 hover:bg-gray-800 hover:text-gray-50",
  danger: "border border-red-500/30 bg-red-500/10 text-red-300 hover:bg-red-500/20",
};

const sizes: Record<Size, string> = {
  sm: "h-8 px-4 text-sm",
  md: "h-10 px-6 text-sm",
};

/** Router <Link> for internal "/x" hrefs, plain <a> for external ones, else a <button>. */
export function Button(props: ButtonProps) {
  const { variant = "primary", size = "md", className, children } = props;
  const classes = cn(
    "inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors duration-200",
    "disabled:pointer-events-none disabled:opacity-50",
    focusRing,
    variants[variant],
    sizes[size],
    className,
  );

  if (props.href !== undefined) {
    const {
      variant: _v,
      size: _s,
      className: _c,
      children: _ch,
      external,
      href,
      ...anchorProps
    } = props;
    if (href.startsWith("/") && !external) {
      return (
        <Link {...anchorProps} to={href} className={classes}>
          {children}
        </Link>
      );
    }
    return (
      <a {...anchorProps} href={href} className={classes}>
        {children}
      </a>
    );
  }

  const {
    variant: _v,
    size: _s,
    className: _c,
    children: _ch,
    external: _e,
    ...buttonProps
  } = props;
  return (
    <button type="button" {...buttonProps} className={classes}>
      {children}
    </button>
  );
}
