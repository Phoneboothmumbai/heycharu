import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useTheme } from "../../contexts/ThemeContext";
import { useAuth } from "../../contexts/AuthContext";
import { Button } from "../ui/button";
import { Avatar, AvatarFallback } from "../ui/avatar";
import * as DropdownMenuPrimitive from "@radix-ui/react-dropdown-menu";
import { LayoutDashboard, Users, MessageSquare, Package, ShoppingCart, Settings, Sun, Moon, LogOut, Menu, X, Brain, Smartphone, Rocket, EyeOff, Zap } from "lucide-react";

var navItems = [
  { icon: LayoutDashboard, label: "Dashboard", path: "/dashboard" },
  { icon: Users, label: "Customers", path: "/customers" },
  { icon: MessageSquare, label: "Conversations", path: "/conversations" },
  { icon: Package, label: "Products", path: "/products" },
  { icon: ShoppingCart, label: "Orders", path: "/orders" },
  { icon: Smartphone, label: "WhatsApp", path: "/whatsapp" },
  { icon: Rocket, label: "Lead Injection", path: "/leads" },
  { icon: EyeOff, label: "Excluded Numbers", path: "/excluded-numbers" },
  { icon: Zap, label: "Auto-Messages", path: "/auto-messages" },
  { icon: Settings, label: "Settings", path: "/settings" },
];

function AppLayout(props) {
  var children = props.children;
  var themeContext = useTheme();
  var theme = themeContext.theme;
  var toggleTheme = themeContext.toggleTheme;
  var authContext = useAuth();
  var user = authContext.user;
  var logout = authContext.logout;
  var location = useLocation();
  var [sidebarOpen, setSidebarOpen] = useState(false);

  function isActive(path) {
    return location.pathname === path || (path === "/dashboard" && location.pathname === "/");
  }

  function closeSidebar() {
    setSidebarOpen(false);
  }

  function openSidebar() {
    setSidebarOpen(true);
  }

  return (
    <div className="min-h-screen bg-background flex">
      {sidebarOpen && <div className="fixed inset-0 bg-black/50 z-40 lg:hidden" onClick={closeSidebar}></div>}

      <aside className={"fixed lg:static inset-y-0 left-0 z-50 w-64 bg-card border-r border-border transform transition-transform duration-200 lg:translate-x-0 " + (sidebarOpen ? "translate-x-0" : "-translate-x-full")}>
        <div className="flex flex-col h-full">
          <div className="flex items-center gap-3 px-6 h-16 border-b border-border">
            <div className="w-9 h-9 rounded-lg gradient-ai flex items-center justify-center">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-lg tracking-tight">Sales Brain</span>
            <Button variant="ghost" size="icon" className="ml-auto lg:hidden" onClick={closeSidebar}>
              <X className="w-5 h-5" />
            </Button>
          </div>

          <nav className="flex-1 py-4 px-3 space-y-1 overflow-auto">
            {navItems.map(function(item) {
              var Icon = item.icon;
              return (
                <Link key={item.path} to={item.path} onClick={closeSidebar} className={"sidebar-link " + (isActive(item.path) ? "active" : "")} data-testid={"nav-" + item.label.toLowerCase()}>
                  <Icon className="w-5 h-5" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>

          <div className="p-4 border-t border-border">
            <DropdownMenuPrimitive.Root>
              <DropdownMenuPrimitive.Trigger asChild>
                <Button variant="ghost" className="w-full justify-start gap-3 h-auto py-2" data-testid="user-menu-trigger">
                  <Avatar className="w-8 h-8">
                    <AvatarFallback className="bg-primary/10 text-primary text-sm">{user && user.name ? user.name.charAt(0).toUpperCase() : "U"}</AvatarFallback>
                  </Avatar>
                  <div className="flex-1 text-left">
                    <p className="text-sm font-medium truncate">{user ? user.name : ""}</p>
                    <p className="text-xs text-muted-foreground truncate">{user ? user.email : ""}</p>
                  </div>
                </Button>
              </DropdownMenuPrimitive.Trigger>
              <DropdownMenuPrimitive.Portal>
                <DropdownMenuPrimitive.Content align="end" className="w-56 z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-md">
                  <DropdownMenuPrimitive.Item onClick={toggleTheme} className="relative flex cursor-default select-none items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none transition-colors focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50 [&>svg]:size-4 [&>svg]:shrink-0" data-testid="theme-toggle">
                    {theme === "light" ? <Moon className="w-4 h-4 mr-2" /> : <Sun className="w-4 h-4 mr-2" />}
                    {theme === "light" ? "Dark Mode" : "Light Mode"}
                  </DropdownMenuPrimitive.Item>
                  <DropdownMenuPrimitive.Separator className="h-px bg-muted -mx-1 my-1" />
                  <DropdownMenuPrimitive.Item onClick={logout} className="relative flex cursor-default select-none items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none transition-colors focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50 [&>svg]:size-4 [&>svg]:shrink-0 text-destructive" data-testid="logout-btn">
                    <LogOut className="w-4 h-4 mr-2" />Logout
                  </DropdownMenuPrimitive.Item>
                </DropdownMenuPrimitive.Content>
              </DropdownMenuPrimitive.Portal>
            </DropdownMenuPrimitive.Root>
          </div>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 border-b border-border bg-card/50 backdrop-blur-sm flex items-center px-4 lg:px-6 sticky top-0 z-30">
          <Button variant="ghost" size="icon" className="lg:hidden mr-2" onClick={openSidebar} data-testid="mobile-menu-btn">
            <Menu className="w-5 h-5" />
          </Button>
          <h1 className="text-lg font-semibold capitalize">{location.pathname === "/" ? "Dashboard" : location.pathname.slice(1)}</h1>
          <div className="ml-auto">
            <Button variant="ghost" size="icon" onClick={toggleTheme} className="hidden lg:flex" data-testid="header-theme-toggle">
              {theme === "light" ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
            </Button>
          </div>
        </header>
        <main className="flex-1 p-4 lg:p-6 overflow-auto">{children}</main>
      </div>
    </div>
  );
}

export default AppLayout;
