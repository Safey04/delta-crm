# Delta CRM — Design Document

**Date:** 2026-03-13
**Type:** CRM + Inventory Management System
**Domain:** Production Printer Servicing (Egypt-based)

---

## 1. Problem Statement

A production printer servicing company needs a unified system to manage:
- Customer relationships and service lifecycle
- Inventory and spare parts across warehouses
- Field engineer dispatching and service tracking
- Quotations, invoices, and financial reporting
- Operational reporting across all departments

Currently these workflows are fragmented across spreadsheets, WhatsApp, and manual processes.

---

## 2. Users & Roles

### 2.1 Manager
- Full dashboard with KPIs (revenue, open tickets, SLA compliance, inventory value)
- Approve/reject quotations above threshold
- Assign engineers to service requests
- View all reports (financial, operational, inventory)
- Manage users, roles, and access control
- Set pricing rules and discount limits
- Configure SLA thresholds per customer segment

### 2.2 Customer Support
- Create and manage customer accounts
- Receive and log service requests (phone, email, walk-in)
- Generate quotations for customers
- Track service request status and update customers
- Schedule service appointments
- Escalate issues to managers
- View customer history and equipment records

### 2.3 Field Engineer
- View assigned service tickets with priority
- Log service visit details (diagnosis, parts used, time spent)
- Request parts from warehouse
- Update ticket status (en route, on-site, completed)
- Upload photos/documentation of service work
- View equipment service history at customer site

### 2.4 Warehouse Worker
- Manage inventory (receive, issue, transfer, adjust)
- Process parts requests from engineers
- Track stock levels and locations
- Flag low-stock items
- Record incoming shipments from suppliers
- Perform stock counts / cycle counts

---

## 3. Core Modules

### 3.1 Dashboard
- Role-specific views (each role sees relevant KPIs)
- **Manager:** Revenue, ticket volume, SLA %, top customers, inventory alerts
- **Support:** Open tickets, pending quotations, today's appointments
- **Engineer:** My assigned tickets, parts requests status
- **Warehouse:** Low stock alerts, pending parts requests, recent movements

### 3.2 Customer Management (CRM)
- Customer profiles (company name, contacts, addresses, tax ID)
- Equipment registry per customer (printer model, serial number, install date, warranty status)
- Interaction history (calls, visits, emails)
- Contract/SLA tracking per customer
- Customer segmentation (enterprise, SMB, walk-in)

### 3.3 Service Management
- **Service Request:** Create, assign, track, close
- **Ticket Lifecycle:** New → Quoted → Approved → Assigned → In Progress → Completed → Invoiced → Closed
- **Quotation:** Line items (labor, parts, travel), approval workflow, PDF generation
- **Scheduling:** Calendar view for engineer assignments
- **SLA Tracking:** Response time, resolution time per contract tier, pause/resume clock

### 3.4 Inventory Management
- **Products/Parts Catalog:** SKU, description, category, unit cost, sell price
- **Stock Tracking:** Quantity on hand, reserved, available per warehouse location
- **Stock Movements:** Receive, issue (to service ticket), transfer, adjust, return
- **Low Stock Alerts:** Configurable min/max thresholds per item
- **Supplier Management:** Supplier contacts, lead times, purchase history
- **Parts Used per Ticket:** Auto-deduct from inventory when engineer logs parts

### 3.5 Financial / Quotations & Invoicing
- **Quotation Builder:** Add labor, parts, discounts; calculate totals with tax. Parts auto-populate price from catalog with manual override.
- **Quotation Approval:** Configurable approval chain (auto-approve below threshold)
- **Quotation Revision:** New quotation created on revision, original marked expired
- **Invoice Generation:** From approved quotation or completed service ticket
- **Payment Tracking:** Mark invoices as paid/partial/overdue
- **Credit Notes:** Reduce invoice balance for disputes, returns, goodwill
- **Tax Handling:** Egyptian tax rules (VAT 14%)
- **Overdue Escalation:** Day 1 dashboard flag → Day 7 support reminder → Day 30 manager alert → Day 60+ aged receivables

### 3.6 Reporting
- **Financial Reports:** Revenue by period, outstanding invoices, quotation conversion rate, aged receivables
- **Operational Reports:** Tickets by status/engineer/customer, SLA compliance, avg resolution time
- **Inventory Reports:** Stock levels, movement history, parts usage by model/customer, dead stock
- **Exportable:** PDF and Excel export for all reports

