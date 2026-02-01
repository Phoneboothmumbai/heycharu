import { useState, useEffect } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Avatar, AvatarFallback } from "../components/ui/avatar";
import { ScrollArea } from "../components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../components/ui/dialog";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "../components/ui/sheet";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { Textarea } from "../components/ui/textarea";
import { toast } from "sonner";
import {
  Search,
  Plus,
  User,
  Phone,
  Mail,
  MapPin,
  IndianRupee,
  Tag,
  Calendar,
  Smartphone,
  Building,
} from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const CustomerTypeColors = {
  individual: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  company: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400",
  employee: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
};

const CustomersPage = () => {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [newCustomer, setNewCustomer] = useState({
    name: "",
    email: "",
    phone: "",
    customer_type: "individual",
    notes: "",
  });

  useEffect(() => {
    fetchCustomers();
  }, [search, typeFilter]);

  const fetchCustomers = async () => {
    try {
      const params = new URLSearchParams();
      if (search) params.append("search", search);
      if (typeFilter) params.append("customer_type", typeFilter);
      
      const response = await axios.get(`${API_URL}/api/customers?${params}`);
      setCustomers(response.data);
    } catch (error) {
      toast.error("Failed to load customers");
    } finally {
      setLoading(false);
    }
  };

  const handleAddCustomer = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/api/customers`, newCustomer);
      toast.success("Customer added successfully");
      setIsAddDialogOpen(false);
      setNewCustomer({ name: "", email: "", phone: "", customer_type: "individual", notes: "" });
      fetchCustomers();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to add customer");
    }
  };

  const handleDeleteCustomer = async (id) => {
    if (!window.confirm("Are you sure you want to delete this customer?")) return;
    
    try {
      await axios.delete(`${API_URL}/api/customers/${id}`);
      toast.success("Customer deleted");
      setSelectedCustomer(null);
      fetchCustomers();
    } catch (error) {
      toast.error("Failed to delete customer");
    }
  };

  return (
    <div className="space-y-6 animate-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Customers</h1>
          <p className="text-muted-foreground">Manage your customer database</p>
        </div>
        
        <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
          <DialogTrigger asChild>
            <Button className="btn-primary" data-testid="add-customer-btn">
              <Plus className="w-4 h-4 mr-2" />
              Add Customer
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>Add New Customer</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleAddCustomer} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Full Name *</Label>
                <Input
                  id="name"
                  value={newCustomer.name}
                  onChange={(e) => setNewCustomer({ ...newCustomer, name: e.target.value })}
                  required
                  placeholder="Enter customer name"
                  data-testid="customer-name-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone">Phone *</Label>
                <Input
                  id="phone"
                  value={newCustomer.phone}
                  onChange={(e) => setNewCustomer({ ...newCustomer, phone: e.target.value })}
                  required
                  placeholder="+91 98765 43210"
                  data-testid="customer-phone-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={newCustomer.email}
                  onChange={(e) => setNewCustomer({ ...newCustomer, email: e.target.value })}
                  placeholder="customer@example.com"
                  data-testid="customer-email-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="type">Customer Type</Label>
                <Select
                  value={newCustomer.customer_type}
                  onValueChange={(value) => setNewCustomer({ ...newCustomer, customer_type: value })}
                >
                  <SelectTrigger data-testid="customer-type-select">
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="individual">Individual</SelectItem>
                    <SelectItem value="company">Company</SelectItem>
                    <SelectItem value="employee">Employee</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="notes">Notes</Label>
                <Textarea
                  id="notes"
                  value={newCustomer.notes}
                  onChange={(e) => setNewCustomer({ ...newCustomer, notes: e.target.value })}
                  placeholder="Additional notes..."
                  rows={3}
                  data-testid="customer-notes-input"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <Button type="button" variant="outline" onClick={() => setIsAddDialogOpen(false)} className="flex-1">
                  Cancel
                </Button>
                <Button type="submit" className="flex-1 btn-primary" data-testid="save-customer-btn">
                  Save Customer
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search customers..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
            data-testid="customer-search-input"
          />
        </div>
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-full sm:w-48" data-testid="customer-type-filter">
            <SelectValue placeholder="All Types" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="individual">Individual</SelectItem>
            <SelectItem value="company">Company</SelectItem>
            <SelectItem value="employee">Employee</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Customer List */}
      <Card className="border-border/50">
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="skeleton-pulse h-16 rounded" />
              ))}
            </div>
          ) : customers.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
              <User className="w-16 h-16 mb-4 opacity-50" />
              <p className="text-lg font-medium">No customers found</p>
              <p className="text-sm">Add your first customer to get started</p>
            </div>
          ) : (
            <div className="divide-y divide-border">
              {customers.map((customer) => (
                <div
                  key={customer.id}
                  onClick={() => setSelectedCustomer(customer)}
                  className="flex items-center gap-4 p-4 hover:bg-accent cursor-pointer transition-colors"
                  data-testid={`customer-row-${customer.id}`}
                >
                  <Avatar className="w-12 h-12">
                    <AvatarFallback className="bg-primary/10 text-primary text-lg">
                      {customer.name?.charAt(0)?.toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="font-semibold truncate">{customer.name}</p>
                      <Badge className={CustomerTypeColors[customer.customer_type]}>
                        {customer.customer_type}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground mt-1">
                      <span className="flex items-center gap-1">
                        <Phone className="w-3 h-3" />
                        {customer.phone}
                      </span>
                      {customer.email && (
                        <span className="flex items-center gap-1 truncate">
                          <Mail className="w-3 h-3" />
                          {customer.email}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="text-right hidden sm:block">
                    <p className="font-semibold text-emerald-600 dark:text-emerald-400 flex items-center justify-end">
                      <IndianRupee className="w-4 h-4" />
                      {(customer.total_spent || 0).toLocaleString('en-IN')}
                    </p>
                    <p className="text-xs text-muted-foreground">Total Spent</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Customer Detail Sheet */}
      <Sheet open={!!selectedCustomer} onOpenChange={() => setSelectedCustomer(null)}>
        <SheetContent className="w-full sm:max-w-lg overflow-y-auto">
          {selectedCustomer && (
            <>
              <SheetHeader className="pb-6">
                <div className="flex items-center gap-4">
                  <Avatar className="w-16 h-16">
                    <AvatarFallback className="bg-primary/10 text-primary text-2xl">
                      {selectedCustomer.name?.charAt(0)?.toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <SheetTitle className="text-xl">{selectedCustomer.name}</SheetTitle>
                    <Badge className={CustomerTypeColors[selectedCustomer.customer_type]}>
                      {selectedCustomer.customer_type}
                    </Badge>
                  </div>
                </div>
              </SheetHeader>

              <div className="space-y-6">
                {/* Contact Info */}
                <div className="space-y-3">
                  <h3 className="font-semibold text-sm text-muted-foreground uppercase tracking-wider">Contact</h3>
                  <div className="space-y-2">
                    <div className="flex items-center gap-3 text-sm">
                      <Phone className="w-4 h-4 text-muted-foreground" />
                      <span>{selectedCustomer.phone}</span>
                    </div>
                    {selectedCustomer.email && (
                      <div className="flex items-center gap-3 text-sm">
                        <Mail className="w-4 h-4 text-muted-foreground" />
                        <span>{selectedCustomer.email}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Addresses */}
                {selectedCustomer.addresses?.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="font-semibold text-sm text-muted-foreground uppercase tracking-wider">Addresses</h3>
                    <div className="space-y-2">
                      {selectedCustomer.addresses.map((addr, idx) => (
                        <div key={idx} className="flex items-start gap-3 text-sm p-3 bg-accent rounded-lg">
                          <MapPin className="w-4 h-4 text-muted-foreground mt-0.5" />
                          <div>
                            <Badge variant="outline" className="text-xs mb-1">{addr.type}</Badge>
                            <p>{addr.address}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Devices */}
                {selectedCustomer.devices?.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="font-semibold text-sm text-muted-foreground uppercase tracking-wider">Devices</h3>
                    <div className="space-y-2">
                      {selectedCustomer.devices.map((device, idx) => (
                        <div key={idx} className="flex items-center gap-3 text-sm p-3 bg-accent rounded-lg">
                          <Smartphone className="w-4 h-4 text-muted-foreground" />
                          <div>
                            <p className="font-medium">{device.type}</p>
                            <p className="text-xs text-muted-foreground">Purchased: {device.purchased}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Tags */}
                {selectedCustomer.tags?.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="font-semibold text-sm text-muted-foreground uppercase tracking-wider">Tags</h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedCustomer.tags.map((tag, idx) => (
                        <Badge key={idx} variant="outline">
                          <Tag className="w-3 h-3 mr-1" />
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Stats */}
                <div className="grid grid-cols-2 gap-4">
                  <Card className="p-4">
                    <p className="text-xs text-muted-foreground">Total Spent</p>
                    <p className="text-xl font-bold text-emerald-600 dark:text-emerald-400 flex items-center">
                      <IndianRupee className="w-5 h-5" />
                      {(selectedCustomer.total_spent || 0).toLocaleString('en-IN')}
                    </p>
                  </Card>
                  <Card className="p-4">
                    <p className="text-xs text-muted-foreground">Orders</p>
                    <p className="text-xl font-bold">
                      {selectedCustomer.purchase_history?.length || 0}
                    </p>
                  </Card>
                </div>

                {/* Notes */}
                {selectedCustomer.notes && (
                  <div className="space-y-3">
                    <h3 className="font-semibold text-sm text-muted-foreground uppercase tracking-wider">Notes</h3>
                    <p className="text-sm bg-accent p-3 rounded-lg">{selectedCustomer.notes}</p>
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-3 pt-4">
                  <Button
                    variant="destructive"
                    onClick={() => handleDeleteCustomer(selectedCustomer.id)}
                    className="flex-1"
                    data-testid="delete-customer-btn"
                  >
                    Delete Customer
                  </Button>
                </div>
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
};

export default CustomersPage;
