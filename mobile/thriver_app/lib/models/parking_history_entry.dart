/// One past recommendation from GET /parking/history.
class ParkingHistoryEntry {
  final int id;
  final int mallId;
  final String slotNumber;
  final int floor;
  final String zone;
  final double distance;
  final DateTime createdAt;

  ParkingHistoryEntry({
    required this.id,
    required this.mallId,
    required this.slotNumber,
    required this.floor,
    required this.zone,
    required this.distance,
    required this.createdAt,
  });

  factory ParkingHistoryEntry.fromJson(Map<String, dynamic> json) {
    return ParkingHistoryEntry(
      id: json["id"],
      mallId: json["mall_id"],
      slotNumber: json["slot_number"],
      floor: json["floor"],
      zone: json["zone"],
      distance: (json["distance"] as num).toDouble(),
      createdAt: DateTime.parse(json["created_at"]),
    );
  }
}
