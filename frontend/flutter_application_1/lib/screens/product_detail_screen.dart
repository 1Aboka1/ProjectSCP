import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models.dart';
import '../providers/cart_provider.dart';
import '../providers/auth_provider.dart';

class ProductDetailScreen extends StatefulWidget {
  final Product product;

  const ProductDetailScreen({required this.product});

  @override
  State<ProductDetailScreen> createState() => _ProductDetailScreenState();
}

class _ProductDetailScreenState extends State<ProductDetailScreen> {
  late TextEditingController qtyController;

  @override
  void initState() {
    super.initState();
    qtyController = TextEditingController(
      text: widget.product.minOrderQuantity.toString(),
    );
  }

  @override
  void dispose() {
    qtyController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext ctx) {
    final cart = Provider.of<CartProvider>(ctx, listen: false);
    final auth = Provider.of<AuthProvider>(ctx, listen: false);

    final isSupplier = auth.user?.role == "owner";

    return Scaffold(
      appBar: AppBar(title: Text(widget.product.name)),
      body: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              widget.product.name,
              style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
            ),

            const SizedBox(height: 8),

            Text("Price: ${widget.product.effectivePrice.toStringAsFixed(2)}"),
            Text("Stock: ${widget.product.stock} ${widget.product.unit}"),

            const SizedBox(height: 20),

            if (!isSupplier) ...[
              const Text("Quantity:", style: TextStyle(fontSize: 16)),
              const SizedBox(height: 8),

              TextField(
                controller: qtyController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                  hintText: "Enter quantity",
                ),
              ),

              const SizedBox(height: 16),

              ElevatedButton.icon(
                icon: const Icon(Icons.add_shopping_cart),
                label: const Text("Add to Cart"),
                onPressed: () {
                  final qty = double.tryParse(qtyController.text);

                  if (qty == null || qty <= 0) {
                    ScaffoldMessenger.of(ctx).showSnackBar(
                      const SnackBar(content: Text("Enter valid quantity")),
                    );
                    return;
                  }

                  if (qty < widget.product.minOrderQuantity) {
                    ScaffoldMessenger.of(ctx).showSnackBar(
                      SnackBar(
                        content: Text(
                          "Minimum order is ${widget.product.minOrderQuantity}",
                        ),
                      ),
                    );
                    return;
                  }

                  if (qty > widget.product.stock) {
                    ScaffoldMessenger.of(ctx).showSnackBar(
                      SnackBar(
                        content: Text(
                          "Cannot order more than stock (${widget.product.stock})",
                        ),
                      ),
                    );
                    return;
                  }

                  cart.add(widget.product, qty);

                  ScaffoldMessenger.of(ctx).showSnackBar(
                    const SnackBar(content: Text("Added to cart")),
                  );
                },
              ),
            ],

            if (isSupplier) ...[
              const SizedBox(height: 20),
              const Text(
                "Supplier view – Cannot order your own products",
                style: TextStyle(color: Colors.grey),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
