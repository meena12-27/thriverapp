import 'package:flutter/material.dart';

/// Step-by-step turn list from the recommendation's `navigation` field,
/// rendered as a vertical timeline.
class NavigationCard extends StatelessWidget {
  final List<String> steps;

  const NavigationCard({super.key, required this.steps});

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 5,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              "🧭 Navigation",
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 15),
            ...steps.asMap().entries.map<Widget>((entry) {
              final int index = entry.key;
              final String step = entry.value;
              final bool isLast = index == steps.length - 1;

              return Padding(
                padding: const EdgeInsets.only(bottom: 15),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Column(
                      children: [
                        CircleAvatar(
                          radius: 16,
                          backgroundColor: isLast ? Colors.green : Colors.blue,
                          child: Icon(
                            isLast ? Icons.flag : Icons.arrow_forward,
                            color: Colors.white,
                            size: 18,
                          ),
                        ),
                        if (!isLast)
                          Container(
                            width: 2,
                            height: 35,
                            color: Colors.blue.shade200,
                          ),
                      ],
                    ),
                    const SizedBox(width: 15),
                    Expanded(
                      child: Text(
                        step,
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                ),
              );
            }),
          ],
        ),
      ),
    );
  }
}
