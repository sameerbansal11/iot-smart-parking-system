#!/usr/bin/env python3
"""
iot-smart-parking-system
IoT Smart Parking System Simulation with real-time slot monitoring,
vehicle entry/exit, revenue tracking, and sensor simulation.

Author: Sameer Bansal
Reg No: RA2311032010061
College: SRM Institute of Science and Technology
Branch: B.Tech CSE (IoT) | Batch: 2023-2027
"""

import random
import time
import datetime
import os
import json
import threading

# ── Configuration ─────────────────────────────────────────
CONFIG = {
    "total_floors": 3,
    "slots_per_floor": 10,
    "rates": {
        "Car": 20,  # ₹ per hour
        "Bike": 10,
        "EV": 15,
        "Truck": 40,
        "Handicapped": 0,
    },
    "ev_slots": [1, 2],  # Slot numbers reserved for EV
    "handicapped_slots": [3],  # Slot numbers reserved for handicapped
    "sensor_update_interval": 2,  # seconds
}

VEHICLE_TYPES = ["Car", "Bike", "EV", "Truck", "Handicapped"]
FLOOR_NAMES = {1: "Ground Floor", 2: "First Floor", 3: "Second Floor"}


# ── Data Structures ───────────────────────────────────────
class ParkingSlot:
    def __init__(self, slot_id, floor, slot_number):
        self.slot_id = slot_id
        self.floor = floor
        self.slot_number = slot_number
        self.is_occupied = False
        self.vehicle = None
        self.entry_time = None
        self.slot_type = self._determine_type()

    def _determine_type(self):
        if self.slot_number in CONFIG["ev_slots"]:
            return "EV"
        elif self.slot_number in CONFIG["handicapped_slots"]:
            return "Handicapped"
        return "General"

    def occupy(self, vehicle):
        self.is_occupied = True
        self.vehicle = vehicle
        self.entry_time = datetime.datetime.now()

    def vacate(self):
        if self.entry_time is None:
            duration = 0
        else:
            duration = (datetime.datetime.now() - self.entry_time).seconds / 3600
        vehicle = self.vehicle
        self.is_occupied = False
        self.vehicle = None
        self.entry_time = None
        return vehicle, duration

    def display(self):
        if self.is_occupied and self.entry_time is not None and self.vehicle is not None:
            elapsed = (datetime.datetime.now() - self.entry_time).seconds // 60
            return f"[🚗 {self.vehicle['plate']:<8} {elapsed:>3}m]"
        else:
            icons = {"EV": "⚡", "Handicapped": "♿", "General": "🟢"}
            return f"[{icons[self.slot_type]} {'FREE':<14}]"


class ParkingSystem:
    def __init__(self):
        self.floors = {}
        self.transaction_log = []
        self.revenue = 0.0
        self.total_vehicles_served = 0
        self.active_vehicles = {}
        self._initialize_parking()

    def _initialize_parking(self):
        slot_id = 1
        for floor in range(1, CONFIG["total_floors"] + 1):
            self.floors[floor] = []
            for slot_num in range(1, CONFIG["slots_per_floor"] + 1):
                slot = ParkingSlot(slot_id, floor, slot_num)
                self.floors[floor].append(slot)
                slot_id += 1

    def get_available_slots(self, vehicle_type="Car"):
        available = []
        for floor in self.floors:
            for slot in self.floors[floor]:
                if not slot.is_occupied:
                    if vehicle_type == "EV" and slot.slot_type != "EV":
                        continue
                    if (
                        vehicle_type == "Handicapped"
                        and slot.slot_type != "Handicapped"
                    ):
                        continue
                    available.append(slot)
        return available

    def get_total_available(self):
        return sum(
            1
            for floor in self.floors.values()
            for slot in floor
            if not slot.is_occupied
        )

    def get_total_occupied(self):
        return sum(
            1 for floor in self.floors.values() for slot in floor if slot.is_occupied
        )

    def park_vehicle(self, plate, vehicle_type):
        plate = plate.upper().strip()
        if plate in self.active_vehicles:
            return False, f"⚠️  Vehicle {plate} is already parked!"

        available = self.get_available_slots(vehicle_type)
        if not available:
            return False, f"❌ No available slots for {vehicle_type}!"

        # Pick nearest slot (lowest floor, lowest slot number)
        slot = available[0]
        vehicle = {
            "plate": plate,
            "type": vehicle_type,
            "slot_id": slot.slot_id,
            "floor": slot.floor,
            "slot_number": slot.slot_number,
        }
        slot.occupy(vehicle)
        self.active_vehicles[plate] = slot

        return True, (
            f"✅ Vehicle {plate} ({vehicle_type}) parked at "
            f"{FLOOR_NAMES[slot.floor]}, Slot {slot.slot_number} "
            f"(ID: {slot.slot_id})"
        )

    def exit_vehicle(self, plate):
        plate = plate.upper().strip()
        if plate not in self.active_vehicles:
            return False, f"❌ Vehicle {plate} not found in parking!"

        slot = self.active_vehicles[plate]
        vehicle, duration = slot.vacate()

        rate = CONFIG["rates"].get(vehicle["type"], 20)
        charge = round(max(rate, rate * duration), 2)  # Minimum 1 hour charge
        self.revenue += charge
        self.total_vehicles_served += 1

        log_entry = {
            "plate": plate,
            "type": vehicle["type"],
            "floor": vehicle["floor"],
            "slot": vehicle["slot_number"],
            "duration_hours": round(duration, 3),
            "charge": charge,
            "exit_time": datetime.datetime.now().strftime("%H:%M:%S"),
        }
        self.transaction_log.append(log_entry)
        del self.active_vehicles[plate]

        return True, (
            f"✅ Vehicle {plate} exited | "
            f"Duration: {duration * 60:.0f} min | "
            f"Charge: ₹{charge:.2f}"
        )

    def get_floor_status(self, floor):
        slots = self.floors[floor]
        occupied = sum(1 for s in slots if s.is_occupied)
        return occupied, len(slots) - occupied, len(slots)


