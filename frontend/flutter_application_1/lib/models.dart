// lib/models.dart
import 'dart:convert';

class User {
  final String id;
  final String username;
  final String? email;
  final String? role;
  final String? displayName;
  final String? phone;
  final bool isActiveUser;

  User({
    required this.id,
    required this.username,
    this.email,
    this.role,
    this.displayName,
    this.phone,
    required this.isActiveUser,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json["id"],
      username: json["username"],
      email: json["email"],
      role: json["role"],
      displayName: json["display_name"],
      phone: json["phone"],
      isActiveUser: json["is_active_user"] ?? true,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'username': username,
      'display_name': displayName,
      'role': role,
    };
  }
}

// lib/models.dart
class Supplier {
  final String id;
  final String name;
  final String? legalName;
  final String? description;
  final String? country;
  final String? city;
  final String? address;
  final String? contactEmail;
  final String? contactPhone;
  final bool isVerified;
  final String verificationStatus;
  final String defaultCurrency;
  final List<String> languages;

  Supplier({
    required this.id,
    required this.name,
    this.legalName,
    this.description,
    this.country,
    this.city,
    this.address,
    this.contactEmail,
    this.contactPhone,
    this.isVerified = false,
    this.verificationStatus = "unsubmitted",
    this.defaultCurrency = "KZT",
    this.languages = const [],
  });

  factory Supplier.fromJson(Map<String, dynamic> json) {
    return Supplier(
      id: json['id'],
      name: json['name'],
      legalName: json['legal_name'],
      description: json['description'],
      country: json['country'],
      city: json['city'],
      address: json['address'],
      contactEmail: json['contact_email'],
      contactPhone: json['contact_phone'],
      isVerified: json['is_verified'] ?? false,
      verificationStatus: json['verification_status'] ?? "unsubmitted",
      defaultCurrency: json['default_currency'] ?? "KZT",
      languages: List<String>.from(json['languages'] ?? []),
    );
  }
}

class Consumer {
  final String id;
  final String name;
  final String consumerType;
  final String? address;
  final String? contactEmail;
  final String? contactPhone;

  Consumer({
    required this.id,
    required this.name,
    required this.consumerType,
    this.address,
    this.contactEmail,
    this.contactPhone,
  });

  factory Consumer.fromJson(Map<String, dynamic> json) {
    return Consumer(
      id: json['id'],
      name: json['name'],
      consumerType: json['consumer_type'],
      address: json['address'],
      contactEmail: json['contact_email'],
      contactPhone: json['contact_phone'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'consumer_type': consumerType,
      'address': address,
      'contact_email': contactEmail,
      'contact_phone': contactPhone,
    };
  }

  @override
  String toString() => name;
}

class Product {
  final int id;
  final String name;
  final String description;
  final double price;

  final double effectivePrice;
  final int minOrderQuantity;
  final int stock;
  final String supplierId;
  final String unit;

  Product({
    required this.id,
    required this.name,
    required this.description,
    required this.price,
    required this.effectivePrice,
    required this.minOrderQuantity,
    required this.stock,
    required this.unit,
    required this.supplierId,
  });

  factory Product.fromJson(Map<String, dynamic> json) {
    return Product(
      id: json['id'],
      name: json['name'],
      description: json['description'] ?? "",
      price: (json['price'] as num).toDouble(),

      effectivePrice: (json['effective_price'] as num).toDouble(),
      minOrderQuantity: json['min_order_quantity'] ?? 1,
      stock: json['stock'] ?? 1,
      unit: json['description'] ?? "",
      supplierId: json['supplier'].toString(),
    );
  }

  static List<Product> listFromJson(String body) {
    final decoded = jsonDecode(body);
    return List<Product>.from(decoded.map((e) => Product.fromJson(e)));
  }
}

class SupplierMini {
  final String id;
  final String? name;
  final bool? isVerified;
  SupplierMini({
    required this.id,
    this.name,
    this.isVerified,
  });

  factory SupplierMini.fromJson(dynamic json) {
    if (json == null) return SupplierMini(id: '', name: null);
    if (json is String) {
      return SupplierMini(id: json);
    }
    // json is Map
    return SupplierMini(
      id: json['id']?.toString() ?? '',
      name: json['name'],
      isVerified: json['is_verified'] == true || json['is_verified'] == 'true',
    );
  }
}

class SupplierConsumerLink {
  final String id;
  String status;
  final String supplierId;
  final SupplierMini? supplier; // may be null if backend returned only id
  final String consumerId;
  final String? requestedById; // id of user who requested
  final DateTime? createdAt;
  final String? note;
  final String? approvedById;
  final DateTime? approvedAt;
  final String? blockedById;
  final DateTime? blockedAt;

