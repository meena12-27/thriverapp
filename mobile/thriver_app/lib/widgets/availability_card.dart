import 'package:flutter/material.dart';

import '../models/parking_slot.dart';

/// Stat row: how many slots are available, total slots, and a simple
/// "traffic" indicator derived from availability count.
class ParkingOverviewCard extends StatelessWidget {
  final List<ParkingSlot> availability;
  final List<ParkingSlot> parkingMap;

  const ParkingOverviewCard({
    super.key,
    required this.availability,
    required this.parkingMap,
  });

  @override
  Widget build(BuildContext context) {
    final bool lowTraffic = availability.length > 5;

    return Card(
      elevation: 6,
      color: Colors.blue.shade50,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              "📊 Parking Overview",
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 15),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _StatColumn(
                  icon: Icons.local_parking,
                  iconColor: Colors.green,
                  value: "${availability.length}",
                  label: "Available",
                ),
                _StatColumn(
                  icon: Icons.directions_car,
                  iconColor: Colors.blue,
                  value: "${parkingMap.length}",
                  label: "Total Slots",
                ),
                _StatColumn(
                  icon: Icons.traffic,
                  iconColor: lowTraffic ? Colors.green : Colors.orange,
                  value: lowTraffic ? "Low" : "Busy",
                  label: "Traffic",
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _StatColumn extends StatelessWidget {
  final IconData icon;
  final Color iconColor;
  final String value;
  final String label;

  const _StatColumn({
    required this.icon,
    required this.iconColor,
    required this.value,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Icon(icon, color: iconColor, size: 35),
        const SizedBox(height: 5),
        Text(
          value,
          style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
        ),
        Text(label),
      ],
    );
  }
}

/// Small "live" badge showing current available-slot count, refreshed
/// automatically by the parent screen's polling timer.
class LiveStatusCard extends StatelessWidget {
  final List<ParkingSlot> availability;

  const LiveStatusCard({super.key, required this.availability});

  @override
  Widget build(BuildContext context) {
    final bool hasAvailability = availability.isNotEmpty;

    return Card(
      elevation: 4,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 12,
                  height: 12,
                  decoration: BoxDecoration(
                    color: hasAvailability ? Colors.green : Colors.red,
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 8),
                const Text(
                  "LIVE STATUS",
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: Colors.grey,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                const Icon(Icons.local_parking, color: Colors.blue, size: 35),
                const SizedBox(width: 15),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      "Available Parking",
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      hasAvailability
                          ? "🟢 ${availability.length} slots ready"
                          : "🔴 No slots available",
                      style: const TextStyle(fontSize: 16),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              "Updated automatically every 10 seconds",
              style: TextStyle(color: Colors.grey.shade600, fontSize: 13),
            ),
          ],
        ),
      ),
    );
  }
}
