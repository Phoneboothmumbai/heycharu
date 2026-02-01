import { useState, useEffect } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Avatar, AvatarFallback } from "../components/ui/avatar";
import { ScrollArea } from "../components/ui/scroll-area";
import { toast } from "sonner";
import {
  Users,
  MessageSquare,
  ListTodo,
  ShoppingCart,
  IndianRupee,
  TrendingUp,
  ArrowRight,
  Sparkles,
} from "lucide-react";
import { Link } from "react-router-dom";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const StatCard = ({ title, value, icon: Icon, trend, color }) => (
  <Card className="stat-card" data-testid={`stat-${title.toLowerCase().replace(/\s/g, '-')}`}>
    <CardContent className="p-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <p className="text-3xl font-bold mt-2">{value}</p>
          {trend && (
            <p className="text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-1 mt-2">
              <TrendingUp className="w-3 h-3" />
              {trend}
            </p>
          )}
        </div>
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${color}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </CardContent>
  </Card>
);

const DashboardPage = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
    seedData();
  }, []);

  const seedData = async () => {
    try {
      await axios.post(`${API_URL}/api/seed`);
    } catch (error) {
      // Already seeded, ignore
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/dashboard/stats`);
      setStats(response.data);
    } catch (error) {
      toast.error("Failed to load dashboard stats");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="stat-card">
              <CardContent className="p-6">
                <div className="skeleton-pulse h-20 rounded" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in">
      {/* Welcome Banner */}
      <Card className="bg-gradient-to-r from-primary/10 via-primary/5 to-transparent border-primary/20">
        <CardContent className="p-6 flex items-center gap-4">
          <div className="w-14 h-14 rounded-xl gradient-ai flex items-center justify-center shadow-glow">
            <Sparkles className="w-7 h-7 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold">Welcome to Sales Brain</h2>
            <p className="text-muted-foreground">Your AI-powered customer intelligence platform is ready</p>
          </div>
        </CardContent>
      </Card>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Customers"
          value={stats?.total_customers || 0}
          icon={Users}
          trend="+12% this month"
          color="bg-blue-500"
        />
        <StatCard
          title="Active Conversations"
          value={stats?.active_conversations || 0}
          icon={MessageSquare}
          color="bg-emerald-500"
        />
        <StatCard
          title="Open Topics"
          value={stats?.open_topics || 0}
          icon={ListTodo}
          color="bg-amber-500"
        />
        <StatCard
          title="Pending Orders"
          value={stats?.pending_orders || 0}
          icon={ShoppingCart}
          color="bg-purple-500"
        />
      </div>

      {/* Revenue Card */}
      <Card className="stat-card col-span-full">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Total Revenue</p>
              <p className="text-4xl font-bold mt-2 flex items-center">
                <IndianRupee className="w-8 h-8" />
                {(stats?.total_revenue || 0).toLocaleString('en-IN')}
              </p>
            </div>
            <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center">
              <TrendingUp className="w-8 h-8 text-white" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Conversations */}
        <Card className="border-border/50">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-lg">Recent Conversations</CardTitle>
            <Link to="/conversations">
              <Button variant="ghost" size="sm" className="text-primary" data-testid="view-all-conversations">
                View All <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[300px]">
              {stats?.recent_conversations?.length > 0 ? (
                <div className="space-y-3">
                  {stats.recent_conversations.map((conv) => (
                    <div
                      key={conv.id}
                      className="flex items-start gap-3 p-3 rounded-lg hover:bg-accent transition-colors cursor-pointer"
                      data-testid={`conversation-${conv.id}`}
                    >
                      <Avatar className="w-10 h-10">
                        <AvatarFallback className="bg-primary/10 text-primary">
                          {conv.customer_name?.charAt(0)?.toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="font-medium truncate">{conv.customer_name}</p>
                          <Badge variant="outline" className="text-xs">
                            {conv.channel}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground truncate mt-1">
                          {conv.last_message || "No messages yet"}
                        </p>
                      </div>
                      {conv.unread_count > 0 && (
                        <Badge className="bg-primary">{conv.unread_count}</Badge>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                  <MessageSquare className="w-12 h-12 mb-3 opacity-50" />
                  <p>No conversations yet</p>
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Top Customers */}
        <Card className="border-border/50">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-lg">Top Customers</CardTitle>
            <Link to="/customers">
              <Button variant="ghost" size="sm" className="text-primary" data-testid="view-all-customers">
                View All <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[300px]">
              {stats?.top_customers?.length > 0 ? (
                <div className="space-y-3">
                  {stats.top_customers.map((customer, index) => (
                    <div
                      key={customer.id}
                      className="flex items-center gap-3 p-3 rounded-lg hover:bg-accent transition-colors"
                      data-testid={`top-customer-${customer.id}`}
                    >
                      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold">
                        {index + 1}
                      </div>
                      <Avatar className="w-10 h-10">
                        <AvatarFallback className="bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400">
                          {customer.name?.charAt(0)?.toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{customer.name}</p>
                      </div>
                      <p className="font-semibold text-emerald-600 dark:text-emerald-400 flex items-center">
                        <IndianRupee className="w-4 h-4" />
                        {(customer.total_spent || 0).toLocaleString('en-IN')}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                  <Users className="w-12 h-12 mb-3 opacity-50" />
                  <p>No customers yet</p>
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default DashboardPage;
