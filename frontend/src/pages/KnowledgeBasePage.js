import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Badge } from "../components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { toast } from "sonner";
import { BookOpen, Plus, Search, Edit2, Trash2, Save } from "lucide-react";

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

  const fetchArticles = useCallback(async () => {
    try {
      const res = await axios.get(`${API_URL}/api/knowledge-base`);
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
        await axios.put(`${API_URL}/api/knowledge-base/${editingArticle.id}`, payload);
        toast.success("Article updated");
      } else {
        await axios.post(`${API_URL}/api/knowledge-base`, payload);
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
      await axios.delete(`${API_URL}/api/knowledge-base/${id}`);
      toast.success("Article deleted");
      fetchArticles();
    } catch (e) {
      toast.error("Failed to delete");
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
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">{article.content}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default KnowledgeBasePage;
