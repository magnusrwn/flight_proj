import type { PropsWithChildren } from "react";

type PanelProps = PropsWithChildren<{
  className?: string;
}>;

export function Panel({ children, className = "" }: PanelProps) {
  return (
    <div
      className={
        `rounded-2xl
        w-full
        border border-white
        p-6 
        shadow-[0_16px_52px_rgba(0,0,0,0.22)] ${className}`}
    >
      {children}
    </div>
  );
}
