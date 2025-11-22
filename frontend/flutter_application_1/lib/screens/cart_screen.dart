// lib/screens/cart_screen.dart
import 'dart:convert';
import 'package:flutter/material.dart';
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

  Future<void> placeOrder(CartProvider cart, String consumerId) async {
    if (cart.items.isEmpty) return;
    // For simplicity require that products are all from same supplier
    final supplierId = cart.items.first.product.supplierId;

    // build payload
    final payload = cart.toOrderPayload(supplierId, consumerId);
    setState(() { loading = true; });
    final resp = await ApiService.post("orders/", payload);
    setState(() { loading = false; });
    if (resp.statusCode == 201) {
      cart.clear();
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Order created")));
      Navigator.of(context).pop();
    } else {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Failed to create order: ${resp.body}")));
    }
  }

  @override
  Widget build(BuildContext ctx) {
    final cart = Provider.of<CartProvider>(ctx);
    final auth = Provider.of<AuthProvider>(ctx);
    // consumerId requirement: user must be consumer contact. Simplify: use auth.user.id
    final consumerId = auth.user?.id ?? "";
    return Scaffold(
      appBar: AppBar(title: Text("Cart")),
      body: Padding(
        padding: EdgeInsets.all(12),
        child: Column(
          children: [
            Expanded(
              child: cart.items.isEmpty ? Center(child: Text("Empty")) : ListView(
                children: cart.items.map((it) => ListTile(
                  title: Text(it.product.name),
                  subtitle: Text("${it.qty} x ${it.product.price}"),
                )).toList(),
              ),
            ),
            Text("Total: ${cart.total.toStringAsFixed(2)}"),
            SizedBox(height: 8),
            ElevatedButton(
              onPressed: loading ? null : () async {
                await placeOrder(cart, consumerId);
              },
              child: loading ? CircularProgressIndicator(color: Colors.white) : Text("Place Order")
            )
          ],
        ),
      ),
    );
  }
}