# ── Display Functions ─────────────────────────────────────
def clear():
    os.system("cls" if os.name == "nt" else "clear")


def display_banner():
    print("=" * 60)
    print("     🅿️  IOT SMART PARKING SYSTEM SIMULATION")
    print("     Author : Sameer Bansal | RA2311032010061")
    print("     College: SRMIST Kattankulathur")
    print("=" * 60)


def display_parking_map(ps):
    print(
        f"\n📊 LIVE PARKING MAP  |  "
        f"🟢 Available: {ps.get_total_available()}  |  "
        f"🔴 Occupied: {ps.get_total_occupied()}  |  "
        f"💰 Revenue: ₹{ps.revenue:.2f}"
    )
    print("=" * 60)

    for floor in ps.floors:
        occ, avail, total = ps.get_floor_status(floor)
        bar_filled = int((occ / total) * 20)
        bar = "█" * bar_filled + "░" * (20 - bar_filled)
        occupancy_pct = (occ / total) * 100
        print(
            f"\n  🏢 {FLOOR_NAMES[floor]}  [{bar}] {occupancy_pct:.0f}%  "
            f"({occ} occupied / {avail} free)"
        )
        print("  " + "-" * 56)

        slots = ps.floors[floor]
        for i in range(0, len(slots), 2):
            slot1 = slots[i].display()
            slot2 = slots[i + 1].display() if i + 1 < len(slots) else ""
            print(
                f"    Slot {slots[i].slot_number:>2}: {slot1}   "
                f"Slot {slots[i+1].slot_number:>2}: {slot2}"
                if slot2
                else f"    Slot {slots[i].slot_number:>2}: {slot1}"
            )

    print(
        "\n  ⚡ = EV Charging Slot  |  ♿ = Handicapped  |  🟢 = Free  |  🚗 = Occupied"
    )


def display_stats(ps):
    print("\n📈 PARKING STATISTICS")
    print("=" * 60)
    print(f"  💰 Total Revenue        : ₹{ps.revenue:.2f}")
    print(f"  🚗 Vehicles Served Today: {ps.total_vehicles_served}")
    print(f"  🅿️  Currently Parked     : {ps.get_total_occupied()}")
    print(f"  🟢 Available Slots       : {ps.get_total_available()}")
    print(
        f"  📊 Occupancy Rate        : "
        f"{(ps.get_total_occupied() / (CONFIG['total_floors'] * CONFIG['slots_per_floor'])) * 100:.1f}%"
    )

    if ps.transaction_log:
        print(f"\n  📋 RECENT TRANSACTIONS (Last 5)")
        print("  " + "-" * 55)
        print(f"  {'Plate':<10} {'Type':<12} {'Duration':<12} {'Charge':<10} {'Exit'}")
        print("  " + "-" * 55)
        for t in ps.transaction_log[-5:]:
            print(
                f"  {t['plate']:<10} {t['type']:<12} "
                f"{t['duration_hours']*60:>6.0f} min   "
                f"₹{t['charge']:<8.2f} {t['exit_time']}"
            )

    print(f"\n  💵 RATE CARD")
    print("  " + "-" * 30)
    for vtype, rate in CONFIG["rates"].items():
        free = " (FREE)" if rate == 0 else f" ₹{rate}/hr"
        print(f"  {vtype:<15} {free}")


def display_menu():
    print("""
  OPTIONS:
  [1] Park a vehicle
  [2] Exit a vehicle
  [3] View parking map
  [4] View statistics
  [5] Run auto simulation
  [6] Search vehicle
  [q] Quit
""")


