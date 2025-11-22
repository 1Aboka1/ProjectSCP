// lib/screens/home_screen.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../widgets/app_bottom_nav.dart';

// reuse existing screens (import them)
import 'products_screen.dart';
import 'conversations_screen.dart';
import 'my_profile_screen.dart';
import 'suppliers_list_screen.dart';
import 'cart_screen.dart';
import 'supplier_requests_screen.dart';
import 'orders_screen.dart';
import 'notifications_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _index = 0;

  List<Widget> _buildPages(String? role) {
    // Base pages (always)
    final List<Widget> pages = [
      // Products (shared)
      ProductsScreen(),
      // Chat
      ConversationsScreen(),
      // Me
      const MyProfilePage(),
    ];

    if (role == 'consumer_contact') {
      pages.addAll([
        SuppliersListScreen(),
        CartScreen(),
        SupplierRequestsScreen(),
      ]);
    } else if (role == 'owner' || role == 'manager' || role == 'sales') {
      pages.addAll([
        OrdersScreen(),
        NotificationsScreen(),
      ]);
    }
    return pages;
  }

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context);
    final role = auth.user?.role;

    final pages = _buildPages(role);

    // Ensure _index is in range (role may change)
    if (_index >= pages.length) {
      _index = 0;
    }

    return Scaffold(
      body: pages[_index],
      bottomNavigationBar: AppBottomNav(
        currentIndex: _index,
        onTabChanged: (i) => setState(() => _index = i),
      ),
    );
  }
}
