// Manual CRM services — will be replaced when API client is regenerated

import type { CancelablePromise } from "./core/CancelablePromise"
import { OpenAPI } from "./core/OpenAPI"
import { request as __request } from "./core/request"
import type {
  CustomerCreate,
  CustomerPublic,
  CustomerUpdate,
  CustomersPublic,
  ContactCreate,
  ContactPublic,
  ContactUpdate,
  ContactsPublic,
  EquipmentCreate,
  EquipmentPublic,
  EquipmentUpdate,
  EquipmentListPublic,
  ServiceRequestCreate,
  ServiceRequestPublic,
  ServiceRequestUpdate,
  ServiceRequestsPublic,
  ServiceVisitCreate,
  ServiceVisitPublic,
  ServiceVisitsPublic,
} from "./crm-types"

export class CustomersService {
  public static readCustomers(
    data: {
      skip?: number
      limit?: number
      segment?: string | null
      is_active?: boolean | null
      search?: string | null
    } = {},
  ): CancelablePromise<CustomersPublic> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/v1/customers/",
      query: {
        skip: data.skip,
        limit: data.limit,
        segment: data.segment,
        is_active: data.is_active,
        search: data.search,
      },
    })
  }

  public static createCustomer(data: {
    requestBody: CustomerCreate
  }): CancelablePromise<CustomerPublic> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/api/v1/customers/",
      body: data.requestBody,
      mediaType: "application/json",
    })
  }

  public static readCustomer(data: {
    customerId: string
  }): CancelablePromise<CustomerPublic> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/v1/customers/{customer_id}",
      path: {
        customer_id: data.customerId,
      },
    })
  }

  public static updateCustomer(data: {
    customerId: string
    requestBody: CustomerUpdate
  }): CancelablePromise<CustomerPublic> {
    return __request(OpenAPI, {
      method: "PATCH",
      url: "/api/v1/customers/{customer_id}",
      path: {
        customer_id: data.customerId,
      },
      body: data.requestBody,
      mediaType: "application/json",
    })
  }

  public static deleteCustomer(data: {
    customerId: string
  }): CancelablePromise<void> {
    return __request(OpenAPI, {
      method: "DELETE",
      url: "/api/v1/customers/{customer_id}",
      path: {
        customer_id: data.customerId,
      },
    })
  }
}

export class ContactsService {
  public static readContacts(data: {
    customerId: string
  }): CancelablePromise<ContactsPublic> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/v1/customers/{customer_id}/contacts/",
      path: {
        customer_id: data.customerId,
      },
    })
  }

  public static createContact(data: {
    customerId: string
    requestBody: ContactCreate
  }): CancelablePromise<ContactPublic> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/api/v1/customers/{customer_id}/contacts/",
      path: {
        customer_id: data.customerId,
      },
      body: data.requestBody,
      mediaType: "application/json",
    })
  }

  public static updateContact(data: {
    customerId: string
    contactId: string
    requestBody: ContactUpdate
  }): CancelablePromise<ContactPublic> {
    return __request(OpenAPI, {
      method: "PATCH",
      url: "/api/v1/customers/{customer_id}/contacts/{contact_id}",
      path: {
        customer_id: data.customerId,
        contact_id: data.contactId,
      },
      body: data.requestBody,
      mediaType: "application/json",
    })
  }

  public static deleteContact(data: {
    customerId: string
    contactId: string
  }): CancelablePromise<void> {
    return __request(OpenAPI, {
      method: "DELETE",
      url: "/api/v1/customers/{customer_id}/contacts/{contact_id}",
      path: {
        customer_id: data.customerId,
        contact_id: data.contactId,
      },
    })
  }
}

