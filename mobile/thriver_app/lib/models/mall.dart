/// A shopping mall that Thriver can find parking in.
class Mall {
  final int id;
  final String name;
  final String location;

  Mall({
    required this.id,
    required this.name,
    required this.location,
  });

  factory Mall.fromJson(Map<String, dynamic> json) {
    return Mall(
      id: json["id"],
      name: json["name"],
      location: json["location"],
    );
  }
}
