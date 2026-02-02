import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { Avatar, AvatarFallback } from "../components/ui/avatar";
import { Textarea } from "../components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "../components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Label } from "../components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { toast } from "sonner";
import { 
  ArrowLeft, Phone, Mail, MapPin, IndianRupee, ShoppingCart, 
  MessageSquare, AlertTriangle, Tag, Plus, X, Smartphone, Clock, 
  CheckCircle, AlertCircle, Ticket, User, Edit2, Save, EyeOff,
  FileText, Upload, Brain, CreditCard, Building, Trash2, StickyNote
} from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const StatusColors = {
  open: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
  in_progress: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  resolved: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400",
  closed: "bg-slate-100 text-slate-800 dark:bg-slate-900/30 dark:text-slate-400",
  pending: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
  delivered: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400",
  processing: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  escalated: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
};

const TopicTypeColors = {
  product_inquiry: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  service_request: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400",
  support: "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400",
  order: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400",
};

function StatCard({ icon: Icon, value, label, colorClass }) {
  return (
    <Card className="p-4 border-border/50">
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${colorClass}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <p className="text-2xl font-bold">{value}</p>
          <p className="text-xs text-muted-foreground">{label}</p>
        </div>
      </div>
    </Card>
  );
}

function TopicCard({ topic }) {
  return (
    <div className="p-3 rounded-lg bg-accent/50 space-y-2">
      <div className="flex items-start justify-between gap-2">
        <p className="font-medium text-sm">{topic.title}</p>
        <Badge className={StatusColors[topic.status] || StatusColors.pending}>{topic.status}</Badge>
      </div>
      <div className="flex items-center gap-2">
        <Badge variant="outline" className={TopicTypeColors[topic.topic_type] || ""}>
          {topic.topic_type?.replace("_", " ")}
        </Badge>
        <span className="text-xs text-muted-foreground">
          {new Date(topic.created_at).toLocaleDateString()}
        </span>
      </div>
    </div>
  );
}

function OrderCard({ order }) {
  const items = order.items || [];
  return (
    <div className="p-4 rounded-lg border border-border/50 space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <p className="font-medium">Order #{order.id.slice(0, 8).toUpperCase()}</p>
          <p className="text-xs text-muted-foreground">
            {new Date(order.created_at).toLocaleDateString()} • {items.length} items
          </p>
        </div>
        <div className="text-right">
          <p className="font-bold text-emerald-600 dark:text-emerald-400 flex items-center justify-end">
            <IndianRupee className="w-4 h-4" />
            {(order.total || 0).toLocaleString('en-IN')}
          </p>
          <div className="flex gap-2 mt-1">
            <Badge className={StatusColors[order.status] || StatusColors.pending}>{order.status}</Badge>
            <Badge variant="outline">{order.payment_status}</Badge>
          </div>
        </div>
      </div>
      {items.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {items.slice(0, 3).map((item, idx) => (
            <Badge key={idx} variant="secondary" className="text-xs">
              {item.product_name || item.name} x{item.quantity}
            </Badge>
          ))}
          {items.length > 3 && (
            <Badge variant="secondary" className="text-xs">+{items.length - 3} more</Badge>
          )}
        </div>
      )}
    </div>
  );
}

function DeviceCard({ device, index, onRemove }) {
  return (
    <div className="p-4 rounded-lg border border-border/50 flex items-start gap-3">
      <div className="w-10 h-10 rounded-lg bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
        <Smartphone className="w-5 h-5 text-slate-600 dark:text-slate-400" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-medium">{device.name}</p>
        {device.model && <p className="text-sm text-muted-foreground">{device.model}</p>}
        {device.serial && <p className="text-xs text-muted-foreground font-mono">{device.serial}</p>}
        {device.purchase_date && (
          <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {new Date(device.purchase_date).toLocaleDateString()}
          </p>
        )}
      </div>
      <Button 
        variant="ghost" 
        size="icon" 
        className="text-red-500 hover:text-red-600 hover:bg-red-50"
        onClick={() => onRemove(index)}
      >
        <X className="w-4 h-4" />
      </Button>
    </div>
  );
}

