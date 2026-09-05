from enum import Enum


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    ATTENDANT = "ATTENDANT"
    DISPATCHER = "DISPATCHER"
    RIDER = "RIDER"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    PICKED_UP = "PICKED_UP"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"