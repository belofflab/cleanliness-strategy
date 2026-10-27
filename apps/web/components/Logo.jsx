// Логотип «Точка Чистоты» (ТЗ п.5): знак-капля с точкой + словесная часть.
// SVG инлайном — ноль сетевых запросов, чёткость на любом экране.

export function LogoMark({ size = 34 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="tc-logo-gradient" x1="4" y1="2" x2="28" y2="30" gradientUnits="userSpaceOnUse">
          <stop stopColor="#0EA5E9" />
          <stop offset="1" stopColor="#0369A1" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="9" fill="url(#tc-logo-gradient)" />
      <path
        d="M16 5.8c3.9 4.4 6.3 7.6 6.3 10.8a6.3 6.3 0 1 1-12.6 0c0-3.2 2.4-6.4 6.3-10.8Z"
        fill="#fff"
      />
      <circle cx="16" cy="17.1" r="2.4" fill="#0EA5E9" />
      <path
        d="M24.6 4.4l.62 1.58 1.58.62-1.58.62-.62 1.58-.62-1.58-1.58-.62 1.58-.62.62-1.58Z"
        fill="#E0F2FE"
      />
    </svg>
  );
}

export default function Logo({ size = 34, textClassName = "" }) {
  return (
    <span className="inline-flex items-center gap-2.5">
      <LogoMark size={size} />
      <span className={`font-display font-semibold leading-tight tracking-tight ${textClassName}`}>
        Точка{" "}
        <span className="text-brand-deep">Чистоты</span>
      </span>
    </span>
  );
}
