/* eslint-disable import/first */
import React from 'react';
import { renderHook, act } from '@testing-library/react';
import { AuthContextProvider, useAuth } from '../AuthContext';

jest.mock('../../../utils/api.service', () => ({
  __esModule: true,
  default: {
    login: jest.fn(),
    logout: jest.fn(),
  },
}));

jest.mock('jwt-decode', () => ({
  jwtDecode: jest.fn(),
}));

import apiService from '../../../utils/api.service';
import { jwtDecode } from 'jwt-decode';

const mockJwtDecode = jwtDecode as jest.Mock;
const mockLogin = apiService.login as jest.Mock;
const mockLogout = apiService.logout as jest.Mock;

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <AuthContextProvider>{children}</AuthContextProvider>
);

const VALID_TOKEN = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.test.signature';

const mockUser = {
  id: 'user-1',
  email: 'test@example.com',
  firstName: 'Test',
  lastName: 'User',
  orgId: 'org-1',
  orgRole: 'member' as const,
  isSuperAdmin: false,
  role: 'member' as const,
  isActive: true,
  isVerified: true,
  status: 'active' as const,
  timezone: 'America/New_York',
  createdAt: '2025-01-01T00:00:00Z',
  updatedAt: '2025-01-01T00:00:00Z',
};

beforeEach(() => {
  localStorage.clear();
  jest.clearAllMocks();
  // Default: token is valid (expires 1 hour from now)
  mockJwtDecode.mockReturnValue({ exp: Math.floor(Date.now() / 1000) + 3600 });
});

