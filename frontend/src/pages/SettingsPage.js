import { useState, useEffect } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Switch } from "../components/ui/switch";
import { Separator } from "../components/ui/separator";
import { Textarea } from "../components/ui/textarea";
import { toast } from "sonner";
import {
  Settings as SettingsIcon,
  Building,
  Phone,
  Bot,
  Bell,
  Save,
  RefreshCw,
  FileText,
} from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const SettingsPage = () => {
  const [settings, setSettings] = useState({
    business_name: "Sales Brain",
    owner_phone: "",
    escalation_phone: "+91 98765 43210",
    follow_up_days: 3,
    ai_enabled: true,
    auto_reply: true,
    ai_instructions: "",
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/settings`);
      setSettings(response.data);
    } catch (error) {
      toast.error("Failed to load settings");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.put(`${API_URL}/api/settings`, settings);
      toast.success("Settings saved successfully");
    } catch (error) {
      toast.error("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6 max-w-2xl mx-auto">
        <div className="skeleton-pulse h-10 w-48 rounded" />
        <Card>
          <CardContent className="p-6">
            <div className="space-y-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="skeleton-pulse h-12 rounded" />
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-2xl mx-auto animate-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-muted-foreground">Configure your Sales Brain platform</p>
      </div>

      {/* Business Settings */}
      <Card className="border-border/50">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <Building className="w-5 h-5 text-primary" />
            </div>
            <div>
              <CardTitle className="text-lg">Business Information</CardTitle>
              <CardDescription>Basic business settings</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="business_name">Business Name</Label>
            <Input
              id="business_name"
              value={settings.business_name}
              onChange={(e) => setSettings({ ...settings, business_name: e.target.value })}
              placeholder="Your Business Name"
              data-testid="business-name-input"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="owner_phone">Owner's Phone (for Lead Injection via WhatsApp)</Label>
            <Input
              id="owner_phone"
              value={settings.owner_phone || ""}
              onChange={(e) => setSettings({ ...settings, owner_phone: e.target.value })}
              placeholder="+91 98765 43210"
              data-testid="owner-phone-input"
            />
            <p className="text-xs text-muted-foreground">
              Messages from this number with lead commands will be processed as lead injections
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Escalation Settings */}
      <Card className="border-border/50">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
              <Phone className="w-5 h-5 text-amber-600 dark:text-amber-400" />
            </div>
            <div>
              <CardTitle className="text-lg">Escalation Settings</CardTitle>
              <CardDescription>Configure human escalation (Charu-in-the-loop)</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="escalation_phone">Escalation Phone Number</Label>
            <Input
              id="escalation_phone"
              value={settings.escalation_phone}
              onChange={(e) => setSettings({ ...settings, escalation_phone: e.target.value })}
              placeholder="+91 98765 43210"
              data-testid="escalation-phone-input"
            />
            <p className="text-xs text-muted-foreground">
              This number will be notified when AI needs human intervention
            </p>
          </div>
        </CardContent>
      </Card>

      {/* AI Settings */}
      <Card className="border-border/50">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
              <Bot className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <CardTitle className="text-lg">AI Configuration</CardTitle>
              <CardDescription>Configure AI behavior and responses</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Enable AI Responses</Label>
              <p className="text-sm text-muted-foreground">
                Allow AI to automatically respond to customer messages
              </p>
            </div>
            <Switch
              checked={settings.ai_enabled}
              onCheckedChange={(checked) => setSettings({ ...settings, ai_enabled: checked })}
              data-testid="ai-enabled-switch"
            />
          </div>
          
          <Separator />
          
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Auto-Reply</Label>
              <p className="text-sm text-muted-foreground">
                Automatically send AI responses without manual approval
              </p>
            </div>
            <Switch
              checked={settings.auto_reply}
              onCheckedChange={(checked) => setSettings({ ...settings, auto_reply: checked })}
              data-testid="auto-reply-switch"
            />
          </div>
        </CardContent>
      </Card>

      {/* Follow-up Settings */}
      <Card className="border-border/50">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
              <Bell className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
            </div>
            <div>
              <CardTitle className="text-lg">Follow-up Settings</CardTitle>
              <CardDescription>Configure intelligent follow-ups</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="follow_up_days">Follow-up After (Days)</Label>
            <Input
              id="follow_up_days"
              type="number"
              min="1"
              max="30"
              value={settings.follow_up_days}
              onChange={(e) => setSettings({ ...settings, follow_up_days: parseInt(e.target.value) || 3 })}
              data-testid="follow-up-days-input"
            />
            <p className="text-xs text-muted-foreground">
              Send a follow-up message if no activity for this many days
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end gap-3 pt-4">
        <Button variant="outline" onClick={fetchSettings}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Reset
        </Button>
        <Button onClick={handleSave} disabled={saving} className="btn-primary" data-testid="save-settings-btn">
          {saving ? (
            <>
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="w-4 h-4 mr-2" />
              Save Settings
            </>
          )}
        </Button>
      </div>
    </div>
  );
};

export default SettingsPage;
