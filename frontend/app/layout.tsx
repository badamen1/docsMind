import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "DocsMind - Chatea con tus Documentos",
  description:
    "Sube documentos y chatea con su contenido usando IA. Extrae información, haz preguntas y obtén respuestas al instante.",
  icons: {
    icon: "/icon.svg",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" className="dark">
      <body className={`${inter.className} bg-slate-900 text-slate-100`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
