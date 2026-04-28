create table if not exists public.sales_orders (
  id uuid primary key default gen_random_uuid(),
  order_id text not null unique,
  order_date date not null,
  customer_name text not null,
  customer_email text not null,
  product_category text not null,
  product_name text not null,
  quantity integer not null check (quantity > 0),
  unit_price numeric(12, 2) not null check (unit_price >= 0),
  discount numeric(12, 2) not null default 0 check (discount >= 0),
  revenue numeric(12, 2) not null check (revenue >= 0),
  payment_method text not null,
  sales_channel text not null,
  region text not null,
  status text not null,
  created_at timestamptz not null default now()
);

create index if not exists sales_orders_order_date_idx on public.sales_orders (order_date);
create index if not exists sales_orders_category_idx on public.sales_orders (product_category);
create index if not exists sales_orders_region_idx on public.sales_orders (region);
