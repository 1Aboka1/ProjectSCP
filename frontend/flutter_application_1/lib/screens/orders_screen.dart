// lib/screens/orders_screen.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models.dart';
import '../providers/auth_provider.dart';
import '../api_service.dart';
import 'dart:convert';

class OrdersScreen extends StatefulWidget {
  @override
  State<OrdersScreen> createState() => _OrdersScreenState();
}

class _OrdersScreenState extends State<OrdersScreen> {
  bool loading = false;
  List<Order> orders = [];

  @override
  void initState() {
    super.initState();
    _fetchOrders();
  }

  Future<void> _fetchOrders() async {
    setState(() => loading = true);
    final auth = Provider.of<AuthProvider>(context, listen: false);

    // Decide endpoint based on role
    final role = auth.user?.role;
    String url;
    if (role == 'owner' || role == 'manager' || role == 'sales') {
      url = "orders/supplier/"; // your API should return orders for supplier
    } else {
      url = "orders/consumer/"; // your API returns orders for consumer contact
    }

    final resp = await ApiService.get(url);
    if (resp.statusCode == 200) {
      final List<dynamic> jsonList = jsonDecode(resp.body);
      setState(() {
        orders = jsonList.map((j) => Order.fromJson(j)).toList();
      });
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Failed to fetch orders: ${resp.statusCode}")),
      );
    }
    setState(() => loading = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("Orders")),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : orders.isEmpty
              ? const Center(child: Text("No orders found"))
              : ListView.builder(
                  itemCount: orders.length,
                  itemBuilder: (ctx, idx) {
                    final order = orders[idx];
                    return Card(
                      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      child: ExpansionTile(
                        title: Text(
                          "${order.consumerName} → ${order.supplierName}",
                          style: TextStyle(fontWeight: FontWeight.bold),
                        ),
                        subtitle: Text(
                            "Status: ${order.status}, Total: ${order.totalAmount.toStringAsFixed(2)}"),
                        children: [
                          if (order.note != null && order.note!.isNotEmpty)
                            Padding(
                              padding: const EdgeInsets.all(8.0),
                              child: Text("Note: ${order.note}"),
                            ),
                          ...order.items.map((item) => ListTile(
                                title: Text("${item.product.name}"),
                                subtitle: Text(
                                    "${item.quantity} x ${item.unitPrice.toStringAsFixed(2)} = ${item.lineTotal.toStringAsFixed(2)}"),
                              )),
                          if (order.trackingCode != null)
                            Padding(
                              padding: const EdgeInsets.all(8.0),
                              child: Text("Tracking: ${order.trackingCode}"),
                            ),
                          if (order.estimatedDelivery != null)
                            Padding(
                              padding: const EdgeInsets.all(8.0),
                              child: Text(
                                  "ETA: ${order.estimatedDelivery!.toLocal().toString().split(".")[0]}"),
                            ),
                        ],
                      ),
                    );
                  },
                ),
    );
  }
}
