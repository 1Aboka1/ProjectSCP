// lib/api_service.dart
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

/// NOTE:
/// We keep using the same token-storage helpers you had (SharedPreferences).
/// If you already have setToken/getToken implemented elsewhere, keep them.
/// Here we still reference them; if you use a different helper, adapt accordingly.
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  static String baseUrl = "http://10.0.2.2:8000/api/";
  static const _tokenKey = "auth_token";

  /// --- Token helpers ---
  static Future<String?> getToken() async {
    final sp = await SharedPreferences.getInstance();
    return sp.getString(_tokenKey);
  }

  static Future<void> setToken(String token) async {
    final sp = await SharedPreferences.getInstance();
    await sp.setString(_tokenKey, token);
  }

  static Future<void> clearToken() async {
    final sp = await SharedPreferences.getInstance();
    await sp.remove(_tokenKey);
  }

  /// --- Default headers with token ---
  static Future<Map<String, String>> defaultHeaders() async {
    final token = await getToken();
    final headers = {
      HttpHeaders.contentTypeHeader: "application/json",
      "Accept": "application/json",
    };
    if (token != null && token.isNotEmpty) {
      headers["Authorization"] = "Token $token"; // use Bearer if JWT
    }
    return headers;
  }

  /// --- GET request ---
  static Future<http.Response> get(String path) async {
    final headers = await defaultHeaders();
    final url = Uri.parse(baseUrl + path);
    return http.get(url, headers: headers);
  }

  /// --- POST request with JSON body ---
  static Future<http.Response> post(String path, Map body) async {
    final headers = await defaultHeaders();
    final url = Uri.parse(baseUrl + path);
    return http.post(url, headers: headers, body: jsonEncode(body));
  }

  /// --- PATCH request ---
  static Future<http.Response> patch(String path, Map body) async {
    final headers = await defaultHeaders();
    final url = Uri.parse(baseUrl + path);
    return http.patch(url, headers: headers, body: jsonEncode(body));
  }

  /// --- DELETE request ---
  static Future<http.Response> delete(String path) async {
    final headers = await defaultHeaders();
    final url = Uri.parse(baseUrl + path);
    return http.delete(url, headers: headers);
  }

  /// --- Existing helper: multipart POST (file uploads) ---
  /// Returns a StreamedResponse (you can convert to http.Response.fromStream).
  static Future<http.StreamedResponse> postMultipart(
    String path,
    Map<String, String> fields,
    List<http.MultipartFile> files,
  ) async {
    final token = await getToken();
    final uri = Uri.parse(baseUrl + path);
    final req = http.MultipartRequest("POST", uri);

    if (token != null && token.isNotEmpty) {
      req.headers['Authorization'] = "Token $token";
    }

    req.fields.addAll(fields);
    req.files.addAll(files);
    return req.send();
  }

  // -------------------------------------------------------
  // Convenience wrappers used by ProductCreateScreen earlier
  // -------------------------------------------------------

  /// Build an empty MultipartRequest for `endpoint` (like "products/").
  /// Caller can mutate `.fields` and `.files`.
  static Future<http.MultipartRequest> multipart(String endpoint) async {
    final uri = Uri.parse(baseUrl + endpoint);
    final req = http.MultipartRequest("POST", uri);
    final token = await getToken();
    if (token != null && token.isNotEmpty) {
      req.headers['Authorization'] = "Token $token";
    }
    // Don't set content-type here; http will set appropriate boundary header
    return req;
  }

  /// Create a MultipartFile from a local file path.
  static Future<http.MultipartFile> multipartFile({
    required String field,
    required File file,
    String? filename,
  }) async {
    // http.MultipartFile.fromPath will guess content-type from file extension
    return await http.MultipartFile.fromPath(field, file.path, filename: filename);
  }

  /// Send a prepared MultipartRequest and return a http.Response
  /// (converts the StreamedResponse to a Response).
  static Future<http.Response> sendMultipart(http.MultipartRequest req) async {
    final streamed = await req.send();
    return await http.Response.fromStream(streamed);
  }
}
