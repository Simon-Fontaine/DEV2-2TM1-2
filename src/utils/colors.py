from ..models.table import TableStatus


def get_status_color(status: TableStatus) -> str:
    """Get color for table status"""
    colors = {
        TableStatus.AVAILABLE: "#2ecc71",  # Green
        TableStatus.OCCUPIED: "#e74c3c",  # Red
        TableStatus.RESERVED: "#f1c40f",  # Yellow
        TableStatus.MAINTENANCE: "#95a5a6",  # Gray
        TableStatus.CLEANING: "#3498db",  # Blue
    }
    return colors.get(status, "#bdc3c7")  # Default gray
