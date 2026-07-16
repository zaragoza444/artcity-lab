import type { ReactNode } from "react";

type PageHeaderProps = {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
};

export function PageHeader({ eyebrow, title, description, actions }: PageHeaderProps) {
  return (
    <div className="mb-12 flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between animate-rise">
      <div className="min-w-0 max-w-2xl">
        {eyebrow ? (
          <p className="ac-display mb-3 text-[0.68rem] tracking-[0.3em] text-[var(--mist)] uppercase">
            {eyebrow}
          </p>
        ) : null}
        <h1 className="ac-display text-4xl tracking-tight text-[var(--paper)] md:text-5xl">
          {title}
        </h1>
        {description ? (
          <p className="ac-serif mt-3 text-[1.05rem] leading-relaxed text-[var(--mist)]">
            {description}
          </p>
        ) : null}
      </div>
      {actions ? <div className="flex flex-wrap gap-3 shrink-0">{actions}</div> : null}
    </div>
  );
}
