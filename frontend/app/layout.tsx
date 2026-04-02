import type React from "react"
import type { Metadata } from "next"
import "./globals.css"

export const dynamic = 'force-dynamic'
import { QueryClientProvider } from "@/components/providers/QueryClientProvider"
import { SchoolThemeProvider } from "@/components/providers/SchoolThemeProvider"
import { ClerkProvider } from "@/components/providers/ClerkProvider"
import { LayoutContent } from "@/components/layout/LayoutContent"
import { ErrorBoundary } from "@/components/ui/error-boundary"
import { TenantProvider, TenantErrorBoundary } from "@/components/tenant/TenantProvider"

export const metadata: Metadata = {
  title: "OneClass - School Management Platform",
  description: "Comprehensive school management system for Zimbabwean schools",
  generator: 'OneClass Platform'
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="min-h-screen font-sans">
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
