// lib/widgets/product_tile.dart
import 'package:flutter/material.dart';
import '../models.dart';

class ProductTile extends StatelessWidget {
  final Product product;
  final VoidCallback? onTap;
  const ProductTile({required this.product, this.onTap});

  @override
  Widget build(BuildContext ctx) {
    return ListTile(
      title: Text(product.name),
      subtitle: Text(
        "${product.effectivePrice.toStringAsFixed(2)} KZT • ${product.unit}\nStock: ${product.stock}",
      ),
      trailing: const Icon(Icons.chevron_right),
      isThreeLine: true,
      onTap: onTap,
    );
  }
}
