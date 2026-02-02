import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { Avatar, AvatarFallback } from "../components/ui/avatar";
import { ScrollArea } from "../components/ui/scroll-area";
import { toast } from "sonner";
import { Search, Send, Phone, MessageSquare, Sparkles, User as UserIcon, Clock, AlertTriangle, CheckCircle2 } from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Status badge helper
const getStatusBadge = (conv) => {
  const status = conv.status?.toLowerCase();
  
  if (status === "waiting_for_owner" || status === "escalated") {
    // Check if overdue (past SLA deadline)
    const isOverdue = conv.sla_deadline && new Date(conv.sla_deadline) < new Date();
    
    if (isOverdue) {
      return (
        <Badge variant="destructive" className="text-xs flex items-center gap-1">
          <AlertTriangle className="w-3 h-3" />
          OVERDUE
        </Badge>
      );
    }
    return (
      <Badge variant="outline" className="text-xs text-orange-500 border-orange-500 flex items-center gap-1">
        <Clock className="w-3 h-3" />
        WAITING
      </Badge>
    );
  }
  
  if (status === "active") {
    return (
      <Badge variant="outline" className="text-xs text-green-500 border-green-500 flex items-center gap-1">
        <CheckCircle2 className="w-3 h-3" />
        ACTIVE
      </Badge>
    );
  }
  
  return null;
};

