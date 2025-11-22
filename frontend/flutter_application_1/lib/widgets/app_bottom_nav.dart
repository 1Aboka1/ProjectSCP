// lib/widgets/app_bottom_nav.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';

typedef OnTabChanged = void Function(int index);

class AppBottomNav extends StatelessWidget {
  final OnTabChanged onTabChanged;
  final int currentIndex;

  const AppBottomNav({
    Key? key,
    required this.onTabChanged,
    required this.currentIndex,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context, listen: true);
    final role = auth.user?.role;

    // Base tabs (visible for everyone)
    final List<BottomNavigationBarItem> baseItems = [
      BottomNavigationBarItem(icon: Icon(Icons.list_alt), label: 'Products'),
      BottomNavigationBarItem(icon: Icon(Icons.chat_bubble_outline), label: 'Chat'),
      BottomNavigationBarItem(icon: Icon(Icons.person_outline), label: 'Me'),
    ];

    // Role-specific items appended after baseItems
    List<BottomNavigationBarItem> roleItems = [];

    if (role == 'consumer_contact') {
      roleItems = [
        BottomNavigationBarItem(icon: Icon(Icons.store), label: 'Suppliers'),
        BottomNavigationBarItem(icon: Icon(Icons.shopping_cart), label: 'Cart'),
        BottomNavigationBarItem(icon: Icon(Icons.link), label: 'Requests'),
      ];
    } else if (role == 'owner' || role == 'manager' || role == 'sales') {
      roleItems = [
        BottomNavigationBarItem(icon: Icon(Icons.receipt_long), label: 'Orders'),
        BottomNavigationBarItem(icon: Icon(Icons.notifications_none), label: 'Notifications'),
      ];
    }

    final items = [...baseItems, ...roleItems];

    return BottomNavigationBar(
      currentIndex: currentIndex,
      type: BottomNavigationBarType.fixed,
      items: items,
      onTap: onTabChanged,
    );
  }
}