### 3.7 Access Control (RBAC)
- Configurable role-based permissions (4 default roles + custom roles)
- Granular permissions per resource and action (view, create, edit, delete, approve, export)
- Default roles protected (is_system flag — can edit permissions, cannot delete)
- Audit log of all actions (who did what, when)

---

## 4. Data Model (25 Entities)

### 4.1 Auth & RBAC

```
User
├── id (UUID PK)
├── supabase_auth_id (UUID, unique — links to Supabase auth.users)
├── full_name, phone, is_active
├── role_id (FK → Role)
├── created_at, updated_at

Role
├── id, name (manager/support/engineer/warehouse/custom...)
├── description, is_system (true for 4 defaults, prevents deletion)
├── created_at, updated_at

Permission
├── id, resource (customer/service_request/inventory/quotation/invoice/report/user)
├── action (view/create/edit/delete/approve/export)
├── description

RolePermission (join table)
├── role_id (FK), permission_id (FK)
```

**Default permission matrix:**

| Permission | Manager | Support | Engineer | Warehouse |
|---|---|---|---|---|
| customer.* | all | view/create/edit | view | view |
| service_request.* | all | all | view/edit (assigned) | view |
| quotation.* | all + approve | create/edit | view | — |
| inventory.* | all | view | view/request | all |
| invoice.* | all | view | — | — |
| report.* | all | operational | — | inventory |
| user.* | all | — | — | — |

### 4.2 CRM

```
Customer
├── id (UUID), name, company_name, phone, email, address
├── tax_id, segment (enterprise/smb/walk_in)
├── notes, is_active, created_at, updated_at
├── has many → Contact
├── has many → Equipment
├── has many → ServiceRequest

Contact
├── id, customer_id (FK)
├── name, title, phone, email, is_primary
├── created_at

Equipment
├── id, customer_id (FK)
├── model, serial_number, manufacturer
├── install_date, warranty_expiry
├── notes, is_active, created_at
├── has many → ServiceRequest
```

### 4.3 Service Management

```
ServiceRequest
├── id, customer_id (FK), equipment_id (FK)
├── assigned_engineer_id (FK → User, nullable)
├── status (new/quoted/approved/assigned/in_progress/completed/invoiced/closed)
├── priority (low/medium/high/critical)
├── source (phone/email/walk_in)
├── description, diagnosis, resolution_notes
├── sla_response_due, sla_resolution_due
├── sla_response_breached (bool, default false)
├── sla_resolution_breached (bool, default false)
├── sla_paused_at (datetime, nullable)
├── sla_total_paused_seconds (int, default 0)
├── created_by (FK → User), created_at, updated_at
├── has one → Quotation
├── has many → ServiceVisit
├── has many → TicketPartsUsed
├── has many → PartsRequest

ServiceVisit
├── id, service_request_id (FK), engineer_id (FK → User)
├── visit_date, arrival_time, departure_time
├── notes, created_at
├── has many → VisitPhoto
├── has many → TicketPartsUsed

VisitPhoto
├── id, service_visit_id (FK)
├── storage_path (Supabase Storage reference)
├── description, uploaded_at

PartsRequest
├── id, service_request_id (FK), requested_by (FK → User)
├── product_id (FK), warehouse_id (FK)
├── quantity_requested, quantity_fulfilled
├── status (pending/approved/partial/fulfilled/cancelled)
├── notes, created_at, updated_at

TicketPartsUsed
├── id, service_request_id (FK), service_visit_id (FK, nullable)
├── product_id (FK), warehouse_id (FK)
├── quantity, unit_price_at_time (snapshot for invoice accuracy)
├── created_at

SLAConfig
├── id, segment (enterprise/smb/walk_in)
├── response_hours, resolution_hours
├── created_at, updated_at
```

### 4.4 Financial

