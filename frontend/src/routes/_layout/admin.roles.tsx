import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { ChevronDown, ChevronRight, Shield } from "lucide-react"
import { useState } from "react"

import { RolesService } from "@/client/crm-services"
import AddRole from "@/components/Admin/AddRole"
import DeleteRole from "@/components/Admin/DeleteRole"
import RolePermissionMatrix from "@/components/Admin/RolePermissionMatrix"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

export const Route = createFileRoute("/_layout/admin/roles")({
  component: AdminRoles,
  head: () => ({ meta: [{ title: "Roles - Delta CRM" }] }),
})

function RolesTableSkeleton() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-10 w-full" />
    </div>
  )
}

function RolesTable() {
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const { data: roles, isLoading } = useQuery({
    queryKey: ["roles"],
    queryFn: () => RolesService.readRoles(),
  })

  if (isLoading) {
    return <RolesTableSkeleton />
  }

  if (!roles || roles.data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-muted p-4 mb-4">
          <Shield className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">No roles yet</h3>
        <p className="text-muted-foreground">
          Create a role to start managing permissions
        </p>
      </div>
    )
  }

  return (
    <>
      <Badge variant="outline">{roles.count} total</Badge>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-10" />
            <TableHead>Name</TableHead>
            <TableHead>Description</TableHead>
            <TableHead>Type</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {roles.data.map((role) => {
            const isExpanded = expandedId === role.id
            return (
              <>
                <TableRow
                  key={role.id}
                  className="cursor-pointer"
                  onClick={() => setExpandedId(isExpanded ? null : role.id)}
                >
                  <TableCell>
                    {isExpanded ? (
                      <ChevronDown className="h-4 w-4" />
                    ) : (
                      <ChevronRight className="h-4 w-4" />
                    )}
                  </TableCell>
                  <TableCell className="font-medium">{role.name}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {role.description ?? "--"}
                  </TableCell>
                  <TableCell>
                    {role.is_system ? (
                      <Badge variant="secondary">System</Badge>
                    ) : (
                      <Badge variant="outline">Custom</Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    {/* biome-ignore lint/a11y/noStaticElementInteractions: stop propagation wrapper for row click */}
                    <span
                      onClick={(e) => e.stopPropagation()}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.stopPropagation()
                        }
                      }}
                    >
                      <DeleteRole role={role} />
                    </span>
                  </TableCell>
                </TableRow>
                {isExpanded && (
                  <TableRow key={`${role.id}-matrix`}>
                    <TableCell colSpan={5} className="bg-muted/30 p-0">
                      <div className="p-4">
                        <h4 className="text-sm font-semibold mb-3">
                          Permissions for {role.name}
                        </h4>
                        <RolePermissionMatrix
                          roleId={role.id}
                          roleName={role.name}
                        />
                      </div>
                    </TableCell>
                  </TableRow>
                )}
              </>
            )
          })}
        </TableBody>
      </Table>
    </>
  )
}

function AdminRoles() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Roles</h1>
          <p className="text-muted-foreground">
            Manage roles and their permissions
          </p>
        </div>
        <AddRole />
      </div>
      <RolesTable />
    </div>
  )
}
