import 'dart:convert';
import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../models/user.dart';

/// Handles registration, login, and holding the current session's token.
///
/// NOTE: the token is kept in memory only (a static field), so it's lost on
/// app restart — the user will need to log in again each launch. That's a
/// deliberate scope cut for this milestone: persisting it securely across
/// restarts needs a package like flutter_secure_storage, which wasn't added
/// here since it couldn't be verified against a real Flutter toolchain in
/// this environment. Swapping in persistent storage later only touches this
/// file — nothing else in the app needs to change.
class AuthService {
  static String? _token;

  static bool get isLoggedIn => _token != null;
  static String? get token => _token;

  static Future<User> register({
    required String email,
    required String password,
    String? fullName,
  }) async {
    final response = await http.post(
      Uri.parse("${AppConfig.apiBaseUrl}/auth/register"),
      headers: {"Content-Type": "application/json"},
      body: json.encode({
        "email": email,
        "password": password,
        if (fullName != null && fullName.isNotEmpty) "full_name": fullName,
      }),
    );

    if (response.statusCode == 201) {
      return User.fromJson(json.decode(response.body));
    }

    throw Exception(_extractError(response.body, "Registration failed"));
  }

  static Future<void> login({
    required String email,
    required String password,
  }) async {
    // OAuth2PasswordRequestForm on the backend expects form-encoded data,
    // not JSON, with the email sent as "username".
    final response = await http.post(
      Uri.parse("${AppConfig.apiBaseUrl}/auth/login"),
      headers: {"Content-Type": "application/x-www-form-urlencoded"},
      body: {"username": email, "password": password},
    );

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      _token = data["access_token"];
      return;
    }

    throw Exception(_extractError(response.body, "Login failed"));
  }

  static Future<User> getProfile() async {
    if (_token == null) throw Exception("Not logged in");

    final response = await http.get(
      Uri.parse("${AppConfig.apiBaseUrl}/auth/me"),
      headers: {"Authorization": "Bearer $_token"},
    );

    if (response.statusCode == 200) {
      return User.fromJson(json.decode(response.body));
    }

    throw Exception(_extractError(response.body, "Failed to load profile"));
  }

  static void logout() {
    _token = null;
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