```
Quotation
├── id, service_request_id (FK), customer_id (FK)
├── status (draft/pending/approved/rejected/expired)
├── subtotal, discount_amount, tax_rate (default 14%), tax_amount, total
├── valid_until, notes
├── created_by (FK → User), approved_by (FK → User, nullable)
├── created_at, approved_at, updated_at

QuotationLineItem
├── id, quotation_id (FK)
├── type (labor/part/travel)
├── description, quantity, unit_price, total
├── product_id (FK → Product, nullable — only for type=part)
├── sort_order

Invoice
├── id, quotation_id (FK), service_request_id (FK), customer_id (FK)
├── invoice_number (sequential, human-readable e.g. INV-2026-0001)
├── status (draft/sent/paid/partial/overdue/cancelled)
├── amount, tax_amount, total
├── paid_amount, balance_due
├── issued_date, due_date
├── notes, created_at, updated_at

Payment
├── id, invoice_id (FK)
├── amount, method (cash/bank_transfer/check/other)
├── reference_number, notes
├── received_by (FK → User), payment_date, created_at

CreditNote
├── id, invoice_id (FK), customer_id (FK)
├── amount, reason
├── created_by (FK → User), created_at
```

### 4.5 Inventory & Procurement

```
Product
├── id, sku, name, description
├── category (toner/drum/fuser/roller/board/other)
├── unit_cost, sell_price
├── min_stock_threshold, max_stock_threshold
├── is_active, created_at, updated_at
├── has many → StockMovement
├── has many → SupplierProduct
├── has many → InventoryLevel

Warehouse
├── id, name, location, is_active
├── created_at

InventoryLevel
├── id, product_id (FK), warehouse_id (FK)
├── quantity_on_hand, quantity_reserved, quantity_available (computed)
├── unique constraint on (product_id, warehouse_id)

StockMovement
├── id, product_id (FK), warehouse_id (FK)
├── type (receive/issue/transfer/adjust/return)
├── quantity (positive for in, negative for out)
├── reference_type (service_request/purchase_order/transfer/manual)
├── reference_id (UUID, nullable)
├── notes, performed_by (FK → User), created_at

Supplier
├── id, name, contact_name, phone, email
├── address, lead_time_days, notes
├── is_active, created_at, updated_at

SupplierProduct
├── id, supplier_id (FK), product_id (FK)
├── supplier_sku, supplier_price
├── is_preferred (one preferred supplier per product)
├── unique constraint on (supplier_id, product_id)

PurchaseOrder
├── id, supplier_id (FK)
├── status (draft/submitted/confirmed/partial/received/cancelled)
├── order_date, expected_delivery_date
├── notes, created_by (FK → User)
├── created_at, updated_at

PurchaseOrderLineItem
├── id, purchase_order_id (FK), product_id (FK)
├── quantity_ordered, quantity_received
├── unit_cost, total
├── sort_order
```

### 4.6 System

```
AuditLog
├── id, user_id (FK → User)
├── action (create/update/delete/approve/reject/login)
├── entity_type (customer/service_request/quotation/invoice/product/...)
├── entity_id (UUID)
├── changes (JSONB — before/after snapshot of changed fields)
├── ip_address, created_at
```

---

## 5. Key Workflows

### 5.1 Service Request Lifecycle

```
Customer calls/emails/walks in
    → Support creates ServiceRequest (status: new)
        → SLA deadlines auto-calculated from customer segment + SLAConfig
    → Support creates Quotation with line items
        ├── Parts: auto-populate price from catalog, allow override
        ├── Labor: manual entry (hours × rate)
        └── Travel: flat fee or per-km

    → Quotation sent to customer (status: pending)

    → BRANCH: Customer responds
        ├── Approved
        │   ├── Total ≤ threshold → auto-approved
        │   └── Total > threshold → manager approval required
        │       ├── Manager approves → proceed
        │       └── Manager rejects → back to support for revision
        │           → Support creates revised quotation (original marked expired)
        │
        ├── Customer requests changes
        │   → Support creates revised quotation (original marked expired)
        │   → New quotation follows same approval flow
        │
        └── Customer declines / no response
            → Quotation expires after valid_until date
            → Ticket status: closed (reason: declined/expired)

    → Approved → Manager assigns engineer (status: assigned)
        └── No available engineer → stays in approved, flagged on dashboard

    → Engineer travels to site (status: in_progress)
    → Engineer logs visit, diagnosis, parts used
        └── Parts auto-deducted from inventory

    → BRANCH: Resolution
        ├── Fixed → engineer marks complete (status: completed)
        ├── Needs follow-up → new ServiceVisit scheduled, stays in_progress
        └── Cannot fix → escalate to manager, notes logged

    → Invoice generated from quotation (status: invoiced)

    → BRANCH: Payment
        ├── Full payment → status: closed
        ├── Partial payment → status stays invoiced, balance tracked
        └── Overdue → escalation ladder (day 1/7/30/60+)

CANCELLATION: Can cancel at any point before completed.
    → If parts were issued → return to inventory (StockMovement type: return)
    → Ticket status: closed (reason: cancelled)
```

