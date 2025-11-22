import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../api_service.dart';
import '../models.dart';
import '../providers/auth_provider.dart';
import '../widgets/product_tile.dart';
import 'product_detail_screen.dart';

class ProductsScreen extends StatefulWidget {
  const ProductsScreen({super.key});

  @override
  State<ProductsScreen> createState() => _ProductsScreenState();
}

class _ProductsScreenState extends State<ProductsScreen> {
  bool loading = true;
  List<Product> products = [];

  @override
  void initState() {
    super.initState();
    loadData();
  }

  Future<void> loadData() async {
    final auth = Provider.of<AuthProvider>(context, listen: false);

    // ROLE DETECTION
    final role = auth.user?.role;

    final endpoint = (role == "owner")
        ? "products/"                // supplier sees own products
        : "products/" ;       // consumer sees allowed products

    final resp = await ApiService.get(endpoint);

    if (resp.statusCode == 200) {
      setState(() {
        products = Product.listFromJson(resp.body);
        loading = false;
      });
    } else {
      setState(() {
        loading = false;
      });
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text("Failed to load products")));
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text("Products"),
        actions: [
          if (auth.user?.role == "owner") ...[
            IconButton(
              icon: const Icon(Icons.add),
              onPressed: () {
                Navigator.pushNamed(context, "/product_create");
              },
            ),
          ]
        ],
      ),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : products.isEmpty
              ? const Center(child: Text("No products found"))
              : ListView.builder(
                  itemCount: products.length,
                  itemBuilder: (ctx, i) {
                    return ProductTile(
                      product: products[i],
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) =>
                                ProductDetailScreen(product: products[i]),
                          ),
                        );
                      },
                    );
                  },
                ),
    );
  }
}
