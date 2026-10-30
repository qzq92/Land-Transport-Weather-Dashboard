import type { ReactNode } from "react";

interface DataPanelProps {
  title: string;
  eyebrow?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function DataPanel({
  title,
  eyebrow,
  action,
  children,
  className = "",
}: DataPanelProps) {
  return (
    <section className={`data-panel ${className}`.trim()}>
      <header className="panel-header">
        <div>
          {eyebrow && <p className="eyebrow">{eyebrow}</p>}
          <h2>{title}</h2>
        </div>
        {action}
      </header>
      <div className="panel-body">{children}</div>
    </section>
  );
}
