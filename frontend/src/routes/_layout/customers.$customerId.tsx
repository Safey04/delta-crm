import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { ArrowLeft, Building2 } from "lucide-react"

import { CustomersService } from "@/client/crm-services"
import CustomerContacts from "@/components/Customers/CustomerContacts"
import CustomerEquipment from "@/components/Customers/CustomerEquipment"
import EditCustomer from "@/components/Customers/EditCustomer"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export const Route = createFileRoute("/_layout/customers/$customerId")({
  component: CustomerDetail,
  head: () => ({
    meta: [
      {
        title: "Customer - Delta CRM",
      },
    ],
  }),
})

const segmentLabels: Record<string, string> = {
  enterprise: "Enterprise",
  smb: "SMB",
  walk_in: "Walk-in",
}

function CustomerDetail() {
  const { customerId } = Route.useParams()

  const {
    data: customer,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["customer", customerId],
    queryFn: () => CustomersService.readCustomer({ customerId }),
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-48" />
        <Skeleton className="h-[400px] w-full" />
      </div>
    )
  }

  if (error || !customer) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <h2 className="text-xl font-semibold">Customer not found</h2>
        <p className="text-muted-foreground mt-2">
          The customer you're looking for doesn't exist or you don't have
          permission to view it.
        </p>
        <Button asChild className="mt-4">
          <Link to="/customers">Back to Customers</Link>
        </Button>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start gap-4">
        <Button variant="ghost" size="icon" asChild className="mt-1">
          <Link to="/customers">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <div className="rounded-full bg-muted p-2">
              <Building2 className="h-5 w-5 text-muted-foreground" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">
                {customer.name}
              </h1>
              <div className="flex items-center gap-2 mt-1">
                {customer.company_name && (
                  <span className="text-muted-foreground">
                    {customer.company_name}
                  </span>
                )}
                <Badge variant="outline">
                  {segmentLabels[customer.segment] ?? customer.segment}
                </Badge>
                <Badge
                  variant={customer.is_active ? "default" : "secondary"}
                >
                  {customer.is_active ? "Active" : "Inactive"}
                </Badge>
              </div>
            </div>
          </div>
        </div>
      </div>

      <Tabs defaultValue="profile">
        <TabsList>
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="contacts">Contacts</TabsTrigger>
          <TabsTrigger value="equipment">Equipment</TabsTrigger>
          <TabsTrigger value="service-history" disabled>
            Service History
          </TabsTrigger>
          <TabsTrigger value="financials" disabled>
            Financials
          </TabsTrigger>
        </TabsList>

        <TabsContent value="profile" className="mt-6">
          <EditCustomer customer={customer} />
        </TabsContent>

        <TabsContent value="contacts" className="mt-6">
          <CustomerContacts customerId={customerId} />
        </TabsContent>

        <TabsContent value="equipment" className="mt-6">
          <CustomerEquipment customerId={customerId} />
        </TabsContent>

        <TabsContent value="service-history" className="mt-6">
          <div className="text-center py-8 text-muted-foreground">
            Service history will be available in a future update.
          </div>
        </TabsContent>

        <TabsContent value="financials" className="mt-6">
          <div className="text-center py-8 text-muted-foreground">
            Financial information will be available in a future update.
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
