import 'package:flutter/material.dart';
import '../services/auth_service.dart';

class RegisterScreen extends StatefulWidget {
  @override
  _RegisterScreenState createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final AuthService auth = AuthService();

  final TextEditingController username = TextEditingController();
  final TextEditingController password = TextEditingController();
  final TextEditingController email = TextEditingController();
  final TextEditingController phone = TextEditingController();
  final TextEditingController displayName = TextEditingController();

  final TextEditingController supplierName = TextEditingController();
  final TextEditingController supplierId = TextEditingController();
  final TextEditingController consumerName = TextEditingController();

  String selectedRole = "owner";

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("Register")),
      body: SingleChildScrollView(
        padding: EdgeInsets.all(16),
        child: Column(
          children: [

            DropdownButtonFormField<String>(
              value: selectedRole,
              items: [
                DropdownMenuItem(value: "owner", child: Text("Supplier Owner")),
                DropdownMenuItem(value: "manager", child: Text("Supplier Manager")),
                DropdownMenuItem(value: "sales", child: Text("Sales Representative")),
                DropdownMenuItem(value: "consumer_contact", child: Text("Consumer Contact")),
              ],
              onChanged: (role) {
                setState(() => selectedRole = role!);
              },
              decoration: InputDecoration(labelText: "Role"),
            ),

            TextField(controller: username, decoration: InputDecoration(labelText: "Username")),
            TextField(controller: password, decoration: InputDecoration(labelText: "Password"), obscureText: true),
            TextField(controller: email, decoration: InputDecoration(labelText: "Email")),
            TextField(controller: phone, decoration: InputDecoration(labelText: "Phone")),
            TextField(controller: displayName, decoration: InputDecoration(labelText: "Display Name")),

            if (selectedRole == "owner")
              TextField(controller: supplierName, decoration: InputDecoration(labelText: "Supplier Name")),

            if (selectedRole == "manager" || selectedRole == "sales")
              TextField(controller: supplierId, decoration: InputDecoration(labelText: "Supplier ID")),

            if (selectedRole == "consumer_contact")
              TextField(controller: consumerName, decoration: InputDecoration(labelText: "Consumer Name")),

            const SizedBox(height: 20),

            ElevatedButton(
              child: Text("Register"),
              onPressed: _register,
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _register() async {
    try {
      final result = await auth.register(
        username: username.text,
        password: password.text,
        email: email.text,
        phone: phone.text,
        displayName: displayName.text,
        role: selectedRole,
        supplierName: supplierName.text,
        supplierId: supplierId.text,
        consumerName: consumerName.text,
      );

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Success! Welcome ${result['username']}")),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error: $e")),
      );
    }
  }
}
