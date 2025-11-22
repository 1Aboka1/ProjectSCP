// lib/widgets/supplier_tile.dart
import 'package:flutter/material.dart';
import '../models.dart';
import '../api_service.dart';

class SupplierTile extends StatefulWidget {
  final Supplier supplier;
  final String consumerId; // current consumer id

  SupplierTile({required this.supplier, required this.consumerId, Key? key})
      : super(key: key);

  @override
  _SupplierTileState createState() => _SupplierTileState();
}

class _SupplierTileState extends State<SupplierTile> {
  bool loading = false;
  String? error;
  bool requested = false;

  Future<void> sendLinkRequest() async {
    setState(() {
      loading = true;
      error = null;
    });
    try {
      final payload = {
        "supplier": widget.supplier.id,
        "consumer": widget.consumerId
      };
      final resp = await ApiService.post("links/", payload);
      if (resp.statusCode == 201) {
        setState(() {
          requested = true;
        });
      } else {
        setState(() {
          error = "Failed: ${resp.body}";
        });
      }
    } catch (e) {
      setState(() {
        error = e.toString();
      });
    } finally {
      setState(() {
        loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListTile(
      title: Text(widget.supplier.name),
      subtitle: Text("Status: ${widget.supplier.verificationStatus}"),
      trailing: loading
          ? SizedBox(
              width: 24,
              height: 24,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          : requested
              ? Icon(Icons.check, color: Colors.green)
              : ElevatedButton(
                  child: Text("Request Link"),
                  onPressed: sendLinkRequest,
                ),
    );
  }
}
