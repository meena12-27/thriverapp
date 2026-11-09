/// App-wide configuration.
///
/// [apiBaseUrl] defaults to localhost for development, but can be
/// overridden at build/run time without touching code, e.g.:
///
///   flutter run --dart-define=API_BASE_URL=http://192.168.1.10:8000
///   flutter build apk --dart-define=API_BASE_URL=https://api.thriver.app
class AppConfig {
  static const String apiBaseUrl = String.fromEnvironment(
    "API_BASE_URL",
    defaultValue: "http://127.0.0.1:8000",
  );
}