export class EquipmentService {
  public static readEquipment(
    data: {
      skip?: number
      limit?: number
      search?: string | null
    } = {},
  ): CancelablePromise<EquipmentListPublic> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/v1/equipment",
      query: {
        skip: data.skip,
        limit: data.limit,
        search: data.search,
      },
    })
  }

  public static readCustomerEquipment(data: {
    customerId: string
  }): CancelablePromise<EquipmentListPublic> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/v1/customers/{customer_id}/equipment",
      path: {
        customer_id: data.customerId,
      },
    })
  }

  public static createEquipment(data: {
    customerId: string
    requestBody: EquipmentCreate
  }): CancelablePromise<EquipmentPublic> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/api/v1/customers/{customer_id}/equipment",
      path: {
        customer_id: data.customerId,
      },
      body: data.requestBody,
      mediaType: "application/json",
    })
  }

  public static updateEquipment(data: {
    equipmentId: string
    requestBody: EquipmentUpdate
  }): CancelablePromise<EquipmentPublic> {
    return __request(OpenAPI, {
      method: "PATCH",
      url: "/api/v1/equipment/{equipment_id}",
      path: {
        equipment_id: data.equipmentId,
      },
      body: data.requestBody,
      mediaType: "application/json",
    })
  }

  public static deleteEquipment(data: {
    equipmentId: string
  }): CancelablePromise<void> {
    return __request(OpenAPI, {
      method: "DELETE",
      url: "/api/v1/equipment/{equipment_id}",
      path: {
        equipment_id: data.equipmentId,
      },
    })
  }
}

export class ServiceRequestsService {
  public static readServiceRequests(
    data: {
      skip?: number
      limit?: number
      status?: string | null
      priority?: string | null
      customer_id?: string | null
      assigned_engineer_id?: string | null
    } = {},
  ): CancelablePromise<ServiceRequestsPublic> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/v1/service-requests/",
      query: {
        skip: data.skip,
        limit: data.limit,
        status: data.status,
        priority: data.priority,
        customer_id: data.customer_id,
        assigned_engineer_id: data.assigned_engineer_id,
      },
    })
  }

  public static createServiceRequest(data: {
    requestBody: ServiceRequestCreate
  }): CancelablePromise<ServiceRequestPublic> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/api/v1/service-requests/",
      body: data.requestBody,
      mediaType: "application/json",
    })
  }

  public static readServiceRequest(data: {
    requestId: string
  }): CancelablePromise<ServiceRequestPublic> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/v1/service-requests/{request_id}",
      path: { request_id: data.requestId },
    })
  }

  public static updateServiceRequest(data: {
    requestId: string
    requestBody: ServiceRequestUpdate
  }): CancelablePromise<ServiceRequestPublic> {
    return __request(OpenAPI, {
      method: "PATCH",
      url: "/api/v1/service-requests/{request_id}",
      path: { request_id: data.requestId },
      body: data.requestBody,
      mediaType: "application/json",
    })
  }

  public static updateStatus(data: {
    requestId: string
    requestBody: { status: string; notes?: string | null }
  }): CancelablePromise<ServiceRequestPublic> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/api/v1/service-requests/{request_id}/status",
      path: { request_id: data.requestId },
      body: data.requestBody,
      mediaType: "application/json",
    })
  }

  public static assignEngineer(data: {
    requestId: string
    engineerId: string
  }): CancelablePromise<ServiceRequestPublic> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/api/v1/service-requests/{request_id}/assign",
      path: { request_id: data.requestId },
      query: { engineer_id: data.engineerId },
    })
  }
}

export class ServiceVisitsService {
  public static readVisits(data: {
    requestId: string
  }): CancelablePromise<ServiceVisitsPublic> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/v1/service-requests/{request_id}/visits/",
      path: { request_id: data.requestId },
    })
  }

  public static createVisit(data: {
    requestId: string
    requestBody: ServiceVisitCreate
  }): CancelablePromise<ServiceVisitPublic> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/api/v1/service-requests/{request_id}/visits/",
      path: { request_id: data.requestId },
      body: data.requestBody,
      mediaType: "application/json",
    })
  }
}
