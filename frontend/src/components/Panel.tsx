import type { PropsWithChildren } from "react";

type PanelProps = PropsWithChildren<{
  className?: string;
}>;

export function Panel({ children, className = "" }: PanelProps) {
  return (
    <div
      className={
        `rounded-[1.75rem]
        border border-white/10
        bg-[linear-gradient(180deg,rgba(19,34,54,0.96),rgba(10,19,31,0.98))]
        p-6 
        shadow-[0_16px_52px_rgba(0,0,0,0.22)] ${className}`}
    >
      {children}
    </div>
  );
}
