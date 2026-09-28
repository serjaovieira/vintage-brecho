"""
SQLAlchemy 2.0 models for Vintage Brechó.
Defines `Product` (1-of-1 pieces with 10-minute atomic lock) and `Order` (PIX checkouts).
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
import uuid

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

try:
    from app.database import Base
except ImportError:
    from backend.app.database import Base


class Product(Base):
    """
    Represents an exclusive 1-of-1 vintage feminine fashion piece.
    Status values:
      - 'available': In vitrine, ready for purchase.
      - 'locked': Temporarily reserved for 10 minutes during checkout.
      - 'sold': Permanently purchased; removed from public vitrine.
    """
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    size: Mapped[str] = mapped_column(String(20), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="available",
        server_default="available"
    )
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    orders: Mapped[List["Order"]] = relationship(
        "Order",
        back_populates="product"
    )

    __table_args__ = (
        Index("idx_products_status_lock", "status", "locked_until"),
        Index("idx_products_category", "category"),
    )

    def is_currently_available(self, now: Optional[datetime] = None) -> bool:
        """Evaluates whether the piece is available or its lock has expired."""
        if self.status == "available":
            return True
        if self.status == "locked" and self.locked_until:
            current_time = now or datetime.now(self.locked_until.tzinfo)
            return self.locked_until < current_time
        return False


class Order(Base):
    """
    Represents a customer purchase order generated during PIX checkout.
    Can contain one or multiple items (OrderItem).
    Payment status values:
      - 'pending': Awaiting PIX confirmation (10-minute window).
      - 'approved': Paid via PIX; pieces transitioned to 'sold'.
      - 'cancelled': Abandoned, expired, or rejected.
    """
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    product_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    customer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    customer_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shipping_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("15.00"),
        server_default="15.00"
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    mercadopago_payment_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )
    payment_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    product: Mapped[Optional["Product"]] = relationship("Product", back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )


class OrderItem(Base):
    """
    Represents an item within an Order.
    Enables multi-item checkouts while tracking individual price at purchase.
    """
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    product_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    price_at_purchase: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped[Optional["Product"]] = relationship("Product")

