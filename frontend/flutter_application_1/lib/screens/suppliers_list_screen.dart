// lib/screens/suppliers_list_screen.dart
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../api_service.dart';
import '../models.dart';
import '../widgets/supplier_tile.dart';
import '../providers/auth_provider.dart';

class SuppliersListScreen extends StatefulWidget {
  @override
  _SuppliersListScreenState createState() => _SuppliersListScreenState();
}

class _SuppliersListScreenState extends State<SuppliersListScreen> {
  List<Supplier> suppliers = [];
  bool loading = true;
  String? error;

  @override
  void initState() {
    super.initState();
    _fetchSuppliers();
  }

  Future<void> _fetchSuppliers() async {
    setState(() {
      loading = true;
      error = null;
    });
    try {
      final resp = await ApiService.get("suppliers/");
      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body) as List;
        setState(() {
          suppliers = data.map((s) => Supplier.fromJson(s)).toList();
        });
      } else {
        setState(() {
          error = "Failed to load suppliers: ${resp.body}";
        });
      }
    } catch (e) {
      setState(() {
        error = e.toString();
      });
    } finally {
      setState(() {
        loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context);
    final consumerId = auth.consumer?.id;

    if (consumerId == null) {
      return Scaffold(
        appBar: AppBar(title: Text("Suppliers")),
        body: Center(child: Text("Not logged in as consumer")),
      );
    }

    return Scaffold(
      appBar: AppBar(title: Text("Suppliers")),
      body: loading
          ? Center(child: CircularProgressIndicator())
          : error != null
              ? Center(child: Text(error!))
              : RefreshIndicator(
                  onRefresh: _fetchSuppliers,
                  child: ListView.builder(
                    itemCount: suppliers.length,
                    itemBuilder: (ctx, i) => SupplierTile(
                      supplier: suppliers[i],
                      consumerId: consumerId,
                    ),
                  ),
                ),
    );
  }
}
