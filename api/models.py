from typing import Optional
from pydantic import BaseModel, Field


class ZoneCreate(BaseModel):
    name: str
    port: int = Field(..., ge=1, le=16)
    duration: int = 15
    icon: str = "mdi-water"
    color: str = "primary"


class ZoneUpdate(BaseModel):
    name: Optional[str] = None
    port: Optional[int] = Field(default=None, ge=1, le=16)
    duration: Optional[int] = None
    icon: Optional[str] = None
    color: Optional[str] = None


class Zone(BaseModel):
    id: str
    name: str
    port: int
    duration: int
    icon: str
    color: str


class ScheduleCreate(BaseModel):
    name: str = Field(..., min_length=1)
    days: list[str] = Field(..., min_length=1)
    startTimes: list[str] = Field(..., min_length=1)
    zoneIds: list[str] = Field(..., min_length=1)
    enabled: bool = True


class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    days: Optional[list[str]] = None
    startTimes: Optional[list[str]] = None
    zoneIds: Optional[list[str]] = None
    enabled: Optional[bool] = None


class Schedule(BaseModel):
    id: str
    name: str
    days: list[str]
    startTimes: list[str]
    zoneIds: list[str]
    enabled: bool


class RunningZone(BaseModel):
    zone_id: str
    zone_name: str
    duration_sec: int
    elapsed_sec: int
    time_remaining_sec: int
    schedule_id: Optional[str]


class ActiveSchedule(BaseModel):
    schedule_id: str
    schedule_name: str
    zone_index: int
    total_zones: int


class SystemStatus(BaseModel):
    any_running: bool
    running_zone: Optional[RunningZone]
    active_schedule: Optional[ActiveSchedule]


class HistoryEvent(BaseModel):
    id: str
    timestamp: str
    type: str
    message: str
    details: dict


class LocationData(BaseModel):
    city: str = ''
    lat: Optional[float] = None
    lon: Optional[float] = None


class AppSettings(BaseModel):
    name: str = ''
    location: LocationData = LocationData()


class AppSettingsUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[LocationData] = None


class WeatherData(BaseModel):
    temperature: float          # °F, current
    weather_code: int
    condition: str              # human-readable WMO label
    icon: str                   # mdi icon name
    precipitation_today: float  # inches fallen today
    precip_probability: int     # % max chance of rain today
    rain_likely: bool           # True when precip_probability >= 50 or precipitation_today > 0.1
    fetched_at: str             # ISO UTC timestamp of last fetch
