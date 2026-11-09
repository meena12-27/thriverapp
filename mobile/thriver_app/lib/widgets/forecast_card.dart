import 'package:flutter/material.dart';

import '../models/floor_forecast.dart';

/// Per-floor outlook for the next 15 / 30 minutes.
///
/// The numbers come from the backend extrapolating the last ~30 minutes of
/// slot activity. It is a trend, not a trained model, and says so on the
/// card. Floors without enough recent activity show that plainly instead of
/// a made-up prediction.
class ForecastCard extends StatelessWidget {
  final List<FloorForecast> forecast;

  const ForecastCard({super.key, required this.forecast});

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              "🔮 Next 30 minutes",
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 4),
            Text(
              "Trend from the last 30 min of activity (an estimate, not a guarantee)",
              style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
            ),
            const SizedBox(height: 14),
            ...forecast.map((f) => _FloorRow(forecast: f)),
          ],
        ),
      ),
    );
  }
}

class _FloorRow extends StatelessWidget {
  final FloorForecast forecast;

  const _FloorRow({required this.forecast});

  Color get _color {
    if (forecast.isFull) return Colors.red;
    switch (forecast.trend) {
      case "filling":
        final soon = forecast.minutesToFull;
        return (soon != null && soon <= 15) ? Colors.red : Colors.orange;
      case "unknown":
        return Colors.grey;
      default:
        return Colors.green; // steady or emptying
    }
  }

  String get _headline {
    if (forecast.isFull) return "Full now";
    switch (forecast.trend) {
      case "filling":
        final m = forecast.minutesToFull;
        return m != null ? "Filling, full in ~$m min" : "Filling";
      case "emptying":
        return "Emptying";
      case "steady":
        return "Steady";
      default:
        return "Not enough recent activity to predict";
    }
  }

  String _pct(double value) => "${value.toStringAsFixed(0)}%";

  @override
  Widget build(BuildContext context) {
    final color = _color;

    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                "Floor ${forecast.floor}",
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
              Flexible(
                child: Text(
                  _headline,
                  textAlign: TextAlign.end,
                  style: TextStyle(color: color, fontWeight: FontWeight.w600),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: LinearProgressIndicator(
              value: (forecast.occupancyNow / 100).clamp(0.0, 1.0).toDouble(),
              minHeight: 10,
              color: color,
              backgroundColor: Colors.grey.shade200,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            forecast.hasTrend
                ? "Now ${_pct(forecast.occupancyNow)} (${forecast.takenNow}/${forecast.totalSlots})"
                    "  →  15 min ${_pct(forecast.predicted15m)}"
                    "  →  30 min ${_pct(forecast.predicted30m)}"
                : "Now ${_pct(forecast.occupancyNow)} (${forecast.takenNow}/${forecast.totalSlots})",
            style: TextStyle(color: Colors.grey.shade700, fontSize: 13),
          ),
        ],
      ),
    );
  }
}
