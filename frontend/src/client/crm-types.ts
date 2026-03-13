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
