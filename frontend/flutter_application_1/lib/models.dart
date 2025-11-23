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
  final String id;
  final String name;
  final String? description;

  final double price;
  final double? discountPercentage; // nullable, percent like 12.5
  final double effectivePrice; // final computed or taken from backend

  final int minOrderQuantity; // stored as int in frontend (no fractional UI)
  final double stock; // allow fractional stock (kg, liters etc.)
  final String unit;

  final String supplierId;
  final String? categoryId;

  final bool isActive;
  final String deliveryOption; // "delivery" / "pickup" / "both"
  final int leadTimeDays;

  final String? imageUrl;

  final DateTime? createdAt;
  final DateTime? updatedAt;

  Product({
    required this.id,
    required this.name,
    this.description,
    required this.price,
    this.discountPercentage,
    required this.effectivePrice,
    required this.minOrderQuantity,
    required this.stock,
    required this.unit,
    required this.supplierId,
    this.categoryId,
    required this.isActive,
    required this.deliveryOption,
    required this.leadTimeDays,
    this.imageUrl,
    this.createdAt,
    this.updatedAt,
  });

  // Helper converters: accept numbers or numeric strings
  static double _toDouble(dynamic v, {double fallback = 0.0}) {
    if (v == null) return fallback;
    if (v is double) return v;
    if (v is int) return v.toDouble();
    if (v is String) {
      return double.tryParse(v) ?? fallback;
    }
    return fallback;
  }

  static int _toInt(dynamic v, {int fallback = 0}) {
    if (v == null) return fallback;
    if (v is int) return v;
    if (v is double) return v.toInt();
    if (v is String) {
      return int.tryParse(v) ?? fallback;
    }
    return fallback;
  }

  factory Product.fromJson(Map<String, dynamic> json) {
    // id might be a UUID string
    final id = (json['id'] ?? json['uuid'] ?? '').toString();

    final price = _toDouble(json['price'], fallback: 0.0);
    final discount = json.containsKey('discount_percentage')
        ? _toDouble(json['discount_percentage'], fallback: 0.0)
        : (json.containsKey('discount')
              ? _toDouble(json['discount'], fallback: 0.0)
              : null);

    // If backend provides effective_price use it; otherwise compute
    double effective;
    if (json.containsKey('effective_price') &&
        json['effective_price'] != null) {
      effective = _toDouble(json['effective_price'], fallback: price);
    } else if (discount != null && discount != 0.0) {
      effective = price * (1.0 - (discount / 100.0));
    } else {
      effective = price;
    }

    // supplier may be object or id
    String supplierId;
    if (json['supplier'] is Map) {
      supplierId =
          (json['supplier']['id'] ??
                  json['supplier']['pk'] ??
                  json['supplier']['uuid'] ??
                  '')
              .toString();
    } else {
      supplierId = json['supplier']?.toString() ?? '';
    }

    // category may be object or id
    String? categoryId;
    if (json['category'] is Map) {
      categoryId =
          (json['category']['id'] ??
                  json['category']['uuid'] ??
                  json['category']['pk'])
              ?.toString();
    } else if (json['category'] != null) {
      categoryId = json['category'].toString();
    } else {
      categoryId = null;
    }

    String unit = (json['unit'] ?? '').toString();

    final stock = _toDouble(json['stock'], fallback: 0.0);
    final minOrderQuantity = _toInt(
      json['min_order_quantity'] ?? json['min_order_qty'] ?? 1,
      fallback: 1,
    );

    final isActive = json['is_active'] == null
        ? true
        : (json['is_active'] == true || json['is_active'].toString() == 'True');

    final deliveryOption = (json['delivery_option'] ?? 'both').toString();
    final leadTimeDays = _toInt(
      json['lead_time_days'] ?? json['lead_time'] ?? 0,
      fallback: 0,
    );

    final imageUrl = json['image'] is String
        ? json['image'] as String
        : (json['image'] is Map ? json['image']['url'] : null);

    DateTime? parseDate(dynamic d) {
      if (d == null) return null;
      if (d is DateTime) return d;
      if (d is String) return DateTime.tryParse(d);
      return null;
    }

    return Product(
      id: id,
      name: (json['name'] ?? '').toString(),
      description: json['description']?.toString(),
      price: price,
      discountPercentage: discount,
      effectivePrice: effective,
      minOrderQuantity: minOrderQuantity,
      stock: stock,
      unit: unit.isNotEmpty ? unit : 'pcs',
      supplierId: supplierId,
      categoryId: categoryId,
      isActive: isActive,
      deliveryOption: deliveryOption,
      leadTimeDays: leadTimeDays,
      imageUrl: imageUrl,
      createdAt: parseDate(json['created_at']),
      updatedAt: parseDate(json['updated_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'description': description,
      'price': price,
      'discount_percentage': discountPercentage,
      'effective_price': effectivePrice,
      'min_order_quantity': minOrderQuantity,
      'stock': stock,
      'unit': unit,
      'supplier': supplierId,
      'category': categoryId,
      'is_active': isActive,
      'delivery_option': deliveryOption,
      'lead_time_days': leadTimeDays,
      'image': imageUrl,
    };
  }

  static List<Product> listFromJson(String body) {
    final decoded = jsonDecode(body);
    if (decoded is List) {
      return decoded.map<Product>((e) {
        if (e is String) {
          // backend sometimes returns a list of ids — handle defensively
          return Product.fromJson({'id': e, 'name': e, 'price': 0});
        }
        return Product.fromJson(e as Map<String, dynamic>);
      }).toList();
    } else if (decoded is Map && decoded['results'] is List) {
      // paginated DRF results
      return (decoded['results'] as List)
          .map((e) => Product.fromJson(e as Map<String, dynamic>))
          .toList();
    } else {
      return [];
    }
  }
}

class SupplierMini {
  final String id;
  final String? name;
  final bool? isVerified;
  SupplierMini({required this.id, this.name, this.isVerified});

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
    final supplierMini = supplierField != null
        ? SupplierMini.fromJson(supplierField)
        : null;
    return SupplierConsumerLink(
      id: json['id'].toString(),
      status: json['status']?.toString() ?? '',
      supplierId: supplierField is String
          ? supplierField
          : (supplierMini?.id ?? ''),
      consumerId: json['consumer']?.toString() ?? '',
      supplier: supplierMini,
      requestedById: json['requested_by']?.toString(),
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'])
          : null,
      note: json['note']?.toString(),
      approvedById: json['approved_by']?.toString(),
      approvedAt: json['approved_at'] != null
          ? DateTime.tryParse(json['approved_at'])
          : null,
      blockedById: json['blocked_by']?.toString(),
      blockedAt: json['blocked_at'] != null
          ? DateTime.tryParse(json['blocked_at'])
          : null,
    );
  }
}

