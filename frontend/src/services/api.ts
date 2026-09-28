/**
 * API client for Vintage Brechó backend services.
 */

export interface Product {
  id: number;
  title: string;
  category: string;
  description: string | null;
  size: string;
  price: number;
  image_url: string;
  status: string;
  locked_until?: string | null;
  created_at?: string | null;
}

export interface OrderCreate {
  product_id?: number;
  product_ids?: number[];
  customer_name?: string;
  customer_email: string;
  customer_phone?: string;
  customer_address?: string;
}

export interface CheckoutResponse {
  order_id: string;
  product_id?: number;
  product_ids?: number[];
  items_count?: number;
  total_amount: number;
  shipping_cost: number;
  product_price: number;
  qr_code: string;
  qr_code_base64: string;
  expires_in: number;
}

export interface OrderStatus {
  order_id: string;
  payment_status: 'pending' | 'approved' | 'cancelled' | string;
  is_paid: boolean;
  product_title?: string | null;
  product_status?: string | null;
  items_count?: number;
  items?: Array<{
    product_id: number;
    price_at_purchase: number;
    product_title?: string;
  }>;
}

export interface AdminOrder {
  order_id: string;
  product_title: string;
  product_price: number;
  customer_name: string;
  customer_email?: string;
  customer_phone: string;
  customer_address: string;
  total_amount: number;
  payment_status?: string;
  created_at: string;
}

export interface ProductCreate {
  title: string;
  category: string;
  description?: string;
  size: string;
  price: number;
  image_url: string;
}

const API_BASE = import.meta.env.VITE_API_URL 
  ? `${import.meta.env.VITE_API_URL}/api` 
  : '/api';

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
    this.name = 'ApiError';
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `Erro HTTP ${res.status}`;
    try {
      const errorJson = await res.json();
      if (errorJson.detail) {
        errorDetail = typeof errorJson.detail === 'string'
          ? errorJson.detail
          : JSON.stringify(errorJson.detail);
      }
    } catch {
      // Non-json error
    }
    throw new ApiError(res.status, errorDetail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  /**
   * Fetches available products. Optionally filters by category.
   */
  async getProducts(category?: string): Promise<Product[]> {
  const baseUrl = API_BASE.startsWith('http') 
    ? API_BASE 
    : `${window.location.origin}${API_BASE}`;
  const url = new URL(`${baseUrl}/products`);
  if (category && category !== 'Todas as Peças') {
    url.searchParams.set('category', category);
  }
  const res = await fetch(url.toString());
  return handleResponse<Product[]>(res);
  },

  /**
   * Fetches distinct categories that have available products in stock.
   */
  async getCategories(): Promise<string[]> {
    const res = await fetch(`${API_BASE}/categories`);
    return handleResponse<string[]>(res);
  },

  /**
   * Fetches product details by ID.
   */
  async getProduct(id: number): Promise<Product> {
    const res = await fetch(`${API_BASE}/products/${id}`);
    return handleResponse<Product>(res);
  },

  /**
   * Initiates transparent PIX checkout and acquires 10-min reservation lock.
   */
  async checkoutPix(order: OrderCreate): Promise<CheckoutResponse> {
    const res = await fetch(`${API_BASE}/checkout/pix`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(order),
    });
    return handleResponse<CheckoutResponse>(res);
  },

  /**
   * Polls order status by order ID.
   */
  async getOrderStatus(orderId: string): Promise<OrderStatus> {
    const res = await fetch(`${API_BASE}/orders/${orderId}/status`);
    return handleResponse<OrderStatus>(res);
  },

  /**
   * Admin: Creates a new vintage product.
   */
  async createProduct(product: ProductCreate): Promise<Product> {
    const res = await fetch(`${API_BASE}/products`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(product),
    });
    return handleResponse<Product>(res);
  },

  /**
   * Admin: Lists paid orders for packaging and dispatch.
   */
  async getAdminOrders(): Promise<AdminOrder[]> {
    const res = await fetch(`${API_BASE}/admin/orders`);
    return handleResponse<AdminOrder[]>(res);
  },

  /**
   * Admin: Lists all products in the catalog regardless of status.
   */
  async getAdminProducts(): Promise<Product[]> {
    const res = await fetch(`${API_BASE}/admin/products`);
    return handleResponse<Product[]>(res);
  },

  /**
   * Admin: Permanently deletes a product from the database.
   */
  async deleteProduct(id: number): Promise<{ status: string; message: string; id: number }> {
    const res = await fetch(`${API_BASE}/products/${id}`, {
      method: 'DELETE',
    });
    return handleResponse<{ status: string; message: string; id: number }>(res);
  },
};