describe('AuthContext', () => {
  describe('useAuth hook', () => {
    it('throws when used outside of AuthContextProvider', () => {
      // Suppress console.error for the expected error boundary output
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      expect(() => {
        renderHook(() => useAuth());
      }).toThrow('useAuth must be used within AuthContextProvider');
      consoleSpy.mockRestore();
    });
  });

  describe('initial state', () => {
    it('has unauthenticated state when no token in localStorage', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      // After the useEffect runs, isLoading becomes false
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.token).toBeNull();
      expect(result.current.user).toBeNull();
      expect(result.current.isLoading).toBe(false);
      expect(result.current.challengeData).toBeNull();
    });

    it('restores authenticated state from valid token in localStorage', async () => {
      localStorage.setItem('authToken', VALID_TOKEN);
      localStorage.setItem('user', JSON.stringify(mockUser));

      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.token).toBe(VALID_TOKEN);
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isLoading).toBe(false);
    });

    it('clears state when stored token is expired', async () => {
      localStorage.setItem('authToken', VALID_TOKEN);
      localStorage.setItem('user', JSON.stringify(mockUser));
      localStorage.setItem('refreshToken', 'refresh-token-123');

      // Token expired 1 hour ago
      mockJwtDecode.mockReturnValue({ exp: Math.floor(Date.now() / 1000) - 3600 });

      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.token).toBeNull();
      expect(result.current.user).toBeNull();
      expect(localStorage.getItem('authToken')).toBeNull();
      expect(localStorage.getItem('user')).toBeNull();
      expect(localStorage.getItem('refreshToken')).toBeNull();
    });

    it('clears state when jwtDecode throws on malformed token', async () => {
      localStorage.setItem('authToken', 'malformed-token');
      localStorage.setItem('user', JSON.stringify(mockUser));

      mockJwtDecode.mockImplementation(() => {
        throw new Error('Invalid token');
      });

      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.token).toBeNull();
    });
  });

  describe('login', () => {
    it('sets auth state on successful login', async () => {
      const loginResponse = {
        data: {
          token: VALID_TOKEN,
          refreshToken: 'refresh-token-456',
          user: mockUser,
        },
      };
      mockLogin.mockResolvedValue(loginResponse);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        await result.current.login('test@example.com', 'password123');
      });

      expect(mockLogin).toHaveBeenCalledWith('test@example.com', 'password123');
      expect(result.current.token).toBe(VALID_TOKEN);
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
      expect(localStorage.getItem('authToken')).toBe(VALID_TOKEN);
      expect(localStorage.getItem('user')).toBe(JSON.stringify(mockUser));
      expect(localStorage.getItem('refreshToken')).toBe('refresh-token-456');
      expect(localStorage.getItem('currentOrgId')).toBe('org-1');
    });

    it('handles login response without nested data (flat response)', async () => {
      const loginResponse = {
        token: VALID_TOKEN,
        refreshToken: 'refresh-token-789',
        user: mockUser,
      };
      mockLogin.mockResolvedValue(loginResponse);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        await result.current.login('test@example.com', 'password123');
      });

      expect(result.current.token).toBe(VALID_TOKEN);
      expect(result.current.user).toEqual(mockUser);
    });

    it('throws NEW_PASSWORD_REQUIRED and sets challengeData on challenge response', async () => {
      const challengeResponse = {
        data: {
          challengeName: 'NEW_PASSWORD_REQUIRED',
          session: 'session-abc',
          email: 'test@example.com',
        },
      };
      mockLogin.mockResolvedValue(challengeResponse);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        await expect(
          result.current.login('test@example.com', 'password123')
        ).rejects.toThrow('NEW_PASSWORD_REQUIRED');
      });

      expect(result.current.challengeData).toEqual({
        challengeName: 'NEW_PASSWORD_REQUIRED',
        session: 'session-abc',
        email: 'test@example.com',
      });
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.token).toBeNull();
    });

    it('propagates API errors on login failure', async () => {
      mockLogin.mockRejectedValue(new Error('Invalid credentials'));

      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        await expect(
          result.current.login('test@example.com', 'wrong-password')
        ).rejects.toThrow('Invalid credentials');
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.token).toBeNull();
    });
  });

  describe('logout', () => {
    it('clears auth state and localStorage', async () => {
      localStorage.setItem('authToken', VALID_TOKEN);
      localStorage.setItem('user', JSON.stringify(mockUser));
      localStorage.setItem('refreshToken', 'refresh-token-123');
      localStorage.setItem('currentOrgId', 'org-1');
      mockLogout.mockResolvedValue({});

      const { result } = renderHook(() => useAuth(), { wrapper });

      // Confirm initially authenticated
      expect(result.current.isAuthenticated).toBe(true);

      act(() => {
        result.current.logout();
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.token).toBeNull();
      expect(result.current.user).toBeNull();
      expect(result.current.challengeData).toBeNull();
      expect(localStorage.getItem('authToken')).toBeNull();
      expect(localStorage.getItem('user')).toBeNull();
      expect(localStorage.getItem('refreshToken')).toBeNull();
      expect(localStorage.getItem('currentOrgId')).toBeNull();
      expect(mockLogout).toHaveBeenCalled();
    });

    it('handles API logout failure gracefully', async () => {
      localStorage.setItem('authToken', VALID_TOKEN);
      localStorage.setItem('user', JSON.stringify(mockUser));
      mockLogout.mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useAuth(), { wrapper });

      // Should not throw even when API call fails
      act(() => {
        result.current.logout();
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.token).toBeNull();
    });
  });

  describe('setAuthData', () => {
    it('updates token, user, and localStorage', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      const authData = {
        token: VALID_TOKEN,
        refreshToken: 'refresh-new',
        user: mockUser,
      };

      act(() => {
        result.current.setAuthData(authData);
      });

      expect(result.current.token).toBe(VALID_TOKEN);
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
      expect(localStorage.getItem('authToken')).toBe(VALID_TOKEN);
      expect(localStorage.getItem('user')).toBe(JSON.stringify(mockUser));
      expect(localStorage.getItem('refreshToken')).toBe('refresh-new');
      expect(localStorage.getItem('currentOrgId')).toBe('org-1');
    });

    it('clears challengeData when setAuthData is called', async () => {
      const challengeResponse = {
        data: {
          challengeName: 'NEW_PASSWORD_REQUIRED',
          session: 'session-abc',
          email: 'test@example.com',
        },
      };
      mockLogin.mockResolvedValue(challengeResponse);

      const { result } = renderHook(() => useAuth(), { wrapper });

      // Trigger challenge
      await act(async () => {
        try {
          await result.current.login('test@example.com', 'password');
        } catch {
          // Expected
        }
      });
      expect(result.current.challengeData).not.toBeNull();

      // Now set auth data (simulating password reset completion)
      act(() => {
        result.current.setAuthData({ token: VALID_TOKEN, user: mockUser });
      });

      expect(result.current.challengeData).toBeNull();
      expect(result.current.isAuthenticated).toBe(true);
    });

    it('does not set refreshToken when not provided', () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      act(() => {
        result.current.setAuthData({ token: VALID_TOKEN, user: mockUser });
      });

      expect(localStorage.getItem('refreshToken')).toBeNull();
    });

    it('does not set currentOrgId when user has no orgId', () => {
      const userWithoutOrg = { ...mockUser, orgId: undefined };
      const { result } = renderHook(() => useAuth(), { wrapper });

      act(() => {
        result.current.setAuthData({ token: VALID_TOKEN, user: userWithoutOrg });
      });

      expect(localStorage.getItem('currentOrgId')).toBeNull();
    });
  });

  describe('clearChallenge', () => {
    it('sets challengeData to null', async () => {
      const challengeResponse = {
        data: {
          challengeName: 'NEW_PASSWORD_REQUIRED',
          session: 'session-abc',
          email: 'test@example.com',
        },
      };
      mockLogin.mockResolvedValue(challengeResponse);

      const { result } = renderHook(() => useAuth(), { wrapper });

      // Trigger challenge
      await act(async () => {
        try {
          await result.current.login('test@example.com', 'password');
        } catch {
          // Expected
        }
      });
      expect(result.current.challengeData).not.toBeNull();

      act(() => {
        result.current.clearChallenge();
      });

      expect(result.current.challengeData).toBeNull();
    });
  });
});
