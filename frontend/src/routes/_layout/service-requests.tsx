import { zodResolver } from "@hookform/resolvers/zod"
import {
  useMutation,
  useQuery,
  useQueryClient,
  useSuspenseQuery,
} from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { Plus, Wrench } from "lucide-react"
import { Suspense, useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import {
  CustomersService,
  EquipmentService,
  ServiceRequestsService,
} from "@/client/crm-services"
import type { ServiceRequestPublic } from "@/client/crm-types"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

export const Route = createFileRoute("/_layout/service-requests")({
  component: ServiceRequests,
  head: () => ({
    meta: [{ title: "Service Requests - Delta CRM" }],
  }),
})

const statusColors: Record<
  string,
  "default" | "secondary" | "destructive" | "outline"
> = {
  new: "outline",
  assigned: "secondary",
  in_progress: "default",
  on_hold: "secondary",
  resolved: "default",
  closed: "secondary",
  cancelled: "destructive",
}

const priorityColors: Record<
  string,
  "default" | "secondary" | "destructive" | "outline"
> = {
  low: "outline",
  medium: "secondary",
  high: "default",
  critical: "destructive",
}

const addFormSchema = z.object({
  customer_id: z.string().min(1, "Customer is required"),
  equipment_id: z.string().optional(),
  description: z.string().min(1, "Description is required"),
  priority: z.string(),
  source: z.string(),
})

type AddFormData = z.infer<typeof addFormSchema>

function AddServiceRequest() {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const form = useForm<AddFormData>({
    resolver: zodResolver(addFormSchema),
    defaultValues: {
      customer_id: "",
      equipment_id: "",
      description: "",
      priority: "medium",
      source: "phone",
    },
  })

  const selectedCustomerId = form.watch("customer_id")

  const { data: customers } = useQuery({
    queryKey: ["customers-list"],
    queryFn: () => CustomersService.readCustomers({ limit: 200 }),
    enabled: isOpen,
  })

  const { data: equipment } = useQuery({
    queryKey: ["equipment", selectedCustomerId],
    queryFn: () =>
      EquipmentService.readCustomerEquipment({
        customerId: selectedCustomerId,
      }),
    enabled: !!selectedCustomerId,
  })

  const mutation = useMutation({
    mutationFn: (data: AddFormData) =>
      ServiceRequestsService.createServiceRequest({
        requestBody: {
          customer_id: data.customer_id,
          equipment_id: data.equipment_id || null,
          description: data.description,
          priority: data.priority,
          source: data.source,
        },
      }),
    onSuccess: () => {
      showSuccessToast("Service request created")
      form.reset()
      setIsOpen(false)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["service-requests"] })
    },
  })

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="mr-2" />
          New Request
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>New Service Request</DialogTitle>
          <DialogDescription>
            Create a new service request for a customer.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit((d) => mutation.mutate(d))}>
            <div className="grid gap-4 py-4">
              <FormField
                control={form.control}
                name="customer_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Customer <span className="text-destructive">*</span>
                    </FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select customer" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {customers?.data.map((c) => (
                          <SelectItem key={c.id} value={c.id}>
                            {c.name}
                            {c.company_name ? ` (${c.company_name})` : ""}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {selectedCustomerId && equipment && equipment.data.length > 0 && (
                <FormField
                  control={form.control}
                  name="equipment_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Equipment</FormLabel>
                      <Select
                        onValueChange={field.onChange}
                        value={field.value}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select equipment (optional)" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {equipment.data.map((eq) => (
                            <SelectItem key={eq.id} value={eq.id}>
                              {eq.model} — {eq.serial_number}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              )}

              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Description <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input placeholder="Describe the issue" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="priority"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Priority</FormLabel>
                      <Select
                        onValueChange={field.onChange}
                        value={field.value}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="low">Low</SelectItem>
                          <SelectItem value="medium">Medium</SelectItem>
                          <SelectItem value="high">High</SelectItem>
                          <SelectItem value="critical">Critical</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="source"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Source</FormLabel>
                      <Select
                        onValueChange={field.onChange}
                        value={field.value}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="phone">Phone</SelectItem>
                          <SelectItem value="email">Email</SelectItem>
                          <SelectItem value="walk_in">Walk-in</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </div>
            <DialogFooter>
              <DialogClose asChild>
                <Button variant="outline" disabled={mutation.isPending}>
                  Cancel
                </Button>
              </DialogClose>
              <LoadingButton type="submit" loading={mutation.isPending}>
                Create
              </LoadingButton>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

