import 'parking_slot.dart';

/// The result of `GET /parking/recommend`: which slot to take, how far it
/// is, why it was chosen, and the step-by-step navigation to get there.
class Recommendation {
  final String mall;
  final ParkingSlot parking;
  final double distance;
  final List<String> navigation;
  final List<String> reasons;
  final String message;

  Recommendation({
    required this.mall,
    required this.parking,
    required this.distance,
    required this.navigation,
    required this.reasons,
    required this.message,
  });

  factory Recommendation.fromJson(Map<String, dynamic> json) {
    return Recommendation(
      mall: json["mall"],
      parking: ParkingSlot.fromJson(json["parking"]),
      distance: (json["distance"] as num).toDouble(),
      navigation: List<String>.from(json["navigation"]),
      reasons: List<String>.from(json["reasons"] ?? const []),
      message: json["message"],
    );
  }
}
