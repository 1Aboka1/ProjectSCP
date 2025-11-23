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
  final _scrollController = ScrollController();
  bool loading = true;

  @override
  void initState() {
    super.initState();
    fetchMessages();
  }

  Future<void> fetchMessages() async {
    setState(() => loading = true);

    final resp = await ApiService.get(
      "conversations/${widget.conversation.id}/",
    );
    if (resp.statusCode == 200) {
      final jsonMap = jsonDecode(resp.body) as Map<String, dynamic>;
      final messagesJson = (jsonMap['messages'] as List<dynamic>?) ?? [];
      messages = messagesJson.map((e) => MessageModel.fromJson(e)).toList();
    } else {
      messages = [];
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Failed to fetch messages: ${resp.statusCode}")),
      );
    }

    setState(() => loading = false);
    WidgetsBinding.instance.addPostFrameCallback((_) => _scrollToBottom());
  }

  Future<void> sendMessage(String text) async {
    if (text.trim().isEmpty) return;
    final resp = await ApiService.post(
      "conversations/${widget.conversation.id}/send_message/",
      {"text": text},
    );
    if (resp.statusCode == 200 || resp.statusCode == 201) {
      await fetchMessages();
      _controller.clear();
    } else {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text("Failed to send: ${resp.body}")));
    }
  }

  Future<void> escalateComplaint() async {
    if (widget.conversation.complaintId == null) return;
    final resp = await ApiService.post(
      "complaints/${widget.conversation.complaintId}/escalate/",
      {},
    );
    if (resp.statusCode == 200) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Complaint escalated successfully")),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Failed to escalate: ${resp.body}")),
      );
    }
  }

  Future<void> resolveComplaint() async {
    if (widget.conversation.complaintId == null) return;

    String resolution = "";
    final resolved = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Resolve Complaint"),
        content: TextField(
          onChanged: (v) => resolution = v,
          decoration: const InputDecoration(
            hintText: "Enter resolution details",
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text("Cancel"),
          ),
          ElevatedButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text("Resolve"),
          ),
        ],
      ),
    );

    if (resolved == true && resolution.trim().isNotEmpty) {
      final resp = await ApiService.post(
        "complaints/${widget.conversation.complaintId}/resolve/",
        {"resolution": resolution.trim()},
      );
      if (resp.statusCode == 200 ||
          resp.statusCode == 202 ||
          resp.statusCode == 204) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Complaint resolved successfully")),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Failed to resolve: ${resp.body}")),
        );
      }
    }
  }

  void _scrollToBottom() {
    if (_scrollController.hasClients) {
      _scrollController.jumpTo(_scrollController.position.maxScrollExtent);
    }
  }

  @override
  Widget build(BuildContext ctx) {
    final auth = Provider.of<AuthProvider>(ctx);
    final userRole = auth.user?.role ?? "";
    final userId = auth.user?.id ?? "";
    final isSupplierStaff = ["owner", "manager", "sales"].contains(userRole);

    return Scaffold(
      appBar: AppBar(title: const Text("Chat")),
      body: Column(
        children: [
          if (isSupplierStaff && widget.conversation.complaintId != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              child: Row(
                children: [
                  ElevatedButton(
                    onPressed: escalateComplaint,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.orange,
                    ),
                    child: const Text("Escalate"),
                  ),
                  const SizedBox(width: 10),
                  ElevatedButton(
                    onPressed: resolveComplaint,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green,
                    ),
                    child: const Text("Resolve"),
                  ),
                ],
              ),
            ),
          Expanded(
            child: loading
                ? const Center(child: CircularProgressIndicator())
                : ListView.builder(
                    controller: _scrollController,
                    itemCount: messages.length,
                    itemBuilder: (ctx, i) {
                      final m = messages[i];
                      final isMe = m.senderId == userId;
                      return Container(
                        alignment: isMe
                            ? Alignment.centerRight
                            : Alignment.centerLeft,
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 4,
                        ),
                        child: Column(
                          crossAxisAlignment: isMe
                              ? CrossAxisAlignment.end
                              : CrossAxisAlignment.start,
                          children: [
                            // Sender name
                            Text(
                              m.senderName ?? (isMe ? "You" : "Unknown"),
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.bold,
                                color: Colors.grey[700],
                              ),
                            ),
                            const SizedBox(height: 2),
                            // Message bubble
                            Container(
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: isMe ? Colors.blue : Colors.grey[300],
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Text(
                                m.text,
                                style: TextStyle(
                                  color: isMe ? Colors.white : Colors.black,
                                ),
                              ),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
          ),

          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    decoration: const InputDecoration(hintText: "Message"),
                  ),
                ),
                IconButton(
                  onPressed: () => sendMessage(_controller.text),
                  icon: const Icon(Icons.send),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
