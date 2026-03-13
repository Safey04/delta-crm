import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import {
  CustomersService,
  ServiceRequestsService,
  UsersAdminService,
} from "@/client/crm-services"
import type { UserPublicCRM } from "@/client/crm-types"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import useAuth from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
  head: () => ({ meta: [{ title: "Dashboard - Delta CRM" }] }),
})

type KpiCard = {
  readonly title: string
  readonly value: number | string
  readonly loading: boolean
}

function KpiCardView({ title, value, loading }: KpiCard) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-8 w-16" />
        ) : (
          <p className="text-3xl font-bold">{value}</p>
        )}
      </CardContent>
    </Card>
  )
}

function useCurrentUserCRM(userId: string | undefined) {
  return useQuery<UserPublicCRM>({
    queryKey: ["currentUserCRM", userId],
    queryFn: () => UsersAdminService.readUser({ userId: userId! }),
    enabled: !!userId,
  })
}

function getRoleName(crmUser: UserPublicCRM | undefined): string {
  return crmUser?.role?.name ?? "unknown"
}

function ManagerDashboard() {
  const { data: customers, isLoading: customersLoading } = useQuery({
    queryKey: ["dashboard", "customers-count"],
    queryFn: () => CustomersService.readCustomers({ limit: 1 }),
  })

  const { data: openRequests, isLoading: openLoading } = useQuery({
    queryKey: ["dashboard", "open-requests"],
    queryFn: () =>
      ServiceRequestsService.readServiceRequests({ status: "open", limit: 1 }),
  })

  const { data: slaBreached, isLoading: slaLoading } = useQuery({
    queryKey: ["dashboard", "sla-breached"],
    queryFn: () => ServiceRequestsService.readServiceRequests({ limit: 100 }),
    select: (data) => ({
      count: data.data.filter(
        (r) => r.sla_response_breached || r.sla_resolution_breached,
      ).length,
    }),
  })

  const { data: unassigned, isLoading: unassignedLoading } = useQuery({
    queryKey: ["dashboard", "unassigned-requests"],
    queryFn: () =>
      ServiceRequestsService.readServiceRequests({
        status: "open",
        assigned_engineer_id: "unassigned",
        limit: 1,
      }),
  })

  const cards: readonly KpiCard[] = [
    {
      title: "Total Customers",
      value: customers?.count ?? 0,
      loading: customersLoading,
    },
    {
      title: "Open Service Requests",
      value: openRequests?.count ?? 0,
      loading: openLoading,
    },
    {
      title: "SLA Breaches",
      value: slaBreached?.count ?? 0,
      loading: slaLoading,
    },
    {
      title: "Unassigned Requests",
      value: unassigned?.count ?? 0,
      loading: unassignedLoading,
    },
  ]

  return <KpiGrid cards={cards} />
}

function SupportDashboard({ userId }: { readonly userId: string }) {
  const { data: myOpen, isLoading: myOpenLoading } = useQuery({
    queryKey: ["dashboard", "my-open-tickets", userId],
    queryFn: () => ServiceRequestsService.readServiceRequests({ limit: 100 }),
    select: (data) => ({
      count: data.data.filter(
        (r) => r.created_by === userId && r.status !== "closed",
      ).length,
    }),
  })

  const { data: todayNew, isLoading: todayLoading } = useQuery({
    queryKey: ["dashboard", "today-new-tickets"],
    queryFn: () => ServiceRequestsService.readServiceRequests({ limit: 100 }),
    select: (data) => {
      const today = new Date().toISOString().slice(0, 10)
      return {
        count: data.data.filter((r) => r.created_at?.slice(0, 10) === today)
          .length,
      }
    },
  })

  const cards: readonly KpiCard[] = [
    {
      title: "My Open Tickets",
      value: myOpen?.count ?? 0,
      loading: myOpenLoading,
    },
    {
      title: "Today's New Tickets",
      value: todayNew?.count ?? 0,
      loading: todayLoading,
    },
  ]

  return <KpiGrid cards={cards} />
}

function EngineerDashboard({ userId }: { readonly userId: string }) {
  const { data: myAssigned, isLoading: assignedLoading } = useQuery({
    queryKey: ["dashboard", "my-assigned", userId],
    queryFn: () =>
      ServiceRequestsService.readServiceRequests({
        assigned_engineer_id: userId,
        limit: 1,
      }),
  })

  const { data: inProgress, isLoading: progressLoading } = useQuery({
    queryKey: ["dashboard", "in-progress", userId],
    queryFn: () =>
      ServiceRequestsService.readServiceRequests({
        assigned_engineer_id: userId,
        status: "in_progress",
        limit: 1,
      }),
  })

  const cards: readonly KpiCard[] = [
    {
      title: "My Assigned Tickets",
      value: myAssigned?.count ?? 0,
      loading: assignedLoading,
    },
    {
      title: "In-Progress Tickets",
      value: inProgress?.count ?? 0,
      loading: progressLoading,
    },
  ]

  return <KpiGrid cards={cards} />
}

function WarehouseDashboard() {
  const cards: readonly KpiCard[] = [
    { title: "Inventory Items", value: "Coming in Phase 2", loading: false },
    { title: "Pending Orders", value: "Coming in Phase 2", loading: false },
    { title: "Low Stock Alerts", value: "Coming in Phase 2", loading: false },
  ]

  return <KpiGrid cards={cards} />
}

function KpiGrid({ cards }: { readonly cards: readonly KpiCard[] }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => (
        <KpiCardView key={card.title} {...card} />
      ))}
    </div>
  )
}

function RoleDashboard({
  roleName,
  userId,
}: {
  readonly roleName: string
  readonly userId: string
}) {
  switch (roleName.toLowerCase()) {
    case "manager":
      return <ManagerDashboard />
    case "support":
      return <SupportDashboard userId={userId} />
    case "engineer":
      return <EngineerDashboard userId={userId} />
    case "warehouse":
      return <WarehouseDashboard />
    default:
      return <ManagerDashboard />
  }
}

function Dashboard() {
  const { user: currentUser } = useAuth()
  const { data: crmUser, isLoading: crmUserLoading } = useCurrentUserCRM(
    currentUser?.id,
  )

  const roleName = getRoleName(crmUser)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl truncate max-w-sm">
          Hi, {currentUser?.full_name || currentUser?.email}
        </h1>
        <p className="text-muted-foreground">
          {crmUserLoading
            ? "Loading your dashboard..."
            : `Role: ${roleName.charAt(0).toUpperCase() + roleName.slice(1)}`}
        </p>
      </div>

      {crmUserLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={`skeleton-${i}`}>
              <CardHeader>
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <RoleDashboard roleName={roleName} userId={currentUser?.id ?? ""} />
      )}
    </div>
  )
}
