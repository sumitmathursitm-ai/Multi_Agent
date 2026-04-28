from random import choice, randint, random
from uuid import uuid4

from faker import Faker

from app.config import get_settings
from app.supabase_client import get_supabase


fake = Faker()

PRODUCTS = {
    "Apparel": ["Denim Jacket", "Running Tee", "Cargo Pants", "Sneakers"],
    "Electronics": ["Wireless Earbuds", "Smart Watch", "Bluetooth Speaker", "USB-C Hub"],
    "Home": ["Cotton Sheet Set", "Desk Lamp", "Ceramic Planter", "Storage Basket"],
    "Beauty": ["Face Serum", "Matte Lipstick", "Hair Mask", "Sunscreen"],
    "Grocery": ["Organic Coffee", "Protein Bars", "Olive Oil", "Herbal Tea"],
}
REGIONS = ["North", "South", "East", "West", "Central"]
CHANNELS = ["Website", "Mobile App", "Marketplace"]
PAYMENTS = ["Credit Card", "UPI", "PayPal", "Debit Card", "Wallet"]
STATUSES = ["paid", "paid", "paid", "refunded", "cancelled"]


def build_fake_sale() -> dict:
    category = choice(list(PRODUCTS.keys()))
    product = choice(PRODUCTS[category])
    quantity = randint(1, 5)
    unit_price = round(randint(15, 400) + random(), 2)
    discount = round(unit_price * quantity * choice([0, 0.05, 0.1, 0.15]), 2)
    revenue = round((unit_price * quantity) - discount, 2)
    order_date = fake.date_between(start_date="-180d", end_date="today")

    return {
        "order_id": f"ORD-{uuid4().hex[:10].upper()}",
        "order_date": order_date.isoformat(),
        "customer_name": fake.name(),
        "customer_email": fake.email(),
        "product_category": category,
        "product_name": product,
        "quantity": quantity,
        "unit_price": unit_price,
        "discount": discount,
        "revenue": revenue,
        "payment_method": choice(PAYMENTS),
        "sales_channel": choice(CHANNELS),
        "region": choice(REGIONS),
        "status": choice(STATUSES),
    }


def seed_sales(rows: int | None = None) -> int:
    settings = get_settings()
    row_count = rows or settings.seed_default_rows
    payload = [build_fake_sale() for _ in range(row_count)]
    get_supabase().table(settings.supabase_sales_table).insert(payload).execute()
    return row_count
