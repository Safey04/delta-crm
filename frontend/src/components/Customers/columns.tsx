import type { ColumnDef } from "@tanstack/react-table"
import { Link } from "@tanstack/react-router"

import type { CustomerPublic } from "@/client/crm-types"
import { Badge } from "@/components/ui/badge"
import { CustomerActionsMenu } from "./CustomerActionsMenu"

const segmentLabels: Record<string, string> = {
  enterprise: "Enterprise",
  smb: "SMB",
  walk_in: "Walk-in",
}

const segmentVariants: Record<string, "default" | "secondary" | "outline"> = {
  enterprise: "default",
  smb: "secondary",
  walk_in: "outline",
}

export const columns: ColumnDef<CustomerPublic>[] = [
  {
    accessorKey: "name",
    header: "Name",
    cell: ({ row }) => (
      <Link
        to="/customers/$customerId"
        params={{ customerId: row.original.id }}
        className="font-medium hover:underline"
      >
        {row.original.name}
      </Link>
    ),
  },
  {
    accessorKey: "company_name",
    header: "Company",
    cell: ({ row }) => (
      <span className="text-muted-foreground">
        {row.original.company_name || "—"}
      </span>
    ),
  },
  {
    accessorKey: "phone",
    header: "Phone",
    cell: ({ row }) => (
      <span className="text-muted-foreground">
        {row.original.phone || "—"}
      </span>
    ),
  },
  {
    accessorKey: "email",
    header: "Email",
    cell: ({ row }) => (
      <span className="text-muted-foreground">
        {row.original.email || "—"}
      </span>
    ),
  },
  {
    accessorKey: "segment",
    header: "Segment",
    cell: ({ row }) => {
      const segment = row.original.segment
      return (
        <Badge variant={segmentVariants[segment] ?? "outline"}>
          {segmentLabels[segment] ?? segment}
        </Badge>
      )
    },
  },
  {
    accessorKey: "is_active",
    header: "Status",
    cell: ({ row }) => (
      <Badge variant={row.original.is_active ? "default" : "secondary"}>
        {row.original.is_active ? "Active" : "Inactive"}
      </Badge>
    ),
  },
  {
    id: "actions",
    header: () => <span className="sr-only">Actions</span>,
    cell: ({ row }) => (
      <div className="flex justify-end">
        <CustomerActionsMenu customer={row.original} />
      </div>
    ),
  },
]
