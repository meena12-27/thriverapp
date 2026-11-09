/// One floor's outlook from `GET /parking/forecast`.
///
/// The backend computes this by extrapolating the last ~30 minutes of slot
/// activity (it is not a trained model), so [trend] is "unknown" when there
/// is not enough recent activity to say anything.
class FloorForecast {
  final int floor;
  final int totalSlots;
  final int takenNow;
  final double occupancyNow;
  final double predicted15m;
  final double predicted30m;
  final int? minutesToFull;
  final String trend; // filling | steady | emptying | unknown
  final String confidence; // low | medium | high
  final int eventsUsed;

  FloorForecast({
    required this.floor,
    required this.totalSlots,
    required this.takenNow,
    required this.occupancyNow,
    required this.predicted15m,
    required this.predicted30m,
    required this.minutesToFull,
    required this.trend,
    required this.confidence,
    required this.eventsUsed,
  });

  bool get isFull => minutesToFull == 0;
  bool get hasTrend => trend != "unknown";

  factory FloorForecast.fromJson(Map<String, dynamic> json) {
    return FloorForecast(
      floor: json["floor"],
      totalSlots: json["total_slots"],
      takenNow: json["taken_now"],
      occupancyNow: (json["occupancy_now"] as num).toDouble(),
      predicted15m: (json["predicted_15m"] as num).toDouble(),
      predicted30m: (json["predicted_30m"] as num).toDouble(),
      minutesToFull: json["minutes_to_full"],
      trend: json["trend"],
      confidence: json["confidence"],
      eventsUsed: json["events_used"],
    );
  }
}
