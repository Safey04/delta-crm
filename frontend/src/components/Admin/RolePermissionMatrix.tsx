import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useCallback, useMemo } from "react"

import { RolesService } from "@/client/crm-services"
import type { PermissionPublic } from "@/client/crm-types"
import { Checkbox } from "@/components/ui/checkbox"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

type Props = {
  roleId: string
  roleName: string
}

const RESOURCE_LABELS: Record<string, string> = {
  customer: "Customer",
  service_request: "Service Request",
  equipment: "Equipment",
  user: "User",
  inventory: "Inventory",
  quotation: "Quotation",
}

const ACTION_LABELS: Record<string, string> = {
  view: "View",
  create: "Create",
  edit: "Edit",
  delete: "Delete",
  approve: "Approve",
  export: "Export",
}

function buildPermissionGrid(allPermissions: PermissionPublic[]) {
  const resources = new Set<string>()
  const actions = new Set<string>()
  const permissionMap = new Map<string, PermissionPublic>()

  for (const perm of allPermissions) {
    resources.add(perm.resource)
    actions.add(perm.action)
    permissionMap.set(`${perm.resource}:${perm.action}`, perm)
  }

  const resourceOrder = Object.keys(RESOURCE_LABELS)
  const actionOrder = Object.keys(ACTION_LABELS)

  const sortedResources = [...resources].sort(
    (a, b) =>
      (resourceOrder.indexOf(a) ?? 99) - (resourceOrder.indexOf(b) ?? 99),
  )
  const sortedActions = [...actions].sort(
    (a, b) => (actionOrder.indexOf(a) ?? 99) - (actionOrder.indexOf(b) ?? 99),
  )

  return { sortedResources, sortedActions, permissionMap }
}

function RolePermissionMatrix({ roleId, roleName }: Props) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const { data: allPermissions, isLoading: loadingPermissions } = useQuery({
    queryKey: ["permissions"],
    queryFn: () => RolesService.readPermissions(),
  })

  const { data: roleDetail, isLoading: loadingRole } = useQuery({
    queryKey: ["roles", roleId],
    queryFn: () => RolesService.readRole({ roleId }),
  })

  const activePermissionIds = useMemo(
    () => new Set(roleDetail?.permissions.map((p) => p.id) ?? []),
    [roleDetail?.permissions],
  )

  const grid = useMemo(
    () => (allPermissions ? buildPermissionGrid(allPermissions.data) : null),
    [allPermissions],
  )

  const mutation = useMutation({
    mutationFn: (permissionIds: string[]) =>
      RolesService.setRolePermissions({
        roleId,
        requestBody: { permission_ids: permissionIds },
      }),
    onSuccess: () => {
      showSuccessToast(`Permissions updated for ${roleName}`)
      queryClient.invalidateQueries({ queryKey: ["roles", roleId] })
    },
    onError: handleError.bind(showErrorToast),
  })

  const handleToggle = useCallback(
    (permissionId: string, checked: boolean) => {
      const updated = checked
        ? [...activePermissionIds, permissionId]
        : [...activePermissionIds].filter((id) => id !== permissionId)
      mutation.mutate(updated)
    },
    [activePermissionIds, mutation],
  )

  if (loadingPermissions || loadingRole || !grid) {
    return (
      <div className="space-y-3 p-4">
        <Skeleton className="h-8 w-full" />
        <Skeleton className="h-8 w-full" />
        <Skeleton className="h-8 w-full" />
      </div>
    )
  }

  const { sortedResources, sortedActions, permissionMap } = grid

  return (
    <TooltipProvider>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="min-w-[140px]">Resource</TableHead>
            {sortedActions.map((action) => (
              <TableHead key={action} className="text-center">
                {ACTION_LABELS[action] ?? action}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {sortedResources.map((resource) => (
            <TableRow key={resource}>
              <TableCell className="font-medium">
                {RESOURCE_LABELS[resource] ?? resource}
              </TableCell>
              {sortedActions.map((action) => {
                const perm = permissionMap.get(`${resource}:${action}`)
                if (!perm) {
                  return (
                    <TableCell key={action} className="text-center">
                      <span className="text-muted-foreground">--</span>
                    </TableCell>
                  )
                }
                const isActive = activePermissionIds.has(perm.id)
                return (
                  <TableCell key={action} className="text-center">
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <div className="inline-flex items-center justify-center">
                          <Checkbox
                            checked={isActive}
                            disabled={mutation.isPending}
                            onCheckedChange={(checked) =>
                              handleToggle(perm.id, checked === true)
                            }
                          />
                        </div>
                      </TooltipTrigger>
                      {perm.description && (
                        <TooltipContent>
                          <p>{perm.description}</p>
                        </TooltipContent>
                      )}
                    </Tooltip>
                  </TableCell>
                )
              })}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TooltipProvider>
  )
}

export default RolePermissionMatrix
