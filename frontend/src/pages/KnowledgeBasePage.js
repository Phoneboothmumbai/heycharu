import { useState, useEffect, useCallback, useRef } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Badge } from "../components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { toast } from "sonner";
import { BookOpen, Plus, Search, Edit2, Trash2, Save, Globe, FileSpreadsheet, Loader2, Link, Upload } from "lucide-react";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const KnowledgeBasePage = () => {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [editingArticle, setEditingArticle] = useState(null);
  const [form, setForm] = useState({
    title: "",
    content: "",
    category: "general",
    tags: ""
  });

  // Scrape URL state
  const [scrapeUrl, setScrapeUrl] = useState("");
  const [scrapeTitle, setScrapeTitle] = useState("");
  const [scrapeCategory, setScrapeCategory] = useState("general");
  const [isScraping, setIsScraping] = useState(false);
  const [isScrapeDialogOpen, setIsScrapeDialogOpen] = useState(false);

  // Excel upload state
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef(null);

  const getToken = () => localStorage.getItem('sales-brain-token');

  const fetchArticles = useCallback(async () => {
    try {
      const res = await axios.get(`${API_URL}/api/kb`, {
        headers: { Authorization: `Bearer ${getToken()}` }
      });
      setArticles(res.data);
    } catch (e) {
      toast.error("Failed to load knowledge base");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchArticles(); }, [fetchArticles]);

  const handleSubmit = async () => {
    if (!form.title || !form.content) {
      toast.error("Title and content are required");
      return;
    }

    try {
      const payload = {
        ...form,
        tags: form.tags.split(",").map(t => t.trim()).filter(t => t)
      };

      if (editingArticle) {
        await axios.put(`${API_URL}/api/kb/${editingArticle.id}`, payload, {
          headers: { Authorization: `Bearer ${getToken()}` }
        });
        toast.success("Article updated");
      } else {
        await axios.post(`${API_URL}/api/kb`, payload, {
          headers: { Authorization: `Bearer ${getToken()}` }
        });
        toast.success("Article added");
      }

      setIsAddOpen(false);
      setEditingArticle(null);
      setForm({ title: "", content: "", category: "general", tags: "" });
      fetchArticles();
    } catch (e) {
      toast.error("Failed to save article");
    }
  };

  const handleEdit = (article) => {
    setEditingArticle(article);
    setForm({
      title: article.title,
      content: article.content,
      category: article.category,
      tags: (article.tags || []).join(", ")
    });
    setIsAddOpen(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this article?")) return;
    try {
      await axios.delete(`${API_URL}/api/kb/${id}`, {
        headers: { Authorization: `Bearer ${getToken()}` }
      });
      toast.success("Article deleted");
      fetchArticles();
    } catch (e) {
      toast.error("Failed to delete");
    }
  };

  // Scrape URL handler
  const handleScrapeUrl = async () => {
    if (!scrapeUrl) {
      toast.error("Please enter a URL");
      return;
    }

    setIsScraping(true);
    try {
      const res = await axios.post(`${API_URL}/api/kb/scrape-url`, {
        url: scrapeUrl,
        title: scrapeTitle || null,
        category: scrapeCategory
      }, {
        headers: { Authorization: `Bearer ${getToken()}` }
      });

      toast.success(`Scraped: ${res.data.title} (${res.data.content_length} chars)`);
      setScrapeUrl("");
      setScrapeTitle("");
      setScrapeCategory("general");
      setIsScrapeDialogOpen(false);
      fetchArticles();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to scrape URL");
    } finally {
      setIsScraping(false);
    }
  };

  // Excel upload handler
  const handleExcelUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      toast.error("Please upload an Excel file (.xlsx or .xls)");
      return;
    }

    setIsUploading(true);
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('file', file);

      const res = await axios.post(`${API_URL}/api/kb/upload-excel`, formData, {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });

      toast.success(`${res.data.message}`);
      fetchArticles();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to upload Excel");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const filteredArticles = articles.filter(a => {
    const matchesSearch = a.title.toLowerCase().includes(search.toLowerCase()) ||
                          a.content.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = categoryFilter === "all" || a.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  const categories = ["general", "products", "services", "policies", "pricing", "repairs", "faq"];

  const CategoryColors = {
    general: "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300",
    products: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
    services: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400",
    policies: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
    pricing: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400",
    repairs: "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400",
    faq: "bg-pink-100 text-pink-800 dark:bg-pink-900/30 dark:text-pink-400",
  };

  return (
    <div className="space-y-6 animate-in" data-testid="knowledge-base-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold">Knowledge Base</h1>
          <p className="text-muted-foreground">Information the AI uses to answer customer questions</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          {/* Scrape URL Button */}
          <Dialog open={isScrapeDialogOpen} onOpenChange={setIsScrapeDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" data-testid="scrape-url-btn">
                <Globe className="w-4 h-4 mr-2" />Scrape URL
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle>Import from Website</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 pt-4">
                <div className="space-y-2">
                  <Label>Website URL *</Label>
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <Link className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                      <Input
                        value={scrapeUrl}
                        onChange={(e) => setScrapeUrl(e.target.value)}
                        placeholder="https://example.com/products"
                        className="pl-10"
                      />
                    </div>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Title (optional)</Label>
                  <Input
                    value={scrapeTitle}
                    onChange={(e) => setScrapeTitle(e.target.value)}
                    placeholder="Auto-detected from page if empty"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Category</Label>
                  <Select value={scrapeCategory} onValueChange={setScrapeCategory}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {categories.map(c => (
                        <SelectItem key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Button onClick={handleScrapeUrl} disabled={isScraping} className="w-full">
                  {isScraping ? (
                    <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Scraping...</>
                  ) : (
                    <><Globe className="w-4 h-4 mr-2" />Scrape & Add to KB</>
                  )}
                </Button>
              </div>
            </DialogContent>
          </Dialog>

          {/* Excel Upload Button */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleExcelUpload}
            accept=".xlsx,.xls"
            className="hidden"
          />
          <Button 
            variant="outline" 
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            data-testid="upload-excel-btn"
          >
            {isUploading ? (
              <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Uploading...</>
            ) : (
              <><FileSpreadsheet className="w-4 h-4 mr-2" />Upload Excel</>
            )}
          </Button>

          {/* Add Article Button */}
          <Dialog open={isAddOpen} onOpenChange={(open) => {
            setIsAddOpen(open);
            if (!open) {
              setEditingArticle(null);
              setForm({ title: "", content: "", category: "general", tags: "" });
            }
          }}>
            <DialogTrigger asChild>
              <Button data-testid="add-article-btn">
                <Plus className="w-4 h-4 mr-2" />Add Article
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-xl">
              <DialogHeader>
                <DialogTitle>{editingArticle ? "Edit Article" : "Add Knowledge Article"}</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 pt-4">
                <div className="space-y-2">
                  <Label>Title *</Label>
                  <Input
                    value={form.title}
                    onChange={(e) => setForm({ ...form, title: e.target.value })}
                    placeholder="e.g., iPhone Repair Pricing"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Category</Label>
                  <Select value={form.category} onValueChange={(v) => setForm({ ...form, category: v })}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {categories.map(c => (
                        <SelectItem key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Content *</Label>
                  <Textarea
                    value={form.content}
                    onChange={(e) => setForm({ ...form, content: e.target.value })}
                    placeholder="Add detailed information that will help AI answer customer questions..."
                    rows={8}
                    className="resize-none"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Tags (comma separated)</Label>
                  <Input
                    value={form.tags}
                    onChange={(e) => setForm({ ...form, tags: e.target.value })}
                    placeholder="e.g., iphone, repair, screen, pricing"
                  />
                </div>
                <div className="flex gap-3 pt-2">
                  <Button variant="outline" onClick={() => setIsAddOpen(false)} className="flex-1">Cancel</Button>
                  <Button onClick={handleSubmit} className="flex-1">
                    <Save className="w-4 h-4 mr-2" />{editingArticle ? "Update" : "Save"}
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Excel Format Help */}
      <Card className="border-border/50 bg-muted/30">
        <CardContent className="py-3">
          <p className="text-sm text-muted-foreground">
            <strong>Excel Format:</strong> For KB articles use columns: <code className="bg-muted px-1 rounded">title, content, category, tags</code> | 
            For Products use: <code className="bg-muted px-1 rounded">name, price, category, description, sku, stock</code>
          </p>
        </CardContent>
      </Card>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search articles..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={categoryFilter} onValueChange={setCategoryFilter}>
          <SelectTrigger className="w-full sm:w-[180px]">
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            {categories.map(c => (
              <SelectItem key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Articles */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map(i => <div key={i} className="skeleton-pulse h-32 rounded-xl" />)}
        </div>
      ) : filteredArticles.length === 0 ? (
        <Card className="border-border/50">
          <CardContent className="flex flex-col items-center justify-center py-16 text-muted-foreground">
            <BookOpen className="w-16 h-16 mb-4 opacity-50" />
            <p className="text-lg font-medium">No articles found</p>
            <p className="text-sm">Add knowledge articles to help AI answer better</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {filteredArticles.map(article => (
            <Card key={article.id} className="border-border/50">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <CardTitle className="text-base">{article.title}</CardTitle>
                      <Badge className={CategoryColors[article.category] || CategoryColors.general}>
                        {article.category}
                      </Badge>
                      {article.source_url && (
                        <Badge variant="outline" className="text-xs">
                          <Globe className="w-3 h-3 mr-1" />scraped
                        </Badge>
                      )}
                    </div>
                    {article.tags?.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {article.tags.map((tag, i) => (
                          <Badge key={i} variant="outline" className="text-xs">{tag}</Badge>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <Button variant="ghost" size="icon" onClick={() => handleEdit(article)}>
                      <Edit2 className="w-4 h-4" />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => handleDelete(article.id)} className="text-red-500 hover:text-red-600">
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap line-clamp-6">{article.content}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default KnowledgeBasePage;
