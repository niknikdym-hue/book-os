export function BrandMark({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`brand-lockup ${compact ? "compact" : ""}`} aria-label="BOOK OS">
      <span className="brand-symbol" aria-hidden="true">
        <span className="brand-page brand-page-left" />
        <span className="brand-spine" />
        <span className="brand-page brand-page-right" />
      </span>
      <span className="brand-wordmark">
        <strong>BOOK</strong>
        <em>OS</em>
      </span>
    </div>
  );
}
