import { useState, useEffect } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "../components/ui/dialog";
import { toast } from "sonner";
import { HelpCircle, Plus, Link, X, Search, Clock, AlertTriangle, CheckCircle2, FileText, MessageSquare, ChevronDown, ChevronRight } from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const UnansweredQuestionsPage = () => {
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState("pending_owner_reply");
  const [filterRelevance, setFilterRelevance] = useState("all");
  const [expandedQuestion, setExpandedQuestion] = useState(null);
  
  // Add KB Article Dialog
  const [showAddKbDialog, setShowAddKbDialog] = useState(false);
  const [selectedQuestion, setSelectedQuestion] = useState(null);
  const [newArticle, setNewArticle] = useState({ title: "", content: "", category: "FAQ" });
  
  // Link KB Article Dialog
  const [showLinkDialog, setShowLinkDialog] = useState(false);
  const [kbArticles, setKbArticles] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState(null);

  useEffect(() => {
    fetchQuestions();
    fetchKbArticles();
  }, [filterStatus, filterRelevance]);

  const fetchQuestions = async () => {
    try {
      const token = localStorage.getItem("auth_token");
      let url = `${API_URL}/api/unanswered-questions`;
      const params = new URLSearchParams();
      if (filterStatus && filterStatus !== "all") params.append("status", filterStatus);
      if (filterRelevance && filterRelevance !== "all") params.append("relevance", filterRelevance);
      if (params.toString()) url += `?${params.toString()}`;
      
      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setQuestions(response.data);
    } catch (error) {
      toast.error("Failed to fetch unanswered questions");
    } finally {
      setLoading(false);
    }
  };

  const fetchKbArticles = async () => {
    try {
      const token = localStorage.getItem("auth_token");
      const response = await axios.get(`${API_URL}/api/kb`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setKbArticles(response.data);
    } catch (error) {
      console.error("Failed to fetch KB articles");
    }
  };

  const handleMarkRelevance = async (questionId, relevance) => {
    try {
      const token = localStorage.getItem("auth_token");
      await axios.put(`${API_URL}/api/unanswered-questions/${questionId}/relevance?relevance=${relevance}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(`Question marked as ${relevance}`);
      fetchQuestions();
    } catch (error) {
      toast.error("Failed to update question");
    }
  };

  const handleAddKbArticle = async () => {
    if (!newArticle.title || !newArticle.content) {
      toast.error("Please fill in title and content");
      return;
    }
    
    try {
      const token = localStorage.getItem("auth_token");
      await axios.post(
        `${API_URL}/api/unanswered-questions/${selectedQuestion.id}/add-kb-article?title=${encodeURIComponent(newArticle.title)}&content=${encodeURIComponent(newArticle.content)}&category=${newArticle.category}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success("KB article created and linked!");
      setShowAddKbDialog(false);
      setNewArticle({ title: "", content: "", category: "FAQ" });
      fetchQuestions();
    } catch (error) {
      toast.error("Failed to create KB article");
    }
  };

  const handleLinkKbArticle = async (kbArticleId) => {
    try {
      const token = localStorage.getItem("auth_token");
      await axios.post(
        `${API_URL}/api/unanswered-questions/${selectedQuestion.id}/link-kb-article/${kbArticleId}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success("KB article linked!");
      setShowLinkDialog(false);
      fetchQuestions();
    } catch (error) {
      toast.error("Failed to link KB article");
    }
  };

  const handleSearchData = async () => {
    if (!searchQuery) {
      toast.error("Please enter a search query");
      return;
    }
    
    try {
      const token = localStorage.getItem("auth_token");
      const response = await axios.post(
        `${API_URL}/api/unanswered-questions/${selectedQuestion.id}/link-excel-data?search_query=${encodeURIComponent(searchQuery)}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSearchResults(response.data);
    } catch (error) {
      toast.error("Search failed");
    }
  };

  const getStatusBadge = (question) => {
    if (question.is_overdue) {
      return (
        <Badge variant="destructive" className="flex items-center gap-1">
          <AlertTriangle className="w-3 h-3" />
          OVERDUE
        </Badge>
      );
    }
    
    if (question.status === "pending_owner_reply") {
      return (
        <Badge variant="outline" className="text-orange-500 border-orange-500 flex items-center gap-1">
          <Clock className="w-3 h-3" />
          WAITING
        </Badge>
      );
    }
    
    if (question.status === "resolved") {
      return (
        <Badge variant="outline" className="text-green-500 border-green-500 flex items-center gap-1">
          <CheckCircle2 className="w-3 h-3" />
          RESOLVED
        </Badge>
      );
    }
    
    if (question.status === "marked_irrelevant") {
      return (
        <Badge variant="secondary" className="flex items-center gap-1">
          <X className="w-3 h-3" />
          IRRELEVANT
        </Badge>
      );
    }
    
    return null;
  };

  const openAddKbDialog = (question) => {
    setSelectedQuestion(question);
    setNewArticle({
      title: `Answer: ${question.question.slice(0, 50)}...`,
      content: "",
      category: "FAQ"
    });
    setShowAddKbDialog(true);
  };

  const openLinkDialog = (question) => {
    setSelectedQuestion(question);
    setSearchQuery(question.question);
    setSearchResults(null);
    setShowLinkDialog(true);
  };

  return (
    <div className="space-y-6" data-testid="unanswered-questions-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <HelpCircle className="w-6 h-6 text-orange-500" />
            Unanswered Questions
          </h1>
          <p className="text-muted-foreground mt-1">
            Questions the AI couldn't answer. Add KB articles to train it.
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Select value={filterStatus} onValueChange={setFilterStatus}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Status filter" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="pending_owner_reply">Pending</SelectItem>
              <SelectItem value="resolved">Resolved</SelectItem>
              <SelectItem value="marked_irrelevant">Irrelevant</SelectItem>
              <SelectItem value="all">All</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-3xl font-bold text-orange-500">
              {questions.filter(q => q.status === "pending_owner_reply").length}
            </div>
            <p className="text-sm text-muted-foreground">Pending</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-3xl font-bold text-red-500">
              {questions.filter(q => q.is_overdue).length}
            </div>
            <p className="text-sm text-muted-foreground">Overdue</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-3xl font-bold text-green-500">
              {questions.filter(q => q.status === "resolved").length}
            </div>
            <p className="text-sm text-muted-foreground">Resolved</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-3xl font-bold text-gray-500">
              {questions.filter(q => q.relevance === "irrelevant").length}
            </div>
            <p className="text-sm text-muted-foreground">Irrelevant</p>
          </CardContent>
        </Card>
      </div>

      {/* Questions List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5" />
            Questions ({questions.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-muted-foreground">Loading...</div>
          ) : questions.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No unanswered questions found.
            </div>
          ) : (
            <div className="divide-y">
              {questions.map((question) => (
                <div key={question.id} className="py-4" data-testid={`question-${question.id}`}>
                  <div className="flex items-start justify-between">
                    {/* Question Info */}
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <button 
                          onClick={() => setExpandedQuestion(expandedQuestion === question.id ? null : question.id)}
                          className="p-1 hover:bg-accent rounded"
                        >
                          {expandedQuestion === question.id ? 
                            <ChevronDown className="w-4 h-4" /> : 
                            <ChevronRight className="w-4 h-4" />
                          }
                        </button>
                        <Badge variant="outline" className="font-mono">
                          {question.escalation_code}
                        </Badge>
                        {getStatusBadge(question)}
                        {question.linked_kb_title && (
                          <Badge variant="secondary" className="flex items-center gap-1">
                            <FileText className="w-3 h-3" />
                            Linked: {question.linked_kb_title.slice(0, 20)}...
                          </Badge>
                        )}
                      </div>
                      
                      <p className="font-medium">{question.question}</p>
                      
                      <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                        <span>From: {question.customer_name}</span>
                        <span>•</span>
                        <span>{new Date(question.created_at).toLocaleString()}</span>
                        {question.reason && (
                          <>
                            <span>•</span>
                            <span className="text-orange-500">{question.reason}</span>
                          </>
                        )}
                      </div>
                      
                      {/* Expanded Details */}
                      {expandedQuestion === question.id && (
                        <div className="mt-4 p-4 bg-accent/50 rounded-lg">
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                              <span className="text-muted-foreground">Customer Phone:</span>
                              <span className="ml-2 font-medium">{question.customer_phone}</span>
                            </div>
                            <div>
                              <span className="text-muted-foreground">SLA Deadline:</span>
                              <span className="ml-2 font-medium">
                                {question.sla_deadline ? new Date(question.sla_deadline).toLocaleString() : "N/A"}
                              </span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                    
                    {/* Actions */}
                    <div className="flex items-center gap-2 ml-4">
                      {question.status === "pending_owner_reply" && (
                        <>
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => openAddKbDialog(question)}
                            data-testid={`add-kb-${question.id}`}
                          >
                            <Plus className="w-4 h-4 mr-1" />
                            Add KB Article
                          </Button>
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => openLinkDialog(question)}
                            data-testid={`link-kb-${question.id}`}
                          >
                            <Link className="w-4 h-4 mr-1" />
                            Link KB/Excel
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="sm"
                            onClick={() => handleMarkRelevance(question.id, "irrelevant")}
                          >
                            <X className="w-4 h-4 mr-1" />
                            Irrelevant
                          </Button>
                        </>
                      )}
                      {question.relevance === "irrelevant" && (
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => handleMarkRelevance(question.id, "relevant")}
                        >
                          Mark Relevant
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add KB Article Dialog */}
      <Dialog open={showAddKbDialog} onOpenChange={setShowAddKbDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Add KB Article</DialogTitle>
            <DialogDescription>
              Create a knowledge base article to answer this question. The AI will use this to answer similar questions in the future.
            </DialogDescription>
          </DialogHeader>
          
          {selectedQuestion && (
            <div className="p-3 bg-accent rounded-lg mb-4">
              <p className="text-sm text-muted-foreground">Customer's Question:</p>
              <p className="font-medium">"{selectedQuestion.question}"</p>
            </div>
          )}
          
          <div className="space-y-4">
            <div>
              <Label htmlFor="title">Article Title</Label>
              <Input
                id="title"
                value={newArticle.title}
                onChange={(e) => setNewArticle({...newArticle, title: e.target.value})}
                placeholder="e.g., iPhone 15 Pro Max Pricing"
              />
            </div>
            
            <div>
              <Label htmlFor="content">Article Content (Answer)</Label>
              <Textarea
                id="content"
                value={newArticle.content}
                onChange={(e) => setNewArticle({...newArticle, content: e.target.value})}
                placeholder="Enter the answer that should be given to customers asking this question..."
                rows={6}
              />
            </div>
            
            <div>
              <Label htmlFor="category">Category</Label>
              <Select value={newArticle.category} onValueChange={(v) => setNewArticle({...newArticle, category: v})}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="FAQ">FAQ</SelectItem>
                  <SelectItem value="Pricing">Pricing</SelectItem>
                  <SelectItem value="Products">Products</SelectItem>
                  <SelectItem value="Policies">Policies</SelectItem>
                  <SelectItem value="Support">Support</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddKbDialog(false)}>Cancel</Button>
            <Button onClick={handleAddKbArticle}>Create & Link Article</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Link KB/Excel Dialog */}
      <Dialog open={showLinkDialog} onOpenChange={setShowLinkDialog}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Link KB Article or Excel Data</DialogTitle>
            <DialogDescription>
              Search and link existing knowledge base articles or Excel data to answer this question.
            </DialogDescription>
          </DialogHeader>
          
          {selectedQuestion && (
            <div className="p-3 bg-accent rounded-lg mb-4">
              <p className="text-sm text-muted-foreground">Customer's Question:</p>
              <p className="font-medium">"{selectedQuestion.question}"</p>
            </div>
          )}
          
          {/* Search */}
          <div className="flex gap-2 mb-4">
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search KB articles, products, or Excel data..."
              className="flex-1"
            />
            <Button onClick={handleSearchData}>
              <Search className="w-4 h-4 mr-1" />
              Search
            </Button>
          </div>
          
          {/* Existing KB Articles */}
          <div className="mb-4">
            <h4 className="font-medium mb-2">Existing KB Articles</h4>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {kbArticles.map((article) => (
                <div 
                  key={article.id} 
                  className="flex items-center justify-between p-2 border rounded hover:bg-accent cursor-pointer"
                  onClick={() => handleLinkKbArticle(article.id)}
                >
                  <div>
                    <p className="font-medium">{article.title}</p>
                    <p className="text-sm text-muted-foreground">{article.category}</p>
                  </div>
                  <Button variant="ghost" size="sm">
                    <Link className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
          </div>
          
          {/* Search Results */}
          {searchResults && (
            <div className="space-y-4">
              {searchResults.kb_articles?.length > 0 && (
                <div>
                  <h4 className="font-medium mb-2">Matching KB Articles</h4>
                  <div className="space-y-2">
                    {searchResults.kb_articles.map((article) => (
                      <div 
                        key={article.id} 
                        className="flex items-center justify-between p-2 border rounded hover:bg-accent cursor-pointer"
                        onClick={() => handleLinkKbArticle(article.id)}
                      >
                        <div>
                          <p className="font-medium">{article.title}</p>
                          <p className="text-sm text-muted-foreground">{article.content?.slice(0, 100)}...</p>
                        </div>
                        <Button variant="outline" size="sm">Link</Button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {searchResults.products?.length > 0 && (
                <div>
                  <h4 className="font-medium mb-2">Matching Products</h4>
                  <div className="space-y-2">
                    {searchResults.products.map((product) => (
                      <div key={product.id} className="p-2 border rounded">
                        <p className="font-medium">{product.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {product.description?.slice(0, 100)} - ₹{product.price}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {searchResults.excel_data?.length > 0 && (
                <div>
                  <h4 className="font-medium mb-2">Matching Excel Data</h4>
                  <div className="space-y-2">
                    {searchResults.excel_data.map((data, idx) => (
                      <div key={idx} className="p-2 border rounded">
                        <pre className="text-sm overflow-x-auto">
                          {JSON.stringify(data.data, null, 2).slice(0, 200)}...
                        </pre>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {searchResults.total_results === 0 && (
                <div className="text-center py-4 text-muted-foreground">
                  No matching data found. Try a different search query.
                </div>
              )}
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowLinkDialog(false)}>Cancel</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default UnansweredQuestionsPage;
