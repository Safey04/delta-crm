import { createFileRoute } from "@tanstack/react-router"

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

function CustomerDetail() {
  const { customerId } = Route.useParams()

  return (
    <div>
      <h1 className="text-2xl font-bold tracking-tight">
        Customer Detail
      </h1>
      <p className="text-muted-foreground">Customer ID: {customerId}</p>
    </div>
  )
}
