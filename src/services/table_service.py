import logging
from itertools import combinations
from sqlalchemy import and_
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from .base import BaseService
from ..models.table import Table, TableStatus

logger = logging.getLogger(__name__)


class TableService(BaseService[Table]):
    def __init__(self, db_session: Session):
        super().__init__(db_session, Table)

    def get_by_number(self, table_number: int) -> Optional[Table]:
        """Get table by its number"""
        return self.db.query(Table).filter(Table.number == table_number).first()

    def get_table_status_counts(self) -> dict:
        """Get count of tables in each status"""
        counts = {}
        for status in TableStatus:
            count = self.db.query(Table).filter(Table.status == status).count()
            counts[status.value] = count
        return counts

    def get_available_tables(
        self, datetime: datetime, party_size: int, duration_minutes: int = 120
    ):
        """Get available tables for a specific time and party size"""
        try:
            suitable_tables = (
                self.db.query(Table)
                .filter(
                    and_(
                        Table.capacity >= party_size,
                        Table.status == TableStatus.AVAILABLE,
                    )
                )
                .all()
            )

            # Filter out tables that have conflicting reservations
            return [
                table
                for table in suitable_tables
                if table.is_available_at(datetime, duration_minutes)
            ]
        except Exception as e:
            logger.error(f"Error finding available tables: {str(e)}")
            raise

    def update_status(
        self, table_number: int, new_status: TableStatus
    ) -> Optional[Table]:
        """Update the status of a table"""
        try:
            table = self.get_by_number(table_number)
            if table:
                table.status = new_status
                return self.update(table)
            return None
        except Exception as e:
            logger.error(f"Error updating table status: {str(e)}")
            raise

    def find_tables_for_party(
        self,
        party_size: int,
        desired_time: datetime,
        duration_minutes: int = 120,
        max_tables: int = 3,
        capacity_buffer: float = 1.5,
    ) -> List[List[Table]]:
        try:
            available_tables = self.get_available_tables(
                desired_time, 1, duration_minutes
            )

            if not available_tables:
                logger.info("No available tables found for the requested time")
                return []

            # Sort tables by capacity
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
            for num_tables in range(1, min(max_tables + 1, len(available_tables) + 1)):
                for combo in combinations(available_tables, num_tables):
                    total_capacity = sum(table.capacity for table in combo)

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

            if not valid_combinations:
                logger.info(f"No suitable combination found for party of {party_size}")
                return []

            # Sort by number of tables and then by how close the capacity is to party_size
            valid_combinations.sort(
                key=lambda tables: (
                    len(tables),
                    abs(sum(t.capacity for t in tables) - party_size),
                )
            )

            return valid_combinations

        except Exception as e:
            logger.error(f"Error finding tables for party: {str(e)}")
            raise
