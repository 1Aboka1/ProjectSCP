import 'package:flutter/material.dart';
import '../models.dart';
import '../api_service.dart';

class ProductEditScreen extends StatefulWidget {
  final Product product;

  const ProductEditScreen({required this.product});

  @override
  State<ProductEditScreen> createState() => _ProductEditScreenState();
}

class _ProductEditScreenState extends State<ProductEditScreen> {
  final _formKey = GlobalKey<FormState>();

  late TextEditingController nameController;
  late TextEditingController descriptionController;
  late TextEditingController priceController;
  late TextEditingController discountController;
  late TextEditingController stockController;
  late TextEditingController unitController;
  late TextEditingController minOrderController;
  late TextEditingController deliveryController;
  late TextEditingController leadTimeController;
  bool isActive = true;
  bool loading = false;

  @override
  void initState() {
    super.initState();
    nameController = TextEditingController(text: widget.product.name);
    descriptionController = TextEditingController(text: widget.product.description ?? '');
    priceController = TextEditingController(text: widget.product.effectivePrice.toString());
    discountController = TextEditingController(
        text: widget.product.discountPercentage?.toString() ?? '0');
    stockController = TextEditingController(text: widget.product.stock.toString());
    unitController = TextEditingController(text: widget.product.unit);
    minOrderController =
        TextEditingController(text: widget.product.minOrderQuantity.toString());
    deliveryController = TextEditingController(text: widget.product.deliveryOption);
    leadTimeController =
        TextEditingController(text: widget.product.leadTimeDays.toString());
    isActive = widget.product.isActive;
  }

  @override
  void dispose() {
    nameController.dispose();
    descriptionController.dispose();
    priceController.dispose();
    discountController.dispose();
    stockController.dispose();
    unitController.dispose();
    minOrderController.dispose();
    deliveryController.dispose();
    leadTimeController.dispose();
    super.dispose();
  }

  Future<void> saveProduct() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => loading = true);

    final payload = {
      "name": nameController.text.trim(),
      "description": descriptionController.text.trim(),
      "price": double.tryParse(priceController.text.trim()) ?? 0,
      "discount_percentage": double.tryParse(discountController.text.trim()) ?? 0,
      "stock": double.tryParse(stockController.text.trim()) ?? 0,
      "unit": unitController.text.trim(),
      "min_order_quantity": double.tryParse(minOrderController.text.trim()) ?? 1,
      "delivery_option": deliveryController.text.trim(),
      "lead_time_days": int.tryParse(leadTimeController.text.trim()) ?? 0,
      "is_active": isActive,
    };

    final resp = await ApiService.patch("products/${widget.product.id}/", payload);

    setState(() => loading = false);

    if (resp.statusCode == 200 || resp.statusCode == 202) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Product updated successfully")),
      );
      Navigator.of(context).pop(true); // pass back a flag to indicate update
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Failed to update product: ${resp.body}")),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Edit Product")),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(12),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Name
                    TextFormField(
                      controller: nameController,
                      decoration: const InputDecoration(labelText: "Product Name"),
                      validator: (v) =>
                          v == null || v.trim().isEmpty ? "Required" : null,
                    ),
                    const SizedBox(height: 8),
                    // Description
                    TextFormField(
                      controller: descriptionController,
                      decoration: const InputDecoration(labelText: "Description"),
                      maxLines: 3,
                    ),
                    const SizedBox(height: 8),
                    // Price
                    TextFormField(
                      controller: priceController,
                      decoration: const InputDecoration(labelText: "Price"),
                      keyboardType: TextInputType.number,
                      validator: (v) {
                        final val = double.tryParse(v ?? '');
                        if (val == null || val < 0) return "Invalid price";
                        return null;
                      },
                    ),
                    const SizedBox(height: 8),
                    // Discount
                    TextFormField(
                      controller: discountController,
                      decoration:
                          const InputDecoration(labelText: "Discount % (0–100)"),
                      keyboardType: TextInputType.number,
                      validator: (v) {
                        final val = double.tryParse(v ?? '');
                        if (val == null || val < 0 || val > 100) return "0–100 only";
                        return null;
                      },
                    ),
                    const SizedBox(height: 8),
                    // Stock
                    TextFormField(
                      controller: stockController,
                      decoration: const InputDecoration(labelText: "Stock"),
                      keyboardType: TextInputType.number,
                      validator: (v) {
                        final val = double.tryParse(v ?? '');
                        if (val == null || val < 0) return "Invalid stock";
                        return null;
                      },
                    ),
                    const SizedBox(height: 8),
                    // Unit
                    TextFormField(
                      controller: unitController,
                      decoration: const InputDecoration(labelText: "Unit"),
                      validator: (v) =>
                          v == null || v.trim().isEmpty ? "Required" : null,
                    ),
                    const SizedBox(height: 8),
                    // Min Order
                    TextFormField(
                      controller: minOrderController,
                      decoration: const InputDecoration(labelText: "Min Order Quantity"),
                      keyboardType: TextInputType.number,
                      validator: (v) {
                        final val = double.tryParse(v ?? '');
                        if (val == null || val < 1) return "Min 1 required";
                        return null;
                      },
                    ),
                    const SizedBox(height: 8),
                    // Delivery Option
                    TextFormField(
                      controller: deliveryController,
                      decoration: const InputDecoration(labelText: "Delivery Option"),
                      validator: (v) =>
                          v == null || v.trim().isEmpty ? "Required" : null,
                    ),
                    const SizedBox(height: 8),
                    // Lead time
                    TextFormField(
                      controller: leadTimeController,
                      decoration: const InputDecoration(labelText: "Lead Time Days"),
                      keyboardType: TextInputType.number,
                      validator: (v) {
                        final val = int.tryParse(v ?? '');
                        if (val == null || val < 0) return "Invalid";
                        return null;
                      },
                    ),
                    const SizedBox(height: 12),
                    // Active toggle
                    Row(
                      children: [
                        const Text("Active"),
                        Switch(
                          value: isActive,
                          onChanged: (v) => setState(() => isActive = v),
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),
                    ElevatedButton(
                      onPressed: saveProduct,
                      child: const Text("Save Changes"),
                    ),
                  ],
                ),
              ),
            ),
    );
  }
}
