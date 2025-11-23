// lib/screens/notifications_screen.dart
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../api_service.dart';
import '../models.dart';
import '../providers/auth_provider.dart';

class NotificationsScreen extends StatefulWidget {
  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  bool loading = true;
  String? error;
  List<SupplierConsumerLink> links = [];

  @override
  void initState() {
    super.initState();
    _fetchLinks();
  }

  Future<void> _fetchLinks() async {
    setState(() {
      loading = true;
      error = null;
    });

    try {
      final auth = Provider.of<AuthProvider>(context, listen: false);
      final supplierId = auth.supplier?.id;

      if (supplierId == null) {
        setState(() {
          error = "No supplier linked to this user.";
          loading = false;
        });
        return;
      }
      final resp = await ApiService.get("links/?supplier=$supplierId");

      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body) as List;
        setState(() {

          links = data.map((e) => SupplierConsumerLink.fromJson(e)).toList();

          loading = false;
        });
      } else {
        setState(() {
          error = "Failed to fetch links: ${resp.body}";
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

  Widget _buildLinkTile(SupplierConsumerLink link) {
    return ListTile(
      title: Text(link.consumerId),
      subtitle: Text("Status: ${link.status}"),
      trailing: link.status == "pending"
          ? Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                IconButton(
                  icon: Icon(Icons.check, color: Colors.green),
                  onPressed: () => _updateLinkStatus(link, "approved"),
                ),
                IconButton(
                  icon: Icon(Icons.close, color: Colors.red),
                  onPressed: () => _updateLinkStatus(link, "rejected"),
                ),
              ],
            )
          : null,
    );
  }

  Future<void> _updateLinkStatus(
    SupplierConsumerLink link,
    String status,
  ) async {
    try {
      final resp = await ApiService.patch(
        "links/${link.id}/",
        {"status": status},
      );

      if (resp.statusCode == 200) {
        setState(() {
          link.status = status; // update local state
        });
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Failed to update: ${resp.body}")),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text("Error: $e")));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Notifications")),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : error != null
          ? Center(child: Text(error!))
          : RefreshIndicator(
              onRefresh: _fetchLinks,
              child: ListView.builder(
                itemCount: links.length,
                itemBuilder: (ctx, i) => _buildLinkTile(links[i]),
              ),
            ),
    );
  }
}
