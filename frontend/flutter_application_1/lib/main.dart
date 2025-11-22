import 'package:flutter/material.dart';
import 'package:flutter_application_1/screens/home_screen.dart';
import 'package:flutter_application_1/screens/login_screen.dart';
import 'package:flutter_application_1/providers/auth_provider.dart';
import 'package:flutter_application_1/providers/cart_provider.dart';
import 'package:provider/provider.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  final appTitle = "SCP Mobile";

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => CartProvider()),
      ],
      child: MaterialApp(
        title: appTitle,
        theme: ThemeData(primarySwatch: Colors.teal),
        home: HomeDecider(),
        routes: {
          "/login": (_) => LoginScreen(),
        },
      ),
    );
  }
}

class HomeDecider extends StatefulWidget {
  @override
  _HomeDeciderState createState() => _HomeDeciderState();
}

class _HomeDeciderState extends State<HomeDecider> {
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _initAuth();
  }

  Future<void> _initAuth() async {
    final auth = Provider.of<AuthProvider>(context, listen: false);
    await auth.loadFromStorage();
    if (!mounted) return;
    setState(() {
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context);

    if (_loading || auth.loading) {
      // Show loading until user data is loaded
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    if (auth.user == null) {
      // Not logged in → show login
      return LoginScreen();
    }

    // Logged in → show main HomeScreen with bottom nav
    return const HomeScreen();
  }
}