class OrderItem {
  final String id;
  final String product;
  final double quantity;
  final double unitPrice;
  String? productName;
  final double lineTotal;
  final String? note;
  final bool? isAccepted;
  final bool? isCancelled;

  OrderItem({
    required this.id,
    required this.product,
    required this.quantity,
    required this.unitPrice,
    required this.lineTotal,
    this.note,
    this.productName,
    this.isAccepted,
    this.isCancelled,
  });

  factory OrderItem.fromJson(Map<String, dynamic> json) {
    return OrderItem(
      id: json['id'] ?? '',
      product: json['product'],
      quantity: _parseDouble(json['quantity']),
      unitPrice: _parseDouble(json['unit_price']),
      lineTotal: _parseDouble(json['line_total']),
      note: json['note'],
      isAccepted: json['is_accepted'] ?? true,
      isCancelled: json['is_cancelled'] ?? false,
    );
  }
}

double _parseDouble(dynamic value) {
  if (value == null) return 0.0;

  if (value is num) return value.toDouble();

  if (value is String) return double.tryParse(value) ?? 0.0;

  throw Exception("Cannot parse $value to double");
}

class Order {
  final String id;
  String status;
  final String? note;
  final double totalAmount;
  final DateTime createdAt;
  final DateTime? acceptedAt;
  final DateTime? completedAt;
  final String? trackingCode;
  final DateTime? estimatedDelivery;
  final String supplierId;
  final String consumerId;
  final List<OrderItem> items;
  final String placedBy;

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
    required this.supplierId,
    required this.consumerId,
    required this.items,
    required this.placedBy,
  });

  factory Order.fromJson(Map<String, dynamic> json) {
    final itemsJson = (json['items'] as List<dynamic>?) ?? [];
    return Order(
      id: json['id'],
      status: json['status'],
      note: json['note'],
      totalAmount: _parseDouble(json['total_amount']),
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
      supplierId: json['supplier'],
      consumerId: json['consumer'],
      items: itemsJson.map((i) => OrderItem.fromJson(i)).toList(),
      placedBy: json['placed_by'],
    );
  }
}

