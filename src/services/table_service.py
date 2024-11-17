import logging
from datetime import datetime
from itertools import combinations
from typing import List, Optional
from sqlalchemy import and_
from .service import Service
from ..models.table import Table, TableStatus

logger = logging.getLogger(__name__)


class TableService(Service[Table]):
    """Table-specific service with specialized methods"""

    def __init__(self, session_factory):
        super().__init__(Table, session_factory)

    def get_by_number(self, number: int) -> Optional[Table]:
        """Get table by number"""
        with self.session_scope() as session:
            table = (
                session.query(self.model).filter(self.model.number == number).first()
            )
            return self._clone_object(table, session)

    def update_status(self, table_id: int, new_status: TableStatus) -> Optional[Table]:
        """Update table status"""
        return self.update(table_id, status=new_status)

    def get_available_tables(
        self, time: datetime, party_size: int, duration_minutes: int = 120
    ) -> List[Table]:
        """Get available tables for a specific time and party size"""
        with self.session_scope() as session:
            tables = (
                session.query(self.model)
                .filter(
                    and_(
                        self.model.capacity >= party_size,
                        self.model.status == TableStatus.AVAILABLE,
                    )
                )
                .all()
            )

            available = [t for t in tables if t.is_available_at(time, duration_minutes)]
            return [self._clone_object(t, session) for t in available]

    def get_status_counts(self) -> dict:
        """Get count of tables in each status"""
        with self.session_scope() as session:
            counts = {}
            for status in TableStatus:
                count = (
                    session.query(self.model)
                    .filter(self.model.status == status)
                    .count()
                )
                counts[status.value] = count
            return counts

    def find_tables_for_party(
        self,
        party_size: int,
        desired_time: datetime,
        duration_minutes: int = 120,
        max_tables: int = 3,
        capacity_buffer: float = 1.5,
    ) -> List[List[Table]]:
        """Find combinations of tables that can accommodate a party."""
        try:
            with self.session_scope() as session:
                # Get all available tables
                available_tables = self.get_available_tables(
                    desired_time,
                    1,  # Minimum capacity of 1 to get all tables
                    duration_minutes,
                )

                if not available_tables:
                    return []

                # Sort tables by capacity for more efficient combinations
                available_tables.sort(key=lambda t: t.capacity)

                # Quick check for a single table that fits well
                perfect_table = next(
                    (
                        t
                        for t in available_tables
                        if party_size <= t.capacity <= party_size * 1.2
                    ),
                    None,
                )
                if perfect_table:
                    return [[perfect_table]]

                max_total_capacity = int(party_size * capacity_buffer)
                valid_combinations = []

                # Try combinations of different sizes
                for num_tables in range(
                    1, min(max_tables + 1, len(available_tables) + 1)
                ):
                    for combo in combinations(available_tables, num_tables):
                        total_capacity = sum(table.capacity for table in combo)

                        # Check if combination is suitable
                        if party_size <= total_capacity <= max_total_capacity:
                            valid_combinations.append(list(combo))

                    # Stop if we found good enough combinations
                    if valid_combinations and num_tables < max_tables:
                        best_current_capacity = min(
                            sum(table.capacity for table in combo)
                            for combo in valid_combinations
                        )
                        if best_current_capacity <= party_size * 1.2:  # 20% buffer
                            break

                # Sort combinations by optimality
                valid_combinations.sort(
                    key=lambda tables: (
                        len(tables),  # Prefer fewer tables
                        abs(
                            sum(t.capacity for t in tables) - party_size
                        ),  # Prefer closer capacity match
                    )
                )

                return valid_combinations

        except Exception as e:
            logger.error(f"Error finding tables for party: {e}")
            raise

    def check_table_availability(
        self, table_id: int, check_time: datetime, duration_minutes: int = 120
    ) -> bool:
        """Check if a specific table is available at a given time"""
        with self.session_scope() as session:
            table = session.query(self.model).get(table_id)
            if not table:
                return False
            return table.is_available_at(check_time, duration_minutes)

    def get_tables_by_location(self, location: str) -> List[Table]:
        """Get all tables in a specific location"""
        with self.session_scope() as session:
            return (
                session.query(self.model).filter(self.model.location == location).all()
            )

    def get_tables_by_capacity(
        self, min_capacity: int, max_capacity: Optional[int] = None
    ) -> List[Table]:
        """Get tables within a capacity range"""
        with self.session_scope() as session:
            query = session.query(self.model).filter(
                self.model.capacity >= min_capacity
            )
            if max_capacity is not None:
                query = query.filter(self.model.capacity <= max_capacity)
            return query.all()

    def get_tables_needing_maintenance(self) -> List[Table]:
        """Get all tables marked for maintenance"""
        with self.session_scope() as session:
            return (
                session.query(self.model)
                .filter(self.model.status == TableStatus.MAINTENANCE)
                .all()
            )

    def bulk_update_status(self, table_ids: List[int], new_status: TableStatus) -> int:
        """Update status for multiple tables at once"""
        with self.session_scope() as session:
            updated = (
                session.query(self.model)
                .filter(self.model.id.in_(table_ids))
                .update({self.model.status: new_status}, synchronize_session=False)
            )
            session.commit()
            return updated
