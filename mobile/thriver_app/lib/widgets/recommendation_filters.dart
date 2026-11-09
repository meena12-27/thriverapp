import 'package:flutter/material.dart';

/// A point the driver starts from. The backend scores slots by distance from
/// this position, so picking a different entrance can change the winner.
class Entrance {
  final String name;
  final int x;
  final int y;

  const Entrance(this.name, this.x, this.y);

  // Coordinates share the slot coordinate space (see seed_data.py): slots
  // sit at roughly x 6-33, y 38-51, so the east entrance (x=60) is nearest
  // the right-hand columns while the main entrance (x=0) favours the left.
  static const List<Entrance> all = [
    Entrance("Main entrance", 0, 0),
    Entrance("East entrance", 60, 0),
  ];
}

/// "Find my spot" controls: which entrance, which floor, and whether the
/// slot must be accessible / have EV charging. Purely presentational; the
/// parent screen owns the state and re-requests the recommendation.
class RecommendationFilters extends StatelessWidget {
  final Entrance entrance;
  final ValueChanged<Entrance> onEntranceChanged;

  final List<int> floors;
  final int? preferredFloor;
  final ValueChanged<int?> onPreferredFloorChanged;

  final bool requiresAccessible;
  final ValueChanged<bool> onAccessibleChanged;

  final bool requiresEvCharging;
  final ValueChanged<bool> onEvChargingChanged;

  const RecommendationFilters({
    super.key,
    required this.entrance,
    required this.onEntranceChanged,
    required this.floors,
    required this.preferredFloor,
    required this.onPreferredFloorChanged,
    required this.requiresAccessible,
    required this.onAccessibleChanged,
    required this.requiresEvCharging,
    required this.onEvChargingChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              "🎯 Find my spot",
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 16,
              runSpacing: 8,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Text("Entering from "),
                    DropdownButton<Entrance>(
                      value: entrance,
                      items: Entrance.all
                          .map((e) => DropdownMenuItem<Entrance>(
                                value: e,
                                child: Text(e.name),
                              ))
                          .toList(),
                      onChanged: (value) {
                        if (value != null) onEntranceChanged(value);
                      },
                    ),
                  ],
                ),
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Text("Preferred floor "),
                    DropdownButton<int?>(
                      value: preferredFloor,
                      items: [
                        const DropdownMenuItem<int?>(
                          value: null,
                          child: Text("Any"),
                        ),
                        ...floors.map((f) => DropdownMenuItem<int?>(
                              value: f,
                              child: Text("Floor $f"),
                            )),
                      ],
                      onChanged: onPreferredFloorChanged,
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              children: [
                FilterChip(
                  label: const Text("♿ Accessible"),
                  selected: requiresAccessible,
                  onSelected: onAccessibleChanged,
                ),
                FilterChip(
                  label: const Text("⚡ EV charging"),
                  selected: requiresEvCharging,
                  onSelected: onEvChargingChanged,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

/// Shown instead of the recommendation cards when the backend found no free
/// slot that satisfies the current filters.
class NoMatchCard extends StatelessWidget {
  final VoidCallback onClearFilters;

  const NoMatchCard({super.key, required this.onClearFilters});

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 3,
      color: Colors.orange.shade50,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              "No matching slot right now",
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 6),
            const Text(
              "Every free slot is ruled out by your filters (or the lot is "
              "full). Try removing a filter.",
            ),
            const SizedBox(height: 10),
            TextButton(
              onPressed: onClearFilters,
              child: const Text("Clear filters"),
            ),
          ],
        ),
      ),
    );
  }
}
