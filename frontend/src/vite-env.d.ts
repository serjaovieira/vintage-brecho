/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_SUPABASE_URL: string;
  readonly VITE_SUPABASE_ANON_KEY: string;
  readonly VITE_SUPABASE_BUCKET: string;
  readonly VITE_STORE_WHATSAPP: string;
  readonly VITE_STORE_PHONE_DISPLAY: string;
  readonly VITE_FIXED_SHIPPING_PRICE: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
