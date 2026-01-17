"""Ticket domain - core ticket operations."""
from .types import JiraTicket
from .query import fetch_ticket, fetch_tickets

__all__ = [
    "JiraTicket",
    "fetch_ticket",
    "fetch_tickets",
]
