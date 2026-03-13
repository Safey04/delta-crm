import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Plus, Trash2 } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { EquipmentService } from "@/client/crm-services"
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

const equipmentFormSchema = z.object({
  model: z.string().min(1, { message: "Model is required" }),
  serial_number: z.string().min(1, { message: "Serial number is required" }),
  manufacturer: z.string().optional(),
  install_date: z.string().optional(),
  warranty_expiry: z.string().optional(),
  notes: z.string().optional(),
})

type EquipmentFormData = z.infer<typeof equipmentFormSchema>

interface CustomerEquipmentProps {
  customerId: string
}

const CustomerEquipment = ({ customerId }: CustomerEquipmentProps) => {
  const [addOpen, setAddOpen] = useState(false)
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const { data: equipment, isLoading } = useQuery({
    queryKey: ["equipment", customerId],
    queryFn: () => EquipmentService.readCustomerEquipment({ customerId }),
  })

  const form = useForm<EquipmentFormData>({
    resolver: zodResolver(equipmentFormSchema),
    defaultValues: {
      model: "",
      serial_number: "",
      manufacturer: "",
      install_date: "",
      warranty_expiry: "",
      notes: "",
    },
  })

  const createMutation = useMutation({
    mutationFn: (data: EquipmentFormData) =>
      EquipmentService.createEquipment({
        customerId,
        requestBody: {
          customer_id: customerId,
          model: data.model,
          serial_number: data.serial_number,
          manufacturer: data.manufacturer || null,
          install_date: data.install_date || null,
          warranty_expiry: data.warranty_expiry || null,
          notes: data.notes || null,
        },
      }),
    onSuccess: () => {
      showSuccessToast("Equipment added")
      form.reset()
      setAddOpen(false)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["equipment", customerId] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (equipmentId: string) =>
      EquipmentService.deleteEquipment({ equipmentId }),
    onSuccess: () => {
      showSuccessToast("Equipment removed")
      setDeleteId(null)
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["equipment", customerId] })
    },
  })

  const isWarrantyExpired = (date: string | null) => {
    if (!date) return false
    return new Date(date) < new Date()
  }

  if (isLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">
          Equipment ({equipment?.count ?? 0})
        </h3>
        <Button size="sm" onClick={() => setAddOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Equipment
        </Button>
      </div>

      {equipment && equipment.data.length > 0 ? (
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead>Model</TableHead>
              <TableHead>Serial Number</TableHead>
              <TableHead>Manufacturer</TableHead>
              <TableHead>Install Date</TableHead>
              <TableHead>Warranty</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {equipment.data.map((eq) => (
              <TableRow key={eq.id}>
                <TableCell className="font-medium">{eq.model}</TableCell>
                <TableCell className="font-mono text-sm">
                  {eq.serial_number}
                </TableCell>
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
                <TableCell className="text-right">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-destructive"
                    onClick={() => setDeleteId(eq.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : (
        <div className="text-center py-8 text-muted-foreground">
          No equipment registered. Add equipment to track service history.
        </div>
      )}

      <Dialog open={addOpen} onOpenChange={setAddOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Add Equipment</DialogTitle>
            <DialogDescription>
              Register new equipment for this customer.
            </DialogDescription>
          </DialogHeader>
          <Form {...form}>
            <form
              onSubmit={form.handleSubmit((d) => createMutation.mutate(d))}
            >
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="model"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>
                          Model <span className="text-destructive">*</span>
                        </FormLabel>
                        <FormControl>
                          <Input placeholder="e.g. HP LaserJet" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="serial_number"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>
                          Serial # <span className="text-destructive">*</span>
                        </FormLabel>
                        <FormControl>
                          <Input placeholder="Serial number" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
                <FormField
                  control={form.control}
                  name="manufacturer"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Manufacturer</FormLabel>
                      <FormControl>
                        <Input placeholder="e.g. HP, Canon, Xerox" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <div className="grid grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="install_date"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Install Date</FormLabel>
                        <FormControl>
                          <Input type="date" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="warranty_expiry"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Warranty Expiry</FormLabel>
                        <FormControl>
                          <Input type="date" {...field} />
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
                        <Input placeholder="Additional notes" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
              <DialogFooter>
                <DialogClose asChild>
                  <Button
                    variant="outline"
                    disabled={createMutation.isPending}
                  >
                    Cancel
                  </Button>
                </DialogClose>
                <LoadingButton
                  type="submit"
                  loading={createMutation.isPending}
                >
                  Add
                </LoadingButton>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>

      <Dialog
        open={!!deleteId}
        onOpenChange={(open) => {
          if (!open) setDeleteId(null)
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remove Equipment</DialogTitle>
            <DialogDescription>
              Are you sure you want to remove this equipment?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <DialogClose asChild>
              <Button variant="outline" disabled={deleteMutation.isPending}>
                Cancel
              </Button>
            </DialogClose>
            <LoadingButton
              variant="destructive"
              loading={deleteMutation.isPending}
              onClick={() => deleteId && deleteMutation.mutate(deleteId)}
            >
              Remove
            </LoadingButton>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default CustomerEquipment
