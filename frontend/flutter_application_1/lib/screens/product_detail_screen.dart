import 'package:flutter/material.dart';
import 'package:flutter_application_1/screens/product_edit_screen.dart';
import 'package:provider/provider.dart';
import '../models.dart';
import '../providers/cart_provider.dart';
import '../providers/auth_provider.dart';
import '../api_service.dart';

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

  Future<void> deleteProduct() async {
    final resp = await ApiService.delete("products/${widget.product.id}/");
    if (resp.statusCode == 204 || resp.statusCode == 200) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Product deleted")),
      );
      Navigator.of(context).pop(); // go back after deletion
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Failed to delete product: ${resp.body}")),
      );
    }
  }

  Future<void> editProduct() async {
    // Navigate to product edit screen (you need to implement it)
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ProductEditScreen(product: widget.product),
      ),
    );
  }

  @override
  Widget build(BuildContext ctx) {
    final cart = Provider.of<CartProvider>(ctx, listen: false);
    final auth = Provider.of<AuthProvider>(ctx, listen: false);

    final role = auth.user?.role;
    final isSupplierStaff = role == "owner" || role == "manager" || role == "sales";

    return Scaffold(
      appBar: AppBar(title: Text(widget.product.name)),
      body: Padding(
        padding: const EdgeInsets.all(12),
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                widget.product.name,
                style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Text(
                "Price: \$${widget.product.effectivePrice.toStringAsFixed(2)}",
              ),
              if (widget.product.discountPercentage != null)
                Text("Discount: ${widget.product.discountPercentage!.toStringAsFixed(2)}%"),
              const SizedBox(height: 4),
              Text("Stock: ${widget.product.stock} ${widget.product.unit}"),
              Text("Minimum order: ${widget.product.minOrderQuantity} ${widget.product.unit}"),
              const SizedBox(height: 4),
              Text("Delivery option: ${widget.product.deliveryOption}"),
              Text("Lead time: ${widget.product.leadTimeDays} days"),
              Text("Active: ${widget.product.isActive ? "Yes" : "No"}"),
              const SizedBox(height: 20),

              if (!isSupplierStaff) ...[
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

              if (isSupplierStaff) ...[
                const SizedBox(height: 20),
                const Text(
                  "Supplier Staff View – Product Management",
                  style: TextStyle(color: Colors.grey),
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: ElevatedButton.icon(
                        icon: const Icon(Icons.edit),
                        label: const Text("Edit"),
                        onPressed: editProduct,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: ElevatedButton.icon(
                        icon: const Icon(Icons.delete),
                        label: const Text("Delete"),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.red,
                        ),
                        onPressed: deleteProduct,
                      ),
                    ),
                  ],
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
