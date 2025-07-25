from http_client import AsyncServiceClient
from config import SERVICE_CONFIGS

user_service = AsyncServiceClient("user_service", SERVICE_CONFIGS["user_service"])
inventory_service = AsyncServiceClient("inventory_service", SERVICE_CONFIGS["inventory_service"])
