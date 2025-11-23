// lib/screens/cart_screen.dart
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_application_1/screens/orders_screen.dart';
import 'package:provider/provider.dart';
import '../providers/cart_provider.dart';
import '../api_service.dart';
import '../providers/auth_provider.dart';

class CartScreen extends StatefulWidget {
  @override
  State<CartScreen> createState() => _CartScreenState();
}

class _CartScreenState extends State<CartScreen> {
  bool loading = false;

  Future<void> placeOrder(
    CartProvider cart,
    String supplierId,
    String consumerId,
  ) async {
    if (cart.items.isEmpty) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text("Cart is empty")));
      return;
    }
    if (consumerId.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Consumer information not available")),
      );
      return;
    }

    final payload = cart.toOrderPayload(supplierId, consumerId);

    setState(() {
      loading = true;
    });
    try {
      final resp = await ApiService.post("orders/", payload);
      setState(() {
        loading = false;
      });

      if (resp.statusCode == 201) {
        cart.clear();
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text("Order created")));
      } else {
        // show helpful server response
        String msg;
        try {
          final j = jsonDecode(resp.body);
          msg = j is Map ? (j['detail']?.toString() ?? resp.body) : resp.body;
        } catch (e) {
          msg = resp.body;
        }
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text("Failed to create order: $msg")));
      }
    } catch (e) {
      setState(() {
        loading = false;
      });
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text("Error: $e")));
    }
  }

  @override
  Widget build(BuildContext ctx) {
    final cart = Provider.of<CartProvider>(ctx);
    final auth = Provider.of<AuthProvider>(ctx);
    // Get consumer id from auth.consumer (Consumer object), NOT auth.user.id
    final consumerId = auth.consumer?.id ?? "";
    // Supplier id must be the supplier that the cart items belong to.
    final supplierId = cart.items.isNotEmpty
        ? cart.items.first.product.supplierId
        : "";

    return Scaffold(
      appBar: AppBar(
        title: const Text("Cart"),
        actions: [
          IconButton(
            icon: const Icon(Icons.list_alt),
            tooltip: "My Orders",
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => OrdersScreen(),
                ),
              );
            },
          ),
        ],
      ),

      body: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            Expanded(
              child: cart.items.isEmpty
                  ? const Center(child: Text("Empty"))
                  : ListView(
                      children: cart.items
                          .map(
                            (it) => ListTile(
                              title: Text(it.product.name),
                              subtitle: Text("${it.qty} x ${it.product.price}"),
                            ),
                          )
                          .toList(),
                    ),
            ),
            Text("Total: ${cart.total.toStringAsFixed(2)}"),
            const SizedBox(height: 8),
            ElevatedButton(
              onPressed: (loading || cart.items.isEmpty || supplierId.isEmpty)
                  ? null
                  : () async {
                      await placeOrder(cart, supplierId, consumerId);
                    },
              child: loading
                  ? const CircularProgressIndicator(color: Colors.white)
                  : const Text("Place Order"),
            ),
          ],
        ),
      ),
    );
  }
}
