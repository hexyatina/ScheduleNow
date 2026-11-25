from fastapi import APIRouter, HTTPException, Depends
from schemas import CreateLocation, UpdateLocation
from database import Location, User, Event, db
from auth import require_manager, get_current_user

router = APIRouter(prefix="/locations", tags=["locations"])

@router.post("/")
def create_location(
    data: CreateLocation,
    current_user: User = Depends(require_manager)
):
    location_exists = Location.select().where(
        Location.office_room == data.office_room
    ).exists()

    if location_exists:
        raise HTTPException(
            status_code=400,
            detail="Location with this office room already exists"
        )
    if data.max_occupancy <= 0:
        raise HTTPException(
            status_code=400,
            detail="Max occupancy must be greater than zero"
        )

    location = Location.create(
        office_room=data.office_room,
        max_occupancy=data.max_occupancy
    )

    return {
        "message": "Location created successfully",
        "location_id": location.id
    }

@router.get("/")
def get_locations(current_user: User = Depends(get_current_user)):
    locations = Location.select().order_by(Location.id.asc())
    return [
        {
            "id": loc.id,
            "office_room": loc.office_room,
            "max_occupancy": loc.max_occupancy
        }
        for loc in locations
    ]

@router.patch("/{location_id}")
def update_location(
    location_id: int,
    data: UpdateLocation,
    current_user: User = Depends(require_manager)
):
    location = Location.get_or_none(Location.id == location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    if data.max_occupancy is not None and data.max_occupancy <= 0:
        raise HTTPException(
            status_code=400,
            detail="Max occupancy must be greater than zero"
        )

    if data.office_room is not None and data.office_room != location.office_room:
        dup_exists = Location.select().where(
            (Location.office_room == data.office_room) &
            (Location.id != location_id)
        ).exists()
        if dup_exists:
            raise HTTPException(
                status_code=400,
                detail="Location with this office room already exists"
            )
        location.office_room = data.office_room

    if data.max_occupancy is not None:
        location.max_occupancy = data.max_occupancy

    location.save()
    return {
        "message": "Location updated successfully",
        "location": {
            "id": location.id,
            "office_room": location.office_room,
            "max_occupancy": location.max_occupancy
        }
    }

@router.delete("/{location_id}")
def delete_location(
    location_id: int,
    current_user: User = Depends(require_manager)
):
    location = Location.get_or_none(Location.id == location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    with db.atomic():
        Event.update(location=None).where(Event.location == location_id).execute()
        location.delete_instance()

    return {"message": "Location deleted successfully"}