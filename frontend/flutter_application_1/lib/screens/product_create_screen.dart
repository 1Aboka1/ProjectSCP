// lib/screens/product_create_screen.dart
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';

import '../api_service.dart';
import '../providers/auth_provider.dart';

class ProductCreateScreen extends StatefulWidget {
  @override
  State<ProductCreateScreen> createState() => _ProductCreateScreenState();
}

class _ProductCreateScreenState extends State<ProductCreateScreen> {
  final _formKey = GlobalKey<FormState>();

  String name = "";
  String? description = "";
  String unit = "";
  String price = "";
  String discount = "";
  String stock = "0";
  String minOrderQuantity = "1";
  String deliveryOption = "both";
  String leadTimeDays = "0";

  File? image;

  bool loading = false;
  String? errorMessage;

  Future<void> pickImage() async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(source: ImageSource.gallery);

    if (picked != null) {
      setState(() => image = File(picked.path));
    }
  }

  Future<void> submit() async {
    if (!_formKey.currentState!.validate()) return;
    _formKey.currentState!.save();

    final auth = Provider.of<AuthProvider>(context, listen: false);
    if (auth.supplier == null) {
      setState(() => errorMessage = "You are not linked to any supplier.");
      return;
    }

    setState(() {
      loading = true;
      errorMessage = null;
    });

    final supplierId = auth.supplier!.id;

    try {
      final request = await ApiService.multipart("products/");

      request.fields["supplier"] = supplierId;
      request.fields["name"] = name;
      request.fields["description"] = description ?? "";
      request.fields["unit"] = unit;
      request.fields["price"] = price;
      request.fields["discount_percentage"] = discount.isEmpty ? "" : discount;
      request.fields["stock"] = stock;
      request.fields["min_order_quantity"] = minOrderQuantity;
      request.fields["delivery_option"] = deliveryOption;
      request.fields["lead_time_days"] = leadTimeDays;

      if (image != null) {
        request.files.add(
          await ApiService.multipartFile(field: "image", file: image!),
        );
      }

      final resp = await ApiService.sendMultipart(request);

      if (resp.statusCode == 201) {
        Navigator.of(context).pop(true);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Product created successfully")),
        );
      } else {
        final body = jsonDecode(resp.body);

        setState(() {
          errorMessage = body.toString();
        });
      }
    } catch (e) {
      setState(() => errorMessage = e.toString());
    }

    setState(() => loading = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Create Product")),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : Padding(
              padding: const EdgeInsets.all(16),
              child: Form(
                key: _formKey,
                child: ListView(
                  children: [
                    if (errorMessage != null)
                      Container(
                        padding: const EdgeInsets.all(12),
                        margin: const EdgeInsets.only(bottom: 12),
                        decoration: BoxDecoration(
                          color: Colors.red.shade100,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          errorMessage!,
                          style: const TextStyle(
                            color: Colors.red,
                            fontSize: 14,
                          ),
                        ),
                      ),

                    // Product name
                    TextFormField(
                      decoration: const InputDecoration(
                        labelText: "Product Name",
                      ),
                      validator: (v) =>
                          v == null || v.isEmpty ? "Required" : null,
                      onSaved: (v) => name = v!.trim(),
                    ),

                    TextFormField(
                      decoration: const InputDecoration(
                        labelText: "Description",
                      ),
                      maxLines: 3,
                      onSaved: (v) => description = v,
                    ),

                    TextFormField(
                      decoration: const InputDecoration(
                        labelText: "Unit (kg, liter, etc.)",
                      ),
                      validator: (v) =>
                          v == null || v.isEmpty ? "Required" : null,
                      onSaved: (v) => unit = v!.trim(),
                    ),

                    TextFormField(
                      decoration: const InputDecoration(labelText: "Price"),
                      keyboardType: const TextInputType.numberWithOptions(
                        decimal: true,
                      ),
                      validator: (v) => v == null || double.tryParse(v) == null
                          ? "Enter number"
                          : null,
                      onSaved: (v) => price = v!,
                    ),

                    TextFormField(
                      decoration: const InputDecoration(
                        labelText: "Discount % (optional)",
                      ),
                      keyboardType: const TextInputType.numberWithOptions(
                        decimal: true,
                      ),
                      onSaved: (v) => discount = v ?? "",
                    ),

                    TextFormField(
                      decoration: const InputDecoration(labelText: "Stock"),
                      keyboardType: const TextInputType.numberWithOptions(
                        decimal: true,
                      ),
                      validator: (v) => v == null || double.tryParse(v) == null
                          ? "Enter number"
                          : null,
                      onSaved: (v) => stock = v!,
                    ),

                    TextFormField(
                      decoration: const InputDecoration(
                        labelText: "Min Order Quantity",
                      ),
                      keyboardType: const TextInputType.numberWithOptions(
                        decimal: true,
                      ),
                      validator: (v) => v == null || double.tryParse(v) == null
                          ? "Enter number"
                          : null,
                      onSaved: (v) => minOrderQuantity = v!,
                    ),

                    DropdownButtonFormField<String>(
                      value: deliveryOption,
                      decoration: const InputDecoration(
                        labelText: "Delivery Option",
                      ),
                      items: const [
                        DropdownMenuItem(
                          value: "both",
                          child: Text("Delivery & Pickup"),
                        ),
                        DropdownMenuItem(
                          value: "delivery",
                          child: Text("Delivery Only"),
                        ),
                        DropdownMenuItem(
                          value: "pickup",
                          child: Text("Pickup Only"),
                        ),
                      ],
                      onChanged: (v) => setState(() => deliveryOption = v!),
                    ),

                    TextFormField(
                      decoration: const InputDecoration(
                        labelText: "Lead Time (days)",
                      ),
                      keyboardType: TextInputType.number,
                      validator: (v) => v == null || int.tryParse(v) == null
                          ? "Enter integer"
                          : null,
                      onSaved: (v) => leadTimeDays = v!,
                    ),

                    const SizedBox(height: 16),

                    // Image picker
                    Row(
                      children: [
                        ElevatedButton(
                          onPressed: pickImage,
                          child: const Text("Pick Image"),
                        ),
                        const SizedBox(width: 12),
                        if (image != null)
                          Text(
                            "Image selected",
                            style: TextStyle(color: Colors.green.shade700),
                          ),
                      ],
                    ),

                    const SizedBox(height: 24),

                    ElevatedButton(
                      onPressed: submit,
                      child: const Text("Create Product"),
                    ),
                  ],
                ),
              ),
            ),
    );
  }
}