def search_vehicle(ps):
    plate = input("\n  Enter plate number: ").strip().upper()
    if plate in ps.active_vehicles:
        slot = ps.active_vehicles[plate]
        elapsed = (datetime.datetime.now() - slot.entry_time).seconds // 60
        rate = CONFIG["rates"].get(slot.vehicle["type"], 20)
        est_charge = round(max(rate, rate * (elapsed / 60)), 2)
        print(f"\n  ✅ Vehicle Found!")
        print(f"  Plate    : {plate}")
        print(f"  Type     : {slot.vehicle['type']}")
        print(f"  Location : {FLOOR_NAMES[slot.floor]}, Slot {slot.slot_number}")
        print(f"  Parked   : {elapsed} minutes ago")
        print(f"  Est. Bill: ₹{est_charge:.2f}")
    else:
        print(f"  ❌ Vehicle {plate} not found in parking.")


def auto_simulation(ps):
    """Simulate random vehicle entries and exits"""
    print("\n🤖 AUTO SIMULATION RUNNING (20 events)")
    print("   Press Ctrl+C to stop early\n")

    plates = [
        f"TN{random.randint(10,99):02d}{chr(random.randint(65,90))}{chr(random.randint(65,90))}{random.randint(1000,9999)}"
        for _ in range(15)
    ]

    events = 0
    try:
        # Park 10 vehicles
        for i in range(10):
            plate = plates[i]
            vtype = random.choice(VEHICLE_TYPES)
            success, msg = ps.park_vehicle(plate, vtype)
            print(f"  [{events+1:>2}] {msg}")
            events += 1
            time.sleep(0.3)

        time.sleep(1)

        # Exit 5 vehicles
        parked = list(ps.active_vehicles.keys())[:5]
        for plate in parked:
            success, msg = ps.exit_vehicle(plate)
            print(f"  [{events+1:>2}] {msg}")
            events += 1
            time.sleep(0.3)

        # Park 5 more
        for i in range(10, 15):
            plate = plates[i]
            vtype = random.choice(VEHICLE_TYPES)
            success, msg = ps.park_vehicle(plate, vtype)
            print(f"  [{events+1:>2}] {msg}")
            events += 1
            time.sleep(0.3)

    except KeyboardInterrupt:
        print("\n  ⏹️  Simulation stopped.")

    print(f"\n  ✅ Simulation complete! {events} events processed.")


# ── Save Log ──────────────────────────────────────────────
def save_log(ps):
    if not ps.transaction_log:
        return
    os.makedirs("output", exist_ok=True)
    filename = (
        f"output/parking_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(filename, "w") as f:
        json.dump(
            {
                "session_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_revenue": ps.revenue,
                "vehicles_served": ps.total_vehicles_served,
                "transactions": ps.transaction_log,
            },
            f,
            indent=2,
        )
    print(f"\n  💾 Session log saved: {filename}")


# ── Main ──────────────────────────────────────────────────
def main():
    clear()
    display_banner()
    ps = ParkingSystem()

    print(f"\n  ✅ Parking system initialized!")
    print(f"  🏢 Floors  : {CONFIG['total_floors']}")
    print(f"  🅿️  Slots   : {CONFIG['total_floors'] * CONFIG['slots_per_floor']} total")
    print(f"  ⚡ EV Slots : {len(CONFIG['ev_slots'])} per floor")
    print(f"  ♿ HC Slots : {len(CONFIG['handicapped_slots'])} per floor")

    display_menu()

    while True:
        try:
            choice = input("\n  Enter option: ").strip().lower()

            if choice == "q":
                save_log(ps)
                print("\n  👋 Thank you for using Smart Parking System!")
                print(f"  💰 Final Revenue: ₹{ps.revenue:.2f}")
                break

            elif choice == "1":
                print("\n  🚗 PARK VEHICLE")
                print("  " + "-" * 40)
                plate = input("  Enter plate number (e.g. TN09AB1234): ").strip()
                print(f"  Vehicle types: {', '.join(VEHICLE_TYPES)}")
                vtype = input("  Enter vehicle type: ").strip().title()
                if vtype not in VEHICLE_TYPES:
                    print(
                        f"  ⚠️  Invalid type. Choose from: {', '.join(VEHICLE_TYPES)}"
                    )
                else:
                    success, msg = ps.park_vehicle(plate, vtype)
                    print(f"\n  {msg}")

            elif choice == "2":
                print("\n  🚪 EXIT VEHICLE")
                print("  " + "-" * 40)
                plate = input("  Enter plate number: ").strip()
                success, msg = ps.exit_vehicle(plate)
                print(f"\n  {msg}")

            elif choice == "3":
                display_parking_map(ps)

            elif choice == "4":
                display_stats(ps)

            elif choice == "5":
                auto_simulation(ps)
                display_parking_map(ps)

            elif choice == "6":
                search_vehicle(ps)

            elif choice == "menu":
                display_menu()

            else:
                print("  ⚠️  Invalid option. Type 'menu' to see options.")

        except KeyboardInterrupt:
            print("\n\n  👋 Goodbye!")
            save_log(ps)
            break


if __name__ == "__main__":
    main()
