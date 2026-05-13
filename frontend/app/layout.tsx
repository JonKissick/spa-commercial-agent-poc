import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SPA Commercial Evaluation Agent",
  description: "Proof of concept commercial evaluation agent for SPA contracts",
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
