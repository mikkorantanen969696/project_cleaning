from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class UserRole(enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    CLEANER = "cleaner"

class OrderStatus(enum.Enum):
    NEW = "new"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PaymentStatus(enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    REFUNDED = "refunded"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(50))
    full_name = Column(String(100))
    phone = Column(String(20))
    role = Column(Enum(UserRole), nullable=False)
    password = Column(String(100))  # For managers
    city_id = Column(Integer, ForeignKey("cities.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    city = relationship("City", back_populates="users")
    created_orders = relationship("Order", foreign_keys="Order.manager_id", back_populates="manager")
    assigned_orders = relationship("Order", foreign_keys="Order.cleaner_id", back_populates="cleaner")
    payments = relationship("Payment", back_populates="user")

class City(Base):
    __tablename__ = "cities"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    telegram_topic_id = Column(String(50))  # ID of the topic in supergroup
    is_active = Column(Boolean, default=True)
    
    # Relationships
    users = relationship("User", back_populates="city")
    orders = relationship("Order", back_populates="city")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True)
    client_name = Column(String(100), nullable=False)
    client_phone = Column(String(20), nullable=False)
    address = Column(Text, nullable=False)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    cleaning_type = Column(String(50), nullable=False)  # regular, deep, post_repair, etc.
    date_time = Column(DateTime, nullable=False)
    duration_hours = Column(Numeric(3,1), nullable=False)
    price = Column(Numeric(10,2), nullable=False)
    equipment_available = Column(Boolean, default=False)
    chemicals_available = Column(Boolean, default=False)
    notes = Column(Text)
    status = Column(Enum(OrderStatus), default=OrderStatus.NEW)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    cleaner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    city = relationship("City", back_populates="orders")
    manager = relationship("User", foreign_keys=[manager_id], back_populates="created_orders")
    cleaner = relationship("User", foreign_keys=[cleaner_id], back_populates="assigned_orders")
    photos = relationship("OrderPhoto", back_populates="order")
    payments = relationship("Payment", back_populates="order")

class OrderPhoto(Base):
    __tablename__ = "order_photos"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    file_id = Column(String(255), nullable=False)  # Telegram file_id
    photo_type = Column(String(20), nullable=False)  # before, after
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    order = relationship("Order", back_populates="photos")

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric(10,2), nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    payment_type = Column(String(20), nullable=False)  # client_payment, cleaner_payment
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime)
    
    # Relationships
    order = relationship("Order", back_populates="payments")
    user = relationship("User", back_populates="payments")

class Statistics(Base):
    __tablename__ = "statistics"
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    city_id = Column(Integer, ForeignKey("cities.id"))
    manager_id = Column(Integer, ForeignKey("users.id"))
    cleaner_id = Column(Integer, ForeignKey("users.id"))
    orders_count = Column(Integer, default=0)
    total_amount = Column(Numeric(10,2), default=0)
    completed_orders = Column(Integer, default=0)
    cancelled_orders = Column(Integer, default=0)
