import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { Avatar, AvatarFallback } from "../components/ui/avatar";
import { ScrollArea } from "../components/ui/scroll-area";
import { Separator } from "../components/ui/separator";
import { toast } from "sonner";
import {
  Search,
  Send,
  Paperclip,
  Phone,
  MoreVertical,
  Bot,
  User as UserIcon,
  AlertCircle,
  Sparkles,
  X,
  MessageSquare,
} from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const TopicTypeColors = {
  product_inquiry: "topic-pill product_inquiry",
  service_request: "topic-pill service_request",
  support: "topic-pill support",
  order: "topic-pill order",
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
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

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
      // Send human message
      await axios.post(`${API_URL}/api/conversations/${selectedConversation.id}/messages`, {
        conversation_id: selectedConversation.id,
        content: userMessage,
        sender_type: "human",
        message_type: "text",
      });

      // Get AI response
      const aiResponse = await axios.post(`${API_URL}/api/ai/chat`, {
        customer_id: selectedConversation.customer_id,
        conversation_id: selectedConversation.id,
        message: userMessage,
      });

      // Save AI response
      await axios.post(`${API_URL}/api/conversations/${selectedConversation.id}/messages`, {
        conversation_id: selectedConversation.id,
        content: aiResponse.data.response,
        sender_type: "ai",
        message_type: "text",
      });

      fetchMessages(selectedConversation.id);
      fetchConversations();

      if (aiResponse.data.needs_escalation) {
        toast.warning("This conversation may need human attention", {
          description: "Customer might need escalation to Charu",
        });
      }
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
                    className={`conversation-item ${
                      selectedConversation?.id === conv.id ? "active" : ""
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
                      <div className="flex items-center gap-2 mt-2">
                        <Badge variant="outline" className="text-xs whatsapp-accent">
                          WhatsApp
                        </Badge>
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
            {/* Chat Header */}
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
                <Button variant="ghost" size="icon">
                  <MoreVertical className="w-5 h-5" />
                </Button>
              </div>

              {/* Open Topics */}
              {selectedConversation.topics?.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-3">
                  {selectedConversation.topics
                    .filter((t) => t.status !== "resolved")
                    .map((topic) => (
                      <span
                        key={topic.id}
                        className={TopicTypeColors[topic.topic_type] || "topic-pill"}
                      >
                        {topic.title}
                      </span>
                    ))}
                </div>
              )}
            </CardHeader>

            {/* Messages */}
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
                        className={`chat-bubble ${message.sender_type}`}
                        data-testid={`message-${message.id}`}
                      >
                        {message.sender_type === "ai" && (
                          <div className="flex items-center gap-1 text-xs text-primary mb-1">
                            <Sparkles className="w-3 h-3" />
                            AI Response
                          </div>
                        )}
                        {message.sender_type === "human" && (
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

            {/* Message Input */}
            <div className="message-input-container">
              <form onSubmit={handleSendMessage} className="flex items-end gap-3 w-full">
                <Button type="button" variant="ghost" size="icon" className="flex-shrink-0">
                  <Paperclip className="w-5 h-5" />
                </Button>
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
                  className="btn-primary flex-shrink-0"
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

      {/* Context Panel - Hidden on smaller screens */}
      {selectedConversation && (
        <Card className="w-80 flex-shrink-0 border-border/50 hidden xl:flex flex-col">
          <CardHeader className="py-4 border-b border-border">
            <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
              Customer Intelligence
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 flex-1 overflow-auto">
            <div className="space-y-6">
              {/* Quick Stats */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-accent rounded-lg text-center">
                  <p className="text-2xl font-bold text-primary">{messages.length}</p>
                  <p className="text-xs text-muted-foreground">Messages</p>
                </div>
                <div className="p-3 bg-accent rounded-lg text-center">
                  <p className="text-2xl font-bold text-amber-500">
                    {selectedConversation.topics?.filter((t) => t.status !== "resolved").length || 0}
                  </p>
                  <p className="text-xs text-muted-foreground">Open Topics</p>
                </div>
              </div>

              {/* Topics List */}
              <div>
                <h4 className="text-sm font-semibold mb-3">Active Topics</h4>
                {selectedConversation.topics?.length > 0 ? (
                  <div className="space-y-2">
                    {selectedConversation.topics.map((topic) => (
                      <div
                        key={topic.id}
                        className="p-3 bg-accent rounded-lg"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className={TopicTypeColors[topic.topic_type] || "topic-pill"}>
                            {topic.topic_type.replace("_", " ")}
                          </span>
                          <Badge
                            variant="outline"
                            className={
                              topic.status === "open"
                                ? "status-active"
                                : topic.status === "resolved"
                                ? "status-closed"
                                : "status-pending"
                            }
                          >
                            {topic.status}
                          </Badge>
                        </div>
                        <p className="text-sm font-medium">{topic.title}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No active topics</p>
                )}
              </div>

              {/* AI Insights */}
              <div>
                <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-primary" />
                  AI Insights
                </h4>
                <div className="p-3 bg-primary/5 border border-primary/20 rounded-lg">
                  <p className="text-sm">
                    This customer is engaged in an active product inquiry. 
                    AI is handling the conversation with persistent context.
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ConversationsPage;
