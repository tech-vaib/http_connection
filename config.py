SERVICE_CONFIGS = {
    "user_service": {
        "base_url": "https://jsonplaceholder.typicode.com",
        "timeout": 5,
        "max_connections": 50,
        "api_key": "USER_API_KEY_ABC123",
        "max_tries": 3
    },
    "inventory_service": {
        "base_url": "https://api.example.com/inventory",
        "timeout": 3,
        "max_connections": 30,
        "api_key": "INVENTORY_API_KEY_456XYZ",
        "max_tries": 5  # Different retry strategy
    }
}