### 5.2 Parts Request Flow

```
Engineer on-site needs a part
    → Engineer creates PartsRequest from ticket
        ├── Selects product from catalog
        ├── Specifies quantity needed
        └── Selects preferred warehouse (or auto: nearest with stock)

    → BRANCH: Stock check
        ├── In stock
        │   → Warehouse worker approves request
        │   → Stock reserved (quantity_reserved increases)
        │   → Parts issued to engineer (StockMovement type: issue)
        │   → TicketPartsUsed record created
        │   → quantity_reserved decreases, quantity_on_hand decreases
        │
        ├── Partial stock
        │   → Warehouse issues what's available
        │   → Remaining quantity flagged for procurement
        │   → Manager notified
        │
        └── Out of stock
            → Request marked as pending_procurement
            → Low stock alert triggered
            → Manager decides:
                ├── Order from supplier → procurement flow
                ├── Transfer from another warehouse → StockMovement type: transfer
                └── Source alternative part → support updates quotation if needed

    → BRANCH: After service
        ├── All parts used → no action
        ├── Unused parts returned
        │   → StockMovement type: return
        │   → InventoryLevel restored
        │   → TicketPartsUsed updated (quantity adjusted)
        └── Part was defective
            → Return to supplier tracked separately
            → Replacement requested
```

### 5.3 Inventory Replenishment

```
TRIGGER: Stock falls below min_stock_threshold
    → System generates low-stock alert
    → Alert visible on warehouse + manager dashboards

    → BRANCH: Replenishment decision
        ├── Order from supplier
        │   → Manager/warehouse creates PurchaseOrder
        │       ├── Selects supplier (preferred supplier auto-suggested)
        │       ├── Line items with quantities and agreed prices
        │       └── Expected delivery date
        │   → PurchaseOrder status: draft → submitted → confirmed
        │
        │   → Supplier delivers
        │       → Warehouse worker receives shipment
        │       → Checks quantities against PurchaseOrder
        │       → BRANCH: Receipt
        │           ├── Full delivery → StockMovement type: receive, PO status: received
        │           ├── Partial delivery → receive what arrived, PO status: partial
        │           └── Damaged/wrong items → log discrepancy, notify manager
        │
        ├── Transfer between warehouses
        │   → Two StockMovements: issue from source, receive at destination
        │   → Both InventoryLevels updated atomically
        │
        └── No action (seasonal item, being discontinued)
            → Manager acknowledges alert, dismisses

    → Stock level restored above min_stock_threshold → alert auto-clears
```

### 5.4 SLA Monitoring

```
On ServiceRequest creation:
    → System calculates SLA deadlines from SLAConfig by customer segment
        ├── Enterprise: respond 2h, resolve 24h (configurable)
        ├── SMB: respond 4h, resolve 48h (configurable)
        └── Walk-in: respond 8h, resolve 72h (configurable)
    → Deadlines stored: sla_response_due, sla_resolution_due

Monitoring (checked periodically or on status change):
    → Response SLA: engineer assigned before deadline → OK, else → breach flagged, priority auto-bumped
    → Resolution SLA: completed before deadline → OK, else → breach flagged, manager notified

Clock rules:
    → Clock PAUSES when waiting on customer (quotation pending) or parts (pending_procurement)
    → Clock RESUMES when blocker clears
    → Total paused time tracked in sla_total_paused_seconds
```

### 5.5 Partial Payments & Overdue Handling

```
Invoice generated (status: sent, due_date = issued_date + 30 days configurable)

    → Full payment → invoice status: paid, ticket status: closed
    → Partial payment → Payment record created, balance_due recalculated, status: partial
        → Multiple partial payments allowed until balance_due == 0
    → No payment by due_date → status: overdue
        → Day 1: flagged on dashboard
        → Day 7: support reminded to follow up
        → Day 30: manager alerted
        → Day 60+: visible in aged receivables report

Credit notes:
    → Manager creates CreditNote against invoice (disputes, returns, goodwill)
    → Reduces balance_due
    → If balance_due reaches 0 → invoice status: paid
```

