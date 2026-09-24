import "./globals.css";
import type { Metadata } from "next";
import { NavBar } from "./NavBar";
import { Footer } from "./Footer";
import { LanguageProvider } from "@/lib/i18n";

export const metadata: Metadata = {
  title: "ChungaMama",
  description: "Kitabu chako cha afya, sasa kinazungumza nawe.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="sw">
      <body className="font-body">
        <LanguageProvider>
          <NavBar />
          <div className="max-w-6xl mx-auto px-7">{children}</div>
          <Footer />
        </LanguageProvider>
      </body>
    </html>
  );
}
