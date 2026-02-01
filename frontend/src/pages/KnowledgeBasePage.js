import React, { useState, useEffect } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Textarea } from "../components/ui/textarea";
import { toast } from "sonner";
import { Search, Plus, BookOpen, Edit, Trash2 } from "lucide-react";

var API_URL = process.env.REACT_APP_BACKEND_URL;

var CategoryColors = {
  faq: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  policy: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400",
  procedure: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
  product_info: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400"
};

function KnowledgeBasePage() {
  var [articles, setArticles] = useState([]);
  var [loading, setLoading] = useState(true);
  var [search, setSearch] = useState("");
  var [isAddOpen, setIsAddOpen] = useState(false);
  var [editingArticle, setEditingArticle] = useState(null);
  var [formTitle, setFormTitle] = useState("");
  var [formCategory, setFormCategory] = useState("faq");
  var [formContent, setFormContent] = useState("");
  var [formTags, setFormTags] = useState("");

  useEffect(function() {
    fetchArticles();
  }, [search]);

  function fetchArticles() {
    var url = API_URL + "/api/kb";
    if (search) {
      url = url + "?search=" + encodeURIComponent(search);
    }
    
    axios.get(url).then(function(res) {
      setArticles(res.data);
      setLoading(false);
    }).catch(function() {
      toast.error("Failed to load articles");
      setLoading(false);
    });
  }

  function handleSubmit(e) {
    e.preventDefault();
    var tagsList = formTags.split(",").map(function(t) { return t.trim(); }).filter(function(t) { return t.length > 0; });
    var data = {
      title: formTitle,
      category: formCategory,
      content: formContent,
      tags: tagsList
    };

    var promise;
    if (editingArticle) {
      promise = axios.put(API_URL + "/api/kb/" + editingArticle.id, data);
    } else {
      promise = axios.post(API_URL + "/api/kb", data);
    }

    promise.then(function() {
      toast.success(editingArticle ? "Article updated" : "Article created");
      closeDialog();
      fetchArticles();
    }).catch(function(err) {
      toast.error(err.response && err.response.data ? err.response.data.detail : "Failed to save");
    });
  }

  function handleEdit(article) {
    setEditingArticle(article);
    setFormTitle(article.title);
    setFormCategory(article.category);
    setFormContent(article.content);
    setFormTags(article.tags ? article.tags.join(", ") : "");
    setIsAddOpen(true);
  }

  function handleDelete(id) {
    if (!window.confirm("Delete this article?")) return;
    axios.delete(API_URL + "/api/kb/" + id).then(function() {
      toast.success("Article deleted");
      fetchArticles();
    }).catch(function() {
      toast.error("Failed to delete");
    });
  }

  function closeDialog() {
    setIsAddOpen(false);
    setEditingArticle(null);
    setFormTitle("");
    setFormCategory("faq");
    setFormContent("");
    setFormTags("");
  }

  function openDialog() {
    setIsAddOpen(true);
  }

  return (
    <div className="space-y-6 animate-in">
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Knowledge Base</h1>
          <p className="text-muted-foreground">Manage FAQs, policies, and procedures for AI</p>
        </div>
        <Dialog open={isAddOpen} onOpenChange={function(open) { if (open) openDialog(); else closeDialog(); }}>
          <DialogTrigger asChild>
            <Button className="btn-primary" data-testid="add-kb-btn">
              <Plus className="w-4 h-4 mr-2" />Add Article
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-lg">
            <DialogHeader>
              <DialogTitle>{editingArticle ? "Edit Article" : "Add KB Article"}</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label>Title *</Label>
                <Input value={formTitle} onChange={function(e) { setFormTitle(e.target.value); }} required data-testid="kb-title-input" />
              </div>
              <div className="space-y-2">
                <Label>Category *</Label>
                <Select value={formCategory} onValueChange={setFormCategory}>
                  <SelectTrigger data-testid="kb-category-select"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="faq">FAQ</SelectItem>
                    <SelectItem value="policy">Policy</SelectItem>
                    <SelectItem value="procedure">Procedure</SelectItem>
                    <SelectItem value="product_info">Product Info</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Content *</Label>
                <Textarea value={formContent} onChange={function(e) { setFormContent(e.target.value); }} required rows={6} data-testid="kb-content-input" />
              </div>
              <div className="space-y-2">
                <Label>Tags (comma-separated)</Label>
                <Input value={formTags} onChange={function(e) { setFormTags(e.target.value); }} data-testid="kb-tags-input" />
              </div>
              <div className="flex gap-3 pt-4">
                <Button type="button" variant="outline" onClick={closeDialog} className="flex-1">Cancel</Button>
                <Button type="submit" className="flex-1 btn-primary" data-testid="save-kb-btn">{editingArticle ? "Update" : "Save"}</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input placeholder="Search articles..." value={search} onChange={function(e) { setSearch(e.target.value); }} className="pl-10" data-testid="kb-search-input" />
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card><CardContent className="p-6"><div className="skeleton-pulse h-32 rounded"></div></CardContent></Card>
          <Card><CardContent className="p-6"><div className="skeleton-pulse h-32 rounded"></div></CardContent></Card>
          <Card><CardContent className="p-6"><div className="skeleton-pulse h-32 rounded"></div></CardContent></Card>
        </div>
      ) : articles.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 text-muted-foreground">
            <BookOpen className="w-16 h-16 mb-4 opacity-50" />
            <p className="text-lg font-medium">No articles found</p>
            <p className="text-sm">Add KB articles to help the AI respond accurately</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {articles.map(function(article) {
            return (
              <Card key={article.id} className="border-border/50 card-hover group" data-testid={"kb-article-" + article.id}>
                <CardHeader className="pb-2">
                  <Badge className={CategoryColors[article.category] || ""}>{article.category}</Badge>
                  <CardTitle className="text-lg line-clamp-2 mt-2">{article.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground line-clamp-4">{article.content}</p>
                  {article.tags && article.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-3">
                      {article.tags.map(function(tag, i) {
                        return <Badge key={i} variant="outline" className="text-xs">{tag}</Badge>;
                      })}
                    </div>
                  )}
                  <div className="flex gap-2 pt-4 opacity-0 group-hover:opacity-100 transition-opacity">
                    <Button variant="outline" size="sm" className="flex-1" onClick={function() { handleEdit(article); }} data-testid={"edit-kb-" + article.id}>
                      <Edit className="w-4 h-4 mr-1" />Edit
                    </Button>
                    <Button variant="outline" size="sm" onClick={function() { handleDelete(article.id); }} className="text-destructive hover:bg-destructive hover:text-white" data-testid={"delete-kb-" + article.id}>
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default KnowledgeBasePage;
