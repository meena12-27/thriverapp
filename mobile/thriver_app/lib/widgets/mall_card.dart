import 'package:flutter/material.dart';

import '../models/mall.dart';

/// Top-of-screen intro banner plus the mall picker dropdown.
class WelcomeBanner extends StatelessWidget {
  const WelcomeBanner({super.key});

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 5,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
      color: Colors.blue.shade50,
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.blue,
                borderRadius: BorderRadius.circular(15),
              ),
              child: const Icon(
                Icons.local_parking,
                color: Colors.white,
                size: 30,
              ),
            ),
            const SizedBox(width: 15),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  "Welcome to Thriver",
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 5),
                Text(
                  "Finding the best parking spot for you",
                  style: TextStyle(color: Colors.grey.shade700),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

/// Dropdown that lets the user switch which mall they're viewing.
class MallSelector extends StatelessWidget {
  final List<Mall> malls;
  final int selectedMallId;
  final ValueChanged<int> onChanged;

  const MallSelector({
    super.key,
    required this.malls,
    required this.selectedMallId,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    if (malls.isEmpty) return const SizedBox.shrink();

    return DropdownButton<int>(
      value: selectedMallId,
      items: malls.map<DropdownMenuItem<int>>((mall) {
        return DropdownMenuItem<int>(
          value: mall.id,
          child: Text(mall.name),
        );
      }).toList(),
      onChanged: (value) {
        if (value != null) onChanged(value);
      },
    );
  }
}
