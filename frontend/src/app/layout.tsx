import type { Metadata } from "next";
import { Providers } from "@/components/providers";
import "@/styles/globals.css";
export const metadata: Metadata = { title: "Axyrel", description: "Work Smarter. Serve Better." };
export default function RootLayout({ children }: { children: React.ReactNode }) { return <html lang="en" dir="ltr"><body><Providers>{children}</Providers></body></html>; }
