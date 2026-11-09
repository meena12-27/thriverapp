import 'dart:convert';
import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../models/floor_forecast.dart';
import '../models/mall.dart';
import '../models/parking_history_entry.dart';
import '../models/parking_slot.dart';
import '../models/recommendation.dart';
import '../models/reservation.dart';
import 'auth_service.dart';

/// Talks to the Thriver backend. All endpoints mirror the FastAPI routes
/// in backend/app/routes/.
class ApiService {
  static const String baseUrl = AppConfig.apiBaseUrl;

  /// Attaches the bearer token when the user is logged in. Several
  /// endpoints (like /parking/recommend) behave the same either way, but
  /// personalize/log activity when this header is present.
  static Map<String, String> get _authHeaders {
    final token = AuthService.token;
    return token != null ? {"Authorization": "Bearer $token"} : {};
  }

  /// Returns the recommended slot, or `null` when nothing qualifies (for
  /// example no free slot matches the accessible / EV filters). The backend
  /// answers that case with a plain `{"message": ...}` body and no `parking`.
  static Future<Recommendation?> getRecommendation(
    int mallId, {
    int entranceX = 0,
    int entranceY = 0,
    int? preferredFloor,
    bool requiresAccessible = false,
    bool requiresEvCharging = false,
  }) async {
    final uri = Uri.parse("$baseUrl/parking/recommend").replace(
      queryParameters: {
        "mall_id": "$mallId",
        "entrance_x": "$entranceX",
        "entrance_y": "$entranceY",
        if (preferredFloor != null) "preferred_floor": "$preferredFloor",
        if (requiresAccessible) "requires_accessible": "true",
        if (requiresEvCharging) "requires_ev_charging": "true",
      },
    );

    final response = await http.get(uri, headers: _authHeaders);

    if (response.statusCode == 200) {
      final Map<String, dynamic> body = json.decode(response.body);
      if (body["parking"] == null) return null;
      return Recommendation.fromJson(body);
    } else {
      throw Exception("Failed to load recommendation");
    }
  }

  static Future<List<ParkingSlot>> getAvailableSlots(int mallId) async {
    final response = await http.get(
      Uri.parse("$baseUrl/parking/available?mall_id=$mallId"),
    );

    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.map((slot) => ParkingSlot.fromJson(slot)).toList();
    } else {
      throw Exception("Failed to load parking slots");
    }
  }

  static Future<List<Mall>> getMalls() async {
    final response = await http.get(Uri.parse("$baseUrl/malls"));

    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.map((mall) => Mall.fromJson(mall)).toList();
    } else {
      throw Exception("Failed to load malls");
    }
  }

  static Future<List<ParkingSlot>> getParkingMap(int mallId) async {
    final response = await http.get(
      Uri.parse("$baseUrl/parking/map?mall_id=$mallId"),
    );

    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.map((slot) => ParkingSlot.fromJson(slot)).toList();
    } else {
      throw Exception("Failed to load parking map");
    }
  }

  /// Per-floor outlook for the next 15 / 30 minutes (see FloorForecast).
  static Future<List<FloorForecast>> getForecast(int mallId) async {
    final response = await http.get(
      Uri.parse("$baseUrl/parking/forecast?mall_id=$mallId"),
    );

    if (response.statusCode == 200) {
      final Map<String, dynamic> body = json.decode(response.body);
      final List<dynamic> floors = body["floors"];
      return floors.map((f) => FloorForecast.fromJson(f)).toList();
    } else {
      throw Exception("Failed to load forecast");
    }
  }

  static Future<List<ParkingHistoryEntry>> getHistory() async {
    final response = await http.get(
      Uri.parse("$baseUrl/parking/history"),
      headers: _authHeaders,
    );

    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.map((entry) => ParkingHistoryEntry.fromJson(entry)).toList();
    } else {
      throw Exception("Failed to load parking history");
    }
  }

  static Future<Reservation> reserveSlot(int parkingSlotId) async {
    final response = await http.post(
      Uri.parse("$baseUrl/reservations"),
      headers: {..._authHeaders, "Content-Type": "application/json"},
      body: json.encode({"parking_slot_id": parkingSlotId}),
    );

    if (response.statusCode == 201) {
      return Reservation.fromJson(json.decode(response.body));
    }

    throw Exception(_extractError(response.body, "Failed to reserve slot"));
  }

  static Future<void> releaseReservation(int reservationId) async {
    final response = await http.post(
      Uri.parse("$baseUrl/reservations/$reservationId/release"),
      headers: _authHeaders,
    );

    if (response.statusCode != 200) {
      throw Exception(_extractError(response.body, "Failed to release reservation"));
    }
  }

  static Future<Reservation?> getActiveReservation() async {
    final response = await http.get(
      Uri.parse("$baseUrl/reservations/active"),
      headers: _authHeaders,
    );

    if (response.statusCode == 200) {
      final body = response.body;
      if (body == "null" || body.isEmpty) return null;
      return Reservation.fromJson(json.decode(body));
    }

    throw Exception("Failed to load active reservation");
  }

  static String _extractError(String body, String fallback) {
    try {
      final decoded = json.decode(body);
      return decoded["detail"]?.toString() ?? fallback;
    } catch (_) {
      return fallback;
    }
  }
}
