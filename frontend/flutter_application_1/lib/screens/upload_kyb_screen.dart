// lib/screens/upload_kyb_screen.dart
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import '../api_service.dart';
import 'package:http/http.dart' as http;

class UploadKYBScreen extends StatefulWidget {
  final String supplierId;
  UploadKYBScreen({required this.supplierId});
  @override
  State<UploadKYBScreen> createState() => _UploadKYBScreenState();
}

class _UploadKYBScreenState extends State<UploadKYBScreen> {
  PlatformFile? file;
  bool loading = false;
  final _note = TextEditingController();

  Future<void> pickFile() async {
    final res = await FilePicker.platform.pickFiles(type: FileType.any);
    if (res != null) {
      setState(() => file = res.files.first);
    }
  }

  Future<void> upload() async {
    if (file == null) return;
    setState(() => loading = true);
    final bytes = File(file!.path!).readAsBytesSync();
    final mp = http.MultipartFile.fromBytes('document', bytes, filename: file!.name, contentType: null);
    final streamed = await ApiService.postMultipart("suppliers/${widget.supplierId}/upload_kyb/", {"note": _note.text}, [mp]);
    final resp = await http.Response.fromStream(streamed);
    setState(() => loading = false);
    if (resp.statusCode == 201) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Uploaded")));
      Navigator.of(context).pop();
    } else {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Upload failed: ${resp.body}")));
    }
  }

  @override
  Widget build(BuildContext ctx) {
    return Scaffold(
      appBar: AppBar(title: Text("Upload KYB")),
      body: Padding(
        padding: EdgeInsets.all(12),
        child: Column(
          children: [
            ElevatedButton(onPressed: pickFile, child: Text(file == null ? "Pick file" : file!.name)),
            TextField(controller: _note, decoration: InputDecoration(labelText: "Note")),
            SizedBox(height: 12),
            ElevatedButton(onPressed: loading ? null : upload, child: loading ? CircularProgressIndicator() : Text("Upload"))
          ],
        ),
      ),
    );
  }
}
