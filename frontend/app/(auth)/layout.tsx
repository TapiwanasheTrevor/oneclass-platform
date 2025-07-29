import type React from "react"
import { Building2 } from "lucide-react"

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen flex flex-col lg:flex-row">
      {/* Left side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 p-12 text-white flex-col justify-between">
        <div className="space-y-6">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
              <Building2 className="w-7 h-7 text-white" />
            </div>
            <span className="text-3xl font-bold">OneClass</span>
          </div>
          
          <div className="space-y-4">
            <h1 className="text-4xl font-bold leading-tight">
              Empowering Education<br />in Zimbabwe
            </h1>
            <p className="text-xl text-blue-100 leading-relaxed">
              Comprehensive school management platform designed for Zimbabwean educational institutions.
            </p>
          </div>
        </div>

        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4">
            <div className="bg-white/10 p-4 rounded-lg backdrop-blur-sm">
              <h3 className="font-semibold text-lg">Multi-School Support</h3>
              <p className="text-blue-100 text-sm">
                Manage multiple institutions from a single platform
              </p>
            </div>
            <div className="bg-white/10 p-4 rounded-lg backdrop-blur-sm">
              <h3 className="font-semibold text-lg">Real-time Collaboration</h3>
              <p className="text-blue-100 text-sm">
                Seamless communication between teachers, parents, and students
              </p>
            </div>
          </div>
          
          <div className="text-center text-blue-200 text-sm">
            <p>© 2025 OneClass. Built for Zimbabwe's future.</p>
          </div>
        </div>
      </div>

      {/* Right side - Auth forms */}
      <div className="flex-1 flex items-center justify-center p-6 bg-gray-50">
        <div className="w-full max-w-md">
          {/* Mobile branding */}
          <div className="lg:hidden text-center mb-8">
            <div className="flex items-center justify-center space-x-2 mb-4">
              <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                <Building2 className="w-6 h-6 text-white" />
              </div>
              <span className="text-2xl font-bold text-gray-900">OneClass</span>
            </div>
            <p className="text-gray-600">Zimbabwe's Education Platform</p>
          </div>
          
          {children}
        </div>
      </div>
    </div>
  )
}