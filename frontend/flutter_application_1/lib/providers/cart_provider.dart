// lib/providers/cart_provider.dart
import 'package:flutter/material.dart';
import '../models.dart';

class CartItem {
  final Product product;
  double qty;
  CartItem({required this.product, required this.qty});
}

class CartProvider extends ChangeNotifier {
  final List<CartItem> _items = [];
  List<CartItem> get items => List.unmodifiable(_items);

  void add(Product product, double qty) {
    final idx = _items.indexWhere((e) => e.product.id == product.id);
    if (idx >= 0) {
      _items[idx].qty += qty;
    } else {
      _items.add(CartItem(product: product, qty: qty));
    }
    notifyListeners();
  }

  void clear() {
    _items.clear();
    notifyListeners();
  }

  double get total {
    return _items.fold(0.0, (s, e) => s + (e.product.price * e.qty));
  }

  /// Build payload expected by backend.
  /// supplierId and consumerId must be supplier/consumer UUID strings.
  Map<String, dynamic> toOrderPayload(String supplierId, String consumerId) {
    return {
      "supplier": supplierId,
      "consumer": consumerId,
      "status": "pending",
      "total_amount": total,
      "items": _items.map((it) => {
        // product.id should be a String (UUID) matching backend Product.id
        "product": it.product.id,
        // quantity must be numeric (use double or int)
        "quantity": it.qty,
        // optionally include unit_price (server can compute, but safe to include)
        "unit_price": it.product.price,
      }).toList()
    };
  }
}
