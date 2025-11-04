from typing import Literal, TypedDict, List, Optional
from langgraph.graph import MessagesState

class ServiceLocation(TypedDict):
    """A service location (bank, government office, mobile shop, etc.)."""
    id: str
    name: str
    address: str
    latitude: float
    longitude: float
    rating: float
    type: str  # "bank", "mobile_shop", "government", "hospital", etc.
    description: Optional[str]

class Property(TypedDict):
    """A property listing."""
    id: str
    name: str
    address: str
    latitude: float
    longitude: float
    bedrooms: int
    rent: int
    furnished: bool
    commute_time: Optional[str]
    description: Optional[str]

class SettlementTask(TypedDict):
    """A settlement task."""
    id: str
    title: str
    description: str
    day_range: str  # e.g., "Day 1-3", "Day 3-7"
    priority: Literal["high", "medium", "low"]
    location: Optional[ServiceLocation]
    documents_needed: List[str]
    estimated_duration: str  # e.g., "1-2 hours"
    status: Literal["pending", "in_progress", "completed"]
    dependencies: List[str]  # IDs of tasks that must be completed first

class CustomerInfo(TypedDict):
    """Customer information."""
    name: Optional[str]
    arrival_date: Optional[str]
    office_address: Optional[str]
    office_coordinates: Optional[tuple]  # (lat, lng)
    housing_budget: Optional[int]
    preferred_areas: List[str]
    bedrooms: Optional[int]
    family_size: Optional[int]
    has_children: bool
    needs_car: bool
    temporary_accommodation_days: Optional[int]

class SettlementPlan(TypedDict):
    """The complete settlement plan."""
    id: str
    customer_name: str
    center_latitude: float
    center_longitude: float
    zoom: int
    tasks: List[SettlementTask]
    properties: List[Property]
    service_locations: List[ServiceLocation]

class SearchProgress(TypedDict):
    """The progress of a search."""
    query: str
    results: list[str]
    done: bool

class PlanningProgress(TypedDict):
    """The progress of planning."""
    plan: SettlementPlan
    done: bool

class AgentState(MessagesState):
    """The state of the immigration settlement agent."""
    customer_info: CustomerInfo
    settlement_plan: Optional[SettlementPlan]
    selected_task_id: Optional[str]
    search_progress: List[SearchProgress]
    planning_progress: List[PlanningProgress]
