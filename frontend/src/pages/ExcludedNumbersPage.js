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
import { Alert, AlertDescription, AlertTitle } from "../components/ui/alert";
import { useToast } from "../components/ui/use-toast";
import { EyeOff, Plus, Phone, Tag, Trash2, ShieldOff, Info } from "lucide-react";

var API_URL = process.env.REACT_APP_BACKEND_URL;

function ExcludedNumbersPage() {
  var [numbers, setNumbers] = useState([]);
  var [loading, setLoading] = useState(true);
  var [isDialogOpen, setIsDialogOpen] = useState(false);
  var [formData, setFormData] = useState({
    phone: "",
    tag: "other",
    reason: "",
    is_temporary: false
  });
  var [submitting, setSubmitting] = useState(false);
  var { toast } = useToast();

  var fetchNumbers = async function() {
    try {
      var token = localStorage.getItem("token");
      var response = await fetch(API_URL + "/api/excluded-numbers", {
        headers: { "Authorization": "Bearer " + token }
      });
      var data = await response.json();
      setNumbers(data);
    } catch (error) {
      console.error("Error fetching numbers:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(function() {
    fetchNumbers();
  }, []);

  var handleAddNumber = async function() {
    if (!formData.phone) {
      toast({ title: "Error", description: "Please enter a phone number", variant: "destructive" });
      return;
    }

    setSubmitting(true);
    try {
      var token = localStorage.getItem("token");
      var response = await fetch(API_URL + "/api/excluded-numbers", {
        method: "POST",
        headers: {
          "Authorization": "Bearer " + token,
          "Content-Type": "application/json"
        },
        body: JSON.stringify(formData)
      });
      var data = await response.json();
      
      if (response.ok) {
        toast({ title: "Number Excluded", description: "AI will no longer reply to " + formData.phone });
        setIsDialogOpen(false);
        setFormData({ phone: "", tag: "other", reason: "", is_temporary: false });
        fetchNumbers();
      } else {
        toast({ title: "Error", description: data.detail || "Failed to exclude number", variant: "destructive" });
      }
    } catch (error) {
      toast({ title: "Error", description: "Failed to exclude number", variant: "destructive" });
    } finally {
      setSubmitting(false);
    }
  };

  var handleDeleteNumber = async function(numberId) {
    try {
      var token = localStorage.getItem("token");
      await fetch(API_URL + "/api/excluded-numbers/" + numberId, {
        method: "DELETE",
        headers: { "Authorization": "Bearer " + token }
      });
      toast({ title: "Number Removed", description: "AI will now respond to this number" });
      fetchNumbers();
    } catch (error) {
      toast({ title: "Error", description: "Failed to remove number", variant: "destructive" });
    }
  };

  var getTagBadge = function(tag) {
    var colors = {
      dealer: "bg-blue-500/10 text-blue-600 border-blue-500/30",
      vendor: "bg-amber-500/10 text-amber-600 border-amber-500/30",
      internal: "bg-purple-500/10 text-purple-600 border-purple-500/30",
      other: "bg-gray-500/10 text-gray-600 border-gray-500/30"
    };
    return (
      <Badge variant="outline" className={colors[tag] || colors.other}>
        {tag}
      </Badge>
    );
  };

  return (
    <div className="space-y-6" data-testid="excluded-numbers-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <EyeOff className="h-6 w-6 text-primary" />
            Excluded Numbers
          </h1>
          <p className="text-muted-foreground">Silent monitoring - record messages but never reply</p>
        </div>
        
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button data-testid="add-excluded-btn">
              <Plus className="h-4 w-4 mr-2" />
              Exclude Number
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Excluded Number</DialogTitle>
              <DialogDescription>
                Messages from this number will be recorded but AI will never reply.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 pt-4">
              <div className="space-y-2">
                <Label htmlFor="phone">Phone Number *</Label>
                <Input
                  id="phone"
                  data-testid="exclude-phone"
                  placeholder="e.g., +91 98765 43210"
                  value={formData.phone}
                  onChange={function(e) { setFormData({...formData, phone: e.target.value}); }}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="tag">Category</Label>
                <Select
                  value={formData.tag}
                  onValueChange={function(value) { setFormData({...formData, tag: value}); }}
                >
                  <SelectTrigger data-testid="exclude-tag">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="dealer">Dealer</SelectItem>
                    <SelectItem value="vendor">Vendor</SelectItem>
                    <SelectItem value="internal">Internal</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="reason">Reason (Optional)</Label>
                <Textarea
                  id="reason"
                  data-testid="exclude-reason"
                  placeholder="Why is this number excluded?"
                  value={formData.reason}
                  onChange={function(e) { setFormData({...formData, reason: e.target.value}); }}
                />
              </div>
              <Button 
                className="w-full" 
                onClick={handleAddNumber}
                disabled={submitting}
                data-testid="submit-exclude-btn"
              >
                {submitting ? "Adding..." : "Exclude Number"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>How Silent Monitoring Works</AlertTitle>
        <AlertDescription>
          Messages from excluded numbers are still recorded and searchable. 
          Use this for dealers, vendors, or internal contacts where AI replies aren't appropriate.
        </AlertDescription>
      </Alert>

      <Card>
        <CardHeader>
          <CardTitle>Excluded Numbers</CardTitle>
          <CardDescription>Numbers where AI will never send automatic replies</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-muted-foreground">Loading...</div>
          ) : numbers.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <ShieldOff className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>No numbers excluded yet</p>
              <p className="text-sm">AI will respond to all incoming messages</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Phone Number</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Reason</TableHead>
                  <TableHead>Added By</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {numbers.map(function(num) {
                  return (
                    <TableRow key={num.id} data-testid={"excluded-row-" + num.id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Phone className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">{num.phone}</span>
                        </div>
                      </TableCell>
                      <TableCell>{getTagBadge(num.tag)}</TableCell>
                      <TableCell className="max-w-[200px] truncate text-muted-foreground">
                        {num.reason || "-"}
                      </TableCell>
                      <TableCell className="text-sm">{num.created_by}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {new Date(num.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={function() { handleDeleteNumber(num.id); }}
                          className="text-destructive hover:text-destructive"
                          data-testid={"delete-excluded-" + num.id}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
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

export default ExcludedNumbersPage;
