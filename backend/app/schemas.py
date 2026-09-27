"""
Pydantic schemas and serialization models for Vintage Brechó API.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, computed_field


class ProductBase(BaseModel):
    title: str = Field(..., max_length=255, description="Nome da peça vintage")
    category: str = Field(..., max_length=100, description="Categoria da peça")
    description: Optional[str] = Field(None, description="Medidas, composição do tecido e estado de conservação")
    size: str = Field(..., max_length=20, description="Tamanho da peça (ex: P, M, G, 38, 40)")
    price: Decimal = Field(..., gt=0, decimal_places=2, description="Preço unitário em Reais (R$)")
    image_url: str = Field(..., description="URL pública da fotografia da peça")


class ProductCreate(ProductBase):
    status: Optional[str] = "available"
    locked_until: Optional[datetime] = None


class ProductOut(BaseModel):
    id: int
    title: str
    category: str
    description: Optional[str] = None
    size: str
    price: Decimal
    image_url: str
    status: str
    locked_until: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    def is_available(self) -> bool:
        if self.status == "available":
            return True
        if self.status == "locked" and self.locked_until:
            now_utc = datetime.now(timezone.utc)
            lock_time = self.locked_until if self.locked_until.tzinfo else self.locked_until.replace(tzinfo=timezone.utc)
            return lock_time < now_utc
        return False

    @computed_field
    def display_status(self) -> str:
        return "available" if self.is_available else self.status


class ProductDetailOut(ProductOut):
    pass


class OrderCreate(BaseModel):
    product_id: int
    customer_name: Optional[str] = Field(None, max_length=255)
    customer_email: str = Field(..., max_length=255)
    customer_phone: Optional[str] = Field(None, max_length=50)
    customer_address: Optional[str] = None


class CheckoutResponse(BaseModel):
    order_id: str
    product_id: int
    total_amount: Decimal
    shipping_cost: Decimal = Decimal("15.00")
    product_price: Decimal
    qr_code: str
    qr_code_base64: str
    expires_in: int = 600


class OrderStatusOut(BaseModel):
    order_id: str
    payment_status: str
    is_paid: bool
    product_title: Optional[str] = None
    product_status: Optional[str] = None


class HealthCheckOut(BaseModel):
    status: str
    database: str
    app: str
    version: str
