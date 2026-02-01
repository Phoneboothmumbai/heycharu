import { useState, useEffect } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { ScrollArea } from "../components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "../components/ui/sheet";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { toast } from "sonner";
import {
  ShoppingCart,
  IndianRupee,
  Package,
  Truck,
  CheckCircle,
  Clock,
  XCircle,
  Ticket,
  MapPin,
  User,
} from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const orderStatuses = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"];
const ticketStatuses = ["open", "in_progress", "resolved", "closed"];

const StatusColors = {
  pending: "status-pending",
  confirmed: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  processing: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400",
  shipped: "bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-400",
  delivered: "status-active",
  cancelled: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
  open: "status-pending",
  in_progress: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  resolved: "status-active",
  closed: "status-closed",
  paid: "status-active",
  failed: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
};

const StatusIcons = {
  pending: Clock,
  confirmed: CheckCircle,
  processing: Package,
  shipped: Truck,
  delivered: CheckCircle,
  cancelled: XCircle,
};

const OrdersPage = () => {
  const [orders, setOrders] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("all");
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [selectedTicket, setSelectedTicket] = useState(null);

  useEffect(() => {
    fetchData();
  }, [statusFilter]);

  const fetchData = async () => {
    try {
      const params = (statusFilter && statusFilter !== "all") ? `?status=${statusFilter}` : "";
      const [ordersRes, ticketsRes] = await Promise.all([
        axios.get(`${API_URL}/api/orders${params}`),
        axios.get(`${API_URL}/api/tickets${params}`),
      ]);
      setOrders(ordersRes.data);
      setTickets(ticketsRes.data);
    } catch (error) {
      toast.error("Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  const updateOrderStatus = async (orderId, status) => {
    try {
      await axios.put(`${API_URL}/api/orders/${orderId}/status?status=${status}`);
      toast.success("Order status updated");
      fetchData();
      setSelectedOrder(null);
    } catch (error) {
      toast.error("Failed to update status");
    }
  };

  const updateTicketStatus = async (ticketId, status) => {
    try {
      await axios.put(`${API_URL}/api/tickets/${ticketId}/status?status=${status}`);
      toast.success("Ticket status updated");
      fetchData();
      setSelectedTicket(null);
    } catch (error) {
      toast.error("Failed to update status");
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return "";
    return new Date(dateString).toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="space-y-6 animate-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Orders & Tickets</h1>
          <p className="text-muted-foreground">Track orders and support tickets</p>
        </div>
      </div>

      <Tabs defaultValue="orders" className="w-full">
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <TabsList>
            <TabsTrigger value="orders" data-testid="orders-tab">
              <ShoppingCart className="w-4 h-4 mr-2" />
              Orders
            </TabsTrigger>
            <TabsTrigger value="tickets" data-testid="tickets-tab">
              <Ticket className="w-4 h-4 mr-2" />
              Tickets (osTicket)
            </TabsTrigger>
          </TabsList>
          
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-full sm:w-48" data-testid="status-filter">
              <SelectValue placeholder="All Statuses" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              {orderStatuses.map((status) => (
                <SelectItem key={status} value={status} className="capitalize">
                  {status}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Orders Tab */}
        <TabsContent value="orders" className="mt-6">
          <Card className="border-border/50">
            <CardContent className="p-0">
              {loading ? (
                <div className="p-6 space-y-4">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="skeleton-pulse h-16 rounded" />
                  ))}
                </div>
              ) : orders.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
                  <ShoppingCart className="w-16 h-16 mb-4 opacity-50" />
                  <p className="text-lg font-medium">No orders found</p>
                  <p className="text-sm">Orders will appear here when customers place them</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Order ID</TableHead>
                      <TableHead>Customer</TableHead>
                      <TableHead>Items</TableHead>
                      <TableHead>Total</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Payment</TableHead>
                      <TableHead>Date</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {orders.map((order) => {
                      const StatusIcon = StatusIcons[order.status] || Clock;
                      return (
                        <TableRow 
                          key={order.id}
                          className="cursor-pointer"
                          onClick={() => setSelectedOrder(order)}
                          data-testid={`order-row-${order.id}`}
                        >
                          <TableCell className="font-mono text-xs">
                            {order.id.slice(0, 8)}...
                          </TableCell>
                          <TableCell className="font-medium">{order.customer_name}</TableCell>
                          <TableCell>{order.items?.length || 0} items</TableCell>
                          <TableCell className="font-semibold flex items-center">
                            <IndianRupee className="w-4 h-4" />
                            {order.total.toLocaleString('en-IN')}
                          </TableCell>
                          <TableCell>
                            <Badge className={StatusColors[order.status]}>
                              <StatusIcon className="w-3 h-3 mr-1" />
                              {order.status}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Badge className={StatusColors[order.payment_status]}>
                              {order.payment_status}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-muted-foreground text-sm">
                            {formatDate(order.created_at)}
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

        {/* Tickets Tab */}
        <TabsContent value="tickets" className="mt-6">
          <Card className="border-border/50">
            <CardHeader className="border-b border-border">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs">MOCKED</Badge>
                <span className="text-sm text-muted-foreground">osTicket Integration</span>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              {loading ? (
                <div className="p-6 space-y-4">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="skeleton-pulse h-16 rounded" />
                  ))}
                </div>
              ) : tickets.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
                  <Ticket className="w-16 h-16 mb-4 opacity-50" />
                  <p className="text-lg font-medium">No tickets found</p>
                  <p className="text-sm">Tickets are auto-created when orders are placed</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Ticket #</TableHead>
                      <TableHead>Subject</TableHead>
                      <TableHead>Customer</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Priority</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Created</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {tickets.map((ticket) => (
                      <TableRow 
                        key={ticket.id}
                        className="cursor-pointer"
                        onClick={() => setSelectedTicket(ticket)}
                        data-testid={`ticket-row-${ticket.id}`}
                      >
                        <TableCell className="font-mono text-xs">
                          {ticket.ticket_number}
                        </TableCell>
                        <TableCell className="font-medium max-w-xs truncate">
                          {ticket.subject}
                        </TableCell>
                        <TableCell>{ticket.customer_name}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{ticket.category}</Badge>
                        </TableCell>
                        <TableCell>
                          <Badge className={
                            ticket.priority === "high" 
                              ? "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"
                              : ticket.priority === "medium"
                              ? "status-pending"
                              : "status-closed"
                          }>
                            {ticket.priority}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge className={StatusColors[ticket.status]}>
                            {ticket.status.replace("_", " ")}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-muted-foreground text-sm">
                          {formatDate(ticket.created_at)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Order Detail Sheet */}
      <Sheet open={!!selectedOrder} onOpenChange={() => setSelectedOrder(null)}>
        <SheetContent className="w-full sm:max-w-lg overflow-y-auto">
          {selectedOrder && (
            <>
              <SheetHeader className="pb-6">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                    <ShoppingCart className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <SheetTitle>Order Details</SheetTitle>
                    <p className="text-sm text-muted-foreground font-mono">
                      {selectedOrder.id.slice(0, 8)}...
                    </p>
                  </div>
                </div>
              </SheetHeader>

              <div className="space-y-6">
                {/* Status */}
                <div className="flex items-center justify-between">
                  <Badge className={StatusColors[selectedOrder.status]} data-testid="order-status">
                    {selectedOrder.status}
                  </Badge>
                  <Badge className={StatusColors[selectedOrder.payment_status]}>
                    Payment: {selectedOrder.payment_status}
                  </Badge>
                </div>

                {/* Customer */}
                <div className="space-y-2">
                  <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Customer</h4>
                  <div className="flex items-center gap-3 p-3 bg-accent rounded-lg">
                    <User className="w-5 h-5 text-muted-foreground" />
                    <span className="font-medium">{selectedOrder.customer_name}</span>
                  </div>
                </div>

                {/* Shipping Address */}
                {selectedOrder.shipping_address && (
                  <div className="space-y-2">
                    <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Shipping Address</h4>
                    <div className="flex items-start gap-3 p-3 bg-accent rounded-lg">
                      <MapPin className="w-5 h-5 text-muted-foreground mt-0.5" />
                      <div>
                        <Badge variant="outline" className="text-xs mb-1">
                          {selectedOrder.shipping_address.type || "Address"}
                        </Badge>
                        <p className="text-sm">{selectedOrder.shipping_address.address}</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Items */}
                <div className="space-y-2">
                  <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Items</h4>
                  <div className="space-y-2">
                    {selectedOrder.items?.map((item, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 bg-accent rounded-lg">
                        <div>
                          <p className="font-medium">{item.name || `Product ${idx + 1}`}</p>
                          <p className="text-sm text-muted-foreground">Qty: {item.quantity}</p>
                        </div>
                        <p className="font-semibold flex items-center">
                          <IndianRupee className="w-4 h-4" />
                          {(item.price * item.quantity).toLocaleString('en-IN')}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Totals */}
                <div className="space-y-2 pt-4 border-t border-border">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Subtotal</span>
                    <span className="flex items-center">
                      <IndianRupee className="w-4 h-4" />
                      {selectedOrder.subtotal.toLocaleString('en-IN')}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Tax (GST)</span>
                    <span className="flex items-center">
                      <IndianRupee className="w-4 h-4" />
                      {selectedOrder.tax.toLocaleString('en-IN')}
                    </span>
                  </div>
                  <div className="flex justify-between text-lg font-bold pt-2">
                    <span>Total</span>
                    <span className="flex items-center text-emerald-600 dark:text-emerald-400">
                      <IndianRupee className="w-5 h-5" />
                      {selectedOrder.total.toLocaleString('en-IN')}
                    </span>
                  </div>
                </div>

                {/* Update Status */}
                <div className="space-y-3 pt-4">
                  <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Update Status</h4>
                  <div className="flex flex-wrap gap-2">
                    {orderStatuses.map((status) => (
                      <Button
                        key={status}
                        variant={selectedOrder.status === status ? "default" : "outline"}
                        size="sm"
                        onClick={() => updateOrderStatus(selectedOrder.id, status)}
                        className="capitalize"
                        data-testid={`update-status-${status}`}
                      >
                        {status}
                      </Button>
                    ))}
                  </div>
                </div>
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>

      {/* Ticket Detail Sheet */}
      <Sheet open={!!selectedTicket} onOpenChange={() => setSelectedTicket(null)}>
        <SheetContent className="w-full sm:max-w-lg overflow-y-auto">
          {selectedTicket && (
            <>
              <SheetHeader className="pb-6">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                    <Ticket className="w-6 h-6 text-amber-600 dark:text-amber-400" />
                  </div>
                  <div>
                    <SheetTitle className="font-mono text-sm">{selectedTicket.ticket_number}</SheetTitle>
                    <p className="text-sm text-muted-foreground">osTicket</p>
                  </div>
                </div>
              </SheetHeader>

              <div className="space-y-6">
                <div className="flex items-center gap-2">
                  <Badge className={StatusColors[selectedTicket.status]}>
                    {selectedTicket.status.replace("_", " ")}
                  </Badge>
                  <Badge className={
                    selectedTicket.priority === "high" 
                      ? "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"
                      : selectedTicket.priority === "medium"
                      ? "status-pending"
                      : "status-closed"
                  }>
                    {selectedTicket.priority} priority
                  </Badge>
                </div>

                <div>
                  <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-2">Subject</h4>
                  <p className="font-medium">{selectedTicket.subject}</p>
                </div>

                <div>
                  <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-2">Description</h4>
                  <p className="text-sm bg-accent p-3 rounded-lg">{selectedTicket.description}</p>
                </div>

                <div>
                  <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-2">Customer</h4>
                  <div className="flex items-center gap-3 p-3 bg-accent rounded-lg">
                    <User className="w-5 h-5 text-muted-foreground" />
                    <span className="font-medium">{selectedTicket.customer_name}</span>
                  </div>
                </div>

                {/* Update Status */}
                <div className="space-y-3 pt-4">
                  <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Update Status</h4>
                  <div className="flex flex-wrap gap-2">
                    {ticketStatuses.map((status) => (
                      <Button
                        key={status}
                        variant={selectedTicket.status === status ? "default" : "outline"}
                        size="sm"
                        onClick={() => updateTicketStatus(selectedTicket.id, status)}
                        className="capitalize"
                        data-testid={`update-ticket-status-${status}`}
                      >
                        {status.replace("_", " ")}
                      </Button>
                    ))}
                  </div>
                </div>
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
};

export default OrdersPage;
