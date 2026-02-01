import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Switch } from "../components/ui/switch";
import { Textarea } from "../components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { Badge } from "../components/ui/badge";
import { Separator } from "../components/ui/separator";
import { useToast } from "../components/ui/use-toast";
import { 
  MessageSquare, 
  Settings, 
  Clock, 
  Shield, 
  Send,
  Save,
  RefreshCw,
  History,
  Calendar,
  CheckCircle,
  XCircle,
  Edit
} from "lucide-react";

var API_URL = process.env.REACT_APP_BACKEND_URL;

var TRIGGER_LABELS = {
  no_response: "No Response Follow-up",
  partial_conversation: "Partial Conversation",
  price_shared: "Price Shared, No Action",
  order_confirmed: "Order Confirmed",
  payment_received: "Payment Received",
  order_completed: "Order Completed",
  ticket_created: "Ticket Created",
  ticket_updated: "Ticket Updated",
  ticket_resolved: "Ticket Resolved",
  ai_uncertain: "AI Uncertain",
  human_takeover: "Human Takeover"
};

function AutoMessagesPage() {
  var [settings, setSettings] = useState({
    max_messages_per_topic: 3,
    cooldown_hours: 24,
    dnd_start_hour: 21,
    dnd_end_hour: 9,
    no_response_days: 2,
    auto_messaging_enabled: true,
    templates: {}
  });
  var [history, setHistory] = useState([]);
  var [scheduled, setScheduled] = useState([]);
  var [loading, setLoading] = useState(true);
  var [saving, setSaving] = useState(false);
  var [editingTemplate, setEditingTemplate] = useState(null);
  var [templateValue, setTemplateValue] = useState("");
  var { toast } = useToast();

  var fetchData = async function() {
    try {
      var token = localStorage.getItem("token");
      var headers = { "Authorization": "Bearer " + token };

      var [settingsRes, historyRes, scheduledRes] = await Promise.all([
        fetch(API_URL + "/api/auto-messages/settings", { headers }),
        fetch(API_URL + "/api/auto-messages/history?limit=20", { headers }),
        fetch(API_URL + "/api/auto-messages/scheduled", { headers })
      ]);

      var settingsData = await settingsRes.json();
      var historyData = await historyRes.json();
      var scheduledData = await scheduledRes.json();

      setSettings(settingsData);
      setHistory(historyData);
      setScheduled(scheduledData);
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(function() {
    fetchData();
  }, []);

  var handleSaveSettings = async function() {
    setSaving(true);
    try {
      var token = localStorage.getItem("token");
      await fetch(API_URL + "/api/auto-messages/settings", {
        method: "PUT",
        headers: {
          "Authorization": "Bearer " + token,
          "Content-Type": "application/json"
        },
        body: JSON.stringify(settings)
      });
      toast({ title: "Settings Saved", description: "Auto-messaging settings updated" });
    } catch (error) {
      toast({ title: "Error", description: "Failed to save settings", variant: "destructive" });
    } finally {
      setSaving(false);
    }
  };

  var handleSaveTemplate = async function(triggerType) {
    try {
      var token = localStorage.getItem("token");
      await fetch(API_URL + "/api/auto-messages/templates/" + triggerType + "?template=" + encodeURIComponent(templateValue), {
        method: "PUT",
        headers: { "Authorization": "Bearer " + token }
      });
      
      setSettings(function(prev) {
        return {
          ...prev,
          templates: { ...prev.templates, [triggerType]: templateValue }
        };
      });
      setEditingTemplate(null);
      toast({ title: "Template Saved" });
    } catch (error) {
      toast({ title: "Error", description: "Failed to save template", variant: "destructive" });
    }
  };

  var handleCancelScheduled = async function(messageId) {
    try {
      var token = localStorage.getItem("token");
      await fetch(API_URL + "/api/auto-messages/scheduled/" + messageId, {
        method: "DELETE",
        headers: { "Authorization": "Bearer " + token }
      });
      toast({ title: "Cancelled", description: "Scheduled message cancelled" });
      fetchData();
    } catch (error) {
      toast({ title: "Error", description: "Failed to cancel", variant: "destructive" });
    }
  };

  var startEditTemplate = function(triggerType) {
    setEditingTemplate(triggerType);
    setTemplateValue(settings.templates[triggerType] || "");
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="skeleton-pulse h-10 w-48 rounded" />
        <Card><CardContent className="p-6"><div className="skeleton-pulse h-64 rounded" /></CardContent></Card>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="auto-messages-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <MessageSquare className="h-6 w-6 text-primary" />
            Auto-Messaging
          </h1>
          <p className="text-muted-foreground">Trigger-based, permission-controlled automated messages</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Switch
              checked={settings.auto_messaging_enabled}
              onCheckedChange={function(checked) {
                setSettings({ ...settings, auto_messaging_enabled: checked });
              }}
              data-testid="auto-msg-master-switch"
            />
            <Label>Enabled</Label>
          </div>
          <Button onClick={handleSaveSettings} disabled={saving} data-testid="save-auto-msg-settings">
            {saving ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
            Save Settings
          </Button>
        </div>
      </div>

      <Tabs defaultValue="settings">
        <TabsList>
          <TabsTrigger value="settings" data-testid="tab-settings">
            <Settings className="h-4 w-4 mr-1" /> Settings
          </TabsTrigger>
          <TabsTrigger value="templates" data-testid="tab-templates">
            <Edit className="h-4 w-4 mr-1" /> Templates
          </TabsTrigger>
          <TabsTrigger value="history" data-testid="tab-history">
            <History className="h-4 w-4 mr-1" /> History
          </TabsTrigger>
          <TabsTrigger value="scheduled" data-testid="tab-scheduled">
            <Calendar className="h-4 w-4 mr-1" /> Scheduled
          </TabsTrigger>
        </TabsList>

        <TabsContent value="settings" className="space-y-6 mt-6">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                  <Shield className="w-5 h-5 text-red-600 dark:text-red-400" />
                </div>
                <div>
                  <CardTitle className="text-lg">Anti-Spam Controls</CardTitle>
                  <CardDescription>Protect customers from over-messaging</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label>Max Messages Per Topic</Label>
                <Input
                  type="number"
                  min="1"
                  max="10"
                  value={settings.max_messages_per_topic}
                  onChange={function(e) { setSettings({ ...settings, max_messages_per_topic: parseInt(e.target.value) || 3 }); }}
                  data-testid="max-per-topic"
                />
                <p className="text-xs text-muted-foreground">Stop after this many auto-messages per topic</p>
              </div>
              <div className="space-y-2">
                <Label>Cooldown Period (Hours)</Label>
                <Input
                  type="number"
                  min="1"
                  max="168"
                  value={settings.cooldown_hours}
                  onChange={function(e) { setSettings({ ...settings, cooldown_hours: parseInt(e.target.value) || 24 }); }}
                  data-testid="cooldown-hours"
                />
                <p className="text-xs text-muted-foreground">Min hours between auto-messages to same customer</p>
              </div>
              <div className="space-y-2">
                <Label>No-Response Follow-up (Days)</Label>
                <Input
                  type="number"
                  min="1"
                  max="14"
                  value={settings.no_response_days}
                  onChange={function(e) { setSettings({ ...settings, no_response_days: parseInt(e.target.value) || 2 }); }}
                  data-testid="no-response-days"
                />
                <p className="text-xs text-muted-foreground">Days before sending no-response follow-up</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
                  <Clock className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                </div>
                <div>
                  <CardTitle className="text-lg">Do Not Disturb Window</CardTitle>
                  <CardDescription>No auto-messages during these hours</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label>DND Start Hour (24h format)</Label>
                <Input
                  type="number"
                  min="0"
                  max="23"
                  value={settings.dnd_start_hour}
                  onChange={function(e) { setSettings({ ...settings, dnd_start_hour: parseInt(e.target.value) || 21 }); }}
                  data-testid="dnd-start"
                />
                <p className="text-xs text-muted-foreground">e.g., 21 = 9 PM</p>
              </div>
              <div className="space-y-2">
                <Label>DND End Hour (24h format)</Label>
                <Input
                  type="number"
                  min="0"
                  max="23"
                  value={settings.dnd_end_hour}
                  onChange={function(e) { setSettings({ ...settings, dnd_end_hour: parseInt(e.target.value) || 9 }); }}
                  data-testid="dnd-end"
                />
                <p className="text-xs text-muted-foreground">e.g., 9 = 9 AM</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="templates" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Message Templates</CardTitle>
              <CardDescription>Customize auto-message content. Use {"{variable}"} for dynamic values.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {Object.keys(TRIGGER_LABELS).map(function(triggerType) {
                var isEditing = editingTemplate === triggerType;
                var template = settings.templates[triggerType] || "";
                
                return (
                  <div key={triggerType} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h4 className="font-medium">{TRIGGER_LABELS[triggerType]}</h4>
                        {isEditing ? (
                          <div className="mt-2 space-y-2">
                            <Textarea
                              value={templateValue}
                              onChange={function(e) { setTemplateValue(e.target.value); }}
                              placeholder="Enter message template..."
                              rows={2}
                            />
                            <div className="flex gap-2">
                              <Button size="sm" onClick={function() { handleSaveTemplate(triggerType); }}>Save</Button>
                              <Button size="sm" variant="outline" onClick={function() { setEditingTemplate(null); }}>Cancel</Button>
                            </div>
                          </div>
                        ) : (
                          <p className="text-sm text-muted-foreground mt-1">{template || "(No template set)"}</p>
                        )}
                      </div>
                      {!isEditing && (
                        <Button variant="ghost" size="sm" onClick={function() { startEditTemplate(triggerType); }}>
                          <Edit className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Recent Auto-Messages</CardTitle>
              <CardDescription>History of sent automated messages</CardDescription>
            </CardHeader>
            <CardContent>
              {history.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Send className="h-12 w-12 mx-auto mb-3 opacity-50" />
                  <p>No auto-messages sent yet</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Trigger</TableHead>
                      <TableHead>Message</TableHead>
                      <TableHead>Sent At</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {history.map(function(msg) {
                      return (
                        <TableRow key={msg.id}>
                          <TableCell>
                            <Badge variant="outline">{TRIGGER_LABELS[msg.trigger_type] || msg.trigger_type}</Badge>
                          </TableCell>
                          <TableCell className="max-w-md truncate">{msg.message}</TableCell>
                          <TableCell className="text-muted-foreground">
                            {new Date(msg.sent_at).toLocaleString()}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="scheduled" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Scheduled Messages</CardTitle>
              <CardDescription>Pending follow-up messages</CardDescription>
            </CardHeader>
            <CardContent>
              {scheduled.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Calendar className="h-12 w-12 mx-auto mb-3 opacity-50" />
                  <p>No scheduled messages</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Trigger</TableHead>
                      <TableHead>Message</TableHead>
                      <TableHead>Scheduled For</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {scheduled.map(function(msg) {
                      return (
                        <TableRow key={msg.id}>
                          <TableCell>
                            <Badge variant="outline">{TRIGGER_LABELS[msg.trigger_type] || msg.trigger_type}</Badge>
                          </TableCell>
                          <TableCell className="max-w-md truncate">{msg.message}</TableCell>
                          <TableCell className="text-muted-foreground">
                            {new Date(msg.scheduled_for).toLocaleString()}
                          </TableCell>
                          <TableCell>
                            {msg.status === "pending" ? (
                              <Badge variant="secondary"><Clock className="h-3 w-3 mr-1" /> Pending</Badge>
                            ) : msg.status === "sent" ? (
                              <Badge variant="success"><CheckCircle className="h-3 w-3 mr-1" /> Sent</Badge>
                            ) : (
                              <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" /> Cancelled</Badge>
                            )}
                          </TableCell>
                          <TableCell>
                            {msg.status === "pending" && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={function() { handleCancelScheduled(msg.id); }}
                                className="text-destructive"
                              >
                                Cancel
                              </Button>
                            )}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default AutoMessagesPage;