const CustomerCoverPage = () => {
  const { customerId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editingNotes, setEditingNotes] = useState(false);
  const [notes, setNotes] = useState("");
  const [newTag, setNewTag] = useState("");
  const [isAddDeviceOpen, setIsAddDeviceOpen] = useState(false);
  const [deviceForm, setDeviceForm] = useState({ name: "", model: "", serial: "", purchase_date: "" });
  
  // New state for enhanced features
  const [editingDetails, setEditingDetails] = useState(false);
  const [customerDetails, setCustomerDetails] = useState({});
  const [isAddAddressOpen, setIsAddAddressOpen] = useState(false);
  const [addressForm, setAddressForm] = useState({ label: "", line1: "", line2: "", city: "", state: "", pincode: "", is_primary: false });
  const [isAddNoteOpen, setIsAddNoteOpen] = useState(false);
  const [newNoteContent, setNewNoteContent] = useState("");
  const [isUploadInvoiceOpen, setIsUploadInvoiceOpen] = useState(false);
  const [invoiceFile, setInvoiceFile] = useState(null);
  const [invoiceDescription, setInvoiceDescription] = useState("");
  const [aiInsights, setAiInsights] = useState({});
  const [paymentPrefs, setPaymentPrefs] = useState({ preferred_method: "", upi_id: "", bank_account: "" });

  const fetchData = useCallback(async () => {
    try {
      const res = await axios.get(`${API_URL}/api/customers/${customerId}/360`);
      setData(res.data);
      setNotes(res.data.customer?.notes || "");
      setCustomerDetails({
        name: res.data.customer?.name || "",
        email: res.data.customer?.email || "",
        phone: res.data.customer?.phone || "",
        company_id: res.data.customer?.company_id || "",
        customer_type: res.data.customer?.customer_type || "individual"
      });
      setPaymentPrefs(res.data.customer?.payment_preferences || { preferred_method: "", upi_id: "", bank_account: "" });
      setAiInsights(res.data.customer?.ai_insights || {});
    } catch (err) {
      toast.error("Failed to load customer data");
      navigate("/customers");
    } finally {
      setLoading(false);
    }
  }, [customerId, navigate]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const saveNotes = async () => {
    try {
      await axios.put(`${API_URL}/api/customers/${customerId}/notes?notes=${encodeURIComponent(notes)}`);
      toast.success("Notes saved");
      setEditingNotes(false);
      fetchData();
    } catch (err) {
      toast.error("Failed to save notes");
    }
  };

  const addTag = async () => {
    if (!newTag.trim()) return;
    const tags = [...(data.customer?.tags || []), newTag.trim()];
    try {
      await axios.put(`${API_URL}/api/customers/${customerId}/tags`, tags);
      toast.success("Tag added");
      setNewTag("");
      fetchData();
    } catch (err) {
      toast.error("Failed to add tag");
    }
  };

  const removeTag = async (tagToRemove) => {
    const tags = (data.customer?.tags || []).filter(t => t !== tagToRemove);
    try {
      await axios.put(`${API_URL}/api/customers/${customerId}/tags`, tags);
      toast.success("Tag removed");
      fetchData();
    } catch (err) {
      toast.error("Failed to remove tag");
    }
  };

  const addDevice = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/api/customers/${customerId}/devices`, deviceForm);
      toast.success("Device added");
      setIsAddDeviceOpen(false);
      setDeviceForm({ name: "", model: "", serial: "", purchase_date: "" });
      fetchData();
    } catch (err) {
      toast.error("Failed to add device");
    }
  };

  const removeDevice = async (index) => {
    if (!window.confirm("Remove this device?")) return;
    try {
      await axios.delete(`${API_URL}/api/customers/${customerId}/devices/${index}`);
      toast.success("Device removed");
      fetchData();
    } catch (err) {
      toast.error("Failed to remove device");
    }
  };

  // === NEW HANDLERS FOR ENHANCED FEATURES ===
  
  const saveCustomerDetails = async () => {
    try {
      await axios.put(`${API_URL}/api/customers/${customerId}/details`, {
        ...customerDetails,
        payment_preferences: paymentPrefs
      });
      toast.success("Customer details updated");
      setEditingDetails(false);
      fetchData();
    } catch (err) {
      toast.error("Failed to update details");
    }
  };

  const addAddress = async () => {
    if (!addressForm.line1 || !addressForm.city) {
      toast.error("Please fill in address line and city");
      return;
    }
    try {
      await axios.post(`${API_URL}/api/customers/${customerId}/addresses`, addressForm);
      toast.success("Address added");
      setIsAddAddressOpen(false);
      setAddressForm({ label: "", line1: "", line2: "", city: "", state: "", pincode: "", is_primary: false });
      fetchData();
    } catch (err) {
      toast.error("Failed to add address");
    }
  };

  const removeAddress = async (addressId) => {
    if (!window.confirm("Remove this address?")) return;
    try {
      await axios.delete(`${API_URL}/api/customers/${customerId}/addresses/${addressId}`);
      toast.success("Address removed");
      fetchData();
    } catch (err) {
      toast.error("Failed to remove address");
    }
  };

  const addNote = async () => {
    if (!newNoteContent.trim()) {
      toast.error("Please enter note content");
      return;
    }
    try {
      await axios.post(`${API_URL}/api/customers/${customerId}/notes?content=${encodeURIComponent(newNoteContent)}`);
      toast.success("Note added");
      setIsAddNoteOpen(false);
      setNewNoteContent("");
      fetchData();
    } catch (err) {
      toast.error("Failed to add note");
    }
  };

  const deleteNote = async (noteId) => {
    if (!window.confirm("Delete this note?")) return;
    try {
      await axios.delete(`${API_URL}/api/customers/${customerId}/notes/${noteId}`);
      toast.success("Note deleted");
      fetchData();
    } catch (err) {
      toast.error("Failed to delete note");
    }
  };

  const uploadInvoice = async () => {
    if (!invoiceFile) {
      toast.error("Please select a file");
      return;
    }
    try {
      const formData = new FormData();
      formData.append("file", invoiceFile);
      formData.append("description", invoiceDescription);
      
      await axios.post(`${API_URL}/api/customers/${customerId}/invoices?description=${encodeURIComponent(invoiceDescription)}`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      toast.success("Invoice uploaded");
      setIsUploadInvoiceOpen(false);
      setInvoiceFile(null);
      setInvoiceDescription("");
      fetchData();
    } catch (err) {
      toast.error("Failed to upload invoice");
    }
  };

  const deleteInvoice = async (invoiceId) => {
    if (!window.confirm("Delete this invoice?")) return;
    try {
      await axios.delete(`${API_URL}/api/customers/${customerId}/invoices/${invoiceId}`);
      toast.success("Invoice deleted");
      fetchData();
    } catch (err) {
      toast.error("Failed to delete invoice");
    }
  };

  const downloadInvoice = (invoiceId, filename) => {
    window.open(`${API_URL}/api/customers/${customerId}/invoices/${invoiceId}`, "_blank");
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="skeleton-pulse h-32 rounded-xl" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1,2,3,4].map(i => <div key={i} className="skeleton-pulse h-24 rounded-xl" />)}
        </div>
        <div className="skeleton-pulse h-64 rounded-xl" />
      </div>
    );
  }

  if (!data) return null;

  const { customer, statistics, active_topics, resolved_topics, orders, tickets, escalations, is_excluded, exclusion_info, lead_info } = data;
  const customerTags = customer.tags || [];
  const customerDevices = customer.devices || [];
  const customerAddresses = customer.addresses || [];
  const customerNotesHistory = customer.notes_history || [];
  const customerInvoices = customer.invoices || [];
  const customerAiInsights = customer.ai_insights || aiInsights;

  return (
    <div className="space-y-6 animate-in" data-testid="customer-360-page">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate("/customers")} data-testid="back-btn">
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold">Customer 360°</h1>
          <p className="text-muted-foreground">Complete overview of {customer.name}</p>
        </div>
      </div>

      {/* Customer Header Card */}
      <Card className="border-border/50" data-testid="customer-header-card">
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row gap-6">
            <Avatar className="w-20 h-20 mx-auto sm:mx-0">
              <AvatarFallback className="bg-primary/10 text-primary text-3xl">
                {customer.name?.charAt(0)?.toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 text-center sm:text-left space-y-3">
              <div>
                <div className="flex items-center justify-center sm:justify-start gap-2 flex-wrap">
                  <h2 className="text-2xl font-bold">{customer.name}</h2>
                  <Badge className={customer.customer_type === 'company' ? 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400' : 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'}>
                    {customer.customer_type}
                  </Badge>
                  {is_excluded && (
                    <Badge className="bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400">
                      <EyeOff className="w-3 h-3 mr-1" />Silent Mode
                    </Badge>
                  )}
                </div>
                <p className="text-sm text-muted-foreground mt-1">
                  Customer since {new Date(customer.created_at).toLocaleDateString()}
                </p>
              </div>
              <div className="flex flex-wrap items-center justify-center sm:justify-start gap-4 text-sm">
                <span className="flex items-center gap-1.5">
                  <Phone className="w-4 h-4 text-muted-foreground" />{customer.phone}
                </span>
                {customer.email && (
                  <span className="flex items-center gap-1.5">
                    <Mail className="w-4 h-4 text-muted-foreground" />{customer.email}
                  </span>
                )}
              </div>
              {customerAddresses.length > 0 && (
                <div className="flex items-start gap-1.5 text-sm">
                  <MapPin className="w-4 h-4 text-muted-foreground mt-0.5" />
                  <span className="text-muted-foreground">
                    {customerAddresses[0]?.street}, {customerAddresses[0]?.city}
                  </span>
                </div>
              )}
            </div>
            <div className="text-center sm:text-right">
              <p className="text-3xl font-bold text-emerald-600 dark:text-emerald-400 flex items-center justify-center sm:justify-end">
                <IndianRupee className="w-7 h-7" />
                {(statistics.total_spent || 0).toLocaleString('en-IN')}
              </p>
              <p className="text-sm text-muted-foreground">Total Lifetime Value</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4" data-testid="customer-stats">
        <StatCard icon={ShoppingCart} value={statistics.total_orders} label="Total Orders" colorClass="bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400" />
        <StatCard icon={AlertCircle} value={statistics.active_topics} label="Active Topics" colorClass="bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400" />
        <StatCard icon={CheckCircle} value={statistics.completed_orders} label="Delivered" colorClass="bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400" />
        <StatCard icon={MessageSquare} value={statistics.total_conversations} label="Conversations" colorClass="bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400" />
      </div>

      {/* Exclusion Warning */}
      {is_excluded && exclusion_info && (
        <Card className="border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-900/10">
          <CardContent className="p-4 flex items-center gap-4">
            <EyeOff className="w-6 h-6 text-red-600 dark:text-red-400" />
            <div className="flex-1">
              <p className="font-medium text-red-800 dark:text-red-300">Silent Monitoring Active</p>
              <p className="text-sm text-red-600 dark:text-red-400">
                {exclusion_info.tag}: {exclusion_info.reason || "No reason specified"}
              </p>
            </div>
            <Link to="/excluded-numbers">
              <Button variant="outline" size="sm">Manage</Button>
            </Link>
          </CardContent>
        </Card>
      )}

      {/* Lead Injection Info */}
      {lead_info && (
        <Card className="border-blue-200 dark:border-blue-900 bg-blue-50 dark:bg-blue-900/10">
          <CardContent className="p-4 flex items-center gap-4">
            <User className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            <div className="flex-1">
              <p className="font-medium text-blue-800 dark:text-blue-300">Owner-Injected Lead</p>
              <p className="text-sm text-blue-600 dark:text-blue-400">
                Interest: {lead_info.product_interest} • Status: {lead_info.status}
              </p>
            </div>
            <Badge className={StatusColors[lead_info.status] || StatusColors.pending}>
              {lead_info.status}
            </Badge>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <Tabs defaultValue="details" className="space-y-4">
        <TabsList className="grid grid-cols-6 lg:w-[600px]">
          <TabsTrigger value="details" data-testid="tab-details">Details</TabsTrigger>
          <TabsTrigger value="topics" data-testid="tab-topics">Topics</TabsTrigger>
          <TabsTrigger value="orders" data-testid="tab-orders">Orders</TabsTrigger>
          <TabsTrigger value="devices" data-testid="tab-devices">Devices</TabsTrigger>
          <TabsTrigger value="invoices" data-testid="tab-invoices">Invoices</TabsTrigger>
          <TabsTrigger value="notes" data-testid="tab-notes">Notes</TabsTrigger>
        </TabsList>

        {/* Details Tab - NEW */}
        <TabsContent value="details" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Customer Details Card */}
            <Card className="border-border/50">
              <CardHeader className="pb-3 flex flex-row items-center justify-between">
                <CardTitle className="text-base flex items-center gap-2">
                  <User className="w-4 h-4" />
                  Customer Details
                </CardTitle>
                {!editingDetails ? (
                  <Button variant="ghost" size="sm" onClick={() => setEditingDetails(true)}>
                    <Edit2 className="w-4 h-4 mr-1" />Edit
                  </Button>
                ) : (
                  <div className="flex gap-2">
                    <Button variant="ghost" size="sm" onClick={() => setEditingDetails(false)}>Cancel</Button>
                    <Button size="sm" onClick={saveCustomerDetails}><Save className="w-4 h-4 mr-1" />Save</Button>
                  </div>
                )}
              </CardHeader>
              <CardContent className="space-y-4">
                {editingDetails ? (
                  <>
                    <div>
                      <Label>Name</Label>
                      <Input value={customerDetails.name} onChange={e => setCustomerDetails({...customerDetails, name: e.target.value})} />
                    </div>
                    <div>
                      <Label>Email</Label>
                      <Input type="email" value={customerDetails.email} onChange={e => setCustomerDetails({...customerDetails, email: e.target.value})} />
                    </div>
                    <div>
                      <Label>Phone</Label>
                      <Input value={customerDetails.phone} onChange={e => setCustomerDetails({...customerDetails, phone: e.target.value})} />
                    </div>
                    <div>
                      <Label>Company</Label>
                      <Input value={customerDetails.company_id} onChange={e => setCustomerDetails({...customerDetails, company_id: e.target.value})} />
                    </div>
                    <div>
                      <Label>Customer Type</Label>
                      <Select value={customerDetails.customer_type} onValueChange={v => setCustomerDetails({...customerDetails, customer_type: v})}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="individual">Individual</SelectItem>
                          <SelectItem value="business">Business</SelectItem>
                          <SelectItem value="reseller">Reseller</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </>
                ) : (
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between"><span className="text-muted-foreground">Name:</span><span className="font-medium">{customer.name}</span></div>
                    <div className="flex justify-between"><span className="text-muted-foreground">Email:</span><span className="font-medium">{customer.email || "-"}</span></div>
                    <div className="flex justify-between"><span className="text-muted-foreground">Phone:</span><span className="font-medium">{customer.phone}</span></div>
                    <div className="flex justify-between"><span className="text-muted-foreground">Company:</span><span className="font-medium">{customer.company_id || "-"}</span></div>
                    <div className="flex justify-between"><span className="text-muted-foreground">Type:</span><Badge variant="outline">{customer.customer_type}</Badge></div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Payment Preferences Card */}
            <Card className="border-border/50">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <CreditCard className="w-4 h-4" />
                  Payment Preferences
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {editingDetails ? (
                  <>
                    <div>
                      <Label>Preferred Method</Label>
                      <Select value={paymentPrefs.preferred_method} onValueChange={v => setPaymentPrefs({...paymentPrefs, preferred_method: v})}>
                        <SelectTrigger><SelectValue placeholder="Select method" /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="cash">Cash</SelectItem>
                          <SelectItem value="upi">UPI</SelectItem>
                          <SelectItem value="card">Card</SelectItem>
                          <SelectItem value="bank_transfer">Bank Transfer</SelectItem>
                          <SelectItem value="cheque">Cheque</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>UPI ID</Label>
                      <Input value={paymentPrefs.upi_id || ""} onChange={e => setPaymentPrefs({...paymentPrefs, upi_id: e.target.value})} placeholder="name@upi" />
                    </div>
                    <div>
                      <Label>Bank Account</Label>
                      <Input value={paymentPrefs.bank_account || ""} onChange={e => setPaymentPrefs({...paymentPrefs, bank_account: e.target.value})} placeholder="Account details" />
                    </div>
                  </>
                ) : (
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between"><span className="text-muted-foreground">Preferred:</span><span className="font-medium">{customer.payment_preferences?.preferred_method || "Not set"}</span></div>
                    <div className="flex justify-between"><span className="text-muted-foreground">UPI:</span><span className="font-medium">{customer.payment_preferences?.upi_id || "-"}</span></div>
                    <div className="flex justify-between"><span className="text-muted-foreground">Bank:</span><span className="font-medium">{customer.payment_preferences?.bank_account || "-"}</span></div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Addresses Section */}
          <Card className="border-border/50">
            <CardHeader className="pb-3 flex flex-row items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <MapPin className="w-4 h-4" />
                Addresses ({customerAddresses.length})
              </CardTitle>
              <Dialog open={isAddAddressOpen} onOpenChange={setIsAddAddressOpen}>
                <DialogTrigger asChild>
                  <Button variant="outline" size="sm"><Plus className="w-4 h-4 mr-1" />Add Address</Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader><DialogTitle>Add Address</DialogTitle></DialogHeader>
                  <div className="space-y-3">
                    <div><Label>Label</Label><Input placeholder="Home, Office, etc." value={addressForm.label} onChange={e => setAddressForm({...addressForm, label: e.target.value})} /></div>
                    <div><Label>Address Line 1 *</Label><Input placeholder="Street address" value={addressForm.line1} onChange={e => setAddressForm({...addressForm, line1: e.target.value})} /></div>
                    <div><Label>Address Line 2</Label><Input placeholder="Apartment, suite, etc." value={addressForm.line2} onChange={e => setAddressForm({...addressForm, line2: e.target.value})} /></div>
                    <div className="grid grid-cols-2 gap-2">
                      <div><Label>City *</Label><Input value={addressForm.city} onChange={e => setAddressForm({...addressForm, city: e.target.value})} /></div>
                      <div><Label>State</Label><Input value={addressForm.state} onChange={e => setAddressForm({...addressForm, state: e.target.value})} /></div>
                    </div>
                    <div><Label>Pincode</Label><Input value={addressForm.pincode} onChange={e => setAddressForm({...addressForm, pincode: e.target.value})} /></div>
                  </div>
                  <DialogFooter><Button onClick={addAddress}>Add Address</Button></DialogFooter>
                </DialogContent>
              </Dialog>
            </CardHeader>
            <CardContent>
              {customerAddresses.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">No addresses added</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {customerAddresses.map((addr, idx) => (
                    <div key={addr.id || idx} className="p-3 rounded-lg bg-accent/50 flex justify-between items-start">
                      <div>
                        {addr.label && <Badge variant="outline" className="mb-1">{addr.label}</Badge>}
                        <p className="text-sm">{addr.line1}</p>
                        {addr.line2 && <p className="text-sm text-muted-foreground">{addr.line2}</p>}
                        <p className="text-sm text-muted-foreground">{addr.city}{addr.state && `, ${addr.state}`} {addr.pincode}</p>
                      </div>
                      <Button variant="ghost" size="icon" className="text-red-500" onClick={() => removeAddress(addr.id)}>
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* AI Insights Section */}
          <Card className="border-border/50 border-purple-200 dark:border-purple-900">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Brain className="w-4 h-4 text-purple-500" />
                AI-Collected Insights
              </CardTitle>
            </CardHeader>
            <CardContent>
              {Object.keys(customerAiInsights).length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">No insights collected yet. AI will learn from conversations.</p>
              ) : (
                <div className="space-y-4">
                  {customerAiInsights.product_interests?.length > 0 && (
                    <div>
                      <p className="text-sm font-medium mb-2">Product Interests</p>
                      <div className="flex flex-wrap gap-2">
                        {customerAiInsights.product_interests.map((item, i) => (
                          <Badge key={i} variant="secondary">{item}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  {customerAiInsights.mentioned_issues?.length > 0 && (
                    <div>
                      <p className="text-sm font-medium mb-2">Mentioned Issues</p>
                      <div className="flex flex-wrap gap-2">
                        {customerAiInsights.mentioned_issues.map((item, i) => (
                          <Badge key={i} variant="outline" className="text-orange-500">{item}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  {customerAiInsights.preferences && (
                    <div>
                      <p className="text-sm font-medium mb-2">Detected Preferences</p>
                      <div className="text-sm space-y-1">
                        {customerAiInsights.preferences.urgency && <p>Urgency: <Badge variant="destructive">{customerAiInsights.preferences.urgency}</Badge></p>}
                        {customerAiInsights.preferences.interested_in_delivery && <p>Interested in delivery</p>}
                        {customerAiInsights.preferences.interested_in_emi && <p>Interested in EMI/Installments</p>}
                        {customerAiInsights.preferences.needs_support && <p>Needs support/repair</p>}
                      </div>
                    </div>
                  )}
                  {customerAiInsights.interaction_count && (
                    <p className="text-xs text-muted-foreground">Total interactions: {customerAiInsights.interaction_count}</p>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Topics Tab */}
        <TabsContent value="topics" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card className="border-border/50">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-amber-500" />
                  Active Topics ({statistics.active_topics})
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {active_topics.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-4">No active topics</p>
                ) : (
                  active_topics.map(topic => <TopicCard key={topic.id} topic={topic} />)
                )}
              </CardContent>
            </Card>

            <Card className="border-border/50">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-emerald-500" />
                  Resolved Topics ({statistics.resolved_topics})
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {resolved_topics.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-4">No resolved topics</p>
                ) : (
                  resolved_topics.slice(0, 5).map(topic => <TopicCard key={topic.id} topic={topic} />)
                )}
              </CardContent>
            </Card>
          </div>

          {(tickets.length > 0 || escalations.length > 0) && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {tickets.length > 0 && (
                <Card className="border-border/50">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center gap-2">
                      <Ticket className="w-4 h-4" />Tickets ({tickets.length})
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {tickets.slice(0, 5).map(ticket => (
                      <div key={ticket.id} className="flex items-center justify-between p-2 rounded bg-accent/30">
                        <div>
                          <p className="text-sm font-medium">{ticket.ticket_number}</p>
                          <p className="text-xs text-muted-foreground">{ticket.subject}</p>
                        </div>
                        <Badge className={StatusColors[ticket.status] || StatusColors.pending}>{ticket.status}</Badge>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}

              {escalations.length > 0 && (
                <Card className="border-border/50">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-red-500" />Escalations ({escalations.length})
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {escalations.slice(0, 5).map(esc => (
                      <div key={esc.id} className="flex items-center justify-between p-2 rounded bg-red-50 dark:bg-red-900/10">
                        <div>
                          <p className="text-sm font-medium text-red-800 dark:text-red-300">{esc.reason}</p>
                          <p className="text-xs text-muted-foreground">{new Date(esc.created_at).toLocaleDateString()}</p>
                        </div>
                        <Badge className={StatusColors[esc.status] || StatusColors.pending}>{esc.status}</Badge>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </TabsContent>

        {/* Orders Tab */}
        <TabsContent value="orders">
          <Card className="border-border/50">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Order History</CardTitle>
            </CardHeader>
            <CardContent>
              {orders.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-8">No orders yet</p>
              ) : (
                <div className="space-y-3">
                  {orders.map(order => <OrderCard key={order.id} order={order} />)}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Devices Tab */}
        <TabsContent value="devices">
          <Card className="border-border/50">
            <CardHeader className="pb-3 flex flex-row items-center justify-between">
              <CardTitle className="text-base">Devices Owned</CardTitle>
              <Dialog open={isAddDeviceOpen} onOpenChange={setIsAddDeviceOpen}>
                <DialogTrigger asChild>
                  <Button size="sm" data-testid="add-device-btn">
                    <Plus className="w-4 h-4 mr-1" />Add Device
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-md">
                  <DialogHeader><DialogTitle>Add Device</DialogTitle></DialogHeader>
                  <form onSubmit={addDevice} className="space-y-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Device Name *</label>
                      <Input 
                        value={deviceForm.name} 
                        onChange={(e) => setDeviceForm({...deviceForm, name: e.target.value})} 
                        placeholder="e.g., iPhone 15 Pro Max"
                        required 
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Model/Variant</label>
                      <Input 
                        value={deviceForm.model} 
                        onChange={(e) => setDeviceForm({...deviceForm, model: e.target.value})} 
                        placeholder="e.g., 256GB Blue Titanium"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Serial/IMEI</label>
                      <Input 
                        value={deviceForm.serial} 
                        onChange={(e) => setDeviceForm({...deviceForm, serial: e.target.value})} 
                        placeholder="Serial number"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Purchase Date</label>
                      <Input 
                        type="date"
                        value={deviceForm.purchase_date} 
                        onChange={(e) => setDeviceForm({...deviceForm, purchase_date: e.target.value})} 
                      />
                    </div>
                    <div className="flex gap-3 pt-2">
                      <Button type="button" variant="outline" onClick={() => setIsAddDeviceOpen(false)} className="flex-1">Cancel</Button>
                      <Button type="submit" className="flex-1">Add Device</Button>
                    </div>
                  </form>
                </DialogContent>
              </Dialog>
            </CardHeader>
            <CardContent>
              {customerDevices.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-8">No devices recorded</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {customerDevices.map((device, idx) => (
                    <DeviceCard key={idx} device={device} index={idx} onRemove={removeDevice} />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notes & Tags Tab */}
        <TabsContent value="notes" className="space-y-4">
          <Card className="border-border/50">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Tag className="w-4 h-4" />Customer Tags
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex flex-wrap gap-2">
                {customerTags.map((tag, idx) => (
                  <Badge key={idx} variant="secondary" className="px-3 py-1 flex items-center gap-1">
                    {tag}
                    <button onClick={() => removeTag(tag)} className="ml-1 hover:text-red-500">
                      <X className="w-3 h-3" />
                    </button>
                  </Badge>
                ))}
                {customerTags.length === 0 && (
                  <p className="text-sm text-muted-foreground">No tags yet</p>
                )}
              </div>
              <div className="flex gap-2">
                <Input 
                  placeholder="Add a tag..." 
                  value={newTag} 
                  onChange={(e) => setNewTag(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addTag()}
                  className="flex-1"
                />
                <Button onClick={addTag} size="sm">
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border/50">
            <CardHeader className="pb-3 flex flex-row items-center justify-between">
              <CardTitle className="text-base">Internal Notes</CardTitle>
              {!editingNotes ? (
                <Button variant="ghost" size="sm" onClick={() => setEditingNotes(true)}>
                  <Edit2 className="w-4 h-4 mr-1" />Edit
                </Button>
              ) : (
                <Button size="sm" onClick={saveNotes}>
                  <Save className="w-4 h-4 mr-1" />Save
                </Button>
              )}
            </CardHeader>
            <CardContent>
              {editingNotes ? (
                <Textarea 
                  value={notes} 
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Add internal notes about this customer..."
                  rows={6}
                  className="resize-none"
                />
              ) : (
                <div className="p-4 rounded-lg bg-accent/50 min-h-[100px]">
                  {notes ? (
                    <p className="text-sm whitespace-pre-wrap">{notes}</p>
                  ) : (
                    <p className="text-sm text-muted-foreground">No notes yet. Click Edit to add notes.</p>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default CustomerCoverPage;
