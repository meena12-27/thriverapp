/// A single parking slot inside a mall.
///
/// The backend exposes two slightly different shapes for a slot:
///   - `/parking/available` and `/parking/recommend` use `slot_number`,
///     `x_coordinate`, `y_coordinate`.
///   - `/parking/map` uses shorter keys: `slot`, `x`, `y`.
/// [fromJson] accepts either shape so the app doesn't care which endpoint
/// the data came from.
class ParkingSlot {
  final int id;
  final int mallId;
  final String slotNumber;
  final int floor;
  final String status;
  final String zone;
  final int xCoordinate;
  final int yCoordinate;
  final bool isAccessible;
  final bool isEvCharging;

  ParkingSlot({
    required this.id,
    required this.mallId,
    required this.slotNumber,
    required this.floor,
    required this.status,
    required this.zone,
    required this.xCoordinate,
    required this.yCoordinate,
    this.isAccessible = false,
    this.isEvCharging = false,
  });

  bool get isAvailable => status == "available";

  factory ParkingSlot.fromJson(Map<String, dynamic> json) {
    return ParkingSlot(
      id: json["id"] ?? 0,
      mallId: json["mall_id"] ?? 0,
      slotNumber: json["slot_number"] ?? json["slot"],
      floor: json["floor"] ?? 0,
      status: json["status"] ?? "unknown",
      zone: json["zone"] ?? "",
      xCoordinate: json["x_coordinate"] ?? json["x"] ?? 0,
      yCoordinate: json["y_coordinate"] ?? json["y"] ?? 0,
      isAccessible: json["is_accessible"] ?? false,
      isEvCharging: json["is_ev_charging"] ?? false,
    );
  }
}