const ConversationsPage = () => {
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [messageInput, setMessageInput] = useState("");
  const [sending, setSending] = useState(false);
  const [search, setSearch] = useState("");
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchConversations();
  }, []);

  useEffect(() => {
    if (selectedConversation) {
      fetchMessages(selectedConversation.id);
    }
  }, [selectedConversation]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const fetchConversations = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/conversations`);
      setConversations(response.data);
      if (response.data.length > 0 && !selectedConversation) {
        setSelectedConversation(response.data[0]);
      }
    } catch (error) {
      toast.error("Failed to load conversations");
    } finally {
      setLoading(false);
    }
  };

  const fetchMessages = async (conversationId) => {
    try {
      const response = await axios.get(`${API_URL}/api/conversations/${conversationId}/messages`);
      setMessages(response.data);
    } catch (error) {
      toast.error("Failed to load messages");
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!messageInput.trim() || !selectedConversation) return;

    setSending(true);
    const userMessage = messageInput;
    setMessageInput("");

    try {
      // Extract phone number from conversation - clean it
      let phone = selectedConversation.customer_phone?.replace(/[^0-9]/g, '') || '';
      
      // Ensure phone is properly formatted (last 10 digits with 91 prefix)
      if (phone.length > 10) {
        phone = '91' + phone.slice(-10);
      } else if (phone.length === 10) {
        phone = '91' + phone;
      }
      
      // Send to WhatsApp first
      if (phone && phone.length >= 12) {
        try {
          await axios.post(`${API_URL}/api/whatsapp/send?phone=${encodeURIComponent(phone)}&message=${encodeURIComponent(userMessage)}`);
          toast.success("Message sent to WhatsApp");
        } catch (waError) {
          console.error("WhatsApp send failed:", waError);
          toast.error("WhatsApp send failed - message saved locally");
        }
      } else {
        toast.warning("Invalid phone number - message saved locally only");
      }

      // Save message to database
      await axios.post(`${API_URL}/api/conversations/${selectedConversation.id}/messages`, {
        conversation_id: selectedConversation.id,
        content: userMessage,
        sender_type: "agent",
        message_type: "text",
      });

      fetchMessages(selectedConversation.id);
      fetchConversations();
    } catch (error) {
      toast.error("Failed to send message");
    } finally {
      setSending(false);
    }
  };

  const filteredConversations = conversations.filter(
    (conv) =>
      conv.customer_name?.toLowerCase().includes(search.toLowerCase()) ||
      conv.customer_phone?.includes(search)
  );

  const formatTime = (dateString) => {
    if (!dateString) return "";
    const date = new Date(dateString);
    return date.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex gap-6 animate-in">
      {/* Conversations List */}
      <Card className="w-full md:w-96 flex-shrink-0 border-border/50 flex flex-col">
        <CardHeader className="py-4 px-4 border-b border-border">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search conversations..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10"
              data-testid="conversation-search"
            />
          </div>
        </CardHeader>
        <CardContent className="p-0 flex-1 overflow-hidden">
          <ScrollArea className="h-full">
            {loading ? (
              <div className="p-4 space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="skeleton-pulse h-20 rounded" />
                ))}
              </div>
            ) : filteredConversations.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
                <MessageSquare className="w-12 h-12 mb-3 opacity-50" />
                <p>No conversations yet</p>
              </div>
            ) : (
              <div className="divide-y divide-border">
                {filteredConversations.map((conv) => (
                  <div
                    key={conv.id}
                    onClick={() => setSelectedConversation(conv)}
                    className={`flex items-start gap-3 p-4 cursor-pointer transition-colors hover:bg-accent ${
                      selectedConversation?.id === conv.id ? "bg-primary/5 border-l-2 border-primary" : ""
                    }`}
                    data-testid={`conversation-item-${conv.id}`}
                  >
                    <Avatar className="w-12 h-12 flex-shrink-0">
                      <AvatarFallback className="bg-[#25D366]/10 text-[#25D366]">
                        {conv.customer_name?.charAt(0)?.toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className="font-semibold truncate">{conv.customer_name}</p>
                        <span className="text-xs text-muted-foreground">
                          {formatTime(conv.last_message_at)}
                        </span>
                      </div>
                      <p className="text-sm text-muted-foreground truncate mt-1">
                        {conv.last_message || "No messages"}
                      </p>
                      <div className="flex items-center gap-2 mt-2 flex-wrap">
                        <Badge variant="outline" className="text-xs text-[#25D366]">
                          WhatsApp
                        </Badge>
                        {getStatusBadge(conv)}
                        {conv.unread_count > 0 && (
                          <Badge className="bg-primary text-xs">{conv.unread_count}</Badge>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Chat Area */}
      <Card className="flex-1 border-border/50 flex flex-col min-w-0 hidden md:flex">
        {selectedConversation ? (
          <>
            <CardHeader className="py-4 px-6 border-b border-border flex-shrink-0">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Avatar className="w-10 h-10">
                    <AvatarFallback className="bg-[#25D366]/10 text-[#25D366]">
                      {selectedConversation.customer_name?.charAt(0)?.toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <h3 className="font-semibold">{selectedConversation.customer_name}</h3>
                    <p className="text-sm text-muted-foreground flex items-center gap-1">
                      <Phone className="w-3 h-3" />
                      {selectedConversation.customer_phone}
                    </p>
                  </div>
                </div>
                {/* Status indicator */}
                <div className="flex items-center gap-2">
                  {getStatusBadge(selectedConversation)}
                  {selectedConversation.escalation_reason && (
                    <span className="text-xs text-muted-foreground max-w-[200px] truncate" title={selectedConversation.escalation_reason}>
                      {selectedConversation.escalation_reason}
                    </span>
                  )}
                </div>
              </div>
            </CardHeader>

            <CardContent className="flex-1 p-6 overflow-hidden">
              <ScrollArea className="h-full pr-4">
                <div className="space-y-4">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${
                        message.sender_type === "customer" ? "justify-start" : "justify-end"
                      }`}
                    >
                      <div
                        className={`max-w-[70%] p-3 rounded-xl ${
                          message.sender_type === "customer"
                            ? "bg-slate-100 dark:bg-slate-800 rounded-bl-none"
                            : message.sender_type === "ai"
                            ? "bg-primary/10 dark:bg-primary/20 rounded-br-none"
                            : "bg-emerald-100 dark:bg-emerald-900/30 rounded-br-none"
                        }`}
                        data-testid={`message-${message.id}`}
                      >
                        {message.sender_type === "ai" && (
                          <div className="flex items-center gap-1 text-xs text-primary mb-1">
                            <Sparkles className="w-3 h-3" />
                            AI Response
                          </div>
                        )}
                        {(message.sender_type === "human" || message.sender_type === "agent") && (
                          <div className="flex items-center gap-1 text-xs text-emerald-600 dark:text-emerald-400 mb-1">
                            <UserIcon className="w-3 h-3" />
                            Human Agent
                          </div>
                        )}
                        <p className="whitespace-pre-wrap">{message.content}</p>
                        <p className="text-xs text-muted-foreground mt-1 text-right">
                          {formatTime(message.created_at)}
                        </p>
                      </div>
                    </div>
                  ))}
                  <div ref={messagesEndRef} />
                </div>
              </ScrollArea>
            </CardContent>

            <div className="p-4 bg-card border-t border-border">
              <form onSubmit={handleSendMessage} className="flex items-center gap-3">
                <Input
                  placeholder="Type a message..."
                  value={messageInput}
                  onChange={(e) => setMessageInput(e.target.value)}
                  className="flex-1"
                  disabled={sending}
                  data-testid="message-input"
                />
                <Button
                  type="submit"
                  className="btn-primary"
                  disabled={sending || !messageInput.trim()}
                  data-testid="send-message-btn"
                >
                  {sending ? (
                    <div className="ai-thinking">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  ) : (
                    <Send className="w-5 h-5" />
                  )}
                </Button>
              </form>
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground">
            <MessageSquare className="w-16 h-16 mb-4 opacity-50" />
            <p className="text-lg font-medium">Select a conversation</p>
            <p className="text-sm">Choose from the list to view messages</p>
          </div>
        )}
      </Card>
    </div>
  );
};

export default ConversationsPage;
