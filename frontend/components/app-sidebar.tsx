"use client"

import { useState } from "react"
import {
  BookOpen,
  ChevronDown,
  DollarSign,
  GraduationCap,
  Home,
  MessageSquare,
  Settings,
  Shield,
  Trophy,
  TrendingUp,
  Users,
  Brain,
  Globe,
  Database,
} from "lucide-react"

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
} from "@/components/ui/sidebar"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Badge } from "@/components/ui/badge"
import { useSchoolContext, useFeatureAccess } from "@/hooks/useSchoolContext"
import { SchoolLogo } from "@/components/providers/SchoolThemeProvider"

const modules = [
  {
    title: "Dashboard",
    icon: Home,
    url: "/",
    isActive: true,
  },
  {
    title: "Student Information",
    icon: Users,
    items: [
      { title: "Student Directory", url: "/students" },
      { title: "Student Registration", url: "/students/enrollment" },
      { title: "Medical Records", url: "/students/medical" },
      { title: "Academic History", url: "/students/academic" },
    ],
  },
  {
    title: "Academic Management",
    icon: BookOpen,
    items: [
      { title: "Curriculum", url: "/academic/curriculum" },
      { title: "Lesson Plans", url: "/academic/lessons" },
      { title: "Assessments", url: "/academic/assessments" },
      { title: "Grade Books", url: "/academic/grades" },
    ],
  },
  {
    title: "Teacher Tools",
    icon: GraduationCap,
    items: [
      { title: "Class Management", url: "/teachers/classes" },
      { title: "Attendance", url: "/teachers/attendance" },
      { title: "Performance Analytics", url: "/teachers/analytics" },
      { title: "Resource Library", url: "/teachers/resources" },
    ],
  },
  {
    title: "Finance & Billing",
    icon: DollarSign,
    badge: "3",
    items: [
      { title: "Fee Structure", url: "/finance/fees" },
      { title: "Payments", url: "/finance/payments" },
      { title: "Invoices", url: "/finance/invoices" },
      { title: "Financial Reports", url: "/finance/reports" },
    ],
  },
  {
    title: "Communications",
    icon: MessageSquare,
    items: [
      { title: "Announcements", url: "/communications/announcements" },
      { title: "Parent Portal", url: "/communications/parents" },
      { title: "SMS & Email", url: "/communications/messaging" },
      { title: "Newsletters", url: "/communications/newsletters" },
    ],
  },
  {
    title: "Extracurricular",
    icon: Trophy,
    items: [
      { title: "Sports & Clubs", url: "/extracurricular/activities" },
      { title: "Events & Trips", url: "/extracurricular/events" },
      { title: "Competitions", url: "/extracurricular/competitions" },
      { title: "Media Gallery", url: "/extracurricular/gallery" },
    ],
  },
  {
    title: "Safety & Compliance",
    icon: Shield,
    items: [
      { title: "Indemnity Forms", url: "/safety/forms" },
      { title: "Disciplinary Records", url: "/safety/discipline" },
      { title: "Emergency Contacts", url: "/safety/emergency" },
      { title: "Privacy Management", url: "/safety/privacy" },
    ],
  },
  {
    title: "AI Learning Tools",
    icon: Brain,
    badge: "New",
    items: [
      { title: "Adaptive Learning", url: "/ai/adaptive" },
      { title: "Auto Lesson Generation", url: "/ai/lessons" },
      { title: "Performance Insights", url: "/ai/insights" },
      { title: "Personalized Content", url: "/ai/content" },
    ],
  },
  {
    title: "Analytics & Reports",
    icon: TrendingUp,
    requiredModule: "advanced_reporting",
    items: [
      { title: "Analytics Dashboard", url: "/analytics" },
      { title: "Custom Reports", url: "/analytics/reports" },
      { title: "Data Insights", url: "/analytics/insights" },
      { title: "Export Data", url: "/analytics/export" },
    ],
  },
  {
    title: "Ministry Dashboard",
    icon: Globe,
    items: [
      { title: "Performance Reports", url: "/ministry/performance" },
      { title: "Curriculum Compliance", url: "/ministry/compliance" },
      { title: "Statistical Analysis", url: "/ministry/statistics" },
      { title: "Data Exports", url: "/ministry/exports" },
    ],
  },
]

