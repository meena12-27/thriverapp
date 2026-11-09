/// An active/released/expired hold on a parking slot.
class Reservation {
  final int id;
  final int parkingSlotId;
  final String status;
  final int secondsRemaining;

  Reservation({
    required this.id,
    required this.parkingSlotId,
    required this.status,
    required this.secondsRemaining,
  });

  factory Reservation.fromJson(Map<String, dynamic> json) {
    return Reservation(
      id: json["id"],
      parkingSlotId: json["parking_slot_id"],
      status: json["status"],
      secondsRemaining: json["seconds_remaining"] ?? 0,
    );
  }
}
