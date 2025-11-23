// lib/screens/orders_screen.dart
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models.dart';
import '../providers/auth_provider.dart';
import '../api_service.dart';

class OrdersScreen extends StatefulWidget {
  const OrdersScreen({Key? key}) : super(key: key);

  @override
  State<OrdersScreen> createState() => _OrdersScreenState();
}

class _OrdersScreenState extends State<OrdersScreen> {
  bool loading = false;
  List<Order> orders = [];
  late String userRole; // 'supplier' or 'consumer'
  late String userId; // consumer.id or supplier.id

  @override
  void initState() {
    super.initState();
    final auth = Provider.of<AuthProvider>(context, listen: false);
    userRole = auth.user?.role ?? "consumer";
    // Supplier has a supplier object, consumer has a consumer object
    userId =
        (userRole == "owner" || userRole == "manager" || userRole == "sales")
        ? auth.supplier?.id ?? ""
        : auth.consumer?.id ?? "";
    _fetchOrders();
  }

  Future<void> createComplaint(Order order, OrderItem item) async {
    final TextEditingController descController = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Create Complaint"),
        content: TextField(
          controller: descController,
          decoration: const InputDecoration(hintText: "Describe the issue"),
          maxLines: 3,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text("Cancel"),
          ),
          ElevatedButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text("Submit"),
          ),
        ],
      ),
    );

    if (ok != true) return;

    final payload = {
      "order": order.id,
      "order_item": item.id,
      "description": descController.text,
    };

    final resp = await ApiService.post("complaints/", payload);

    if (resp.statusCode == 201) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text("Complaint submitted")));
    } else {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text("Failed: ${resp.body}")));
    }
  }

  /// --- API Calls for actions ---
  Future<bool> acceptOrder(String id) async =>
      (await ApiService.post("orders/$id/accept/", {})).statusCode == 200;

  Future<bool> rejectOrder(String id) async =>
      (await ApiService.post("orders/$id/reject/", {})).statusCode == 200;

  Future<bool> completeOrder(String id) async =>
      (await ApiService.post("orders/$id/complete/", {})).statusCode == 200;

  Future<bool> cancelOrder(String id) async =>
      (await ApiService.post("orders/$id/cancel/", {})).statusCode == 200;

  Future<String?> fetchProductName(String productId) async {
    final resp = await ApiService.get("products/$productId/");
    if (resp.statusCode == 200) {
      final json = jsonDecode(resp.body);
      return json["name"];
    }
    return null;
  }

  /// --- Fetch Orders depending on role ---
  Future<void> _fetchOrders() async {
    if (userId.isEmpty) return;

    setState(() => loading = true);

    String url;
    if (userRole == "owner" || userRole == "manager" || userRole == "sales") {
      // Supplier: orders for their products
      url = "orders/?supplier=$userId";
    } else {
      // Consumer: orders submitted by themselves
      url = "orders/?consumer=$userId";
    }

    final resp = await ApiService.get(url);

    if (resp.statusCode == 200) {
      final List<dynamic> jsonList = jsonDecode(resp.body);
      orders = jsonList.map((j) => Order.fromJson(j)).toList();

      // Ensure product names are fetched if product field is only ID
      for (final order in orders) {
        for (final item in order.items) {
          if (item.product is String) {
            item.productName =
                await fetchProductName(item.product as String) ??
                "Unknown product";
          }
        }
      }
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Failed to fetch orders: ${resp.statusCode}")),
      );
    }

    setState(() => loading = false);
  }

  /// --- Buttons displayed depending on role & order status ---
  Widget buildActionButtons(Order order) {
    if (userRole == "consumer_contact") {

      // Consumer: can cancel pending or in-progress orders
      if (order.status == "pending" || order.status == "in_progress") {
        return ElevatedButton(
          style: ElevatedButton.styleFrom(backgroundColor: Colors.orange),
          onPressed: () async {
            final ok = await cancelOrder(order.id);
            if (ok) {
              setState(() => order.status = "cancelled");
              ScaffoldMessenger.of(
                context,
              ).showSnackBar(const SnackBar(content: Text("Order cancelled")));
            }
          },
          child: const Text("Cancel"),
        );
      }
      return const SizedBox();
    } else {
      // Supplier: full workflow
      switch (order.status) {
        case "pending":
          return Row(
            children: [
              Expanded(
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.green,
                  ),
                  onPressed: () async {
                    final ok = await acceptOrder(order.id);
                    if (ok) {
                      setState(() => order.status = "in_progress");
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text("Order accepted")),
                      );
                    }
                  },
                  child: const Text("Accept"),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
                  onPressed: () async {
                    final ok = await rejectOrder(order.id);
                    if (ok) {
                      setState(() => order.status = "rejected");
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text("Order rejected")),
                      );
                    }
                  },
                  child: const Text("Reject"),
                ),
              ),
            ],
          );

        case "in_progress":
          return Row(
            children: [
              Expanded(
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.blue),
                  onPressed: () async {
                    final ok = await completeOrder(order.id);
                    if (ok) {
                      setState(() => order.status = "completed");
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text("Order completed")),
                      );
                    }
                  },
                  child: const Text("Complete"),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.orange,
                  ),
                  onPressed: () async {
                    final ok = await cancelOrder(order.id);
                    if (ok) {
                      setState(() => order.status = "cancelled");
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text("Order cancelled")),
                      );
                    }
                  },
                  child: const Text("Cancel"),
                ),
              ),
            ],
          );

        default:
          return const SizedBox(); // rejected, completed, cancelled → no buttons
      }
    }
  }

  /// --- Single order card ---
  Widget buildOrderCard(Order order) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              "Order #${order.id}",
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 4),
            Text("Status: ${order.status.toUpperCase()}"),
            Text("Total: \$${order.totalAmount.toStringAsFixed(2)}"),
            const SizedBox(height: 8),
            ...order.items.map(
              (it) => Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Text(
                      "- ${it.productName ?? 'Unknown product'} x ${it.quantity}",
                    ),
                  ),
                  if (userRole == "consumer_contact")
                    TextButton(
                      onPressed: () => createComplaint(order, it),
                      child: const Text("Create Complaint"),
                    ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            buildActionButtons(order),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Orders")),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : orders.isEmpty
          ? const Center(child: Text("No orders found"))
          : ListView(children: orders.map(buildOrderCard).toList()),
    );
  }
}
