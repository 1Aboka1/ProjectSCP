// lib/screens/conversations_screen.dart
import 'dart:convert';
import 'package:flutter/material.dart';
import '../api_service.dart';
import '../models.dart';
import 'chat_screen.dart';

class ConversationsScreen extends StatefulWidget {
  @override
  State<ConversationsScreen> createState() => _ConversationsScreenState();
}

class _ConversationsScreenState extends State<ConversationsScreen> {
  bool loading = true;
  List<Conversation> convs = [];

  @override
  void initState() {
    super.initState();
    fetch();
  }

  Future<void> fetch() async {
    setState(() => loading = true);
    final resp = await ApiService.get("conversations/");
    if (resp.statusCode == 200) {
      final arr = jsonDecode(resp.body) as List;
      convs = arr.map((e) => Conversation.fromJson(e)).toList();
    } else convs = [];
    setState(() => loading = false);
  }

  @override
  Widget build(BuildContext ctx) {
    return Scaffold(
      appBar: AppBar(title: Text("Conversations")),
      body: loading ? Center(child: CircularProgressIndicator()) : ListView.builder(
        itemCount: convs.length,
        itemBuilder: (c, i) => ListTile(
          title: Text("Conversation ${convs[i].id}"),
          subtitle: Text("Complaint: ${convs[i].complaintId ?? '—'}"),
          onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => ChatScreen(conversation: convs[i]))),
        ),
      ),
    );
  }
}