class SupplierStaffMembership {
  final String id; // optional, if backend sends it
  final String supplierId;
  final User user; // nested user object
  final String role; // "owner", "manager", "sales"
  final bool isActive;

  SupplierStaffMembership({
    required this.id,
    required this.supplierId,
    required this.user,
    required this.role,
    required this.isActive,
  });

  factory SupplierStaffMembership.fromJson(Map<String, dynamic> json) {
    return SupplierStaffMembership(
      id: json['id']?.toString() ?? '',
      supplierId: json['supplier']?.toString() ?? '',
      user: User.fromJson(json['user'] ?? {}),
      role: json['role'] ?? '',
      isActive: json['is_active'] ?? false,
    );
  }
}

class ConsumerContact {
  final String id;
  final String consumerId;
  final User user;
  final String? title;
  final bool isPrimary;

  ConsumerContact({
    required this.id,
    required this.consumerId,
    required this.user,
    this.title,
    required this.isPrimary,
  });

  factory ConsumerContact.fromJson(Map<String, dynamic> json) {
    return ConsumerContact(
      id: json['id']?.toString() ?? '',
      consumerId: json['consumer']?.toString() ?? '',
      user: User.fromJson(json['user'] ?? {}),
      title: json['title'],
      isPrimary: json['is_primary'] ?? false,
    );
  }
}

class Conversation {
  final String id;
  final String? complaintId;
  final List<String> supplierStaffIds; // list of supplier staff user IDs
  final String consumerId; // consumer user ID
  String? status;

  Conversation({
    required this.id,
    required this.consumerId,
    this.complaintId,
    required this.supplierStaffIds,
    this.status,
  });

  factory Conversation.fromJson(Map<String, dynamic> json) {
    List<String> staffIds = [];
    if (json['supplier_staff'] != null && json['supplier_staff'] is List) {
      staffIds = (json['supplier_staff'] as List)
          .map((e) => e.toString())
          .toList();
    }

    return Conversation(
      id: json['id'].toString(),
      complaintId: json['complaint']?.toString(),
      consumerId: json['consumer_contact'].toString(),
      supplierStaffIds: staffIds,
    );
  }
}

class MessageModel {
  final String id;
  final String senderId;
  final String text;
  final bool isRead;
  final String senderName;

  MessageModel({
    required this.id,
    required this.senderId,
    required this.text,
    required this.isRead,
    required this.senderName,
  });

  factory MessageModel.fromJson(Map<String, dynamic> json) {
    String senderId = '';
    if (json['sender'] != null) {
      senderId = json['sender'] is String
          ? json['sender']
          : json['sender']['id'].toString();
    }

    return MessageModel(
      id: json['id'].toString(),
      senderId: senderId,
      text: json['text'] ?? '',
      isRead: json['is_read'] ?? false,
      senderName: json['sender_name'] ?? '',
    );
  }
}
