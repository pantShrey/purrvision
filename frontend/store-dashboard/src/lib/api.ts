import axios from 'axios';

export const api = axios.create({
  baseURL: 'http://localhost:8000', 
});

export interface Store {
  id: string;
  name: string;
  status: "QUEUED" | "PROVISIONING" | "READY" | "FAILED" | "DELETING" | "DELETED";
  engine: "woocommerce" | "medusa";
  url: string | null;
  store_admin_url: string | null;
}

export interface StoreCredentials {
  username: string;
  password: string;
}
export interface AuditLog {
  event: string;
  details: string | null; 
  timestamp: string;
}