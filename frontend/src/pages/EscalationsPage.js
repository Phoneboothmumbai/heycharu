import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "../components/ui/sheet";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { toast } from "sonner";
import { AlertTriangle, User, MessageSquare, Clock, CheckCircle, Eye } from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const StatusColors = {
  pending: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
  reviewed: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  resolved: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400"
};

const PriorityColors = {
  high: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
  medium: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
  low: "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-400"
};

function EscalationsPage() {
  var [escalations, setEscalations] = useState([]);
  var [loading, setLoading] = useState(true);
  var [statusFilter, setStatusFilter] = useState("all");
  var [selectedEscalation, setSelectedEscalation] = useState(null);

  var fetchEscalations = useCallback(function() {
    var params = (statusFilter && statusFilter !== "all") ? "?status=" + statusFilter : "";
    axios.get(API_URL + "/api/escalations" + params).then(function(res) {
      setEscalations(res.data);
    }).catch(function() {
      toast.error("Failed to load escalations");
    }).finally(function() {
      setLoading(false);
    });
  }, [statusFilter]);

  useEffect(function() { fetchEscalations(); }, [fetchEscalations]);

  function updateStatus(escalationId, status) {
    axios.put(API_URL + "/api/escalations/" + escalationId + "/status?status=" + status).then(function() {
      toast.success("Status updated");
      fetchEscalations();
      setSelectedEscalation(null);
    }).catch(function() {
      toast.error("Failed to update status");
    });
  }

  function formatDate(dateString) {
    if (!dateString) return "";
    return new Date(dateString).toLocaleString("en-IN", {
      day: "numeric", month: "short", hour: "2-digit", minute: "2-digit"
    });
  }

  var pendingCount = escalations.filter(function(e) { return e.status === "pending"; }).length;

  return (
    <div className="space-y-6 animate-in">
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <AlertTriangle className="w-6 h-6 text-amber-500" />
            Escalations
            {pendingCount > 0 && <Badge className="bg-amber-500 text-white ml-2">{pendingCount} pending</Badge>}
          </h1>
          <p className="text-muted-foreground">Cases requiring human attention (Charu-in-the-loop)</p>
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-full sm:w-48" data-testid="escalation-status-filter">
            <SelectValue placeholder="All Statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="reviewed">Reviewed</SelectItem>
            <SelectItem value="resolved">Resolved</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {pendingCount > 0 && (
        <Card className="bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800">
          <CardContent className="p-4 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            <span className="text-amber-800 dark:text-amber-200">{pendingCount} escalation(s) require your immediate attention</span>
          </CardContent>
        </Card>
      )}

      <Card className="border-border/50">
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-4">
              {[1,2,3].map(function(i) { return <div key={i} className="skeleton-pulse h-16 rounded"></div>; })}
            </div>
          ) : escalations.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
              <CheckCircle className="w-16 h-16 mb-4 opacity-50 text-emerald-500" />
              <p className="text-lg font-medium">No escalations</p>
              <p className="text-sm">All conversations are being handled by AI</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Customer</TableHead>
                  <TableHead>Reason</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {escalations.map(function(esc) {
                  return (
                    <TableRow key={esc.id} className="cursor-pointer" onClick={function() { setSelectedEscalation(esc); }} data-testid={"escalation-row-" + esc.id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <User className="w-4 h-4 text-muted-foreground" />
                          <span className="font-medium">{esc.customer_name}</span>
                        </div>
                      </TableCell>
                      <TableCell className="max-w-xs truncate">{esc.reason}</TableCell>
                      <TableCell><Badge className={PriorityColors[esc.priority]}>{esc.priority}</Badge></TableCell>
                      <TableCell><Badge className={StatusColors[esc.status]}>{esc.status}</Badge></TableCell>
                      <TableCell className="text-muted-foreground text-sm">{formatDate(esc.created_at)}</TableCell>
                      <TableCell>
                        <Button variant="ghost" size="sm"><Eye className="w-4 h-4" /></Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Sheet open={!!selectedEscalation} onOpenChange={function() { setSelectedEscalation(null); }}>
        <SheetContent className="w-full sm:max-w-lg overflow-y-auto">
          {selectedEscalation && (
            <div>
              <SheetHeader className="pb-6">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                    <AlertTriangle className="w-6 h-6 text-amber-600" />
                  </div>
                  <div>
                    <SheetTitle>Escalation Details</SheetTitle>
                    <p className="text-sm text-muted-foreground">{formatDate(selectedEscalation.created_at)}</p>
                  </div>
                </div>
              </SheetHeader>

              <div className="space-y-6">
                <div className="flex items-center gap-2">
                  <Badge className={StatusColors[selectedEscalation.status]}>{selectedEscalation.status}</Badge>
                  <Badge className={PriorityColors[selectedEscalation.priority]}>{selectedEscalation.priority} priority</Badge>
                </div>

                <div className="space-y-2">
                  <h4 className="text-sm font-semibold text-muted-foreground uppercase">Customer</h4>
                  <div className="flex items-center gap-3 p-3 bg-accent rounded-lg">
                    <User className="w-5 h-5 text-muted-foreground" />
                    <span className="font-medium">{selectedEscalation.customer_name}</span>
                  </div>
                </div>

                <div className="space-y-2">
                  <h4 className="text-sm font-semibold text-muted-foreground uppercase">Reason for Escalation</h4>
                  <p className="p-3 bg-accent rounded-lg">{selectedEscalation.reason}</p>
                </div>

                <div className="space-y-2">
                  <h4 className="text-sm font-semibold text-muted-foreground uppercase">Customer Message</h4>
                  <div className="p-3 bg-accent rounded-lg flex items-start gap-3">
                    <MessageSquare className="w-5 h-5 text-muted-foreground mt-0.5" />
                    <p className="text-sm">{selectedEscalation.message_content}</p>
                  </div>
                </div>

                <div className="space-y-3 pt-4">
                  <h4 className="text-sm font-semibold text-muted-foreground uppercase">Update Status</h4>
                  <div className="flex flex-wrap gap-2">
                    {["pending", "reviewed", "resolved"].map(function(status) {
                      return (
                        <Button
                          key={status}
                          variant={selectedEscalation.status === status ? "default" : "outline"}
                          size="sm"
                          onClick={function() { updateStatus(selectedEscalation.id, status); }}
                          className="capitalize"
                          data-testid={"update-escalation-" + status}
                        >
                          {status}
                        </Button>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
}

export default EscalationsPage;
