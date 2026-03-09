const API_BASE = "/api/nx";

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

async function postAPI<T>(path: string, body: unknown): Promise<T> {
  return fetchAPI<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

async function patchAPI<T>(path: string, body: unknown): Promise<T> {
  return fetchAPI<T>(path, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

async function deleteAPI(path: string): Promise<void> {
  const res = await fetch(`${API_BASE}${path}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
}

// --- Types ---

export interface NxClient {
  id: number;
  name: string;
  industry: string | null;
  budget_range: string | null;
  status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
  documents?: NxDocument[];
  tags?: NxTag[];
}

export interface NxPartner {
  id: number;
  name: string;
  trust_level: string;
  team_size: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  tags?: NxTag[];
}

export interface NxContact {
  id: number;
  name: string;
  title: string | null;
  phone: string | null;
  email: string | null;
  org_type: string | null;
  org_id: number | null;
  role: string | null;
  notes: string | null;
}

export interface NxIntel {
  id: number;
  raw_input: string;
  input_type: string;
  parsed_json: string | null;
  status: string;
  source_contact_id: number | null;
  created_at: string;
}

export interface NxDeal {
  id: number;
  name: string;
  client_id: number;
  client_name?: string;
  client_industry?: string;
  stage: string;
  budget_range: string | null;
  timeline: string | null;
  meddic_json: string | null;
  status: string;
  idle_days?: number;
  last_activity_at: string;
  partners?: NxDealPartner[];
  intel?: NxIntel[];
  tbds?: NxTbdItem[];
  files?: NxFile[];
  tags?: NxTag[];
  meddic_progress?: MeddicProgress;
}

export interface NxDealPartner {
  id: number;
  deal_id: number;
  partner_id: number;
  partner_name: string;
  trust_level: string;
  role: string | null;
}

export interface NxTag {
  id: number;
  name: string;
  category: string;
}

export interface NxTbdItem {
  id: number;
  question: string;
  context: string | null;
  linked_type: string | null;
  linked_id: number | null;
  source: string;
  resolved: number;
  created_at: string;
}

export interface NxDocument {
  id: number;
  client_id: number;
  doc_type: string;
  status: string;
  sign_date: string | null;
  expiry_date: string | null;
  file_path: string | null;
}

export interface NxMeeting {
  id: number;
  deal_id: number;
  deal_name?: string;
  client_name?: string;
  title: string;
  meeting_date: string;
  participants_json: string | null;
  status: string;
}

export interface NxReminder {
  id: number;
  deal_id: number | null;
  deal_name?: string;
  reminder_type: string;
  due_date: string;
  content: string;
  resolved: number;
}

export interface NxFile {
  id: number;
  deal_id: number;
  file_type: string;
  file_name: string;
  file_path: string;
  source_url: string | null;
  parsed_json: string | null;
  parse_status: string;
}

export interface MeddicProgress {
  completed: number;
  total: number;
  missing: string[];
  details?: Record<string, string | null>;
}

// --- API ---

export const nxApi = {
  clients: {
    list: (status?: string) => fetchAPI<NxClient[]>(`/clients/${status ? `?status=${status}` : ""}`),
    get: (id: number) => fetchAPI<NxClient>(`/clients/${id}`),
    create: (data: { name: string; industry?: string; budget_range?: string }) =>
      postAPI<NxClient>("/clients/", data),
    update: (id: number, data: Partial<NxClient>) =>
      patchAPI<NxClient>(`/clients/${id}`, data),
  },
  partners: {
    list: (trustLevel?: string) => fetchAPI<NxPartner[]>(`/partners/${trustLevel ? `?trust_level=${trustLevel}` : ""}`),
    get: (id: number) => fetchAPI<NxPartner>(`/partners/${id}`),
    create: (data: { name: string; trust_level?: string; team_size?: string }) =>
      postAPI<NxPartner>("/partners/", data),
    update: (id: number, data: Partial<NxPartner>) =>
      patchAPI<NxPartner>(`/partners/${id}`, data),
  },
  contacts: {
    list: (orgType?: string, orgId?: number) => {
      const params = new URLSearchParams();
      if (orgType) params.set("org_type", orgType);
      if (orgId) params.set("org_id", String(orgId));
      const qs = params.toString();
      return fetchAPI<NxContact[]>(`/contacts/${qs ? `?${qs}` : ""}`);
    },
    get: (id: number) => fetchAPI<NxContact>(`/contacts/${id}`),
    create: (data: Partial<NxContact> & { name: string }) =>
      postAPI<NxContact>("/contacts/", data),
  },
  intel: {
    list: (status?: string, limit?: number) => {
      const params = new URLSearchParams();
      if (status) params.set("status", status);
      if (limit) params.set("limit", String(limit));
      const qs = params.toString();
      return fetchAPI<NxIntel[]>(`/intel/${qs ? `?${qs}` : ""}`);
    },
    get: (id: number) => fetchAPI<NxIntel>(`/intel/${id}`),
    create: (data: { raw_input: string; input_type?: string }) =>
      postAPI<NxIntel>("/intel/", data),
    confirm: (id: number, parsed_json?: string) =>
      postAPI<NxIntel>(`/intel/${id}/confirm`, { parsed_json }),
  },
  deals: {
    list: (view?: string) => fetchAPI<NxDeal[]>(`/deals/?view=${view || "urgency"}`),
    needsPush: (days?: number) => fetchAPI<NxDeal[]>(`/deals/needs-push${days ? `?threshold_days=${days}` : ""}`),
    get: (id: number) => fetchAPI<NxDeal>(`/deals/${id}`),
    create: (data: { name: string; client_id: number; budget_range?: string; timeline?: string }) =>
      postAPI<NxDeal>("/deals/", data),
    update: (id: number, data: Partial<NxDeal>) =>
      patchAPI<NxDeal>(`/deals/${id}`, data),
    advance: (id: number, stage: string) =>
      postAPI<NxDeal>(`/deals/${id}/advance?stage=${stage}`, {}),
    close: (id: number, reason: string, notes?: string) =>
      postAPI<NxDeal>(`/deals/${id}/close`, { reason, notes }),
    addPartner: (dealId: number, partnerId: number, role?: string) =>
      postAPI<NxDealPartner>(`/deals/${dealId}/partners`, { partner_id: partnerId, role }),
    linkIntel: (dealId: number, intelId: number) =>
      postAPI<unknown>(`/deals/${dealId}/intel`, { intel_id: intelId }),
  },
  calendar: {
    meetingsByDate: (date: string) => fetchAPI<NxMeeting[]>(`/calendar/meetings?date=${date}`),
    meetingsByMonth: (year: number, month: number) =>
      fetchAPI<NxMeeting[]>(`/calendar/meetings/month/${year}/${month}`),
    createMeeting: (data: { deal_id: number; title: string; meeting_date: string; participants_json?: string }) =>
      postAPI<NxMeeting>("/calendar/meetings", data),
    remindersByDate: (date: string) => fetchAPI<NxReminder[]>(`/calendar/reminders?date=${date}`),
    remindersByMonth: (year: number, month: number) =>
      fetchAPI<NxReminder[]>(`/calendar/reminders/month/${year}/${month}`),
    pendingReminders: () => fetchAPI<NxReminder[]>("/calendar/reminders"),
  },
  tbd: {
    list: (linkedType?: string, linkedId?: number) => {
      const params = new URLSearchParams();
      if (linkedType) params.set("linked_type", linkedType);
      if (linkedId) params.set("linked_id", String(linkedId));
      const qs = params.toString();
      return fetchAPI<NxTbdItem[]>(`/tbd/${qs ? `?${qs}` : ""}`);
    },
    create: (data: { question: string; linked_type?: string; linked_id?: number; source?: string }) =>
      postAPI<NxTbdItem>("/tbd/", data),
    resolve: (id: number) => postAPI<NxTbdItem>(`/tbd/${id}/resolve`, {}),
  },
  tags: {
    list: (category?: string) => fetchAPI<NxTag[]>(`/tags/${category ? `?category=${category}` : ""}`),
    create: (name: string, category: string) => postAPI<NxTag>("/tags/", { name, category }),
    tagEntity: (entityType: string, entityId: number, tagId: number) =>
      postAPI<unknown>("/tags/entity", { entity_type: entityType, entity_id: entityId, tag_id: tagId }),
    getEntityTags: (entityType: string, entityId: number) =>
      fetchAPI<NxTag[]>(`/tags/entity/${entityType}/${entityId}`),
  },
};
