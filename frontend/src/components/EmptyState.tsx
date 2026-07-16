import type { ReactNode } from "react";

type EmptyStateProps = {
  title: string;
  description: string;
  action?: ReactNode;
};

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="ac-empty">
      <div className="mx-auto mb-4 h-px w-16 bg-gradient-to-r from-transparent via-[var(--gold)] to-transparent" />
      <p className="ac-display text-xl tracking-tight text-[var(--paper)]">{title}</p>
      <p className="ac-serif mx-auto mt-3 max-w-md text-[0.98rem] leading-relaxed text-[var(--mist)]">
        {description}
      </p>
      {action ? <div className="mt-6 flex justify-center">{action}</div> : null}
    </div>
  );
}