---

## 6. Pages / Routes Structure

### 6.1 Auth & Shared

```
/login                                  → Supabase Auth login form
/forgot-password                        → Password reset via Supabase
/reset-password                         → Set new password callback
/dashboard                              → Role-specific dashboard
/settings/profile                       → Current user's own profile
/notifications                          → In-app notification center
```

### 6.2 CRM

```
/customers                              → List (search, filter by segment, active/inactive)
/customers/new                          → Create customer form
/customers/:id                          → Customer profile (tabs below)
/customers/:id/contacts                 → Contact people at this company
/customers/:id/equipment                → Equipment registry
/customers/:id/equipment/new            → Add equipment
/customers/:id/service-history          → All tickets for this customer
/customers/:id/financials               → Invoices, payments, outstanding balance
```

### 6.3 Equipment (global)

```
/equipment                              → Global list (search by serial, model, customer)
/equipment/:id                          → Equipment detail (links to customer, service history)
```

### 6.4 Service Management

```
/service-requests                       → List (filter by status/priority/engineer/customer)
/service-requests/new                   → Create (select customer → equipment → description)
/service-requests/:id                   → Detail view with tabs:
    /service-requests/:id/timeline      → Status history, activity log
    /service-requests/:id/quotation     → Quotation (create/view/revise)
    /service-requests/:id/visits        → Service visits with notes + photos
    /service-requests/:id/parts         → Parts used/requested
/quotations                             → List (filter by status, date range)
/quotations/:id                         → Detail (line items, approval actions, PDF preview)
/quotations/:id/pdf                     → PDF download
/engineers/my-tickets                   → Engineer's assigned work (filtered view)
/engineers/schedule                     → Calendar view of assignments
```

### 6.5 Financial

```
/invoices                               → List (filter by status: sent/paid/partial/overdue)
/invoices/:id                           → Detail (line items, payment history, credit notes)
/invoices/:id/pdf                       → PDF download
/invoices/:id/payments/new              → Record a payment
/credit-notes                           → List
/credit-notes/:id                       → Detail
```

### 6.6 Inventory

```
/inventory                              → Stock levels dashboard (summary cards, alerts)
/inventory/products                     → Parts catalog (search, filter by category)
/inventory/products/new                 → Add product
/inventory/products/:id                 → Product detail (stock per warehouse, movement history, suppliers)
/inventory/movements                    → All stock movements log (filter by type/warehouse/date)
/inventory/alerts                       → Low stock items needing attention
```

### 6.7 Warehouse

```
/warehouse/parts-requests               → Pending requests from engineers (approve/issue)
/warehouse/receive                      → Record incoming shipment against PurchaseOrder
/warehouse/transfer                     → Transfer stock between warehouses
```

### 6.8 Procurement

```
/purchase-orders                        → List (filter by status/supplier)
/purchase-orders/new                    → Create PO (select supplier, add line items)
/purchase-orders/:id                    → Detail (line items, receipt status)
/suppliers                              → List
/suppliers/new                          → Add supplier
/suppliers/:id                          → Detail (contact info, products supplied, PO history)
```

### 6.9 Reports

```
/reports/financial                      → Revenue, outstanding invoices, quotation conversion, aged receivables
/reports/operational                    → Tickets by status/engineer, SLA compliance, avg resolution time
/reports/inventory                      → Stock levels, usage by model/customer, dead stock
```

### 6.10 Admin (manager only)

```
/admin/users                            → User list (create, activate/deactivate)
/admin/users/new                        → Create user (triggers Supabase Auth account)
/admin/users/:id                        → Edit user details, role assignment
/admin/roles                            → Role list with permission matrix toggle
/admin/roles/new                        → Create custom role
/admin/roles/:id                        → Edit permissions
/admin/sla-config                       → SLA thresholds per segment
/admin/company                          → Company info, tax rate, invoice numbering
/admin/audit-log                        → Action history (filter by user/entity/date)
```

---

