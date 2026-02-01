import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "../components/ui/dialog";
import { Textarea } from "../components/ui/textarea";
import { toast } from "sonner";
import { Rocket, UserPlus, Phone, Package, MessageSquare, Clock, CheckCircle, AlertCircle } from "lucide-react";

var API_URL = process.env.REACT_APP_BACKEND_URL;

function LeadsPage() {
  var [leads, setLeads] = useState([]);
  var [loading, setLoading] = useState(true);
  var [isDialogOpen, setIsDialogOpen] = useState(false);
  var [formData, setFormData] = useState({
    customer_name: "",
    phone: "",
    product_interest: "",
    notes: ""
  });
  var [submitting, setSubmitting] = useState(false);

  var fetchLeads = async function() {
    try {
      var token = localStorage.getItem("sales-brain-token");
      if (!token) {
        console.error("No auth token found");
        setLoading(false);
        return;
      }
      var response = await fetch(API_URL + "/api/leads", {
        headers: { "Authorization": "Bearer " + token }
      });
      if (!response.ok) {
        throw new Error("Failed to fetch leads: " + response.status);
      }
      var data = await response.json();
      setLeads(data);
    } catch (error) {
      console.error("Error fetching leads:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(function() {
    fetchLeads();
  }, []);

  var handleInjectLead = async function() {
    if (!formData.customer_name || !formData.phone || !formData.product_interest) {
      toast.error("Please fill all required fields");
      return;
    }

    setSubmitting(true);
    try {
      var token = localStorage.getItem("token");
      var response = await fetch(API_URL + "/api/leads/inject", {
        method: "POST",
        headers: {
          "Authorization": "Bearer " + token,
          "Content-Type": "application/json"
        },
        body: JSON.stringify(formData)
      });
      var data = await response.json();
      
      if (response.ok) {
        if (data.outbound_message_sent) {
          toast.success("Lead Injected! AI has initiated contact with " + formData.customer_name);
        } else {
          toast.success("Lead created. WhatsApp message pending (connect WhatsApp first).");
        }
        setIsDialogOpen(false);
        setFormData({ customer_name: "", phone: "", product_interest: "", notes: "" });
        fetchLeads();
      } else {
        toast.error(data.detail || "Failed to inject lead");
      }
    } catch (error) {
      console.error("Error injecting lead:", error);
      toast.error("Failed to inject lead");
    } finally {
      setSubmitting(false);
    }
  };

  var updateLeadStatus = async function(leadId, newStatus) {
    try {
      var token = localStorage.getItem("token");
      await fetch(API_URL + "/api/leads/" + leadId + "/status?status=" + newStatus, {
        method: "PUT",
        headers: { "Authorization": "Bearer " + token }
      });
      toast.success("Status Updated");
      fetchLeads();
    } catch (error) {
      toast.error("Failed to update status");
    }
  };

  var getStatusBadge = function(status) {
    var variants = {
      pending: { variant: "secondary", icon: Clock },
      in_progress: { variant: "default", icon: MessageSquare },
      completed: { variant: "success", icon: CheckCircle },
      escalated: { variant: "destructive", icon: AlertCircle }
    };
    var config = variants[status] || variants.pending;
    var Icon = config.icon;
    return (
      <Badge variant={config.variant} className="gap-1">
        <Icon className="h-3 w-3" />
        {status.replace("_", " ")}
      </Badge>
    );
  };

  return (
    <div className="space-y-6" data-testid="leads-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Rocket className="h-6 w-6 text-primary" />
            Lead Injection
          </h1>
          <p className="text-muted-foreground">Inject leads and let AI handle outreach automatically</p>
        </div>
        
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button data-testid="inject-lead-btn">
              <UserPlus className="h-4 w-4 mr-2" />
              Inject New Lead
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Inject New Lead</DialogTitle>
              <DialogDescription>
                Enter lead details. AI will create the customer profile and initiate contact automatically.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 pt-4">
              <div className="space-y-2">
                <Label htmlFor="customer_name">Customer Name *</Label>
                <Input
                  id="customer_name"
                  data-testid="lead-customer-name"
                  placeholder="e.g., Rahul Sharma"
                  value={formData.customer_name}
                  onChange={function(e) { setFormData({...formData, customer_name: e.target.value}); }}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone">Phone Number *</Label>
                <Input
                  id="phone"
                  data-testid="lead-phone"
                  placeholder="e.g., 9876543210"
                  value={formData.phone}
                  onChange={function(e) { setFormData({...formData, phone: e.target.value}); }}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="product_interest">Product Interest *</Label>
                <Input
                  id="product_interest"
                  data-testid="lead-product"
                  placeholder="e.g., iPhone 15 Pro Max"
                  value={formData.product_interest}
                  onChange={function(e) { setFormData({...formData, product_interest: e.target.value}); }}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="notes">Notes (Optional)</Label>
                <Textarea
                  id="notes"
                  data-testid="lead-notes"
                  placeholder="Any additional context..."
                  value={formData.notes}
                  onChange={function(e) { setFormData({...formData, notes: e.target.value}); }}
                />
              </div>
              <Button 
                className="w-full" 
                onClick={handleInjectLead}
                disabled={submitting}
                data-testid="submit-lead-btn"
              >
                {submitting ? "Injecting..." : "Inject Lead & Start AI Outreach"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Injected Leads</CardTitle>
          <CardDescription>Track leads you've assigned to the AI sales assistant</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-muted-foreground">Loading...</div>
          ) : leads.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Rocket className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>No leads injected yet</p>
              <p className="text-sm">Click "Inject New Lead" to get started</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Customer</TableHead>
                  <TableHead>Product Interest</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Message Sent</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {leads.map(function(lead) {
                  return (
                    <TableRow key={lead.id} data-testid={"lead-row-" + lead.id}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{lead.customer_name}</div>
                          <div className="text-sm text-muted-foreground flex items-center gap-1">
                            <Phone className="h-3 w-3" />
                            {lead.phone}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Package className="h-4 w-4 text-muted-foreground" />
                          {lead.product_interest}
                        </div>
                      </TableCell>
                      <TableCell>{getStatusBadge(lead.status)}</TableCell>
                      <TableCell>
                        {lead.outbound_message_sent ? (
                          <Badge variant="success" className="gap-1">
                            <CheckCircle className="h-3 w-3" />
                            Sent
                          </Badge>
                        ) : (
                          <Badge variant="secondary">Pending</Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {new Date(lead.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <Select
                          value={lead.status}
                          onValueChange={function(value) { updateLeadStatus(lead.id, value); }}
                        >
                          <SelectTrigger className="w-32">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="pending">Pending</SelectItem>
                            <SelectItem value="in_progress">In Progress</SelectItem>
                            <SelectItem value="completed">Completed</SelectItem>
                            <SelectItem value="escalated">Escalated</SelectItem>
                          </SelectContent>
                        </Select>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default LeadsPage;
