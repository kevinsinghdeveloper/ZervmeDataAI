import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { jwtDecode } from 'jwt-decode';
import { User, AuthResponse } from '../../types';
import apiService from '../../utils/api.service';

interface ChallengeData {
  challengeName: string;
  session: string;
  email: string;
}

interface AuthContextType {
  isAuthenticated: boolean;
  token: string | null;
  user: User | null;
  isLoading: boolean;
  challengeData: ChallengeData | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  setAuthData: (data: AuthResponse) => void;
  clearChallenge: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthContextProvider');
  return context;
};

export const AuthContextProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem('authToken'));
  const [user, setUser] = useState<User | null>(() => {
    const stored = localStorage.getItem('user');
    return stored ? JSON.parse(stored) : null;
  });
  const [isLoading, setIsLoading] = useState(true);
  const [challengeData, setChallengeData] = useState<ChallengeData | null>(null);

  const checkTokenExpiration = useCallback(() => {
    if (!token) return false;
    try {
      const decoded: any = jwtDecode(token);
      return decoded.exp * 1000 > Date.now();
    } catch {
      return false;
    }
  }, [token]);

  useEffect(() => {
    if (token && !checkTokenExpiration()) {
      setToken(null);
      setUser(null);
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');
      localStorage.removeItem('refreshToken');
    }
    setIsLoading(false);
  }, [token, checkTokenExpiration]);

  const setAuthData = (data: AuthResponse) => {
    setToken(data.token);
    setUser(data.user);
    setChallengeData(null);
    localStorage.setItem('authToken', data.token);
    localStorage.setItem('user', JSON.stringify(data.user));
    if (data.refreshToken) {
      localStorage.setItem('refreshToken', data.refreshToken);
    }

    // Multi-org: set currentOrgId
    const storedOrg = localStorage.getItem('currentOrgId');
    const memberships = data.user?.orgMemberships || [];
    const memberOrgIds = memberships.map(m => m.orgId);

    if (storedOrg && memberOrgIds.includes(storedOrg)) {
      // Keep existing org selection if still a member
    } else if (data.user?.orgId) {
      localStorage.setItem('currentOrgId', data.user.orgId);
    } else if (memberOrgIds.length > 0) {
      localStorage.setItem('currentOrgId', memberOrgIds[0]);
    }
  };

  const login = async (email: string, password: string) => {
    const response = await apiService.login(email, password);
    const data = response.data || response;

    // Check for challenge response (NEW_PASSWORD_REQUIRED)
    if (data.challengeName === 'NEW_PASSWORD_REQUIRED') {
      setChallengeData({
        challengeName: data.challengeName,
        session: data.session,
        email: data.email || email,
      });
      throw new Error('NEW_PASSWORD_REQUIRED');
    }

    setAuthData(data);
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    setChallengeData(null);
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('currentOrgId');
    apiService.logout().catch(() => {});
  };

  const clearChallenge = () => {
    setChallengeData(null);
  };

  return (
    <AuthContext.Provider value={{
      isAuthenticated: !!token && checkTokenExpiration(),
      token, user, isLoading, challengeData,
      login, logout, setAuthData, clearChallenge,
    }}>
      {children}
    </AuthContext.Provider>
  );
};
