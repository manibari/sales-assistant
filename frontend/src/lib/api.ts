const API_BASE = "/api";

async function fetchAPI<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export interface Client {
  client_id: string;
  company_name: string;
  industry: string | null;
  department: string | null;
  email: string | null;
  notes: string | null;
  client_health_score: number | null;
}

export interface Project {
  project_id: number;
  project_name: string;
  client_id: string | null;
  status_code: string;
  presale_owner: string | null;
  sales_owner: string | null;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface GraphNode {
  id: string;
  label: string;
  type: "person" | "org" | "project" | "intel";
  status?: string;
  leverage?: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
  label: string;
  leverage?: string;
}

export const api = {
  crm: {
    list: () => fetchAPI<Client[]>("/crm/"),
    get: (id: string) => fetchAPI<Client>(`/crm/${id}`),
  },
  projects: {
    list: () => fetchAPI<Project[]>("/projects/"),
    presale: () => fetchAPI<Project[]>("/projects/presale"),
    postsale: () => fetchAPI<Project[]>("/projects/postsale"),
  },
  network: {
    graph: () => fetchAPI<GraphData>("/network/graph"),
  },
};
