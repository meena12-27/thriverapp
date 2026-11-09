import 'dart:async';

import 'package:flutter/material.dart';

import '../models/floor_forecast.dart';
import '../models/mall.dart';
import '../models/parking_slot.dart';
import '../models/recommendation.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import '../widgets/availability_card.dart';
import '../widgets/forecast_card.dart';
import '../widgets/mall_card.dart';
import '../widgets/navigation_widget.dart';
import '../widgets/parking_map_widget.dart';
import '../widgets/recommendation_card.dart';
import '../widgets/recommendation_filters.dart';
import 'history_screen.dart';
import 'login_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  // `recommendation` is null both before the first response and when the
  // backend found no matching slot; `recommendationLoaded` tells them apart.
  Recommendation? recommendation;
  bool recommendationLoaded = false;
  int _recommendationRequestId = 0;
  String? errorMessage;
  Timer? _pollTimer;

  List<Mall> malls = [];
  int selectedMallId = 1;

  List<ParkingSlot> availability = [];
  List<ParkingSlot> parkingMap = [];
  List<FloorForecast> forecast = [];

  int selectedFloor = 1;
  ParkingSlot? selectedSlot;
  bool showAvailableOnly = false;

  // Recommendation filters (Milestone 5)
  Entrance entrance = Entrance.all.first;
  int? preferredFloor;
  bool requiresAccessible = false;
  bool requiresEvCharging = false;

  static const Duration _pollInterval = Duration(seconds: 10);

  /// Floors that actually exist in the selected mall (falls back to [1]
  /// until the map has loaded). Different malls have different floor counts.
  List<int> get _floors {
    final floors = parkingMap.map((s) => s.floor).toSet().toList()..sort();
    return floors.isEmpty ? [1] : floors;
  }

  @override
  void initState() {
    super.initState();
    _loadAll();

    _pollTimer = Timer.periodic(_pollInterval, (_) {
      _loadRecommendation();
      _loadAvailability();
      _loadForecast();
    });
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  void _loadAll() {
    _loadMalls();
    _loadRecommendation();
    _loadAvailability();
    _loadParkingMap();
    _loadForecast();
  }

  Future<void> _loadRecommendation() async {
    final requestedMallId = selectedMallId;
    // Only the newest request may update the screen, so a slow response for
    // old filters (or an old mall) can't overwrite a newer one.
    final requestId = ++_recommendationRequestId;
    try {
      final data = await ApiService.getRecommendation(
        requestedMallId,
        entranceX: entrance.x,
        entranceY: entrance.y,
        preferredFloor: preferredFloor,
        requiresAccessible: requiresAccessible,
        requiresEvCharging: requiresEvCharging,
      );
      if (!mounted || requestId != _recommendationRequestId) return;
      setState(() {
        errorMessage = null;
        recommendation = data;
        recommendationLoaded = true;
      });
    } catch (_) {
      if (!mounted || requestId != _recommendationRequestId) return;
      setState(() => errorMessage = "Unable to connect to parking server");
    }
  }

  void _clearFilters() {
    setState(() {
      preferredFloor = null;
      requiresAccessible = false;
      requiresEvCharging = false;
    });
    _loadRecommendation();
  }

  Future<void> _loadAvailability() async {
    final requestedMallId = selectedMallId;
    final data = await ApiService.getAvailableSlots(requestedMallId);
    if (!mounted || requestedMallId != selectedMallId) return;
    setState(() => availability = data);
  }

  /// The forecast is a nice-to-have: if it fails the rest of the screen
  /// still works, so errors just clear it instead of showing an error state.
  Future<void> _loadForecast() async {
    final requestedMallId = selectedMallId;
    try {
      final data = await ApiService.getForecast(requestedMallId);
      if (!mounted || requestedMallId != selectedMallId) return;
      setState(() => forecast = data);
    } catch (_) {
      if (!mounted || requestedMallId != selectedMallId) return;
      setState(() => forecast = []);
    }
  }

  Future<void> _loadParkingMap() async {
    final requestedMallId = selectedMallId;
    final data = await ApiService.getParkingMap(requestedMallId);
    if (!mounted || requestedMallId != selectedMallId) return;
    setState(() => parkingMap = data);
  }

  Future<void> _loadMalls() async {
    final data = await ApiService.getMalls();
    setState(() => malls = data);
  }

  void _onMallChanged(int mallId) {
    setState(() {
      selectedMallId = mallId;
      // The previously selected slot belongs to the old mall — holding
      // onto it here would let a user reserve a slot from the wrong mall.
      selectedSlot = null;
      selectedFloor = 1;
      // Floor numbers differ between malls, so a floor preference from the
      // previous mall may not exist here.
      preferredFloor = null;
      // Another mall's floors would be misleading while the new one loads.
      forecast = [];
    });
    _loadRecommendation();
    _loadAvailability();
    _loadParkingMap();
    _loadForecast();
  }

  void _onReserve() async {
    if (selectedSlot == null) return;

    if (!AuthService.isLoggedIn) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Log in to reserve a parking slot")),
      );
      Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => const LoginScreen()),
      );
      return;
    }

    try {
      final reservation = await ApiService.reserveSlot(selectedSlot!.id);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            "Slot ${selectedSlot!.slotNumber} reserved for ${(reservation.secondsRemaining / 60).ceil()} min",
          ),
        ),
      );
      _loadAvailability();
      _loadParkingMap();
      _loadForecast();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString().replaceFirst("Exception: ", ""))),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: _buildAppBar(),
      body: _buildBody(),
    );
  }

  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      elevation: 2,
      title: const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            "Good Morning 👋",
            style: TextStyle(fontSize: 14, color: Colors.white70),
          ),
          Text(
            "🚗 Thriver",
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
          ),
        ],
      ),
      actions: [
        Padding(
          padding: const EdgeInsets.only(right: 8),
          child: PopupMenuButton<String>(
            onSelected: _onProfileMenuSelected,
            itemBuilder: (context) => [
              if (AuthService.isLoggedIn) ...[
                const PopupMenuItem(value: "history", child: Text("Parking History")),
                const PopupMenuItem(value: "logout", child: Text("Log out")),
              ] else
                const PopupMenuItem(value: "login", child: Text("Log in")),
            ],
            child: const CircleAvatar(
              backgroundColor: Colors.white,
              child: Icon(Icons.person, color: Colors.blue),
            ),
          ),
        ),
      ],
    );
  }

  void _onProfileMenuSelected(String value) {
    switch (value) {
      case "history":
        Navigator.of(context).push(
          MaterialPageRoute(builder: (_) => const HistoryScreen()),
        );
        break;
      case "logout":
        AuthService.logout();
        Navigator.of(context).pushAndRemoveUntil(
          MaterialPageRoute(builder: (_) => const LoginScreen()),
          (route) => false,
        );
        break;
      case "login":
        Navigator.of(context).push(
          MaterialPageRoute(builder: (_) => const LoginScreen()),
        );
        break;
    }
  }

  Widget _buildBody() {
    if (errorMessage != null) {
      return _ErrorState(message: errorMessage!, onRetry: _loadAll);
    }

    if (!recommendationLoaded) {
      return const _LoadingState();
    }

    final rec = recommendation; // null when no slot matches the filters
    final floors = _floors;

    return Padding(
      padding: const EdgeInsets.all(20),
      child: ListView(
        children: [
          MallSelector(
            malls: malls,
            selectedMallId: selectedMallId,
            onChanged: _onMallChanged,
          ),
          RecommendationFilters(
            entrance: entrance,
            onEntranceChanged: (value) {
              setState(() => entrance = value);
              _loadRecommendation();
            },
            floors: floors,
            // A dropdown asserts if its value isn't in its items, so only
            // pass a floor this mall actually has.
            preferredFloor: floors.contains(preferredFloor) ? preferredFloor : null,
            onPreferredFloorChanged: (value) {
              setState(() => preferredFloor = value);
              _loadRecommendation();
            },
            requiresAccessible: requiresAccessible,
            onAccessibleChanged: (value) {
              setState(() => requiresAccessible = value);
              _loadRecommendation();
            },
            requiresEvCharging: requiresEvCharging,
            onEvChargingChanged: (value) {
              setState(() => requiresEvCharging = value);
              _loadRecommendation();
            },
          ),
          const SizedBox(height: 15),
          ParkingOverviewCard(availability: availability, parkingMap: parkingMap),
          const SizedBox(height: 15),
          const WelcomeBanner(),
          if (rec != null)
            RecommendationSummaryCard(
              recommendation: rec,
              availableCount: availability.length,
            )
          else
            NoMatchCard(onClearFilters: _clearFilters),
          const SizedBox(height: 20),
          if (availability.isNotEmpty) LiveStatusCard(availability: availability),
          if (forecast.isNotEmpty) ...[
            const SizedBox(height: 20),
            ForecastCard(forecast: forecast),
          ],
          const SizedBox(height: 20),
          if (rec != null) AiRecommendationCard(recommendation: rec),
          if (rec != null) const SizedBox(height: 20),
          const Text(
            "🗺️ Parking Map",
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          ParkingMapControls(
            showAvailableOnly: showAvailableOnly,
            onShowAvailableOnlyChanged: (value) =>
                setState(() => showAvailableOnly = value),
            selectedFloor: floors.contains(selectedFloor) ? selectedFloor : floors.first,
            floors: floors,
            onFloorChanged: (value) => setState(() => selectedFloor = value),
          ),
          const SizedBox(height: 10),
          const Text(
            "Legend",
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 10),
          const ParkingMapLegend(),
          const SizedBox(height: 20),
          ParkingMapGrid(
            parkingMap: parkingMap,
            selectedFloor: selectedFloor,
            showAvailableOnly: showAvailableOnly,
            recommendation: recommendation,
            selectedSlot: selectedSlot,
            onSlotTapped: (slot) => setState(() => selectedSlot = slot),
          ),
          const SizedBox(height: 20),
          if (selectedSlot != null && selectedSlot!.mallId == selectedMallId)
            SelectedSlotCard(slot: selectedSlot!, onReserve: _onReserve),
          if (rec != null) NavigationCard(steps: rec.navigation),
          const SizedBox(height: 20),
          ElevatedButton.icon(
            onPressed: _loadAll,
            icon: const Icon(Icons.refresh),
            label: const Text("Refresh Parking"),
          ),
        ],
      ),
    );
  }
}

class _LoadingState extends StatelessWidget {
  const _LoadingState();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(),
          SizedBox(height: 20),
          Text("🚗 Finding your parking spot...", style: TextStyle(fontSize: 18)),
        ],
      ),
    );
  }
}

class _ErrorState extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _ErrorState({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.cloud_off, size: 60, color: Colors.red),
          const SizedBox(height: 20),
          Text(message, style: const TextStyle(fontSize: 18)),
          const SizedBox(height: 20),
          ElevatedButton.icon(
            onPressed: onRetry,
            icon: const Icon(Icons.refresh),
            label: const Text("Retry"),
          ),
        ],
      ),
    );
  }
}
