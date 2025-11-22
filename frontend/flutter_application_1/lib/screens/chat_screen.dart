// lib/screens/chat_screen.dart
import 'dart:convert';
import 'package:flutter/material.dart';
import '../models.dart';
import '../api_service.dart';
import '../providers/auth_provider.dart';
import 'package:provider/provider.dart';

class ChatScreen extends StatefulWidget {
  final Conversation conversation;
  ChatScreen({required this.conversation});
  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  List<MessageModel> messages = [];
  final _controller = TextEditingController();
  bool loading = true;

  @override
  void initState() {
    super.initState();
    fetchMessages();
  }

  Future<void> fetchMessages() async {
    setState(() => loading = true);
    final resp = await ApiService.get("conversations/${widget.conversation.id}/messages/");
    if (resp.statusCode == 200) {
      final arr = jsonDecode(resp.body) as List;
      messages = arr.map((e) => MessageModel.fromJson(e)).toList();
    } else {
      messages = [];
    }
    setState(() => loading = false);
  }

  Future<void> sendMessage(String text) async {
    if (text.trim().isEmpty) return;
    final resp = await ApiService.post("conversations/${widget.conversation.id}/send_message/", {"text": text});
    if (resp.statusCode == 200 || resp.statusCode == 201) {
      await fetchMessages();
      _controller.clear();
    } else {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Failed to send: ${resp.body}")));
    }
  }

  @override
  Widget build(BuildContext ctx) {
    final auth = Provider.of<AuthProvider>(ctx);
    return Scaffold(
      appBar: AppBar(title: Text("Chat")),
      body: Column(
        children: [
          Expanded(child: loading ? Center(child: CircularProgressIndicator()) : ListView(
            children: messages.map((m) => ListTile(
              title: Text(m.text),
              subtitle: Text("${m.senderId} • ${m.createdAt}"),
              trailing: m.isRead ? Icon(Icons.check) : null,
            )).toList(),
          )),
          Padding(
            padding: EdgeInsets.symmetric(horizontal: 8, vertical: 6),
            child: Row(
              children: [
                Expanded(child: TextField(controller: _controller, decoration: InputDecoration(hintText: "Message"))),
                IconButton(onPressed: () => sendMessage(_controller.text), icon: Icon(Icons.send))
              ],
            ),
          )
        ],
      ),
    );
  }
}
