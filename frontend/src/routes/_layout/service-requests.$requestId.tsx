import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { ArrowLeft, Calendar, Clock, Plus, UserCheck } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { UsersService } from "@/client"
import {
  ServiceRequestsService,
  ServiceVisitsService,
} from "@/client/crm-services"
import type {
  ServiceRequestPublic,
  ServiceVisitPublic,
} from "@/client/crm-types"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
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
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

export const Route = createFileRoute("/_layout/service-requests/$requestId")({
  component: ServiceRequestDetail,
  head: () => ({ meta: [{ title: "Service Request - Delta CRM" }] }),
})

type BadgeVariant = "default" | "secondary" | "destructive" | "outline"
const statusColors: Record<string, BadgeVariant> = {
  new: "outline",
  assigned: "secondary",
  in_progress: "default",
  on_hold: "secondary",
  resolved: "default",
  closed: "secondary",
  cancelled: "destructive",
}
const priorityColors: Record<string, BadgeVariant> = {
  low: "outline",
  medium: "secondary",
  high: "default",
  critical: "destructive",
}

const VALID_TRANSITIONS: Record<string, readonly string[]> = {
  new: ["assigned", "cancelled"],
  assigned: ["in_progress", "on_hold", "cancelled"],
  in_progress: ["on_hold", "resolved"],
  on_hold: ["in_progress", "cancelled"],
  resolved: ["closed"],
  closed: [],
  cancelled: [],
}

const label = (s: string) => s.replace(/_/g, " ")
const fmtDate = (v: string | null | undefined) =>
  v ? new Date(v).toLocaleDateString() : "\u2014"
const fmtDateTime = (v: string | null | undefined) =>
  v ? new Date(v).toLocaleString() : "\u2014"

const visitSchema = z.object({
  visit_date: z.string().min(1, "Visit date is required"),
  arrival_time: z.string().optional(),
  departure_time: z.string().optional(),
  notes: z.string().optional(),
})
type VisitFormData = z.infer<typeof visitSchema>

// ---------- Header ----------

function SRHeader({ sr }: { sr: ServiceRequestPublic }) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <CardTitle className="text-xl">{sr.description}</CardTitle>
            <CardDescription>
              Created {fmtDateTime(sr.created_at)}
              {sr.updated_at && ` \u00b7 Updated ${fmtDateTime(sr.updated_at)}`}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={priorityColors[sr.priority] ?? "outline"}>
              {sr.priority}
            </Badge>
            <Badge variant={statusColors[sr.status] ?? "outline"}>
              {label(sr.status)}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
          <div>
            <p className="text-muted-foreground">Source</p>
            <p className="font-medium capitalize">{label(sr.source)}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Customer</p>
            <p className="font-medium">{sr.customer_id.slice(0, 8)}...</p>
          </div>
          <div>
            <p className="text-muted-foreground">SLA Response Due</p>
            <p className="font-medium">
              {fmtDateTime(sr.sla_response_due)}
              {sr.sla_response_breached && (
                <Badge variant="destructive" className="ml-2">
                  Breached
                </Badge>
              )}
            </p>
          </div>
          <div>
            <p className="text-muted-foreground">SLA Resolution Due</p>
            <p className="font-medium">
              {fmtDateTime(sr.sla_resolution_due)}
              {sr.sla_resolution_breached && (
                <Badge variant="destructive" className="ml-2">
                  Breached
                </Badge>
              )}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// ---------- Timeline ----------

