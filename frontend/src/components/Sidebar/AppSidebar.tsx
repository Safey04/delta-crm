import { Briefcase, Home, Printer, Settings, Users, Wrench } from "lucide-react"

import { SidebarAppearance } from "@/components/Common/Appearance"
import { Logo } from "@/components/Common/Logo"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
} from "@/components/ui/sidebar"
import useAuth from "@/hooks/useAuth"
import { usePermissions } from "@/hooks/usePermissions"
import { type Item, Main } from "./Main"
import { User } from "./User"

function buildNavItems(
  hasPermission: (resource: string, action: string) => boolean,
  isSuperuser: boolean,
): Item[] {
  const items: Item[] = [{ icon: Home, title: "Dashboard", path: "/" }]

  if (hasPermission("customer", "view")) {
    items.push({ icon: Users, title: "Customers", path: "/customers" })
    items.push({ icon: Printer, title: "Equipment", path: "/equipment" })
  }

  if (hasPermission("service_request", "view")) {
    items.push({
      icon: Wrench,
      title: "Service Requests",
      path: "/service-requests",
    })
  }

  items.push({ icon: Briefcase, title: "Items", path: "/items" })

  if (isSuperuser || hasPermission("user", "view")) {
    items.push({ icon: Settings, title: "Admin", path: "/admin" })
  }

  return items
}

export function AppSidebar() {
  const { user: currentUser } = useAuth()
  const { hasPermission } = usePermissions()

  const items = buildNavItems(hasPermission, currentUser?.is_superuser ?? false)

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="px-4 py-6 group-data-[collapsible=icon]:px-0 group-data-[collapsible=icon]:items-center">
        <Logo variant="responsive" />
      </SidebarHeader>
      <SidebarContent>
        <Main items={items} />
      </SidebarContent>
      <SidebarFooter>
        <SidebarAppearance />
        <User user={currentUser} />
      </SidebarFooter>
    </Sidebar>
  )
}

export default AppSidebar
