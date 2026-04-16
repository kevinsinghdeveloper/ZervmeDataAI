import React from 'react';
import { Navigate } from 'react-router-dom';
import { OrgRole } from '../../types';
import { useAuth } from '../context_providers/AuthContext';
import { useRBAC } from '../context_providers/RBACContext';
import LoadingSpinner from './LoadingSpinner';

interface ProtectedRouteProps {
  children: React.ReactNode;
  adminOnly?: boolean;
  superAdminOnly?: boolean;
  minOrgRole?: OrgRole;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  adminOnly = false,
  superAdminOnly = false,
  minOrgRole,
}) => {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { isSuperAdmin, meetsMinOrgRole, isLoading: rbacLoading } = useRBAC();

  if (authLoading || rbacLoading) return <LoadingSpinner message="Checking access..." />;
  if (!isAuthenticated) return <Navigate to="/login" replace />;

  if ((superAdminOnly || adminOnly) && !isSuperAdmin) {
    return <Navigate to="/projects" replace />;
  }

  if (minOrgRole && !meetsMinOrgRole(minOrgRole)) {
    return <Navigate to="/projects" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
