from datetime import datetime
from pydantic import BaseModel, root_validator
from typing import List, Optional, Dict
from enum import Enum, IntEnum


class MessageCodeEnum(int, Enum):
    position_report = 0
    locate_response = 2
    free_text_message = 3
    declare_sos = 4
    confirm_sos = 6
    cancel_sos = 7
    reference_point = 8
    check_in = 9
    start_track = 10
    track_interval_changed = 11
    stop_track = 12
    puck_message_1 = 14
    puck_message_2 = 15
    puck_message_3 = 16
    map_share = 17
    mail_check = 20
    # Others exist (See garmin Outbound IPC docs)


class InreachEventAddress(BaseModel):
    address: str


class InreachEventPoint(BaseModel):
    latitude: float
    longitude: float
    altitude: int
    gpsFix: int
    course: int
    speed: int


low_battery_status_label = {0: "ok", 1: "low", 2: "not indicated"}


class InreachEventStatus(BaseModel):
    autonomous: int
    lowBattery: int
    intervalChange: int
    resetDetected: int

    low_battery_label: Optional[str]

    @root_validator
    def compute_low_battery_label(cls, values) -> Dict:
        values["low_battery_label"] = low_battery_status_label.get(
            values.get("lowBattery", -1), None
        )
        return values


class InreachEvent(BaseModel):
    imei: str
    messageCode: int
    freeText: Optional[str] = None
    timeStamp: datetime
    addresses: List[InreachEventAddress]
    point: InreachEventPoint
    status: InreachEventStatus

    integration_id: Optional[str]
    owner: Optional[str]


class InreachEventPayload(BaseModel):

    Version: str
    Events: List[InreachEvent]

    class Config:
        title = "InReachEventPayload"
