import Link from "next/link";

const productLabel = {
  platform: "AI Platform",
  studio: "Studio",
  cinema: "Cinema",
  edit: "Edit",
  hub: "Production Hub",
  vertical: "Vertical Drama",
} as const;

type BrandMarkProps = {
  href?: string;
  product?: keyof typeof productLabel;
};

export function BrandMark({ href = "/", product = "platform" }: BrandMarkProps) {
  return (
    <Link href={href} className="group inline-flex items-center gap-3 min-w-0">
      <span className="ac-mark transition group-hover:border-[var(--gold-bright)] group-hover:shadow-[0_0_24px_rgba(197,161,94,0.2)]">
        AC
      </span>
      <span className="min-w-0">
        <span className="ac-display block text-[0.68rem] tracking-[0.34em] text-[var(--mist)] uppercase transition group-hover:text-[var(--gold-bright)]">
          Art City
        </span>
        <span className="block truncate text-[0.8rem] text-[var(--paper-dim)]">
          {productLabel[product]}
        </span>
      </span>
    </Link>
  );
}