## 7. Tech Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Backend | FastAPI + Python | Async, OpenAPI auto-docs, DDD layered architecture |
| ORM | SQLModel | Hybrid SQLAlchemy + Pydantic |
| Database | PostgreSQL on Supabase | Managed, scalable, built-in tooling |
| Auth | Supabase Auth | Supabase manages identity; backend validates JWT, local users table for app data (role, permissions) |
| File Storage | Supabase Storage | Accessed through backend repository layer (DDD), not direct from frontend |
| Frontend | React 19 + Vite + TypeScript | SPA with type safety |
| Routing | TanStack Router | File-based, auto-generated route tree |
| State | TanStack Query | Server state caching, optimistic updates |
| UI | shadcn/ui + Tailwind CSS | Consistent, accessible components |
| Forms | React Hook Form + Zod | Validation, type-safe forms |
| API Client | Auto-generated from OpenAPI (openapi-ts) | Type-safe API calls |
| Tables | TanStack Table | Sortable, filterable data tables |
| Charts | Recharts | Dashboard visualizations |
| PDF | WeasyPrint (server-side) | Python-native, HTML templates → PDF |
| Deployment | Docker Compose + Traefik | Already configured in template |

### Auth Flow

```
Manager creates user in app (name, email, role)
    → Backend creates Supabase Auth user (email + temp password)
    → Local users table stores app data (role, phone, is_active)
    → Linked by Supabase auth UID

Login:
    → Frontend calls Supabase Auth (email/password)
    → Gets Supabase JWT
    → Frontend sends JWT on API requests
    → Backend validates JWT with Supabase, looks up local user by UID
    → Injects user + role into request context
```

---

## 8. Non-Functional Requirements

- **Localization-ready:** Structure supports future Arabic/RTL if needed
- **Responsive:** Tablet-friendly for engineers in the field
- **Offline consideration:** Engineers may have poor connectivity — consider optimistic UI
- **Audit trail:** Every create/update/delete logged with user and timestamp
- **Data export:** All list views exportable to Excel/CSV
- **PDF generation:** Quotations and invoices as downloadable PDFs (server-side via WeasyPrint)
- **Search:** Global search across customers, tickets, and inventory
- **Notifications:** In-app notifications for assignments, approvals, low stock
- **DDD Architecture:** All external service access (Supabase Storage, Auth) through backend repository/service layers

---

## 9. Implementation Phases

### Phase 1 — Foundation (MVP)
- Supabase Auth integration + RBAC (4 default roles + configurable permissions)
- User management (manager creates accounts)
- Customer management (CRUD + contacts + equipment)
- Service request lifecycle (create → assign → complete → close)
- Basic dashboard per role

### Phase 2 — Financial
- Quotation builder with line items (auto-populate from catalog with override)
- Approval workflow (threshold-based auto-approve + manager approval)
- Quotation revision flow
- Invoice generation with sequential numbering
- Payment tracking (full, partial, overdue)
- Credit notes
- PDF generation (WeasyPrint)

### Phase 3 — Inventory & Procurement
- Parts catalog (CRUD, categories)
- Warehouse management (multiple warehouses)
- Stock tracking (on hand, reserved, available)
- Stock movements (receive, issue, transfer, adjust, return)
- Parts request flow (engineer → warehouse)
- Low stock alerts with configurable thresholds
- Supplier management
- Purchase orders (create, track, receive)

### Phase 4 — Reporting & Polish
- Financial reports (revenue, aged receivables, quotation conversion)
- Operational reports (SLA compliance, engineer performance)
- Inventory reports (stock levels, usage, dead stock)
- Excel/PDF export for all reports
- SLA monitoring with pause/resume clock
- Audit log viewer
- Global search
- In-app notifications system

---

## 10. Success Criteria

- All 4 roles can log in via Supabase Auth and see role-appropriate dashboards
- Configurable RBAC with granular permissions per resource and action
- Full service request lifecycle from creation to payment
- Quotations generated with correct Egyptian VAT (14%) and revision support
- Inventory accurately tracks parts across service tickets with reservation
- Parts request flow between engineers and warehouse workers
- Purchase orders track supplier deliveries (full, partial)
- SLA monitoring with configurable thresholds and pause/resume clock
- Invoices support partial payments, overdue escalation, and credit notes
- Reports exportable to PDF and Excel
- Audit trail captures all state changes with before/after snapshots
- File uploads (photos, documents) stored via Supabase Storage through backend
- System handles 50+ concurrent users without degradation
