import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { User, UserPreferences } from '../../types';
import { useAuth } from './AuthContext';
import apiService from '../../utils/api.service';

interface UserContextType {
  user: User | null;
  isLoading: boolean;
  error: string | null;
  fetchCurrentUser: () => Promise<void>;
  updateUser: (data: Partial<User>) => Promise<void>;
  updatePreferences: (prefs: Partial<UserPreferences>) => Promise<void>;
  setUser: (user: User) => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export const useUser = () => {
  const context = useContext(UserContext);
  if (!context) throw new Error('useUser must be used within UserContextProvider');
  return context;
};

export const UserContextProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCurrentUser = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiService.getCurrentUser();
      setUser(response.data || response);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) fetchCurrentUser();
    else setUser(null);
  }, [isAuthenticated, fetchCurrentUser]);

  const updateUser = async (data: Partial<User>) => {
    if (!user) throw new Error('No authenticated user');
    const response = await apiService.updateUser(user.id, data);
    setUser(response.data || response);
  };

  const updatePreferences = async (prefs: Partial<UserPreferences>) => {
    await apiService.updatePreferences(prefs);
    await fetchCurrentUser();
  };

  return (
    <UserContext.Provider value={{ user, isLoading, error, fetchCurrentUser, updateUser, updatePreferences, setUser }}>
      {children}
    </UserContext.Provider>
  );
};
