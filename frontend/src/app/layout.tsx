import type { Metadata } from "next";
import { Figtree, Literata, Noto_Sans_Arabic, Syne } from "next/font/google";
import { Providers } from "@/components/Providers";
import "./globals.css";

const syne = Syne({
  variable: "--font-syne",
  subsets: ["latin"],
  weight: ["500", "600", "700", "800"],
});

const figtree = Figtree({
  variable: "--font-figtree",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const literata = Literata({
  variable: "--font-literata",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

const notoArabic = Noto_Sans_Arabic({
  variable: "--font-kurdish",
  subsets: ["arabic"],
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: {
    default: "Art City AI Studio",
    template: "%s · Art City AI Studio",
  },
  description:
    "Art City’s proprietary AI production studio for cinema-grade video, image, voice, and music workflows.",
  applicationName: "Art City AI Studio",
  icons: {
    icon: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${syne.variable} ${figtree.variable} ${literata.variable} ${notoArabic.variable} antialiased`}
      >
        <div className="ac-shell">
          <div className="ac-grain" aria-hidden />
          <div className="ac-vignette" aria-hidden />
          <div className="ac-content">
            <Providers>{children}</Providers>
          </div>
        </div>
      </body>
    </html>
  );
}
