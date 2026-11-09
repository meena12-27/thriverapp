import 'package:flutter/material.dart';

import '../models/parking_slot.dart';
import '../models/recommendation.dart';

/// Header controls above the map: "available only" toggle and floor picker.
class ParkingMapControls extends StatelessWidget {
  final bool showAvailableOnly;
  final ValueChanged<bool> onShowAvailableOnlyChanged;
  final int selectedFloor;
  final List<int> floors;
  final ValueChanged<int> onFloorChanged;

  const ParkingMapControls({
    super.key,
    required this.showAvailableOnly,
    required this.onShowAvailableOnlyChanged,
    required this.selectedFloor,
    required this.floors,
    required this.onFloorChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              "Available Only",
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            Switch(
              value: showAvailableOnly,
              onChanged: onShowAvailableOnlyChanged,
            ),
          ],
        ),
        DropdownButton<int>(
          value: selectedFloor,
          items: floors.map((floor) {
            return DropdownMenuItem<int>(
              value: floor,
              child: Text("Floor $floor"),
            );
          }).toList(),
          onChanged: (value) {
            if (value != null) onFloorChanged(value);
          },
        ),
      ],
    );
  }
}

/// Legend explaining the slot colors used in [ParkingMapGrid].
class ParkingMapLegend extends StatelessWidget {
  const ParkingMapLegend({super.key});

  @override
  Widget build(BuildContext context) {
    return const Wrap(
      spacing: 20,
      children: [
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.square, color: Colors.green),
            SizedBox(width: 5),
            Text("Available"),
          ],
        ),
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.square, color: Colors.orange),
            SizedBox(width: 5),
            Text("Reserved"),
          ],
        ),
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.square, color: Colors.red),
            SizedBox(width: 5),
            Text("Occupied"),
          ],
        ),
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.square, color: Colors.blue),
            SizedBox(width: 5),
            Text("Recommended"),
          ],
        ),
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text("♿"),
            SizedBox(width: 5),
            Text("Accessible"),
          ],
        ),
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text("⚡"),
            SizedBox(width: 5),
            Text("EV charging"),
          ],
        ),
      ],
    );
  }
}

/// Interactive floor-plan grid. Tapping a slot selects it (see
/// [SelectedSlotCard]); the recommended slot is highlighted in blue.
class ParkingMapGrid extends StatelessWidget {
  final List<ParkingSlot> parkingMap;
  final int selectedFloor;
  final bool showAvailableOnly;
  final Recommendation? recommendation;
  final ParkingSlot? selectedSlot;
  final ValueChanged<ParkingSlot> onSlotTapped;

  const ParkingMapGrid({
    super.key,
    required this.parkingMap,
    required this.selectedFloor,
    required this.showAvailableOnly,
    required this.recommendation,
    required this.selectedSlot,
    required this.onSlotTapped,
  });

  @override
  Widget build(BuildContext context) {
    final slotsOnFloor = parkingMap.where(
      (slot) =>
          slot.floor == selectedFloor &&
          (!showAvailableOnly || slot.status == "available"),
    );

    return Card(
      elevation: 4,
      child: SizedBox(
        height: 350,
        child: Container(
          decoration: BoxDecoration(
            color: Colors.grey.shade100,
            borderRadius: BorderRadius.circular(10),
          ),
          child: Stack(
            children: [
              Positioned(
                top: 10,
                left: 20,
                child: Text(
                  "🚪 Entrance",
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: Colors.grey.shade700,
                  ),
                ),
              ),
              Positioned(
                top: 160,
                left: 0,
                right: 0,
                child: Container(
                  height: 35,
                  color: Colors.grey.shade300,
                  alignment: Alignment.center,
                  child: const Text(
                    "Driving Lane",
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                ),
              ),
              if (recommendation != null)
                Positioned(
                  bottom: 10,
                  left: 20,
                  child: Text(
                    recommendation!.parking.zone,
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: Colors.grey,
                    ),
                  ),
                ),
              ...slotsOnFloor.map<Widget>((slot) => _SlotTile(
                    slot: slot,
                    isRecommended: recommendation != null &&
                        recommendation!.parking.slotNumber == slot.slotNumber,
                    isSelected: selectedSlot != null &&
                        selectedSlot!.slotNumber == slot.slotNumber,
                    onTap: () => onSlotTapped(slot),
                  )),
            ],
          ),
        ),
      ),
    );
  }
}

class _SlotTile extends StatelessWidget {
  final ParkingSlot slot;
  final bool isRecommended;
  final bool isSelected;
  final VoidCallback onTap;

  const _SlotTile({
    required this.slot,
    required this.isRecommended,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    Color color;
    switch (slot.status) {
      case "available":
        color = Colors.green;
        break;
      case "reserved":
        color = Colors.orange;
        break;
      default:
        color = Colors.red; // occupied
    }
    if (isRecommended) color = Colors.blue;

    return Positioned(
      left: (slot.xCoordinate * 8.0) - 20,
      top: (slot.yCoordinate * 6.0) - 20,
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          width: 60,
          height: 45,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(8),
            border: isSelected
                ? Border.all(color: Colors.yellow, width: 4)
                : isRecommended
                    ? Border.all(color: Colors.blueAccent, width: 3)
                    : null,
            boxShadow: isSelected
                ? [
                    BoxShadow(
                      color: Colors.yellow.withOpacity(0.6),
                      blurRadius: 12,
                      spreadRadius: 3,
                    ),
                  ]
                : isRecommended
                    ? [
                        BoxShadow(
                          color: Colors.blue.withOpacity(0.6),
                          blurRadius: 15,
                          spreadRadius: 4,
                        ),
                      ]
                    : null,
          ),
          child: Stack(
            alignment: Alignment.center,
            children: [
              Text(
                slot.slotNumber,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                ),
              ),
              if (isRecommended)
                const Positioned(
                  top: -10,
                  right: -5,
                  child: Text("⭐", style: TextStyle(fontSize: 18)),
                ),
              if (slot.isAccessible || slot.isEvCharging)
                Positioned(
                  bottom: 1,
                  left: 4,
                  child: Text(
                    "${slot.isAccessible ? '♿' : ''}${slot.isEvCharging ? '⚡' : ''}",
                    style: const TextStyle(fontSize: 11),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Detail card + reserve button shown once the user taps a slot on the map.
class SelectedSlotCard extends StatelessWidget {
  final ParkingSlot slot;
  final VoidCallback onReserve;

  const SelectedSlotCard({
    super.key,
    required this.slot,
    required this.onReserve,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 6,
      color: Colors.white,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              "🚗 Selected Parking Slot",
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 15),
            Center(
              child: Text(
                slot.slotNumber,
                style: const TextStyle(
                  fontSize: 45,
                  fontWeight: FontWeight.bold,
                  color: Colors.blue,
                ),
              ),
            ),
            const SizedBox(height: 10),
            Text(
              slot.isAvailable ? "🟢 Available" : "🔴 Occupied",
              style: TextStyle(
                fontSize: 17,
                color: slot.isAvailable ? Colors.green : Colors.red,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Text("🏢 Floor ${slot.floor}", style: const TextStyle(fontSize: 16)),
            Text("📍 Zone ${slot.zone}", style: const TextStyle(fontSize: 16)),
            const SizedBox(height: 15),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: slot.isAvailable ? onReserve : null,
                icon: const Icon(Icons.bookmark),
                label: const Text("Reserve Slot"),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
