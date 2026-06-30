export default function SiteHeader({ eyebrow, title, description, actions }) {
  return (
    <header className="site-header">
      <div className="header-copy">
        <span className="eyebrow">{eyebrow}</span>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {actions && <div className="header-actions">{actions}</div>}
    </header>
  );
}

export function TopNav({ current }) {
  return (
    <nav className="top-nav" aria-label="Prototype navigation">
      <a className="brand" href="/index.html">
        FAS Studio
      </a>
      <div className="nav-links">
        <a className={current === "config" ? "active" : ""} href="/fas-config.html">
          Question configuration
        </a>
        <a className={current === "ai" ? "active" : ""} href="/dynamic-fas.html">
          AI Autofill
        </a>
      </div>
    </nav>
  );
}
