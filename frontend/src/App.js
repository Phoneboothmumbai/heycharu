import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "./components/ui/sonner";
import { ThemeProvider } from "./contexts/ThemeContext";
import { AuthProvider, useAuth } from "./contexts/AuthContext";

// Pages
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import CustomersPage from "./pages/CustomersPage";
import CustomerCoverPage from "./pages/CustomerCoverPage";
import ConversationsPage from "./pages/ConversationsPage";
import ProductsPage from "./pages/ProductsPage";
import OrdersPage from "./pages/OrdersPage";
import WhatsAppPage from "./pages/WhatsAppPage";
import SettingsPage from "./pages/SettingsPage";
import LeadsPage from "./pages/LeadsPage";
import ExcludedNumbersPage from "./pages/ExcludedNumbersPage";
import AutoMessagesPage from "./pages/AutoMessagesPage";
import KnowledgeBasePage from "./pages/KnowledgeBasePage";

// Layout
import AppLayout from "./components/layout/AppLayout";

import "./App.css";

function ProtectedRoute(props) {
  var children = props.children;
  var auth = useAuth();
  var user = auth.user;
  var loading = auth.loading;
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="ai-thinking">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    );
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <Routes>
                      <Route path="/" element={<DashboardPage />} />
                      <Route path="/dashboard" element={<DashboardPage />} />
                      <Route path="/customers" element={<CustomersPage />} />
                      <Route path="/customers/:customerId" element={<CustomerCoverPage />} />
                      <Route path="/conversations" element={<ConversationsPage />} />
                      <Route path="/products" element={<ProductsPage />} />
                      <Route path="/orders" element={<OrdersPage />} />
                      <Route path="/whatsapp" element={<WhatsAppPage />} />
                      <Route path="/leads" element={<LeadsPage />} />
                      <Route path="/excluded-numbers" element={<ExcludedNumbersPage />} />
                      <Route path="/auto-messages" element={<AutoMessagesPage />} />
                      <Route path="/settings" element={<SettingsPage />} />
                    </Routes>
                  </AppLayout>
                </ProtectedRoute>
              }
            />
          </Routes>
        </BrowserRouter>
        <Toaster position="top-right" richColors />
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
