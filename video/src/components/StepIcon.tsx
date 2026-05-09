import React from "react";

type IconKey =
  | "sprint"
  | "architecture"
  | "build"
  | "lint"
  | "test"
  | "security"
  | "loop"
  | "commit"
  | "pr"
  | "review";

const icons: Record<IconKey, React.ReactNode> = {
  sprint: (
    <>
      <circle cx="32" cy="32" r="22" />
      <path d="M22 32 L30 40 L44 24" strokeLinecap="round" />
    </>
  ),
  architecture: (
    <>
      <rect x="10" y="10" width="20" height="20" rx="3" />
      <rect x="34" y="10" width="20" height="20" rx="3" />
      <rect x="22" y="34" width="20" height="20" rx="3" />
      <line x1="20" y1="30" x2="32" y2="34" />
      <line x1="44" y1="30" x2="32" y2="34" />
    </>
  ),
  build: (
    <>
      <path d="M14 38 L30 22 L36 28 L20 44 Z" />
      <path d="M36 22 L42 28" strokeLinecap="round" />
      <circle cx="46" cy="18" r="4" />
    </>
  ),
  lint: (
    <>
      <rect x="12" y="12" width="40" height="40" rx="6" />
      <path d="M20 26 L26 32 L36 22" strokeLinecap="round" />
      <line x1="20" y1="40" x2="44" y2="40" strokeLinecap="round" />
    </>
  ),
  test: (
    <>
      <path d="M24 10 H40 V22 L48 44 C50 50 46 54 40 54 H24 C18 54 14 50 16 44 L24 22 Z" />
      <line x1="24" y1="22" x2="40" y2="22" />
      <circle cx="28" cy="44" r="2" fill="currentColor" stroke="none" />
      <circle cx="36" cy="40" r="2.5" fill="currentColor" stroke="none" />
    </>
  ),
  security: (
    <>
      <path d="M32 8 L52 18 V32 C52 44 42 52 32 56 C22 52 12 44 12 32 V18 Z" />
      <path d="M24 32 L30 38 L42 24" strokeLinecap="round" />
    </>
  ),
  loop: (
    <>
      <path d="M16 28 A16 16 0 0 1 48 28" strokeLinecap="round" />
      <path d="M48 36 A16 16 0 0 1 16 36" strokeLinecap="round" />
      <path d="M44 22 L48 28 L42 30" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M20 42 L16 36 L22 34" strokeLinecap="round" strokeLinejoin="round" />
    </>
  ),
  commit: (
    <>
      <line x1="32" y1="10" x2="32" y2="26" />
      <line x1="32" y1="38" x2="32" y2="54" />
      <circle cx="32" cy="32" r="8" />
    </>
  ),
  pr: (
    <>
      <circle cx="18" cy="16" r="4" />
      <circle cx="18" cy="48" r="4" />
      <circle cx="46" cy="48" r="4" />
      <line x1="18" y1="20" x2="18" y2="44" />
      <path d="M46 44 V28 A6 6 0 0 0 40 22 H30" strokeLinecap="round" />
      <path d="M34 18 L30 22 L34 26" strokeLinecap="round" strokeLinejoin="round" />
    </>
  ),
  review: (
    <>
      <circle cx="28" cy="28" r="14" />
      <line x1="38" y1="38" x2="52" y2="52" strokeLinecap="round" />
      <line x1="22" y1="28" x2="34" y2="28" />
      <line x1="22" y1="34" x2="30" y2="34" />
    </>
  ),
};

type Props = {
  name: IconKey;
  size?: number;
  color?: string;
  strokeWidth?: number;
};

export const StepIcon: React.FC<Props> = ({
  name,
  size = 80,
  color = "white",
  strokeWidth = 3,
}) => {
  return (
    <svg
      viewBox="0 0 64 64"
      width={size}
      height={size}
      fill="none"
      stroke={color}
      strokeWidth={strokeWidth}
      strokeLinejoin="round"
    >
      {icons[name]}
    </svg>
  );
};

export type { IconKey };
