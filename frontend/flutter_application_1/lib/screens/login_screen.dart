// lib/screens/login_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_application_1/screens/register_screen.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';

class LoginScreen extends StatefulWidget {
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _userCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  bool _loading = false;
  String _error = "";

  @override
  Widget build(BuildContext ctx) {
    final auth = Provider.of<AuthProvider>(ctx, listen: false);

    return Scaffold(
      appBar: AppBar(title: Text("Sign in")),
      body: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: _userCtrl,
              decoration: InputDecoration(labelText: "Username"),
            ),
            TextField(
              controller: _passCtrl,
              decoration: InputDecoration(labelText: "Password"),
              obscureText: true,
            ),
            SizedBox(height: 16),
            if (_error.isNotEmpty)
              Text(_error, style: TextStyle(color: Colors.red)),
            ElevatedButton(
              child: _loading
                  ? CircularProgressIndicator(color: Colors.white)
                  : Text("Login"),
              onPressed: _loading
                  ? null
                  : () async {
                      setState(() {
                        _loading = true;
                        _error = "";
                      });
                      try {
                        final res = await auth.login(
                          _userCtrl.text.trim(),
                          _passCtrl.text.trim(),
                        );
                        if (!mounted) return;
                        setState(() {
                          _loading = false;
                        });

                        if (res['ok'] == true) {
                          Navigator.of(context).pushReplacementNamed("/");
                        } else {
                          if (!mounted) return;
                          setState(() {
                            _error = res['error'] ?? "Login failed";
                          });
                        }
                      } catch (e) {
                        print("Login exception: $e");
                        if (!mounted) return;
                        setState(() {
                          _loading = false;
                          _error = "Network error or server unreachable";
                        });
                      }
                    },
            ),
            TextButton(
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => RegisterScreen()),
                );
              },
              child: Text("Create an account"),
            ),
          ],
        ),
      ),
    );
  }
}