  SupplierConsumerLink({
    required this.id,
    required this.status,
    required this.supplierId,
    required this.consumerId,
    this.supplier,
    this.requestedById,
    this.createdAt,
    this.note,
    this.approvedById,
    this.approvedAt,
    this.blockedById,
    this.blockedAt,
  });

  factory SupplierConsumerLink.fromJson(Map<String, dynamic> json) {
    // supplier may be nested or string id
    final supplierField = json['supplier'];
    final supplierMini = supplierField != null ? SupplierMini.fromJson(supplierField) : null;
    return SupplierConsumerLink(
      id: json['id'].toString(),
      status: json['status']?.toString() ?? '',
      supplierId: supplierField is String ? supplierField : (supplierMini?.id ?? ''),
      consumerId: json['consumer']?.toString() ?? '',
      supplier: supplierMini,
      requestedById: json['requested_by']?.toString(),
      createdAt: json['created_at'] != null ? DateTime.tryParse(json['created_at']) : null,
      note: json['note']?.toString(),
      approvedById: json['approved_by']?.toString(),
      approvedAt: json['approved_at'] != null ? DateTime.tryParse(json['approved_at']) : null,
      blockedById: json['blocked_by']?.toString(),
      blockedAt: json['blocked_at'] != null ? DateTime.tryParse(json['blocked_at']) : null,
    );
  }
}

class OrderItem {
  final String id;
  final Product product;
  final double quantity;
  final double unitPrice;
  final double lineTotal;
  final String? note;
  final bool isAccepted;
  final bool isCancelled;

  OrderItem({
    required this.id,
    required this.product,
    required this.quantity,
    required this.unitPrice,
    required this.lineTotal,
    this.note,
    required this.isAccepted,
    required this.isCancelled,
  });

  factory OrderItem.fromJson(Map<String, dynamic> json) {
    return OrderItem(
      id: json['id'] ?? '',
      product: Product.fromJson(json['product']),
      quantity: (json['quantity'] as num).toDouble(),
      unitPrice: (json['unit_price'] as num).toDouble(),
      lineTotal: (json['line_total'] as num).toDouble(),
      note: json['note'],
      isAccepted: json['is_accepted'] ?? false,
      isCancelled: json['is_cancelled'] ?? false,
    );
  }
}

class Order {
  final String id;
  final String status;
  final String? note;
  final double totalAmount;
  final DateTime createdAt;
  final DateTime? acceptedAt;
  final DateTime? completedAt;
  final String? trackingCode;
  final DateTime? estimatedDelivery;
  final String supplierName;
  final String consumerName;
  final List<OrderItem> items;

  Order({
    required this.id,
    required this.status,
    this.note,
    required this.totalAmount,
    required this.createdAt,
    this.acceptedAt,
    this.completedAt,
    this.trackingCode,
    this.estimatedDelivery,
    required this.supplierName,
    required this.consumerName,
    required this.items,
  });

  factory Order.fromJson(Map<String, dynamic> json) {
    final itemsJson = (json['items'] as List<dynamic>?) ?? [];
    return Order(
      id: json['id'],
      status: json['status'],
      note: json['note'],
      totalAmount: (json['total_amount'] as num).toDouble(),
      createdAt: DateTime.parse(json['created_at']),
      acceptedAt: json['accepted_at'] != null
          ? DateTime.tryParse(json['accepted_at'])
          : null,
      completedAt: json['completed_at'] != null
          ? DateTime.tryParse(json['completed_at'])
          : null,
      trackingCode: json['tracking_code'],
      estimatedDelivery: json['estimated_delivery'] != null
          ? DateTime.tryParse(json['estimated_delivery'])
          : null,
      supplierName: json['supplier']['name'],
      consumerName: json['consumer']['name'],
      items: itemsJson.map((i) => OrderItem.fromJson(i)).toList(),
    );
  }
}

class Conversation {
  final String id;
  final String? complaintId;
  // note: supplier_staff & consumer_contact are nested; UI uses display only
  Conversation({required this.id, this.complaintId});
  factory Conversation.fromJson(Map<String, dynamic> j) => Conversation(
    id: j['id'].toString(),
    complaintId: j['complaint']?.toString(),
  );
}

class MessageModel {
  final String id;
  final String senderId;
  final String text;
  final String createdAt;
  final bool isRead;
  MessageModel({
    required this.id,
    required this.senderId,
    required this.text,
    required this.createdAt,
    required this.isRead,
  });
  factory MessageModel.fromJson(Map<String, dynamic> j) => MessageModel(
    id: j['id'].toString(),
    senderId: j['sender'] is Map
        ? j['sender']['id'].toString()
        : (j['sender']?.toString() ?? ''),
    text: j['text'] ?? '',
    createdAt: j['created_at'] ?? '',
    isRead: j['is_read'] ?? false,
  );
}
