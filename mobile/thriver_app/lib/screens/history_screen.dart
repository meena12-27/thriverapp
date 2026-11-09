import 'package:flutter/material.dart';

import '../models/parking_history_entry.dart';
import '../services/api_service.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  late Future<List<ParkingHistoryEntry>> _historyFuture;

  @override
  void initState() {
    super.initState();
    _historyFuture = ApiService.getHistory();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Parking History")),
      body: FutureBuilder<List<ParkingHistoryEntry>>(
        future: _historyFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }

          if (snapshot.hasError) {
            return Center(child: Text("Couldn't load history: ${snapshot.error}"));
          }

          final entries = snapshot.data ?? [];
          if (entries.isEmpty) {
            return const Center(child: Text("No parking history yet."));
          }

          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: entries.length,
            separatorBuilder: (_, __) => const SizedBox(height: 8),
            itemBuilder: (context, index) {
              final entry = entries[index];
              return Card(
                child: ListTile(
                  leading: const Icon(Icons.local_parking, color: Colors.blue),
                  title: Text("Slot ${entry.slotNumber} • Floor ${entry.floor}"),
                  subtitle: Text(
                    "${entry.zone} Zone • ${entry.distance} m away\n${entry.createdAt.toLocal()}",
                  ),
                  isThreeLine: true,
                ),
              );
            },
          );
        },
      ),
    );
  }
}
