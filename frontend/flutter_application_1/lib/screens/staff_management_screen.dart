// lib/screens/staff_management_screen.dart
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../api_service.dart';
import '../providers/auth_provider.dart';
import '../models.dart'; // SupplierStaffMembership, ConsumerContact

class StaffManagementScreen extends StatefulWidget {
  @override
  State<StaffManagementScreen> createState() => _StaffManagementScreenState();
}

class _StaffManagementScreenState extends State<StaffManagementScreen> {
  bool loading = false;
  List<SupplierStaffMembership> staffList = [];
  List<ConsumerContact> consumerList = [];

  @override
  void initState() {
    super.initState();
    fetchStaffAndConsumers();
  }

  Future<void> fetchStaffAndConsumers() async {
    setState(() => loading = true);
    final auth = Provider.of<AuthProvider>(context, listen: false);

    try {
      // Fetch staff for this owner
      final staffResp = await ApiService.get("staff/?supplier=${auth.supplier?.id}");
      if (staffResp.statusCode == 200) {
        final staffJson = jsonDecode(staffResp.body) as List;
        staffList = staffJson
            .map((e) => SupplierStaffMembership.fromJson(e))
            .toList();
      } else {
        staffList = [];
      }

      // Fetch consumer contacts linked to this owner's supplier
      final consumerResp = await ApiService.get("consumer-contacts/?supplier_owner=${auth.user!.id}");
      if (consumerResp.statusCode == 200) {
        final consumerJson = jsonDecode(consumerResp.body) as List;
        consumerList = consumerJson
            .map((e) => ConsumerContact.fromJson(e))
            .toList();
      } else {
        consumerList = [];
      }
    } catch (e) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text("Failed to load: $e")));
    }

    setState(() => loading = false);
  }

  Future<void> deleteStaff(String staffId) async {
    final resp = await ApiService.delete("supplier-staff/$staffId/");
    if (resp.statusCode == 204 || resp.statusCode == 200) {
      setState(() {
        staffList.removeWhere((s) => s.id == staffId);
      });
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text("Staff deleted")));
    } else {
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text("Failed to delete staff")));
    }
  }

  Widget buildStaffList() {
    if (staffList.isEmpty) {
      return const Text("No supplier staff found.");
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          "Supplier Staff",
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        ...staffList.map((staff) => ListTile(
              title: Text(staff.user.username), // you can later map userId to actual username
              subtitle: Text(staff.role),
              trailing: IconButton(
                icon: const Icon(Icons.delete, color: Colors.red),
                onPressed: () => deleteStaff(staff.id),
              ),
            )),
        const Divider(),
      ],
    );
  }

  Widget buildConsumerList() {
    if (consumerList.isEmpty) {
      return const Text("No consumer contacts found.");
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          "Consumer Contacts",
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        ...consumerList.map((c) => ListTile(
              title: Text(c.user.username), // you can map userId to username later
              subtitle: Text(c.consumerId), // optionally show consumer name
            )),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Staff Management")),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [buildStaffList(), const SizedBox(height: 16), buildConsumerList()],
              ),
            ),
    );
  }
}
