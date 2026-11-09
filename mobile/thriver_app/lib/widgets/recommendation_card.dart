import 'package:flutter/material.dart';

import '../models/recommendation.dart';

/// Headline card: which mall, how many slots are free, and the
/// recommended slot's basic details.
class RecommendationSummaryCard extends StatelessWidget {
  final Recommendation recommendation;
  final int availableCount;

  const RecommendationSummaryCard({
    super.key,
    required this.recommendation,
    required this.availableCount,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 6,
      color: Colors.blue.shade50,
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              "🏬 ${recommendation.mall}",
              style: const TextStyle(fontSize: 26, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 15),
            Row(
              children: [
                const Icon(Icons.local_parking, color: Colors.green),
                const SizedBox(width: 8),
                Text(
                  availableCount > 0
                      ? "$availableCount parking slots available"
                      : "No parking available",
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const Divider(height: 30),
            const Text(
              "⭐ Recommended Spot",
              style: TextStyle(fontSize: 16, color: Colors.grey),
            ),
            const SizedBox(height: 8),
            Text(
              recommendation.parking.slotNumber,
              style: const TextStyle(
                fontSize: 42,
                fontWeight: FontWeight.bold,
                color: Colors.blue,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              "Floor ${recommendation.parking.floor} • ${recommendation.parking.zone} Zone",
              style: const TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 8),
            Text(
              "📍 ${recommendation.distance} m away",
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
          ],
        ),
      ),
    );
  }
}

/// Larger "hero" card highlighting the recommended slot. The "Why this
/// spot?" list comes straight from the backend scoring engine
/// (`Recommendation.reasons`), so it always matches what was actually
/// computed. (Class keeps its old name to avoid touching every import.)
class AiRecommendationCard extends StatelessWidget {
  final Recommendation recommendation;

  const AiRecommendationCard({super.key, required this.recommendation});

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 8,
      color: Colors.blue.shade50,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            const Text(
              "⭐ RECOMMENDED PARKING",
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 15),
            Container(
              padding: const EdgeInsets.all(15),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(15),
              ),
              child: Column(
                children: [
                  Text(
                    recommendation.parking.slotNumber,
                    style: const TextStyle(
                      fontSize: 50,
                      fontWeight: FontWeight.bold,
                      color: Colors.blue,
                    ),
                  ),
                  const SizedBox(height: 10),
                  Text(
                    "🏢 Floor ${recommendation.parking.floor}",
                    style: const TextStyle(fontSize: 18),
                  ),
                  Text(
                    "📍 ${recommendation.parking.zone} Zone",
                    style: const TextStyle(fontSize: 18),
                  ),
                  const SizedBox(height: 10),
                  Text(
                    "🚶 ${recommendation.distance} m away",
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
            const Align(
              alignment: Alignment.centerLeft,
              child: Text(
                "Why this spot?",
                style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
              ),
            ),
            const SizedBox(height: 8),
            Align(
              alignment: Alignment.centerLeft,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: recommendation.reasons
                    .map<Widget>((reason) => Text("✓ $reason"))
                    .toList(),
              ),
            ),
            if (recommendation.parking.isAccessible ||
                recommendation.parking.isEvCharging) ...[
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                children: [
                  if (recommendation.parking.isAccessible)
                    const Chip(label: Text("♿ Accessible")),
                  if (recommendation.parking.isEvCharging)
                    const Chip(label: Text("⚡ EV charging")),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}
