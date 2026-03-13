import { useQuery } from "@tanstack/react-query"

import { RolesService } from "@/client/crm-services"
import useAuth from "./useAuth"

export function usePermissions() {
  const { user } = useAuth()

  // role_id is added to the backend User model but the generated client
  // types may not yet include it. Cast to any as a temporary workaround
  // until the OpenAPI client is regenerated.
  const roleId = (user as any)?.role_id as string | undefined

  const { data: role } = useQuery({
    queryKey: ["role", roleId],
    queryFn: () => RolesService.readRole({ roleId: roleId! }),
    enabled: !!roleId,
  })

  const hasPermission = (resource: string, action: string): boolean => {
    return (
      role?.permissions?.some(
        (p: { resource: string; action: string }) =>
          p.resource === resource && p.action === action,
      ) ?? false
    )
  }

  return { hasPermission, role, roleName: role?.name }
}
