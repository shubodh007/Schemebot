import type { Metadata } from "next";
import { ThemeProvider } from "next-themes";
import { fontHeading, fontBody } from "@/lib/fonts";
import { cn } from "@/lib/utils";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "GovScheme AI — Discover Government Schemes You Qualify For",
    template: "%s | GovScheme AI",
  },
  description:
    "AI-powered platform that helps Indian citizens discover, understand, and apply for government welfare schemes they qualify for.",
  keywords: [
    "government schemes",
    "india",
    "welfare",
    "eligibility",
    "AI",
    "yojana",
    "subsidy",
  ],
  openGraph: {
    title: "GovScheme AI",
    description: "Discover every government scheme you qualify for",
    type: "website",
    locale: "en_IN",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning className="dark">
      <body className={cn(fontHeading.variable, fontBody.variable, "antialiased")}>
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem={false}
          storageKey="govscheme-theme"
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
