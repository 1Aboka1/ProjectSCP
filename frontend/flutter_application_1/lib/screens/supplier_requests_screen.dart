// lib/screens/supplier_requests_screen.dart
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../api_service.dart';
import '../models.dart';
import '../providers/auth_provider.dart';

class SupplierRequestsScreen extends StatefulWidget {
  const SupplierRequestsScreen({Key? key}) : super(key: key);

  @override
  _SupplierRequestsScreenState createState() => _SupplierRequestsScreenState();
}

class _SupplierRequestsScreenState extends State<SupplierRequestsScreen> {
  List<SupplierConsumerLink> links = [];
  bool loading = true;
  String? error;

  @override
  void initState() {
    super.initState();
    _loadRequests();
  }

  Future<String?> _ensureConsumerId() async {
    final auth = Provider.of<AuthProvider>(context, listen: false);

    if (auth.consumer != null && auth.consumer!.id != null) {
      return auth.consumer!.id;
    }

    // fallback - ask backend for consumer_contact for current user
    if (auth.user == null) return null;
    final resp = await ApiService.get("consumer-contacts/?user=${auth.user!.id}");
    if (resp.statusCode == 200) {
      final arr = jsonDecode(resp.body);
      if (arr is List && arr.isNotEmpty) {
        final first = arr[0];
        // first likely contains 'consumer' as nested or id, handle both
        final consumerField = first['consumer'];
        if (consumerField is String) return consumerField;
        if (consumerField is Map && consumerField['id'] != null) return consumerField['id'].toString();
      }
    }
    return null;
  }

  Future<void> _loadRequests() async {
    setState(() {
      loading = true;
      error = null;
    });

    try {
      final auth = Provider.of<AuthProvider>(context, listen: false);
      final userId = auth.user?.id;

      final consumerId = await _ensureConsumerId();

      // Build query - prefer filtering by consumer if available, and restrict to requests made by this user
      final queryParts = <String>[];
      if (consumerId != null && consumerId.isNotEmpty) {
        queryParts.add("consumer=$consumerId");
      }
      if (userId != null && userId.isNotEmpty) {
        queryParts.add("requested_by=$userId");
      }
      final query = queryParts.isNotEmpty ? "?${queryParts.join('&')}" : "";

      final resp = await ApiService.get("links/$query");
      if (resp.statusCode == 200) {
        final arr = jsonDecode(resp.body);
        if (arr is List) {
          setState(() {
            links = arr.map<SupplierConsumerLink>((e) {
              if (e is String) {
                // improbable — but be safe
                return SupplierConsumerLink.fromJson({'id': e, 'status': 'unknown', 'supplier': '', 'consumer': ''});
              }
              return SupplierConsumerLink.fromJson(Map<String, dynamic>.from(e));
            }).toList();
            loading = false;
          });
        } else {
          setState(() {
            error = "Invalid response from server";
            loading = false;
          });
        }
      } else if (resp.statusCode == 401 || resp.statusCode == 403) {
        setState(() {
          error = "Authentication required (please login)";
          loading = false;
        });
      } else {
        setState(() {
          error = "Failed to load requests: ${resp.body}";
          loading = false;
        });
      }
    } catch (e) {
      setState(() {
        error = e.toString();
        loading = false;
      });
    }
  }

  Future<void> _cancelRequest(SupplierConsumerLink link) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text("Cancel request"),
        content: Text("Cancel link request to ${link.supplier?.name ?? link.supplierId}?"),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx).pop(false), child: Text("No")),
          TextButton(onPressed: () => Navigator.of(ctx).pop(true), child: Text("Yes")),
        ],
      ),
    );
    if (confirmed != true) return;

    final resp = await ApiService.delete("links/${link.id}/");
    if (resp.statusCode == 204 || resp.statusCode == 200) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Request cancelled")));
      await _loadRequests();
    } else {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Failed to cancel: ${resp.body}")));
    }
  }

  Widget _buildRow(SupplierConsumerLink link) {
    final supplierName = link.supplier?.name ?? link.supplierId;
    final created = link.createdAt != null ? link.createdAt!.toLocal().toString() : null;

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      child: ListTile(
        title: Text(supplierName),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (link.note != null && link.note!.isNotEmpty) Text(link.note!),
            if (created != null) Text("Requested: $created", style: TextStyle(fontSize: 12, color: Colors.grey)),
            Text("Status: ${link.status}", style: TextStyle(fontWeight: FontWeight.w600)),
          ],
        ),
        trailing: link.status == 'pending'
            ? IconButton(
                icon: Icon(Icons.cancel, color: Colors.red),
                tooltip: "Cancel request",
                onPressed: () => _cancelRequest(link),
              )
            : null,
        onTap: () {
          // Could go to supplier page
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("My Link Requests"),
        actions: [
          IconButton(
            icon: Icon(Icons.refresh),
            onPressed: _loadRequests,
          )
        ],
      ),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : error != null
              ? Center(child: Text(error!))
              : links.isEmpty
                  ? Center(child: Text("No link requests"))
                  : RefreshIndicator(
                      onRefresh: _loadRequests,
                      child: ListView.builder(
                        physics: const AlwaysScrollableScrollPhysics(),
                        itemCount: links.length,
                        itemBuilder: (ctx, i) => _buildRow(links[i]),
                      ),
                    ),
      floatingActionButton: FloatingActionButton(
        child: Icon(Icons.add),
        tooltip: "Request link to supplier",
        onPressed: () async {
          // optionally open supplier list for creating a new request,
          // or show dialog to enter supplier id. Here we open supplier list route if exists.
          Navigator.of(context).pushNamed("/suppliers");
        },
      ),
    );
  }
}
