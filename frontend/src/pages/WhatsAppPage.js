import React, { useState, useEffect } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "../components/ui/alert";
import { toast } from "sonner";
import { Smartphone, Check, X, RefreshCw, MessageSquare, Send, Wifi, WifiOff, Loader2 } from "lucide-react";

var API_URL = process.env.REACT_APP_BACKEND_URL;

function WhatsAppPage() {
  var [status, setStatus] = useState({
    connected: false,
    phone_number: null,
    qr_code: null,
    status: "loading",
    sync_progress: { total: 0, synced: 0, status: "idle" },
    previewMode: false
  });
  var [loading, setLoading] = useState(true);
  var [testPhone, setTestPhone] = useState("+91 98765 00000");
  var [testMessage, setTestMessage] = useState("Hi, I want to buy AirPods Pro");
  var [sending, setSending] = useState(false);

  useEffect(function() {
    fetchStatus();
    var interval = setInterval(fetchStatus, 3000); // Poll every 3 seconds
    return function() { clearInterval(interval); };
  }, []);

  function fetchStatus() {
    axios.get(API_URL + "/api/whatsapp/status").then(function(res) {
      setStatus(res.data);
      setLoading(false);
    }).catch(function(err) {
      console.error("Status error:", err);
      setLoading(false);
    });
  }

  function handleDisconnect() {
    axios.post(API_URL + "/api/whatsapp/disconnect").then(function() {
      toast.success("WhatsApp disconnected");
      fetchStatus();
    }).catch(function() {
      toast.error("Failed to disconnect");
    });
  }

  function handleReconnect() {
    axios.post(API_URL + "/api/whatsapp/reconnect").then(function() {
      toast.success("Reconnecting... New QR will appear shortly");
      fetchStatus();
    }).catch(function() {
      toast.error("Failed to reconnect");
    });
  }

  function handleSimulateMessage(e) {
    e.preventDefault();
    if (!testPhone.trim() || !testMessage.trim()) return;

    setSending(true);
    axios.post(API_URL + "/api/whatsapp/simulate-message?phone=" + encodeURIComponent(testPhone) + "&message=" + encodeURIComponent(testMessage)).then(function(res) {
      toast.success("Message received!", { description: "Check Conversations page" });
      setTestMessage("");
    }).catch(function(err) {
      toast.error(err.response && err.response.data ? err.response.data.detail : "Failed");
    }).finally(function() {
      setSending(false);
    });
  }

  var isConnected = status.connected;
  var isSyncing = status.sync_progress && status.sync_progress.status === "syncing";

  return (
    <div className="space-y-6 animate-in max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold">WhatsApp Connection</h1>
        <p className="text-muted-foreground">Scan QR to connect your WhatsApp</p>
      </div>

      <Card className="border-border/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={"w-12 h-12 rounded-xl flex items-center justify-center " + (isConnected ? "bg-[#25D366]/10" : "bg-muted")}>
                <Smartphone className={"w-6 h-6 " + (isConnected ? "text-[#25D366]" : "text-muted-foreground")} />
              </div>
              <div>
                <CardTitle className="text-lg">WhatsApp Web</CardTitle>
                <CardDescription>
                  {isConnected ? "Connected to +" + status.phone_number : status.status === "service_unavailable" ? "Service starting..." : "Scan QR to connect"}
                </CardDescription>
              </div>
            </div>
            <Badge className={isConnected ? "status-active" : "status-pending"} data-testid="whatsapp-status-badge">
              {isConnected ? (
                <span className="flex items-center gap-1"><Wifi className="w-3 h-3" />Connected</span>
              ) : (
                <span className="flex items-center gap-1"><WifiOff className="w-3 h-3" />Disconnected</span>
              )}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center p-12">
              <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
            </div>
          ) : isConnected ? (
            <div className="space-y-6">
              <Alert className="bg-[#25D366]/10 border-[#25D366]/30">
                <Check className="h-4 w-4 text-[#25D366]" />
                <AlertTitle className="text-[#25D366]">Connected Successfully</AlertTitle>
                <AlertDescription>
                  WhatsApp is connected. Messages are being received and processed.
                </AlertDescription>
              </Alert>

              {isSyncing && (
                <Alert>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <AlertTitle>Syncing Messages</AlertTitle>
                  <AlertDescription>
                    Syncing chat history: {status.sync_progress.synced} / {status.sync_progress.total} chats
                  </AlertDescription>
                </Alert>
              )}

              <div className="flex items-center justify-between p-4 bg-accent rounded-xl">
                <div className="flex items-center gap-3">
                  <MessageSquare className="w-5 h-5 text-[#25D366]" />
                  <div>
                    <p className="font-medium">Phone Number</p>
                    <p className="text-sm text-muted-foreground">+{status.phone_number}</p>
                  </div>
                </div>
                <Button variant="outline" onClick={handleDisconnect} className="text-destructive hover:bg-destructive hover:text-white" data-testid="disconnect-whatsapp-btn">
                  <X className="w-4 h-4 mr-2" />Disconnect
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="flex flex-col items-center justify-center p-8 bg-white dark:bg-slate-900 rounded-2xl border-2 border-dashed border-border">
                {status.qr_code ? (
                  <div className="text-center">
                    <img src={status.qr_code} alt="WhatsApp QR Code" className="w-64 h-64 rounded-lg" />
                    <p className="text-sm text-muted-foreground mt-4">Scan with WhatsApp on your phone</p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-3 p-8">
                    <Loader2 className="w-12 h-12 text-muted-foreground animate-spin" />
                    <p className="text-sm text-muted-foreground">Generating QR code...</p>
                  </div>
                )}
              </div>

              <div className="space-y-3">
                <p className="text-sm font-medium">How to connect:</p>
                <ol className="text-sm text-muted-foreground space-y-2 list-decimal list-inside">
                  <li>Open WhatsApp on your phone</li>
                  <li>Go to Settings → Linked Devices</li>
                  <li>Tap "Link a Device"</li>
                  <li>Scan the QR code above</li>
                </ol>
              </div>

              <Button onClick={handleReconnect} variant="outline" className="w-full" data-testid="reconnect-whatsapp-btn">
                <RefreshCw className="w-4 h-4 mr-2" />Refresh QR Code
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="border-border/50">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Send className="w-5 h-5" />
            Test Message Simulation
          </CardTitle>
          <CardDescription>
            Simulate receiving a WhatsApp message (for testing without real WhatsApp)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSimulateMessage} className="space-y-4">
            <div className="space-y-2">
              <Label>Customer Phone</Label>
              <Input value={testPhone} onChange={function(e) { setTestPhone(e.target.value); }} placeholder="+91 98765 43210" data-testid="simulate-phone-input" />
            </div>
            <div className="space-y-2">
              <Label>Message</Label>
              <Input value={testMessage} onChange={function(e) { setTestMessage(e.target.value); }} placeholder="Type a message..." data-testid="simulate-message-input" />
            </div>
            <Button type="submit" className="w-full btn-primary" disabled={sending} data-testid="simulate-send-btn">
              {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <span className="flex items-center gap-2"><Send className="w-4 h-4" />Simulate Message</span>}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

export default WhatsAppPage;
