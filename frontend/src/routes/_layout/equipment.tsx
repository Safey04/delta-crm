import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Printer, Search } from "lucide-react"
import { Suspense, useState } from "react"

import { EquipmentService } from "@/client/crm-services"
import type { EquipmentPublic } from "@/client/crm-types"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

export const Route = createFileRoute("/_layout/equipment")({
  component: Equipment,
  head: () => ({
    meta: [{ title: "Equipment - Delta CRM" }],
  }),
})

function isWarrantyExpired(date: string | null) {
  if (!date) return false
  return new Date(date) < new Date()
}

function EquipmentTableContent({ search }: { search: string }) {
  const { data: equipment } = useSuspenseQuery({
    queryKey: ["equipment-global", search],
    queryFn: () =>
      EquipmentService.readEquipment({
        skip: 0,
        limit: 100,
        search: search || null,
      }),
  })

  if (equipment.data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-muted p-4 mb-4">
          <Printer className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">
          {search ? "No equipment matches your search" : "No equipment yet"}
        </h3>
        <p className="text-muted-foreground">
          {search
            ? "Try a different search term"
            : "Equipment is added through customer profiles"}
        </p>
      </div>
    )
  }

  return (
    <>
      <Badge variant="outline" className="w-fit">
        {equipment.count} total
      </Badge>
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead>Serial #</TableHead>
            <TableHead>Model</TableHead>
            <TableHead>Manufacturer</TableHead>
            <TableHead>Install Date</TableHead>
            <TableHead>Warranty</TableHead>
            <TableHead>Status</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {equipment.data.map((eq: EquipmentPublic) => (
            <TableRow key={eq.id}>
              <TableCell className="font-mono text-sm">
                {eq.serial_number}
              </TableCell>
              <TableCell className="font-medium">{eq.model}</TableCell>
              <TableCell className="text-muted-foreground">
                {eq.manufacturer || "—"}
              </TableCell>
              <TableCell className="text-muted-foreground">
                {eq.install_date || "—"}
              </TableCell>
              <TableCell>
                {eq.warranty_expiry ? (
                  <Badge
                    variant={
                      isWarrantyExpired(eq.warranty_expiry)
                        ? "secondary"
                        : "default"
                    }
                  >
                    {isWarrantyExpired(eq.warranty_expiry)
                      ? "Expired"
                      : eq.warranty_expiry}
                  </Badge>
                ) : (
                  <span className="text-muted-foreground">—</span>
                )}
              </TableCell>
              <TableCell>
                <Badge variant={eq.is_active ? "default" : "secondary"}>
                  {eq.is_active ? "Active" : "Inactive"}
                </Badge>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </>
  )
}

function Equipment() {
  const [search, setSearch] = useState("")

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Equipment</h1>
        <p className="text-muted-foreground">
          All registered equipment across customers
        </p>
      </div>

      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search by serial, model..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
        />
      </div>

      <Suspense
        fallback={
          <div className="space-y-3">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        }
      >
        <EquipmentTableContent search={search} />
      </Suspense>
    </div>
  )
}
