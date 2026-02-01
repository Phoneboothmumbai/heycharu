import { useState, useEffect } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "../components/ui/alert";
import { toast } from "sonner";
import {
  Smartphone,
  QrCode,
  Check,
  X,
  RefreshCw,
  MessageSquare,
  Send,
  Wifi,
  WifiOff,
} from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const WhatsAppPage = () => {
  const [status, setStatus] = useState({
    connected: false,
    phone_number: null,
    qr_code: null,
    status: "disconnected",
  });
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  
  // Simulate message form
  const [testPhone, setTestPhone] = useState("+91 98765 00000");
  const [testMessage, setTestMessage] = useState("Hello, I want to buy AirPods Pro");
  const [sending, setSending] = useState(false);

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/whatsapp/status`);
      setStatus(response.data);
    } catch (error) {
      toast.error("Failed to fetch WhatsApp status");
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async () => {
    setConnecting(true);
    try {
      // Simulate QR scan delay
      await new Promise((resolve) => setTimeout(resolve, 2000));
      await axios.post(`${API_URL}/api/whatsapp/connect`);
      toast.success("WhatsApp connected successfully!");
      fetchStatus();
    } catch (error) {
      toast.error("Failed to connect WhatsApp");
    } finally {
      setConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      await axios.post(`${API_URL}/api/whatsapp/disconnect`);
      toast.success("WhatsApp disconnected");
      fetchStatus();
    } catch (error) {
      toast.error("Failed to disconnect WhatsApp");
    }
  };

  const handleSimulateMessage = async (e) => {
    e.preventDefault();
    if (!testPhone.trim() || !testMessage.trim()) return;

    setSending(true);
    try {
      const response = await axios.post(
        `${API_URL}/api/whatsapp/simulate-message?phone=${encodeURIComponent(testPhone)}&message=${encodeURIComponent(testMessage)}`
      );
      toast.success("Message received!", {
        description: `Conversation created for ${testPhone}`,
      });
      setTestMessage("");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to simulate message");
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="space-y-6 animate-in max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">WhatsApp Connection</h1>
        <p className="text-muted-foreground">Connect your WhatsApp to receive and send messages</p>
      </div>

      {/* Connection Status Card */}
      <Card className="border-border/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                status.connected 
                  ? "bg-[#25D366]/10" 
                  : "bg-muted"
              }`}>
                <Smartphone className={`w-6 h-6 ${status.connected ? "text-[#25D366]" : "text-muted-foreground"}`} />
              </div>
              <div>
                <CardTitle className="text-lg">WhatsApp Web</CardTitle>
                <CardDescription>
                  {status.connected 
                    ? `Connected to ${status.phone_number}` 
                    : "Not connected"
                  }
                </CardDescription>
              </div>
            </div>
            <Badge 
              className={status.connected ? "status-active" : "status-pending"}
              data-testid="whatsapp-status-badge"
            >
              {status.connected ? (
                <>
                  <Wifi className="w-3 h-3 mr-1" />
                  Connected
                </>
              ) : (
                <>
                  <WifiOff className="w-3 h-3 mr-1" />
                  Disconnected
                </>
              )}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="qr-container">
              <div className="skeleton-pulse w-48 h-48 rounded-xl" />
            </div>
          ) : status.connected ? (
            <div className="space-y-6">
              <Alert className="bg-[#25D366]/10 border-[#25D366]/30">
                <Check className="h-4 w-4 text-[#25D366]" />
                <AlertTitle className="text-[#25D366]">Connected Successfully</AlertTitle>
                <AlertDescription>
                  Your WhatsApp is connected and ready to receive messages. All incoming messages will be captured and processed by Sales Brain AI.
                </AlertDescription>
              </Alert>
              
              <div className="flex items-center justify-between p-4 bg-accent rounded-xl">
                <div className="flex items-center gap-3">
                  <MessageSquare className="w-5 h-5 text-[#25D366]" />
                  <div>
                    <p className="font-medium">Phone Number</p>
                    <p className="text-sm text-muted-foreground">{status.phone_number}</p>
                  </div>
                </div>
                <Button 
                  variant="outline" 
                  onClick={handleDisconnect}
                  className="text-destructive hover:bg-destructive hover:text-white"
                  data-testid="disconnect-whatsapp-btn"
                >
                  <X className="w-4 h-4 mr-2" />
                  Disconnect
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* QR Code Area */}
              <div className="qr-container flex-col">
                <div className="w-48 h-48 bg-white rounded-xl p-4 flex items-center justify-center border-2 border-dashed border-border">
                  {connecting ? (
                    <div className="flex flex-col items-center gap-3">
                      <RefreshCw className="w-12 h-12 text-[#25D366] animate-spin" />
                      <p className="text-sm text-muted-foreground">Connecting...</p>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center gap-3">
                      <QrCode className="w-24 h-24 text-muted-foreground" />
                      <p className="text-xs text-muted-foreground text-center">
                        Click Connect to simulate QR scan
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Instructions */}
              <div className="space-y-3">
                <p className="text-sm font-medium">How to connect:</p>
                <ol className="text-sm text-muted-foreground space-y-2 list-decimal list-inside">
                  <li>Open WhatsApp on your phone</li>
                  <li>Go to Settings → Linked Devices</li>
                  <li>Tap "Link a Device"</li>
                  <li>Scan the QR code above</li>
                </ol>
              </div>

              <Button 
                onClick={handleConnect} 
                className="w-full whatsapp-bg text-white hover:bg-[#20BA5C]"
                disabled={connecting}
                data-testid="connect-whatsapp-btn"
              >
                {connecting ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Connecting...
                  </>
                ) : (
                  <>
                    <Smartphone className="w-4 h-4 mr-2" />
                    Simulate QR Scan & Connect
                  </>
                )}
              </Button>

              <Alert>
                <Badge variant="outline" className="mb-2">DEMO MODE</Badge>
                <AlertDescription className="text-sm">
                  In production, this would display a real WhatsApp Web QR code using whatsapp-web.js library. 
                  For demo purposes, clicking "Connect" simulates a successful connection.
                </AlertDescription>
              </Alert>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Simulate Message Card - Only show when connected */}
      {status.connected && (
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Send className="w-5 h-5" />
              Simulate Incoming Message
            </CardTitle>
            <CardDescription>
              Test the system by simulating a WhatsApp message from a customer
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSimulateMessage} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="phone">Customer Phone</Label>
                <Input
                  id="phone"
                  value={testPhone}
                  onChange={(e) => setTestPhone(e.target.value)}
                  placeholder="+91 98765 43210"
                  data-testid="simulate-phone-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="message">Message</Label>
                <Input
                  id="message"
                  value={testMessage}
                  onChange={(e) => setTestMessage(e.target.value)}
                  placeholder="Type a message..."
                  data-testid="simulate-message-input"
                />
              </div>
              <Button 
                type="submit" 
                className="w-full btn-primary"
                disabled={sending}
                data-testid="simulate-send-btn"
              >
                {sending ? (
                  <div className="ai-thinking">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                ) : (
                  <>
                    <Send className="w-4 h-4 mr-2" />
                    Simulate Message
                  </>
                )}
              </Button>
            </form>

            <div className="mt-4 p-3 bg-accent rounded-lg">
              <p className="text-sm text-muted-foreground">
                <strong>Tip:</strong> After simulating a message, go to the Conversations page to see the new conversation and test the AI responses.
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default WhatsAppPage;
