// Manual CRM types — will be replaced when API client is regenerated

export type CustomerPublic = {
  id: string
  name: string
  company_name: string | null
  phone: string | null
  email: string | null
  address: string | null
  tax_id: string | null
  segment: string
  notes: string | null
  is_active: boolean
  created_at: string | null
  updated_at: string | null
}

export type CustomersPublic = {
  data: CustomerPublic[]
  count: number
}

export type CustomerCreate = {
  name: string
  company_name?: string | null
  phone?: string | null
  email?: string | null
  address?: string | null
  tax_id?: string | null
  segment?: string
  notes?: string | null
}

export type CustomerUpdate = {
  name?: string | null
  company_name?: string | null
  phone?: string | null
  email?: string | null
  address?: string | null
  tax_id?: string | null
  segment?: string | null
  notes?: string | null
  is_active?: boolean | null
}

export type ContactPublic = {
  id: string
  customer_id: string
  name: string
  title: string | null
  phone: string | null
  email: string | null
  is_primary: boolean
  created_at: string | null
}

export type ContactCreate = {
  customer_id: string
  name: string
  title?: string | null
  phone?: string | null
  email?: string | null
  is_primary?: boolean
}

export type ContactUpdate = {
  name?: string | null
  title?: string | null
  phone?: string | null
  email?: string | null
  is_primary?: boolean | null
}

export type ContactsPublic = {
  data: ContactPublic[]
  count: number
}

export type EquipmentPublic = {
  id: string
  customer_id: string
  model: string
  serial_number: string
  manufacturer: string | null
  install_date: string | null
  warranty_expiry: string | null
  notes: string | null
  is_active: boolean
  created_at: string | null
}

export type EquipmentCreate = {
  customer_id: string
  model: string
  serial_number: string
  manufacturer?: string | null
  install_date?: string | null
  warranty_expiry?: string | null
  notes?: string | null
}

export type EquipmentUpdate = {
  model?: string | null
  serial_number?: string | null
  manufacturer?: string | null
  install_date?: string | null
  warranty_expiry?: string | null
  notes?: string | null
  is_active?: boolean | null
}

export type EquipmentListPublic = {
  data: EquipmentPublic[]
  count: number
}

export type EquipmentWithCustomer = EquipmentPublic & {
  customer_name: string | null
}

export type ServiceRequestPublic = {
  id: string
  customer_id: string
  equipment_id: string | null
  assigned_engineer_id: string | null
  description: string
  priority: string
  source: string
  status: string
  diagnosis: string | null
  resolution_notes: string | null
  sla_response_due: string | null
  sla_resolution_due: string | null
  sla_response_breached: boolean
  sla_resolution_breached: boolean
  created_by: string | null
  created_at: string | null
  updated_at: string | null
}

export type ServiceRequestsPublic = {
  data: ServiceRequestPublic[]
  count: number
}

export type ServiceRequestCreate = {
  customer_id: string
  equipment_id?: string | null
  description: string
  priority?: string
  source?: string
}

export type ServiceRequestUpdate = {
  description?: string | null
  priority?: string | null
  diagnosis?: string | null
  resolution_notes?: string | null
  assigned_engineer_id?: string | null
  status?: string | null
}

export type ServiceVisitPublic = {
  id: string
  service_request_id: string
  engineer_id: string
  visit_date: string
  arrival_time: string | null
  departure_time: string | null
  notes: string | null
  created_at: string | null
}

export type ServiceVisitsPublic = {
  data: ServiceVisitPublic[]
  count: number
}

export type ServiceVisitCreate = {
  service_request_id: string
  visit_date: string
  arrival_time?: string | null
  departure_time?: string | null
  notes?: string | null
}