function SRTableContent({
  status,
  priority,
}: {
  status: string | null
  priority: string | null
}) {
  const { data: requests } = useSuspenseQuery({
    queryKey: ["service-requests", status ?? "", priority ?? ""],
    queryFn: () =>
      ServiceRequestsService.readServiceRequests({
        skip: 0,
        limit: 100,
        status,
        priority,
      }),
  })

  if (requests.data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-muted p-4 mb-4">
          <Wrench className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">
          {status || priority
            ? "No requests match your filters"
            : "No service requests yet"}
        </h3>
        <p className="text-muted-foreground">
          {status || priority
            ? "Try adjusting your filters"
            : "Create a new service request to get started"}
        </p>
      </div>
    )
  }

  return (
    <>
      <Badge variant="outline" className="w-fit">
        {requests.count} total
      </Badge>
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead>Description</TableHead>
            <TableHead>Priority</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Source</TableHead>
            <TableHead>SLA</TableHead>
            <TableHead>Created</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {requests.data.map((sr: ServiceRequestPublic) => (
            <TableRow key={sr.id}>
              <TableCell>
                <Link
                  to="/service-requests/$requestId"
                  params={{ requestId: sr.id }}
                  className="font-medium hover:underline line-clamp-1 max-w-xs"
                >
                  {sr.description}
                </Link>
              </TableCell>
              <TableCell>
                <Badge variant={priorityColors[sr.priority] ?? "outline"}>
                  {sr.priority}
                </Badge>
              </TableCell>
              <TableCell>
                <Badge variant={statusColors[sr.status] ?? "outline"}>
                  {sr.status.replace("_", " ")}
                </Badge>
              </TableCell>
              <TableCell className="text-muted-foreground">
                {sr.source.replace("_", " ")}
              </TableCell>
              <TableCell>
                {(sr.sla_response_breached || sr.sla_resolution_breached) && (
                  <Badge variant="destructive">Breached</Badge>
                )}
              </TableCell>
              <TableCell className="text-muted-foreground text-sm">
                {sr.created_at
                  ? new Date(sr.created_at).toLocaleDateString()
                  : "—"}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </>
  )
}

function ServiceRequests() {
  const [status, setStatus] = useState<string | null>(null)
  const [priority, setPriority] = useState<string | null>(null)

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Service Requests
          </h1>
          <p className="text-muted-foreground">
            Track and manage service requests
          </p>
        </div>
        <AddServiceRequest />
      </div>

      <div className="flex items-center gap-4">
        <Select
          value={status ?? "all"}
          onValueChange={(v) => setStatus(v === "all" ? null : v)}
        >
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="All statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="new">New</SelectItem>
            <SelectItem value="assigned">Assigned</SelectItem>
            <SelectItem value="in_progress">In Progress</SelectItem>
            <SelectItem value="on_hold">On Hold</SelectItem>
            <SelectItem value="resolved">Resolved</SelectItem>
            <SelectItem value="closed">Closed</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={priority ?? "all"}
          onValueChange={(v) => setPriority(v === "all" ? null : v)}
        >
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="All priorities" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All priorities</SelectItem>
            <SelectItem value="low">Low</SelectItem>
            <SelectItem value="medium">Medium</SelectItem>
            <SelectItem value="high">High</SelectItem>
            <SelectItem value="critical">Critical</SelectItem>
          </SelectContent>
        </Select>
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
        <SRTableContent status={status} priority={priority} />
      </Suspense>
    </div>
  )
}
