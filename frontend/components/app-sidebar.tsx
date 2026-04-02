"use client"

import Link from "next/link"
import { useState } from "react"
import {
  ChevronDown,
  DollarSign,
  GraduationCap,
  Home,
  Settings,
  TrendingUp,
  Users,
  Package,
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
import { useSchoolContext } from "@/hooks/useSchoolContext"
import { SchoolLogo } from "@/components/providers/SchoolThemeProvider"

const modules = [
  {
    title: "Dashboard",
    icon: Home,
    url: "/dashboard",
    isActive: true,
  },
  {
    title: "Students",
    icon: Users,
    items: [
      { title: "Student Directory", url: "/students" },
      { title: "Student Registration", url: "/students/enrollment" },
    ],
  },
  {
    title: "Finance & Billing",
    icon: DollarSign,
    items: [
      { title: "Finance Overview", url: "/finance" },
    ],
  },
  {
    title: "Analytics & Reports",
    icon: TrendingUp,
    items: [
      { title: "Analytics Dashboard", url: "/analytics" },
      { title: "Custom Reports", url: "/analytics/reports" },
    ],
  },
  {
    title: "Migration Services",
    icon: Package,
    items: [
      { title: "Migration Packages", url: "/migration" },
      { title: "Care Packages", url: "/admin/migration/care-packages" },
    ],
  },
]

const adminItems = [
  {
    title: "School Dashboard",
    icon: Settings,
    url: "/admin",
  },
  {
    title: "Reports",
    icon: TrendingUp,
    url: "/analytics/reports",
  },
]

export function AppSidebar() {
  const [openItems, setOpenItems] = useState<string[]>(["Students"])
  const schoolContext = useSchoolContext()

  const toggleItem = (title: string) => {
    setOpenItems((prev) => (prev.includes(title) ? prev.filter((item) => item !== title) : [...prev, title]))
  }

  const availableModules = modules.filter((module) => {
    if (module.title === "Finance & Billing") {
      return schoolContext?.hasFeature("finance_module")
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
              {schoolContext?.school?.name || "OneClass Platform"}
            </span>
            <span className="text-xs text-muted-foreground">
              {schoolContext?.school?.type ? `${schoolContext.school.type} School` : "School Management"}
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
                          <ChevronDown className="ml-auto h-4 w-4 transition-transform duration-200 group-data-[state=open]:rotate-180" />
                        </SidebarMenuButton>
                      </CollapsibleTrigger>
                      <CollapsibleContent>
                        <SidebarMenuSub>
                          {module.items.map((item) => (
                            <SidebarMenuSubItem key={item.title}>
                              <SidebarMenuSubButton asChild>
                                <Link href={item.url}>
                                  <span>{item.title}</span>
                                </Link>
                              </SidebarMenuSubButton>
                            </SidebarMenuSubItem>
                          ))}
                        </SidebarMenuSub>
                      </CollapsibleContent>
                    </Collapsible>
                  ) : (
                    <SidebarMenuButton asChild isActive={module.isActive}>
                      <Link href={module.url}>
                        <module.icon className="h-4 w-4" />
                        <span>{module.title}</span>
                      </Link>
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
                    <Link href={item.url}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </Link>
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
