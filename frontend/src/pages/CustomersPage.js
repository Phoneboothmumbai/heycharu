import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { Card, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Avatar, AvatarFallback } from "../components/ui/avatar";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../components/ui/dialog";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "../components/ui/sheet";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Textarea } from "../components/ui/textarea";
import { toast } from "sonner";
import { Search, Plus, User, Phone, Mail, IndianRupee } from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const TypeColors = {
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
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", phone: "", customer_type: "individual", notes: "" });

  const fetchCustomers = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (search) params.append("search", search);
      if (typeFilter && typeFilter !== "all") params.append("customer_type", typeFilter);
      const res = await axios.get(`${API_URL}/api/customers?${params}`);
      setCustomers(res.data);
    } catch (e) {
      toast.error("Failed to load customers");
    } finally {
      setLoading(false);
    }
  }, [search, typeFilter]);

  useEffect(() => { fetchCustomers(); }, [fetchCustomers]);

  const handleAdd = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/api/customers`, form);
      toast.success("Customer added");
      setIsAddOpen(false);
      setForm({ name: "", email: "", phone: "", customer_type: "individual", notes: "" });
      fetchCustomers();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to add");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this customer?")) return;
    try {
      await axios.delete(`${API_URL}/api/customers/${id}`);
      toast.success("Customer deleted");
      setSelectedCustomer(null);
      fetchCustomers();
    } catch (e) {
      toast.error("Failed to delete");
    }
  };

  return (
    <div className="space-y-6 animate-in">
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Customers</h1>
          <p className="text-muted-foreground">Manage your customer database</p>
        </div>
        <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
          <DialogTrigger asChild>
            <Button className="btn-primary" data-testid="add-customer-btn">
              <Plus className="w-4 h-4 mr-2" />Add Customer
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-md">
            <DialogHeader><DialogTitle>Add New Customer</DialogTitle></DialogHeader>
            <form onSubmit={handleAdd} className="space-y-4">
              <div className="space-y-2">
                <Label>Full Name *</Label>
                <Input value={form.name} onChange={(e) => setForm({...form, name: e.target.value})} required data-testid="customer-name-input" />
              </div>
              <div className="space-y-2">
                <Label>Phone *</Label>
                <Input value={form.phone} onChange={(e) => setForm({...form, phone: e.target.value})} required data-testid="customer-phone-input" />
              </div>
              <div className="space-y-2">
                <Label>Email</Label>
                <Input type="email" value={form.email} onChange={(e) => setForm({...form, email: e.target.value})} data-testid="customer-email-input" />
              </div>
              <div className="space-y-2">
                <Label>Type</Label>
                <Select value={form.customer_type} onValueChange={(v) => setForm({...form, customer_type: v})}>
                  <SelectTrigger data-testid="customer-type-select"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="individual">Individual</SelectItem>
                    <SelectItem value="company">Company</SelectItem>
                    <SelectItem value="employee">Employee</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Notes</Label>
                <Textarea value={form.notes} onChange={(e) => setForm({...form, notes: e.target.value})} rows={3} data-testid="customer-notes-input" />
              </div>
              <div className="flex gap-3 pt-4">
                <Button type="button" variant="outline" onClick={() => setIsAddOpen(false)} className="flex-1">Cancel</Button>
                <Button type="submit" className="flex-1 btn-primary" data-testid="save-customer-btn">Save</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input placeholder="Search customers..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-10" data-testid="customer-search-input" />
        </div>
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-full sm:w-48" data-testid="customer-type-filter"><SelectValue placeholder="All Types" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="individual">Individual</SelectItem>
            <SelectItem value="company">Company</SelectItem>
            <SelectItem value="employee">Employee</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card className="border-border/50">
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-4">{[1,2,3].map(i => <div key={i} className="skeleton-pulse h-16 rounded" />)}</div>
          ) : customers.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
              <User className="w-16 h-16 mb-4 opacity-50" />
              <p className="text-lg font-medium">No customers found</p>
            </div>
          ) : (
            <div className="divide-y divide-border">
              {customers.map(c => (
                <div key={c.id} onClick={() => setSelectedCustomer(c)} className="flex items-center gap-4 p-4 hover:bg-accent cursor-pointer transition-colors" data-testid={`customer-row-${c.id}`}>
                  <Avatar className="w-12 h-12"><AvatarFallback className="bg-primary/10 text-primary text-lg">{c.name?.charAt(0)?.toUpperCase()}</AvatarFallback></Avatar>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="font-semibold truncate">{c.name}</p>
                      <Badge className={TypeColors[c.customer_type]}>{c.customer_type}</Badge>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground mt-1">
                      <span className="flex items-center gap-1"><Phone className="w-3 h-3" />{c.phone}</span>
                      {c.email && <span className="flex items-center gap-1 truncate"><Mail className="w-3 h-3" />{c.email}</span>}
                    </div>
                  </div>
                  <div className="text-right hidden sm:block">
                    <p className="font-semibold text-emerald-600 dark:text-emerald-400 flex items-center justify-end">
                      <IndianRupee className="w-4 h-4" />{(c.total_spent || 0).toLocaleString('en-IN')}
                    </p>
                    <p className="text-xs text-muted-foreground">Total Spent</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Sheet open={!!selectedCustomer} onOpenChange={() => setSelectedCustomer(null)}>
        <SheetContent className="w-full sm:max-w-lg overflow-y-auto">
          {selectedCustomer && (
            <>
              <SheetHeader className="pb-6">
                <div className="flex items-center gap-4">
                  <Avatar className="w-16 h-16"><AvatarFallback className="bg-primary/10 text-primary text-2xl">{selectedCustomer.name?.charAt(0)?.toUpperCase()}</AvatarFallback></Avatar>
                  <div>
                    <SheetTitle className="text-xl">{selectedCustomer.name}</SheetTitle>
                    <Badge className={TypeColors[selectedCustomer.customer_type]}>{selectedCustomer.customer_type}</Badge>
                  </div>
                </div>
              </SheetHeader>
              <div className="space-y-6">
                <div className="space-y-2">
                  <p className="flex items-center gap-3 text-sm"><Phone className="w-4 h-4 text-muted-foreground" />{selectedCustomer.phone}</p>
                  {selectedCustomer.email && <p className="flex items-center gap-3 text-sm"><Mail className="w-4 h-4 text-muted-foreground" />{selectedCustomer.email}</p>}
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <Card className="p-4">
                    <p className="text-xs text-muted-foreground">Total Spent</p>
                    <p className="text-xl font-bold text-emerald-600 dark:text-emerald-400 flex items-center"><IndianRupee className="w-5 h-5" />{(selectedCustomer.total_spent || 0).toLocaleString('en-IN')}</p>
                  </Card>
                  <Card className="p-4">
                    <p className="text-xs text-muted-foreground">Orders</p>
                    <p className="text-xl font-bold">{selectedCustomer.purchase_history?.length || 0}</p>
                  </Card>
                </div>
                {selectedCustomer.notes && <div className="space-y-2"><h3 className="text-sm font-semibold text-muted-foreground uppercase">Notes</h3><p className="text-sm bg-accent p-3 rounded-lg">{selectedCustomer.notes}</p></div>}
                <Button variant="destructive" onClick={() => handleDelete(selectedCustomer.id)} className="w-full" data-testid="delete-customer-btn">Delete Customer</Button>
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
};

export default CustomersPage;
