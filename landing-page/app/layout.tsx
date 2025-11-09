import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Passez au Solaire - Simulez votre installation",
  description: "Calculez vos économies avec une installation solaire personnalisée",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
