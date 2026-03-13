import { useMutation, useQueryClient } from "@tanstack/react-query"
import { EllipsisVertical, ShieldCheck, ShieldOff } from "lucide-react"
import { useState } from "react"
import { UsersAdminService } from "@/client/crm-services"
import type { UserPublicCRM } from "@/client/crm-types"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import useAuth from "@/hooks/useAuth"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import EditUser from "./EditUser"

interface UserActionsMenuProps {
  user: UserPublicCRM
}

export const UserActionsMenu = ({ user }: UserActionsMenuProps) => {
  const [open, setOpen] = useState(false)
  const { user: currentUser } = useAuth()
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const activateMutation = useMutation({
    mutationFn: () => UsersAdminService.activateUser({ userId: user.id }),
    onSuccess: () => {
      showSuccessToast("User activated successfully")
      setOpen(false)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
    },
  })

  const deactivateMutation = useMutation({
    mutationFn: () => UsersAdminService.deactivateUser({ userId: user.id }),
    onSuccess: () => {
      showSuccessToast("User deactivated successfully")
      setOpen(false)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
    },
  })

  if (user.id === currentUser?.id) {
    return null
  }

  const isPending = activateMutation.isPending || deactivateMutation.isPending

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon">
          <EllipsisVertical />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <EditUser user={user} onSuccess={() => setOpen(false)} />
        <DropdownMenuSeparator />
        {user.is_active ? (
          <DropdownMenuItem
            variant="destructive"
            disabled={isPending}
            onClick={() => deactivateMutation.mutate()}
          >
            <ShieldOff />
            Deactivate
          </DropdownMenuItem>
        ) : (
          <DropdownMenuItem
            disabled={isPending}
            onClick={() => activateMutation.mutate()}
          >
            <ShieldCheck />
            Activate
          </DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
