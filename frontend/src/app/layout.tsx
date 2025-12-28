import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "FPL Team of the Week Predictor",
  description: "Predict the FPL Dream Team using machine learning",
  icons: {
    icon: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen">
          {/* Header */}
          <header className="bg-fpl-purple border-b border-fpl-purple-light/30">
            <div className="container mx-auto px-4 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-fpl-green font-bold text-xl">FPL</span>
                  <span className="text-white font-semibold text-xl">
                    Team of the Week Predictor
                  </span>
                </div>
                <nav className="flex gap-6">
                  <a
                    href="/"
                    className="text-white hover:text-fpl-green transition-colors"
                  >
                    Predictions
                  </a>
                  <a
                    href="/backtest"
                    className="text-white hover:text-fpl-green transition-colors"
                  >
                    Backtest
                  </a>
                </nav>
              </div>
            </div>
          </header>

          {/* Main content */}
          <main className="container mx-auto px-4 py-8">{children}</main>

          {/* Footer */}
          <footer className="bg-fpl-purple/50 border-t border-fpl-purple-light/20 mt-auto">
            <div className="container mx-auto px-4 py-4 text-center text-white/60 text-sm">
              FPL TOTW Predictor - Not affiliated with the Premier League
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
