// lib/providers/auth_provider.dart
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../api_service.dart';
import '../models.dart';
import 'package:http/http.dart' as http;

class AuthProvider extends ChangeNotifier {
  User? user;
  Supplier? supplier; // if user is supplier staff
  Consumer? consumer; // if user is consumer contact
  bool loading = false;
  String? token;

  Future<void> loadFromStorage() async {
    loading = true;
    notifyListeners();

    final t = await ApiService.getToken();
    if (t != null) {
      token = t;
      print('IS THIS EVEN HAPPENING?');

      final resp = await ApiService.get("users/me/");
      if (resp.statusCode == 200) {
        user = User.fromJson(jsonDecode(resp.body));
        print('THEN THIS?');

        // fetch linked organization
        if (user!.role == "owner" ||
            user!.role == "manager" ||
            user!.role == "sales") {
          print('AND MAYBE THIS?');

          final sResp = await ApiService.get(
            "staff/?user=${user!.id}",
          );
          if (sResp.statusCode == 200) {
            print('OR COULD BE THIS?');

            final data = jsonDecode(sResp.body);
            if (data.isNotEmpty) {
              print('AMAYBE MAYBE THIS?');

              final supplierId =
                  data[0]['supplier']; // <-- this is a string UUID
              final supplierResp = await ApiService.get(
                "suppliers/$supplierId/",
              ); // fetch full supplier
              if (supplierResp.statusCode == 200) {
                supplier = Supplier.fromJson(jsonDecode(supplierResp.body));
              }
            }
          }
        } else if (user!.role == "consumer_contact") {
          // fetch consumer_contact linked to this user
          final cResp = await ApiService.get(
            "consumer-contacts/?user=${user!.id}",
          );
          if (cResp.statusCode == 200) {
            final data = jsonDecode(cResp.body);
            if (data.isNotEmpty) {
              final consumerId =
                  data[0]['consumer']; // <-- this is a string UUID
              final consumerResp = await ApiService.get(
                "consumers/$consumerId/",
              ); // fetch full consumer
              if (consumerResp.statusCode == 200) {
                consumer = Consumer.fromJson(jsonDecode(consumerResp.body));
              }
            }
          }
        }
      } else {
        // invalid token or failed request
        token = null;
        user = null;
        supplier = null;
        consumer = null;
        await ApiService.clearToken();
      }
    } else {
      user = null;
      supplier = null;
      consumer = null;
    }

    loading = false;
    notifyListeners();
  }

  Future<Map<String, dynamic>> login(String username, String password) async {
    loading = true;
    notifyListeners();
    // Try default DRF token endpoint
    final resp = await http.post(
      Uri.parse(ApiService.baseUrl + "users/login/"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({"username": username, "password": password}),
    );
    if (resp.statusCode == 200) {
      final j = jsonDecode(resp.body);
      token = j['token'];
      await ApiService.setToken(token!);
      final meResp = await ApiService.get("users/me/");
      if (meResp.statusCode == 200) {
        user = User.fromJson(jsonDecode(meResp.body));
      }
      loading = false;
      notifyListeners();
      return {"ok": true};
    } else {
      loading = false;
      notifyListeners();
      return {"ok": false, "error": resp.body};
    }
  }

  Future<Map<String, dynamic>> register(
    String username,
    String email,
    String password,
    String role,
  ) async {
    loading = true;
    notifyListeners();
    final resp = await ApiService.post("users/", {
      "username": username,
      "email": email,
      "password": password,
      "role": role,
    });
    loading = false;
    notifyListeners();
    if (resp.statusCode == 201 || resp.statusCode == 200) {
      return {"ok": true, "user": jsonDecode(resp.body)};
    } else {
      return {"ok": false, "error": resp.body};
    }
  }

  Future<void> logout() async {
    user = null;
    token = null;
    final sp = await SharedPreferences.getInstance();
    await sp.remove("auth_token");
    notifyListeners();
  }
}
