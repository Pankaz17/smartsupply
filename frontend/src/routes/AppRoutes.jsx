import { Navigate, Route, Routes } from 'react-router-dom'
import AppLayout from '../components/layout/AppLayout'
import CategoriesPage from '../pages/CategoriesPage'
import ChangePasswordPage from '../pages/ChangePasswordPage'
import DashboardPage from '../pages/DashboardPage'
import DeadStockPage from '../pages/DeadStockPage'
import LoginPage from '../pages/LoginPage'
import NotificationsPage from '../pages/NotificationsPage'
import ProductsPage from '../pages/ProductsPage'
import PurchaseOrdersPage from '../pages/PurchaseOrdersPage'
import RecommendationsPage from '../pages/RecommendationsPage'
import DeadStockReportPage from '../pages/reports/DeadStockReportPage'
import InventoryReportPage from '../pages/reports/InventoryReportPage'
import RecommendationsReportPage from '../pages/reports/RecommendationsReportPage'
import ProfitAdvisorReportPage from '../pages/reports/ProfitAdvisorReportPage'
import ReportsDashboardPage from '../pages/reports/ReportsDashboardPage'
import SalesReportPage from '../pages/reports/SalesReportPage'
import SupplierReportPage from '../pages/reports/SupplierReportPage'
import SalesPage from '../pages/SalesPage'
import SeasonalEventsPage from '../pages/SeasonalEventsPage'
import SettingsPage from '../pages/SettingsPage'
import StaffPage from '../pages/StaffPage'
import SupplierAnalyticsPage from '../pages/SupplierAnalyticsPage'
import SuppliersPage from '../pages/SuppliersPage'
import ProtectedRoute from './ProtectedRoute'

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="recommendations" element={<RecommendationsPage />} />
          <Route path="purchase-orders" element={<PurchaseOrdersPage />} />
          <Route path="dead-stock" element={<DeadStockPage />} />
          <Route path="supplier-analytics" element={<SupplierAnalyticsPage />} />
          <Route path="seasonal-events" element={<SeasonalEventsPage />} />
          <Route path="notifications" element={<NotificationsPage />} />
          <Route path="change-password" element={<ChangePasswordPage />} />
          <Route path="reports" element={<ReportsDashboardPage />} />
          <Route path="reports/inventory" element={<InventoryReportPage />} />
          <Route path="reports/sales" element={<SalesReportPage />} />
          <Route path="reports/dead-stock" element={<DeadStockReportPage />} />
          <Route path="reports/suppliers" element={<SupplierReportPage />} />
          <Route path="reports/recommendations" element={<RecommendationsReportPage />} />
          <Route path="reports/profit-advisor" element={<ProfitAdvisorReportPage />} />
          <Route path="products" element={<ProductsPage />} />
          <Route path="sales" element={<SalesPage />} />
          <Route element={<ProtectedRoute ownerOnly />}>
            <Route path="categories" element={<CategoriesPage />} />
            <Route path="suppliers" element={<SuppliersPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="staff" element={<StaffPage />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