function TimelineTab({ sr }: { sr: ServiceRequestPublic }) {
  const qc = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const mutation = useMutation({
    mutationFn: (status: string) =>
      ServiceRequestsService.updateStatus({
        requestId: sr.id,
        requestBody: { status },
      }),
    onSuccess: (u) => showSuccessToast(`Status changed to ${label(u.status)}`),
    onError: handleError.bind(showErrorToast),
    onSettled: () =>
      qc.invalidateQueries({ queryKey: ["service-request", sr.id] }),
  })

  const next = VALID_TRANSITIONS[sr.status] ?? []

  return (
    <Card>
      <CardHeader>
        <CardTitle>Current Status</CardTitle>
        <CardDescription>
          Transition the service request to a valid next state.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-3">
          <span className="text-muted-foreground text-sm">Current:</span>
          <Badge
            variant={statusColors[sr.status] ?? "outline"}
            className="text-base px-3 py-1"
          >
            {label(sr.status)}
          </Badge>
        </div>
        <Separator />
        {next.length > 0 ? (
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">
              Available transitions:
            </p>
            <div className="flex flex-wrap gap-2">
              {next.map((s) => (
                <LoadingButton
                  key={s}
                  variant={s === "cancelled" ? "destructive" : "outline"}
                  loading={mutation.isPending && mutation.variables === s}
                  disabled={mutation.isPending}
                  onClick={() => mutation.mutate(s)}
                >
                  {label(s)}
                </LoadingButton>
              ))}
            </div>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            No further transitions available. This request is{" "}
            <strong>{label(sr.status)}</strong>.
          </p>
        )}
        {sr.diagnosis && (
          <>
            <Separator />
            <div>
              <p className="text-sm text-muted-foreground mb-1">Diagnosis</p>
              <p className="text-sm">{sr.diagnosis}</p>
            </div>
          </>
        )}
        {sr.resolution_notes && (
          <div>
            <p className="text-sm text-muted-foreground mb-1">
              Resolution Notes
            </p>
            <p className="text-sm">{sr.resolution_notes}</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// ---------- Add Visit Dialog ----------

function AddVisitDialog({
  requestId,
  open,
  onOpenChange,
}: {
  requestId: string
  open: boolean
  onOpenChange: (v: boolean) => void
}) {
  const qc = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const form = useForm<VisitFormData>({
    resolver: zodResolver(visitSchema),
    defaultValues: {
      visit_date: "",
      arrival_time: "",
      departure_time: "",
      notes: "",
    },
  })

  const mutation = useMutation({
    mutationFn: (d: VisitFormData) =>
      ServiceVisitsService.createVisit({
        requestId,
        requestBody: {
          service_request_id: requestId,
          visit_date: d.visit_date,
          arrival_time: d.arrival_time || null,
          departure_time: d.departure_time || null,
          notes: d.notes || null,
        },
      }),
    onSuccess: () => {
      showSuccessToast("Visit added")
      form.reset()
      onOpenChange(false)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () =>
      qc.invalidateQueries({ queryKey: ["service-visits", requestId] }),
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add Service Visit</DialogTitle>
          <DialogDescription>
            Record a new service visit for this request.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit((d) => mutation.mutate(d))}>
            <div className="grid gap-4 py-4">
              <FormField
                control={form.control}
                name="visit_date"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Visit Date <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="arrival_time"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Arrival Time</FormLabel>
                      <FormControl>
                        <Input type="time" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="departure_time"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Departure Time</FormLabel>
                      <FormControl>
                        <Input type="time" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
              <FormField
                control={form.control}
                name="notes"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Notes</FormLabel>
                    <FormControl>
                      <Input placeholder="Visit notes (optional)" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <DialogFooter>
              <DialogClose asChild>
                <Button variant="outline" disabled={mutation.isPending}>
                  Cancel
                </Button>
              </DialogClose>
              <LoadingButton type="submit" loading={mutation.isPending}>
                Add Visit
              </LoadingButton>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

// ---------- Visits Tab ----------

function VisitsTab({ requestId }: { requestId: string }) {
  const [addOpen, setAddOpen] = useState(false)

  const { data: visits, isLoading } = useQuery({
    queryKey: ["service-visits", requestId],
    queryFn: () => ServiceVisitsService.readVisits({ requestId }),
  })

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Service Visits</CardTitle>
            <CardDescription>
              {visits ? `${visits.count} visit(s)` : "Loading..."}
            </CardDescription>
          </div>
          <Button onClick={() => setAddOpen(true)}>
            <Plus className="mr-2 h-4 w-4" /> Add Visit
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        ) : visits && visits.data.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead>
                  <Calendar className="inline mr-1 h-4 w-4" />
                  Date
                </TableHead>
                <TableHead>
                  <Clock className="inline mr-1 h-4 w-4" />
                  Arrival
                </TableHead>
                <TableHead>
                  <Clock className="inline mr-1 h-4 w-4" />
                  Departure
                </TableHead>
                <TableHead>Notes</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {visits.data.map((v: ServiceVisitPublic) => (
                <TableRow key={v.id}>
                  <TableCell>{fmtDate(v.visit_date)}</TableCell>
                  <TableCell>{v.arrival_time ?? "\u2014"}</TableCell>
                  <TableCell>{v.departure_time ?? "\u2014"}</TableCell>
                  <TableCell className="max-w-xs truncate">
                    {v.notes ?? "\u2014"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <p className="text-sm text-muted-foreground py-4 text-center">
            No visits recorded yet.
          </p>
        )}
      </CardContent>
      <AddVisitDialog
        requestId={requestId}
        open={addOpen}
        onOpenChange={setAddOpen}
      />
    </Card>
  )
}

// ---------- Assign Engineer ----------

function AssignEngineer({ sr }: { sr: ServiceRequestPublic }) {
  const qc = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const { data: users } = useQuery({
    queryKey: ["users-list"],
    queryFn: () => UsersService.readUsers({ limit: 200 }),
  })

  const mutation = useMutation({
    mutationFn: (engineerId: string) =>
      ServiceRequestsService.assignEngineer({ requestId: sr.id, engineerId }),
    onSuccess: (u) =>
      showSuccessToast(
        `Engineer assigned (${u.assigned_engineer_id?.slice(0, 8)}...)`,
      ),
    onError: handleError.bind(showErrorToast),
    onSettled: () =>
      qc.invalidateQueries({ queryKey: ["service-request", sr.id] }),
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <UserCheck className="h-5 w-5" /> Assign Engineer
        </CardTitle>
        <CardDescription>
          {sr.assigned_engineer_id
            ? `Currently assigned: ${sr.assigned_engineer_id.slice(0, 8)}...`
            : "No engineer assigned yet."}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Select
          value={sr.assigned_engineer_id ?? ""}
          onValueChange={(v) => mutation.mutate(v)}
          disabled={mutation.isPending}
        >
          <SelectTrigger className="w-full max-w-xs">
            <SelectValue placeholder="Select engineer" />
          </SelectTrigger>
          <SelectContent>
            {users?.data.map((u) => (
              <SelectItem key={u.id} value={u.id}>
                {u.full_name || u.email}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </CardContent>
    </Card>
  )
}

// ---------- Main Page ----------

function ServiceRequestDetail() {
  const { requestId } = Route.useParams()

  const { data: sr, isLoading } = useQuery({
    queryKey: ["service-request", requestId],
    queryFn: () => ServiceRequestsService.readServiceRequest({ requestId }),
  })

  if (isLoading) {
    return (
      <div className="flex flex-col gap-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (!sr) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <h3 className="text-lg font-semibold">Service request not found</h3>
        <Link
          to="/service-requests"
          className="text-sm text-muted-foreground hover:underline mt-2"
        >
          Back to list
        </Link>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <Link to="/service-requests">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-5 w-5" />
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Service Request</h1>
          <p className="text-muted-foreground text-sm">
            ID: {sr.id.slice(0, 8)}...
          </p>
        </div>
      </div>

      <SRHeader sr={sr} />

      <div className="grid gap-6 lg:grid-cols-[1fr_300px]">
        <Tabs defaultValue="timeline">
          <TabsList>
            <TabsTrigger value="timeline">Timeline</TabsTrigger>
            <TabsTrigger value="visits">Visits</TabsTrigger>
            <TabsTrigger value="parts">Parts</TabsTrigger>
            <TabsTrigger value="quotation">Quotation</TabsTrigger>
          </TabsList>
          <TabsContent value="timeline">
            <TimelineTab sr={sr} />
          </TabsContent>
          <TabsContent value="visits">
            <VisitsTab requestId={requestId} />
          </TabsContent>
          <TabsContent value="parts">
            <Card>
              <CardHeader>
                <CardTitle>Parts</CardTitle>
                <CardDescription>
                  Parts tracking will be available in a future update.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  No parts data available yet.
                </p>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="quotation">
            <Card>
              <CardHeader>
                <CardTitle>Quotation</CardTitle>
                <CardDescription>
                  Quotation management will be available in a future update.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  No quotation data available yet.
                </p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
        <div className="space-y-6">
          <AssignEngineer sr={sr} />
        </div>
      </div>
    </div>
  )
}
