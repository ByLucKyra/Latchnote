import type { InlineIcon as IconData } from "../lib/icon";

interface Props {
  icon: IconData;
  size?: number;
  className?: string;
}

/** Renders build-time Phosphor markup. The body is static package data. */
export default function InlineIcon({ icon, size = 16, className }: Props) {
  return (
    <svg
      viewBox={icon.viewBox}
      width={size}
      height={size}
      fill="currentColor"
      aria-hidden="true"
      className={className}
      dangerouslySetInnerHTML={{ __html: icon.body }}
    />
  );
}
