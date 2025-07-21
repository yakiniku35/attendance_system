import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Analytics } from "@vercel/analytics/next";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Attendance System | Class Management",
  description: "A modern, secure, and user-friendly platform for managing class attendance.",
  openGraph: {
    title: "Attendance System | Class Management",
    description: "A modern, secure, and user-friendly platform for managing class attendance.",
    url: "https://attendance-system-one-kohl.vercel.app/",
    siteName: "Attendance System",
    images: [
      {
        url: "/next.svg",
        width: 180,
        height: 38,
        alt: "Attendance System Logo",
      },
    ],
    locale: "en_US",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
        {children}
        <Analytics />
      </body>
    </html>
  );
}
