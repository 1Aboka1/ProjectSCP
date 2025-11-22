import 'dart:convert';
import 'package:http/http.dart' as http;

class AuthService {
  final String baseUrl = "http://10.0.2.2:8000/api/users/register/";

  Future<Map<String, dynamic>> register({
    required String username,
    required String password,
    required String role,
    String? supplierName,
    String? supplierId,
    String? consumerName,
    String? email,
    String? phone,
    String? displayName,
  }) async {

    final Map<String, dynamic> body = {
      "username": username,
      "password": password,
      "role": role,
      "email": email ?? "",
      "phone": phone ?? "",
      "display_name": displayName ?? username,
    };

    // --- Role-specific requirements ---

    // Supplier Owner → must create supplier
    if (role == "owner") {
      body["supplier_name"] = supplierName;
    }

    // Manager / Sales → must join existing supplier
    if (role == "manager" || role == "sales") {
      body["supplier_id"] = supplierId;
    }

    // Consumer Contact → must create consumer
    if (role == "consumer_contact") {
      body["consumer_name"] = consumerName;
    }

    final response = await http.post(
      Uri.parse(baseUrl),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode(body),
    );

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return jsonDecode(response.body);
    } else {
      throw Exception("Registration failed: ${response.body}");
    }
  }
}
