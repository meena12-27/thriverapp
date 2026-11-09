/// The logged-in user's profile, as returned by /auth/register and /auth/me.
class User {
  final int id;
  final String email;
  final String? fullName;

  User({
    required this.id,
    required this.email,
    this.fullName,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json["id"],
      email: json["email"],
      fullName: json["full_name"],
    );
  }
}
