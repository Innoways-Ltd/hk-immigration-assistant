export type ServiceLocation = {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  rating: number;
  type: string;
  description?: string;
};

export type Property = {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  bedrooms: number;
  rent: number;
  furnished: boolean;
  commute_time?: string;
  description?: string;
};

export type SettlementTask = {
  id: string;
  title: string;
  description: string;
  day_range: string;
  priority: "high" | "medium" | "low";
  location?: ServiceLocation;
  documents_needed: string[];
  estimated_duration: string;
  status: "pending" | "in_progress" | "completed";
  dependencies: string[];
  task_type?: "core" | "extended";  // Task type: core (essential) or extended (AI-suggested)
  recommendation_reason?: string;    // Why this extended task is recommended
  related_core_task?: string;        // ID of the related core task (for extended tasks)
};

export type CustomerInfo = {
  name?: string;
  arrival_date?: string;
  office_address?: string;
  office_coordinates?: [number, number];
  housing_budget?: number;
  preferred_areas?: string[];
  bedrooms?: number;
  family_size?: number;
  has_children?: boolean;
  needs_car?: boolean;
  temporary_accommodation_days?: number;
};

export type SettlementPlan = {
  id: string;
  customer_name: string;
  center_latitude: number;
  center_longitude: number;
  zoom: number;
  tasks: SettlementTask[];
  properties: Property[];
  service_locations: ServiceLocation[];
  summary?: string;  // Human-readable summary generated from finalized plan
};

export type SearchProgress = {
  query: string;
  done: boolean;
  results?: string[];
};

export type AgentState = {
  customer_info: CustomerInfo;
  settlement_plan: SettlementPlan | null;
  selected_task_id: string | null;
  search_progress?: SearchProgress[];
  planning_progress?: any[];
};

// Keep old types for compatibility
export type Place = ServiceLocation;
export type Trip = SettlementPlan;
