import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { Role, OrgRole, ROLE_PERMISSIONS, ORG_ROLE_HIERARCHY, ORG_ROLE_PERMISSIONS } from '../../types';
import { useAuth } from './AuthContext';

interface RBACContextType {
  role: Role | null;
  orgRole: OrgRole | null;
  orgRoles: OrgRole[];
  isSuperAdmin: boolean;
  isAdmin: boolean;
  isEditor: boolean;
  isViewer: boolean;
  isLendee: boolean;
  hasPermission: (resource: string, action: string) => boolean;
  hasOrgPermission: (permission: string) => boolean;
  meetsMinOrgRole: (minRole: OrgRole) => boolean;
  hasAnyOrgRole: (roles: OrgRole[]) => boolean;
  isLoading: boolean;
}

const RBACContext = createContext<RBACContextType | undefined>(undefined);

export const useRBAC = () => {
  const context = useContext(RBACContext);
  if (!context) throw new Error('useRBAC must be used within RBACContextProvider');
  return context;
};

export const useIsAdmin = () => useRBAC().isAdmin;

export const usePermission = (resource: string, action: string) => {
  const { hasPermission } = useRBAC();
  return hasPermission(resource, action);
};

export const useHasOrgPermission = (permission: string) => {
  const { hasOrgPermission } = useRBAC();
  return hasOrgPermission(permission);
};

export const RBACContextProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, user } = useAuth();
  const [role, setRole] = useState<Role | null>(null);
  const [orgRole, setOrgRole] = useState<OrgRole | null>(null);
  const [orgRoles, setOrgRoles] = useState<OrgRole[]>([]);
  const [isSuperAdmin, setIsSuperAdmin] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const syncRoles = useCallback(() => {
    if (!user) return;
    setIsLoading(true);

    setIsSuperAdmin(!!user.isSuperAdmin);
    setRole((user.role || 'member') as Role);

    // Determine roles in the active org from orgMemberships
    const activeOrgId = localStorage.getItem('currentOrgId');
    const memberships = user.orgMemberships || [];
    const currentOrgMembership = memberships.find(m => m.orgId === activeOrgId);
    const currentOrgRoles = currentOrgMembership?.roles || [];

    if (currentOrgRoles.length > 0) {
      setOrgRoles(currentOrgRoles as OrgRole[]);
      // Set orgRole to the highest role for backward compat
      const highest = currentOrgRoles.reduce((best, r) => {
        const currentIdx = ORG_ROLE_HIERARCHY.indexOf(r as OrgRole);
        const bestIdx = ORG_ROLE_HIERARCHY.indexOf(best as OrgRole);
        return currentIdx > bestIdx ? r : best;
      }, currentOrgRoles[0]);
      setOrgRole(highest as OrgRole);
    } else {
      // Fallback to inline orgRole for backward compat
      setOrgRole((user.orgRole || 'member') as OrgRole);
      setOrgRoles(user.orgRole ? [user.orgRole as OrgRole] : []);
    }

    setIsLoading(false);
  }, [user]);

  useEffect(() => {
    if (isAuthenticated && user) syncRoles();
    else {
      setRole(null);
      setOrgRole(null);
      setOrgRoles([]);
      setIsSuperAdmin(false);
    }
  }, [isAuthenticated, user, syncRoles]);

  // Re-sync when org is switched
  useEffect(() => {
    const handleOrgSwitch = () => syncRoles();
    window.addEventListener('org-switched', handleOrgSwitch);
    return () => window.removeEventListener('org-switched', handleOrgSwitch);
  }, [syncRoles]);

  const hasPermission = (resource: string, action: string): boolean => {
    if (!role) return false;
    const permissions = ROLE_PERMISSIONS[role];
    if (!permissions) return false;
    return permissions.some(
      (p) => (p.resource === '*' || p.resource === resource) && (p.actions.includes('*') || p.actions.includes(action))
    );
  };

  const hasOrgPermission = (permission: string): boolean => {
    if (isSuperAdmin) return true;
    if (orgRoles.length === 0) return false;
    // Aggregate permissions across all roles in the active org
    for (const r of orgRoles) {
      const permissions = ORG_ROLE_PERMISSIONS[r];
      if (permissions && permissions.includes(permission)) return true;
    }
    return false;
  };

  const meetsMinOrgRole = (minRole: OrgRole): boolean => {
    if (isSuperAdmin) return true;
    if (orgRoles.length === 0) return false;
    const requiredIndex = ORG_ROLE_HIERARCHY.indexOf(minRole);
    // Check if any of the user's roles meets the minimum
    return orgRoles.some(r => {
      const currentIndex = ORG_ROLE_HIERARCHY.indexOf(r);
      return currentIndex >= requiredIndex;
    });
  };

  const hasAnyOrgRole = (roles: OrgRole[]): boolean => {
    if (isSuperAdmin) return true;
    return orgRoles.some(r => roles.includes(r));
  };

  const isAdmin = isSuperAdmin || orgRole === 'admin' || orgRole === 'owner' || role === 'admin';

  return (
    <RBACContext.Provider value={{
      role, orgRole, orgRoles, isSuperAdmin, isAdmin,
      isEditor: role === 'editor', isViewer: role === 'viewer', isLendee: role === 'lendee',
      hasPermission, hasOrgPermission, meetsMinOrgRole, hasAnyOrgRole, isLoading,
    }}>
      {children}
    </RBACContext.Provider>
  );
};