const adminItems = [
  {
    title: "System Settings",
    icon: Settings,
    url: "/admin/settings",
  },
  {
    title: "User Management",
    icon: Users,
    url: "/admin/users",
  },
  {
    title: "Data Management",
    icon: Database,
    url: "/admin/data",
  },
  {
    title: "Analytics",
    icon: TrendingUp,
    url: "/admin/analytics",
  },
]

export function AppSidebar() {
  const [openItems, setOpenItems] = useState<string[]>(["Student Information"])
  const schoolContext = useSchoolContext()

  const toggleItem = (title: string) => {
    setOpenItems((prev) => (prev.includes(title) ? prev.filter((item) => item !== title) : [...prev, title]))
  }

  // Filter modules based on available features
  const availableModules = modules.filter(module => {
    const featureMap: Record<string, string> = {
      "Finance & Billing": "finance_module",
      "AI Learning Tools": "ai_assistance",
      "Ministry Dashboard": "ministry_reporting",
    }
    
    const requiredFeature = featureMap[module.title]
    if (requiredFeature) {
      return schoolContext?.hasFeature(requiredFeature)
    }
    return true
  })

  return (
    <Sidebar>
      <SidebarHeader className="border-b border-sidebar-border">
        <div className="flex items-center gap-2 px-2 py-2">
          <SchoolLogo 
            className="h-8 w-8 rounded-lg"
            fallback={
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <GraduationCap className="h-4 w-4" />
              </div>
            }
          />
          <div className="flex flex-col">
            <span className="text-sm font-semibold">
              {schoolContext?.school.name || "OneClass Platform"}
            </span>
            <span className="text-xs text-muted-foreground">
              {schoolContext?.school.type ? `${schoolContext.school.type} School` : "School Management"}
            </span>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Main Modules</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {availableModules.map((module) => (
                <SidebarMenuItem key={module.title}>
                  {module.items ? (
                    <Collapsible open={openItems.includes(module.title)} onOpenChange={() => toggleItem(module.title)}>
                      <CollapsibleTrigger asChild>
                        <SidebarMenuButton className="w-full">
                          <module.icon className="h-4 w-4" />
                          <span>{module.title}</span>
                          {module.badge && (
                            <Badge variant="secondary" className="ml-auto text-xs">
                              {module.badge}
                            </Badge>
                          )}
                          <ChevronDown className="ml-auto h-4 w-4 transition-transform duration-200 group-data-[state=open]:rotate-180" />
                        </SidebarMenuButton>
                      </CollapsibleTrigger>
                      <CollapsibleContent>
                        <SidebarMenuSub>
                          {module.items.map((item) => (
                            <SidebarMenuSubItem key={item.title}>
                              <SidebarMenuSubButton asChild>
                                <a href={item.url}>
                                  <span>{item.title}</span>
                                </a>
                              </SidebarMenuSubButton>
                            </SidebarMenuSubItem>
                          ))}
                        </SidebarMenuSub>
                      </CollapsibleContent>
                    </Collapsible>
                  ) : (
                    <SidebarMenuButton asChild isActive={module.isActive}>
                      <a href={module.url}>
                        <module.icon className="h-4 w-4" />
                        <span>{module.title}</span>
                      </a>
                    </SidebarMenuButton>
                  )}
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel>Administration</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {adminItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <a href={item.url}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t border-sidebar-border">
        <div className="p-2">
          <div className="rounded-lg bg-muted p-3">
            <div className="flex items-center gap-2 mb-2">
              <div className="h-2 w-2 rounded-full bg-green-500"></div>
              <span className="text-xs font-medium">System Status</span>
            </div>
            <p className="text-xs text-muted-foreground">All systems operational</p>
            <p className="text-xs text-muted-foreground">Last sync: 2 min ago</p>
          </div>
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}
