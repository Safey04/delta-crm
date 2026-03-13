import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Search, Users } from "lucide-react"
import { Suspense, useState } from "react"

import { CustomersService } from "@/client/crm-services"
import { DataTable } from "@/components/Common/DataTable"
import AddCustomer from "@/components/Customers/AddCustomer"
import { columns } from "@/components/Customers/columns"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"

function getCustomersQueryOptions(params?: {
  search?: string
  segment?: string | null
}) {
  return {
    queryFn: () =>
      CustomersService.readCustomers({
        skip: 0,
        limit: 100,
        search: params?.search || null,
        segment: params?.segment || null,
      }),
    queryKey: ["customers", params?.search ?? "", params?.segment ?? ""],
  }
}

export const Route = createFileRoute("/_layout/customers")({
  component: Customers,
  head: () => ({
    meta: [
      {
        title: "Customers - Delta CRM",
      },
    ],
  }),
})

function CustomersTableContent({
  search,
  segment,
}: {
  search: string
  segment: string | null
}) {
  const { data: customers } = useSuspenseQuery(
    getCustomersQueryOptions({ search: search || undefined, segment }),
  )

  if (customers.data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-muted p-4 mb-4">
          <Users className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">
          {search || segment
            ? "No customers match your filters"
            : "No customers yet"}
        </h3>
        <p className="text-muted-foreground">
          {search || segment
            ? "Try adjusting your search or filters"
            : "Add a new customer to get started"}
        </p>
      </div>
    )
  }

  return (
    <>
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Badge variant="outline">{customers.count} total</Badge>
      </div>
      <DataTable columns={columns} data={customers.data} />
    </>
  )
}

function CustomersTableSkeleton() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-10 w-full" />
    </div>
  )
}

function Customers() {
  const [search, setSearch] = useState("")
  const [segment, setSegment] = useState<string | null>(null)

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Customers</h1>
          <p className="text-muted-foreground">
            Manage your customers and their information
          </p>
        </div>
        <AddCustomer />
      </div>

      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search customers..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select
          value={segment ?? "all"}
          onValueChange={(value) => setSegment(value === "all" ? null : value)}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="All segments" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All segments</SelectItem>
            <SelectItem value="enterprise">Enterprise</SelectItem>
            <SelectItem value="smb">SMB</SelectItem>
            <SelectItem value="walk_in">Walk-in</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Suspense fallback={<CustomersTableSkeleton />}>
        <CustomersTableContent search={search} segment={segment} />
      </Suspense>
    </div>
  )
}
