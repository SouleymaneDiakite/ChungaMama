export function GuideIcon({ name, className = "" }: { name: string; className?: string }) {
  const common = { width: 20, height: 20, viewBox: "0 0 24 24", fill: "none" as const };

  switch (name) {
    case "calendar":
      return (
        <svg {...common} className={className}>
          <rect x="4" y="5" width="16" height="15" rx="2" stroke="currentColor" strokeWidth="1.6" />
          <path d="M4 9.5h16M8 3v3.5M16 3v3.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
        </svg>
      );
    case "leaf":
      return (
        <svg {...common} className={className}>
          <path d="M12 20c-4-2.5-7-6-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 4-3 7.5-7 10Z" stroke="currentColor" strokeWidth="1.6" />
        </svg>
      );
    case "warning":
      return (
        <svg {...common} className={className}>
          <path d="M12 3 3 20h18L12 3Z" stroke="currentColor" strokeWidth="1.6" />
          <path d="M12 10v4M12 17h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        </svg>
      );
    case "syringe":
      return (
        <svg {...common} className={className}>
          <path d="M18 3l3 3-2 2-3-3 2-2Z" stroke="currentColor" strokeWidth="1.6" />
          <path d="M17 6 8 15l-1 4 4-1 9-9-3-3Z" stroke="currentColor" strokeWidth="1.6" />
          <path d="M13 8l2 2M11 10l2 2" stroke="currentColor" strokeWidth="1.4" />
        </svg>
      );
    case "heart":
      return (
        <svg {...common} className={className}>
          <path d="M12 20.5c-4.3-2.7-9-6.4-9-11a5 5 0 0 1 9-3 5 5 0 0 1 9 3c0 4.6-4.7 8.3-9 11Z" stroke="currentColor" strokeWidth="1.6" />
        </svg>
      );
    case "clipboard":
      return (
        <svg {...common} className={className}>
          <rect x="5" y="4" width="14" height="17" rx="2" stroke="currentColor" strokeWidth="1.6" />
          <path d="M9 4V3a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v1" stroke="currentColor" strokeWidth="1.6" />
          <path d="M8.5 11h7M8.5 15h7M8.5 19h4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
        </svg>
      );
    case "support":
      return (
        <svg {...common} className={className}>
          <circle cx="9" cy="8" r="3.2" stroke="currentColor" strokeWidth="1.6" />
          <path d="M3.5 20c1-4 3.5-6 5.5-6s4.5 2 5.5 6" stroke="currentColor" strokeWidth="1.6" />
          <circle cx="17" cy="8" r="2.4" stroke="currentColor" strokeWidth="1.4" />
          <path d="M15.5 14c2-.3 4 1.3 5 5.2" stroke="currentColor" strokeWidth="1.4" />
        </svg>
      );
    case "mic":
      return (
        <svg {...common} className={className}>
          <path d="M12 2a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" stroke="currentColor" strokeWidth="1.7" />
          <path d="M6 11a6 6 0 0 0 12 0M12 19v3" stroke="currentColor" strokeWidth="1.7" />
        </svg>
      );
    case "chat":
      return (
        <svg {...common} className={className}>
          <path d="M4 5h16v11H8l-4 4V5Z" stroke="currentColor" strokeWidth="1.7" />
        </svg>
      );
    default:
      return null;
  }
}
