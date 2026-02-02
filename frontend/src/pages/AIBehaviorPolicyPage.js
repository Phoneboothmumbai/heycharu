import { useState, useEffect } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Switch } from "../components/ui/switch";
import { Badge } from "../components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "../components/ui/accordion";
import { toast } from "sonner";
import { Brain, Shield, MessageSquare, AlertTriangle, Settings2, RotateCcw, Save, Clock, User } from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const AIBehaviorPolicyPage = () => {
  const [policy, setPolicy] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchPolicy();
  }, []);

  const fetchPolicy = async () => {
    try {
      const token = localStorage.getItem("sales-brain-token");
      const response = await axios.get(`${API_URL}/api/ai-policy`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPolicy(response.data);
    } catch (error) {
      toast.error("Failed to load AI Policy");
    } finally {
      setLoading(false);
    }
  };

  const savePolicy = async () => {
    setSaving(true);
    try {
      const token = localStorage.getItem("sales-brain-token");
      await axios.put(`${API_URL}/api/ai-policy`, policy, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("AI Policy saved successfully!");
      fetchPolicy();
    } catch (error) {
      toast.error("Failed to save AI Policy");
    } finally {
      setSaving(false);
    }
  };

  const resetPolicy = async () => {
    if (!window.confirm("Reset AI Policy to defaults? This cannot be undone.")) return;
    try {
      const token = localStorage.getItem("sales-brain-token");
      await axios.post(`${API_URL}/api/ai-policy/reset`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("AI Policy reset to defaults");
      fetchPolicy();
    } catch (error) {
      toast.error("Failed to reset AI Policy");
    }
  };

  const updateGlobalRules = (field, value) => {
    setPolicy(prev => ({
      ...prev,
      global_rules: { ...prev.global_rules, [field]: value }
    }));
  };

  const updateState = (stateName, field, value) => {
    setPolicy(prev => ({
      ...prev,
      states: {
        ...prev.states,
        [stateName]: { ...prev.states[stateName], [field]: value }
      }
    }));
  };

  const updateResponseRules = (field, value) => {
    setPolicy(prev => ({
      ...prev,
      response_rules: { ...prev.response_rules, [field]: value }
    }));
  };

  const updateFallback = (type, field, value) => {
    setPolicy(prev => ({
      ...prev,
      fallback: {
        ...prev.fallback,
        [type]: { ...prev.fallback[type], [field]: value }
      }
    }));
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64">Loading AI Policy...</div>;
  }

  if (!policy) {
    return <div className="text-center py-8 text-red-500">Failed to load policy</div>;
  }

  return (
    <div className="space-y-6" data-testid="ai-policy-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Brain className="w-6 h-6 text-purple-500" />
            AI Behavior Policy
          </h1>
          <p className="text-muted-foreground mt-1">
            Configure how the AI responds to customers. Changes apply instantly.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {policy.last_updated && (
            <div className="text-xs text-muted-foreground flex items-center gap-1">
              <Clock className="w-3 h-3" />
              Last updated: {new Date(policy.last_updated).toLocaleString()}
              {policy.updated_by && <span>by {policy.updated_by}</span>}
            </div>
          )}
          <Button variant="outline" onClick={resetPolicy}>
            <RotateCcw className="w-4 h-4 mr-1" />
            Reset
          </Button>
          <Button onClick={savePolicy} disabled={saving}>
            <Save className="w-4 h-4 mr-1" />
            {saving ? "Saving..." : "Save Policy"}
          </Button>
        </div>
      </div>

      {/* Master Toggle */}
      <Card className="border-purple-200 dark:border-purple-900">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold">AI Policy Enforcement</h3>
              <p className="text-sm text-muted-foreground">When enabled, AI must follow all rules below</p>
            </div>
            <Switch
              checked={policy.enabled}
              onCheckedChange={(checked) => setPolicy({ ...policy, enabled: checked })}
            />
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="global" className="space-y-4">
        <TabsList className="grid grid-cols-5 w-full">
          <TabsTrigger value="global">Global Rules</TabsTrigger>
          <TabsTrigger value="states">States</TabsTrigger>
          <TabsTrigger value="response">Response</TabsTrigger>
          <TabsTrigger value="fallback">Fallback</TabsTrigger>
          <TabsTrigger value="triggers">Triggers</TabsTrigger>
        </TabsList>

        {/* Global Rules Tab */}
        <TabsContent value="global">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Global Rules
              </CardTitle>
              <CardDescription>Define what the AI is allowed and not allowed to do</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Allowed Topics */}
              <div>
                <Label className="text-base font-semibold">Allowed Topics</Label>
                <p className="text-sm text-muted-foreground mb-2">AI will ONLY talk about these topics</p>
                <div className="flex flex-wrap gap-2 mb-2">
                  {policy.global_rules.allowed_topics?.map((topic, idx) => (
                    <Badge key={idx} variant="secondary" className="px-3 py-1">
                      {topic}
                      <button 
                        className="ml-2 text-red-500"
                        onClick={() => updateGlobalRules("allowed_topics", policy.global_rules.allowed_topics.filter((_, i) => i !== idx))}
                      >
                        x
                      </button>
                    </Badge>
                  ))}
                </div>
                <Input
                  placeholder="Add topic (press Enter)"
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && e.target.value) {
                      updateGlobalRules("allowed_topics", [...(policy.global_rules.allowed_topics || []), e.target.value]);
                      e.target.value = "";
                    }
                  }}
                />
              </div>

              {/* Disallowed Behavior */}
              <div>
                <Label className="text-base font-semibold">Disallowed Behavior</Label>
                <p className="text-sm text-muted-foreground mb-2">AI will NEVER do these things</p>
                <div className="flex flex-wrap gap-2 mb-2">
                  {policy.global_rules.disallowed_behavior?.map((behavior, idx) => (
                    <Badge key={idx} variant="destructive" className="px-3 py-1">
                      {behavior.replace(/_/g, " ")}
                      <button 
                        className="ml-2"
                        onClick={() => updateGlobalRules("disallowed_behavior", policy.global_rules.disallowed_behavior.filter((_, i) => i !== idx))}
                      >
                        x
                      </button>
                    </Badge>
                  ))}
                </div>
                <Input
                  placeholder="Add disallowed behavior (press Enter)"
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && e.target.value) {
                      updateGlobalRules("disallowed_behavior", [...(policy.global_rules.disallowed_behavior || []), e.target.value.replace(/ /g, "_")]);
                      e.target.value = "";
                    }
                  }}
                />
              </div>

              {/* Scope Message */}
              <div>
                <Label className="text-base font-semibold">Out-of-Scope Message</Label>
                <p className="text-sm text-muted-foreground mb-2">Response when customer asks about something not allowed</p>
                <Textarea
                  value={policy.global_rules.scope_message || ""}
                  onChange={(e) => updateGlobalRules("scope_message", e.target.value)}
                  rows={2}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* States Tab */}
        <TabsContent value="states">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="w-5 h-5" />
                Conversation States
              </CardTitle>
              <CardDescription>Configure how AI behaves at each conversation stage</CardDescription>
            </CardHeader>
            <CardContent>
              <Accordion type="multiple" className="space-y-2">
                {/* GREETING State */}
                <AccordionItem value="greeting">
                  <AccordionTrigger className="text-left">
                    <div className="flex items-center gap-2">
                      <Badge variant={policy.states.GREETING?.enabled ? "default" : "secondary"}>
                        {policy.states.GREETING?.enabled ? "ON" : "OFF"}
                      </Badge>
                      GREETING State
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 pt-4">
                    <div className="flex items-center justify-between">
                      <Label>Enabled</Label>
                      <Switch
                        checked={policy.states.GREETING?.enabled}
                        onCheckedChange={(v) => updateState("GREETING", "enabled", v)}
                      />
                    </div>
                    <div>
                      <Label>Trigger Words (comma-separated)</Label>
                      <Input
                        value={policy.states.GREETING?.triggers?.join(", ") || ""}
                        onChange={(e) => updateState("GREETING", "triggers", e.target.value.split(",").map(s => s.trim().toLowerCase()))}
                      />
                    </div>
                    <div>
                      <Label>Response Template</Label>
                      <Input
                        value={policy.states.GREETING?.response_template || ""}
                        onChange={(e) => updateState("GREETING", "response_template", e.target.value)}
                      />
                    </div>
                    <div>
                      <Label>Forbidden Actions (comma-separated)</Label>
                      <Input
                        value={policy.states.GREETING?.forbidden_actions?.join(", ") || ""}
                        onChange={(e) => updateState("GREETING", "forbidden_actions", e.target.value.split(",").map(s => s.trim()))}
                      />
                    </div>
                  </AccordionContent>
                </AccordionItem>

                {/* INTENT_COLLECTION State */}
                <AccordionItem value="intent">
                  <AccordionTrigger className="text-left">
                    <div className="flex items-center gap-2">
                      <Badge variant={policy.states.INTENT_COLLECTION?.enabled ? "default" : "secondary"}>
                        {policy.states.INTENT_COLLECTION?.enabled ? "ON" : "OFF"}
                      </Badge>
                      INTENT COLLECTION State
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 pt-4">
                    <div className="flex items-center justify-between">
                      <Label>Enabled</Label>
                      <Switch
                        checked={policy.states.INTENT_COLLECTION?.enabled}
                        onCheckedChange={(v) => updateState("INTENT_COLLECTION", "enabled", v)}
                      />
                    </div>
                    <div>
                      <Label>Trigger Words (comma-separated)</Label>
                      <Input
                        value={policy.states.INTENT_COLLECTION?.triggers?.join(", ") || ""}
                        onChange={(e) => updateState("INTENT_COLLECTION", "triggers", e.target.value.split(",").map(s => s.trim().toLowerCase()))}
                      />
                    </div>
                    <div>
                      <Label>Clarification Template</Label>
                      <Input
                        value={policy.states.INTENT_COLLECTION?.clarification_template || ""}
                        onChange={(e) => updateState("INTENT_COLLECTION", "clarification_template", e.target.value)}
                      />
                    </div>
                  </AccordionContent>
                </AccordionItem>

                {/* ACTION State */}
                <AccordionItem value="action">
                  <AccordionTrigger className="text-left">
                    <div className="flex items-center gap-2">
                      <Badge variant={policy.states.ACTION?.enabled ? "default" : "secondary"}>
                        {policy.states.ACTION?.enabled ? "ON" : "OFF"}
                      </Badge>
                      ACTION State
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 pt-4">
                    <div className="flex items-center justify-between">
                      <Label>Enabled</Label>
                      <Switch
                        checked={policy.states.ACTION?.enabled}
                        onCheckedChange={(v) => updateState("ACTION", "enabled", v)}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <Label>Mention Delivery Only If Asked</Label>
                      <Switch
                        checked={policy.states.ACTION?.sales_flow?.mention_delivery_only_if_asked}
                        onCheckedChange={(v) => updateState("ACTION", "sales_flow", {...policy.states.ACTION?.sales_flow, mention_delivery_only_if_asked: v})}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <Label>Ask One Field at a Time (Repairs)</Label>
                      <Switch
                        checked={policy.states.ACTION?.repair_flow?.ask_one_field_at_a_time}
                        onCheckedChange={(v) => updateState("ACTION", "repair_flow", {...policy.states.ACTION?.repair_flow, ask_one_field_at_a_time: v})}
                      />
                    </div>
                  </AccordionContent>
                </AccordionItem>

                {/* CLOSURE State */}
                <AccordionItem value="closure">
                  <AccordionTrigger className="text-left">
                    <div className="flex items-center gap-2">
                      <Badge variant={policy.states.CLOSURE?.enabled ? "default" : "secondary"}>
                        {policy.states.CLOSURE?.enabled ? "ON" : "OFF"}
                      </Badge>
                      CLOSURE State
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 pt-4">
                    <div className="flex items-center justify-between">
                      <Label>Enabled</Label>
                      <Switch
                        checked={policy.states.CLOSURE?.enabled}
                        onCheckedChange={(v) => updateState("CLOSURE", "enabled", v)}
                      />
                    </div>
                    <div>
                      <Label>Trigger Words (comma-separated)</Label>
                      <Input
                        value={policy.states.CLOSURE?.triggers?.join(", ") || ""}
                        onChange={(e) => updateState("CLOSURE", "triggers", e.target.value.split(",").map(s => s.trim().toLowerCase()))}
                      />
                    </div>
                    <div>
                      <Label>Thanks Response</Label>
                      <Input
                        value={policy.states.CLOSURE?.templates?.thanks || ""}
                        onChange={(e) => updateState("CLOSURE", "templates", {...policy.states.CLOSURE?.templates, thanks: e.target.value})}
                      />
                    </div>
                    <div>
                      <Label>Bye Response</Label>
                      <Input
                        value={policy.states.CLOSURE?.templates?.bye || ""}
                        onChange={(e) => updateState("CLOSURE", "templates", {...policy.states.CLOSURE?.templates, bye: e.target.value})}
                      />
                    </div>
                    <div>
                      <Label>OK Response</Label>
                      <Input
                        value={policy.states.CLOSURE?.templates?.ok || ""}
                        onChange={(e) => updateState("CLOSURE", "templates", {...policy.states.CLOSURE?.templates, ok: e.target.value})}
                      />
                    </div>
                  </AccordionContent>
                </AccordionItem>

                {/* ESCALATION State */}
                <AccordionItem value="escalation">
                  <AccordionTrigger className="text-left">
                    <div className="flex items-center gap-2">
                      <Badge variant={policy.states.ESCALATION?.enabled ? "default" : "secondary"}>
                        {policy.states.ESCALATION?.enabled ? "ON" : "OFF"}
                      </Badge>
                      ESCALATION State
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 pt-4">
                    <div className="flex items-center justify-between">
                      <Label>Enabled</Label>
                      <Switch
                        checked={policy.states.ESCALATION?.enabled}
                        onCheckedChange={(v) => updateState("ESCALATION", "enabled", v)}
                      />
                    </div>
                    <div>
                      <Label>Placeholder Message (while checking)</Label>
                      <Input
                        value={policy.states.ESCALATION?.placeholder_message || ""}
                        onChange={(e) => updateState("ESCALATION", "placeholder_message", e.target.value)}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <Label>Notify Owner on WhatsApp</Label>
                      <Switch
                        checked={policy.states.ESCALATION?.notify_owner}
                        onCheckedChange={(v) => updateState("ESCALATION", "notify_owner", v)}
                      />
                    </div>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Response Rules Tab */}
        <TabsContent value="response">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings2 className="w-5 h-5" />
                Response Constraints
              </CardTitle>
              <CardDescription>Control how AI responses should look</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Greeting Limit</Label>
                  <Input
                    value={policy.response_rules?.greeting_limit || ""}
                    onChange={(e) => updateResponseRules("greeting_limit", e.target.value)}
                    placeholder="once_per_conversation"
                  />
                </div>
                <div>
                  <Label>Question Limit</Label>
                  <Input
                    value={policy.response_rules?.question_limit || ""}
                    onChange={(e) => updateResponseRules("question_limit", e.target.value)}
                    placeholder="one_at_a_time"
                  />
                </div>
                <div>
                  <Label>Max Response Length (chars)</Label>
                  <Input
                    type="number"
                    value={policy.response_rules?.max_response_length || 150}
                    onChange={(e) => updateResponseRules("max_response_length", parseInt(e.target.value))}
                  />
                </div>
                <div>
                  <Label>Tone</Label>
                  <Input
                    value={policy.response_rules?.tone || ""}
                    onChange={(e) => updateResponseRules("tone", e.target.value)}
                    placeholder="friendly_professional"
                  />
                </div>
                <div>
                  <Label>Language</Label>
                  <Input
                    value={policy.response_rules?.language || ""}
                    onChange={(e) => updateResponseRules("language", e.target.value)}
                    placeholder="english_hinglish"
                  />
                </div>
                <div>
                  <Label>Emoji Usage</Label>
                  <Input
                    value={policy.response_rules?.emoji_usage || ""}
                    onChange={(e) => updateResponseRules("emoji_usage", e.target.value)}
                    placeholder="minimal"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Fallback Tab */}
        <TabsContent value="fallback">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5" />
                Fallback & Error Handling
              </CardTitle>
              <CardDescription>What to do when AI is unsure or encounters errors</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Unclear Data */}
              <div className="p-4 border rounded-lg">
                <h4 className="font-semibold mb-3">When Data is Unclear</h4>
                <div className="space-y-3">
                  <div>
                    <Label>Action</Label>
                    <Input
                      value={policy.fallback?.unclear_data?.action || ""}
                      onChange={(e) => updateFallback("unclear_data", "action", e.target.value)}
                    />
                  </div>
                  <div>
                    <Label>Response Template</Label>
                    <Textarea
                      value={policy.fallback?.unclear_data?.template || ""}
                      onChange={(e) => updateFallback("unclear_data", "template", e.target.value)}
                      rows={2}
                    />
                  </div>
                </div>
              </div>

              {/* Out of Scope */}
              <div className="p-4 border rounded-lg">
                <h4 className="font-semibold mb-3">When Out of Scope</h4>
                <div className="space-y-3">
                  <div>
                    <Label>Action</Label>
                    <Input
                      value={policy.fallback?.out_of_scope?.action || ""}
                      onChange={(e) => updateFallback("out_of_scope", "action", e.target.value)}
                    />
                  </div>
                  <div>
                    <Label>Response Template</Label>
                    <Textarea
                      value={policy.fallback?.out_of_scope?.template || ""}
                      onChange={(e) => updateFallback("out_of_scope", "template", e.target.value)}
                      rows={2}
                    />
                  </div>
                </div>
              </div>

              {/* System Error */}
              <div className="p-4 border rounded-lg">
                <h4 className="font-semibold mb-3">On System Error</h4>
                <div className="space-y-3">
                  <div>
                    <Label>Action</Label>
                    <Input
                      value={policy.fallback?.system_error?.action || ""}
                      onChange={(e) => updateFallback("system_error", "action", e.target.value)}
                    />
                  </div>
                  <div>
                    <Label>Response Template</Label>
                    <Textarea
                      value={policy.fallback?.system_error?.template || ""}
                      onChange={(e) => updateFallback("system_error", "template", e.target.value)}
                      rows={2}
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* System Triggers Tab */}
        <TabsContent value="triggers">
          <Card>
            <CardHeader>
              <CardTitle>System Triggers</CardTitle>
              <CardDescription>Internal message handling (like Lead Inject)</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="p-4 border rounded-lg">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-semibold">Lead Inject Trigger</h4>
                  <Switch
                    checked={policy.system_triggers?.lead_inject?.enabled}
                    onCheckedChange={(v) => setPolicy(prev => ({
                      ...prev,
                      system_triggers: {
                        ...prev.system_triggers,
                        lead_inject: { ...prev.system_triggers?.lead_inject, enabled: v }
                      }
                    }))}
                  />
                </div>
                <div className="space-y-3">
                  <div>
                    <Label>Keywords (comma-separated)</Label>
                    <Input
                      value={policy.system_triggers?.lead_inject?.keywords?.join(", ") || ""}
                      onChange={(e) => setPolicy(prev => ({
                        ...prev,
                        system_triggers: {
                          ...prev.system_triggers,
                          lead_inject: { 
                            ...prev.system_triggers?.lead_inject, 
                            keywords: e.target.value.split(",").map(s => s.trim().toLowerCase()) 
                          }
                        }
                      }))}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label>Reply to User After Lead Inject</Label>
                    <Switch
                      checked={policy.system_triggers?.lead_inject?.reply_to_user}
                      onCheckedChange={(v) => setPolicy(prev => ({
                        ...prev,
                        system_triggers: {
                          ...prev.system_triggers,
                          lead_inject: { ...prev.system_triggers?.lead_inject, reply_to_user: v }
                        }
                      }))}
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AIBehaviorPolicyPage;
