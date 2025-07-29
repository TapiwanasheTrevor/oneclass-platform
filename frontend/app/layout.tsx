import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { QueryClientProvider } from "@/components/providers/QueryClientProvider"
import { SchoolThemeProvider } from "@/components/providers/SchoolThemeProvider"
import { ClerkProvider } from "@/components/providers/ClerkProvider"
import { LayoutContent } from "@/components/layout/LayoutContent"
import { ErrorBoundary } from "@/components/ui/error-boundary"
import { TenantProvider, TenantErrorBoundary } from "@/components/tenant/TenantProvider"


const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "OneClass - School Management Platform",
  description: "Comprehensive school management system for Zimbabwean schools",
  generator: 'v0.dev'
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <ErrorBoundary>
          <QueryClientProvider>
            <ClerkProvider>
              <TenantProvider>
                <TenantErrorBoundary>
                  <SchoolThemeProvider>
                    <LayoutContent>
                      {children}
                    </LayoutContent>
                  </SchoolThemeProvider>
                </TenantErrorBoundary>
              </TenantProvider>
            </ClerkProvider>
          </QueryClientProvider>
        </ErrorBoundary>
      </body>
    </html>
  )
}
