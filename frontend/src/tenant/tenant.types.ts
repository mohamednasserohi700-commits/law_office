export type SubscriptionPlan = "Basic" | "Pro" | "Enterprise";

export interface Tenant {
  id: number;
  name: string;
  slug: string;
  subscription_plan: SubscriptionPlan;
  theme_primary: string;
  active: number;
}

export interface TenantSummaryResponse {
  tenant: {
    id: number;
    name: string;
    slug: string;
    subscription_plan: SubscriptionPlan;
    theme_primary: string;
  };
  plan_features: {
    max_users: number;
    storage_limit_mb: number;
    advanced_analytics: boolean;
  };
  usage: {
    users: number;
    cases: number;
    storage_docs: number;
  };
}
