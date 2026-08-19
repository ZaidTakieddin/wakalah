import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "WAKALAH Balance Demo",
  description: "A live trust-layer demo for agent-initiated financial transfers.",
  other: {
    "codex-preview": "development",
  },
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
