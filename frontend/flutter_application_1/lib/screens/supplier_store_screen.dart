// lib/screens/supplier_store_screen.dart
import 'dart:convert';
import 'package:flutter/material.dart';
import '../models.dart';
import '../api_service.dart';
import '../widgets/product_tile.dart';
import 'product_detail_screen.dart';

class SupplierStoreScreen extends StatefulWidget {
  final Supplier supplier;
  SupplierStoreScreen({required this.supplier});
  @override
  State<SupplierStoreScreen> createState() => _SupplierStoreScreenState();
}

class _SupplierStoreScreenState extends State<SupplierStoreScreen> {
  bool loading = true;
  List<Product> products = [];

  @override
  void initState() {
    super.initState();
    fetchProducts();
  }

  Future<void> fetchProducts() async {
    setState(() { loading = true; });
    // we expect backend to support ?supplier=<id> filter
    final resp = await ApiService.get("products/?supplier=${widget.supplier.id}");
    if (resp.statusCode == 200) {
      final arr = jsonDecode(resp.body) as List;
      products = arr.map((e) => Product.fromJson(e)).toList();
    } else {
      products = [];
    }
    setState(() { loading = false; });
  }

  @override
  Widget build(BuildContext ctx) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.supplier.name)),
      body: loading ? Center(child: CircularProgressIndicator()) : ListView.builder(
        itemCount: products.length,
        itemBuilder: (c, i) {
          final p = products[i];
          return ProductTile(product: p, onTap: () {
            Navigator.of(context).push(MaterialPageRoute(builder: (_) => ProductDetailScreen(product: p)));
          });
        },
      ),
    );
  }
}
