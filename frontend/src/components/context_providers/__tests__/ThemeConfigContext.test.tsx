/* eslint-disable import/first, testing-library/no-wait-for-multiple-assertions */
import React from 'react';
import { renderHook, act, waitFor } from '@testing-library/react';
import { ThemeConfigProvider, useThemeConfig } from '../ThemeConfigContext';

jest.mock('../../../utils/api.service', () => ({
  __esModule: true,
  default: {
    getThemeConfig: jest.fn(),
    saveThemeConfig: jest.fn(),
  },
}));

import apiService from '../../../utils/api.service';

const mockGetThemeConfig = apiService.getThemeConfig as jest.Mock;
const mockSaveThemeConfig = apiService.saveThemeConfig as jest.Mock;

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <ThemeConfigProvider>{children}</ThemeConfigProvider>
);

let consoleErrorSpy: jest.SpyInstance;

beforeEach(() => {
  localStorage.clear();
  jest.clearAllMocks();
  // Suppress React "not wrapped in act(...)" warnings from async fetchTheme
  consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation((...args: any[]) => {
    const msg = typeof args[0] === 'string' ? args[0] : '';
    if (msg.includes('not wrapped in act')) return;
    // eslint-disable-next-line no-console
    console.warn(...args);
  });
  // Default: API returns nothing so defaults are used
  mockGetThemeConfig.mockResolvedValue({});
  document.documentElement.removeAttribute('data-theme');
  document.documentElement.style.removeProperty('--color-primary');
  document.documentElement.style.removeProperty('--color-secondary');
  document.title = '';
});

afterEach(() => {
  consoleErrorSpy.mockRestore();
});

describe('ThemeConfigContext', () => {
  describe('useThemeConfig hook', () => {
    it('throws when used outside of ThemeConfigProvider', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      expect(() => {
        renderHook(() => useThemeConfig());
      }).toThrow('useThemeConfig must be used within ThemeConfigProvider');
      consoleSpy.mockRestore();
    });
  });

  describe('default state', () => {
    it('has default theme values when localStorage is empty and API returns nothing', async () => {
      const { result } = renderHook(() => useThemeConfig(), { wrapper });

      expect(result.current.config.colors.primary).toBe('#7b6df6');
      expect(result.current.config.colors.secondary).toBe('#10b981');
      expect(result.current.config.appName).toBe('Zerve Data AI');
      expect(result.current.mode).toBe('dark');
    });

    it('sets CSS custom properties from default config', async () => {
      renderHook(() => useThemeConfig(), { wrapper });

      await waitFor(() => {
        expect(document.documentElement.style.getPropertyValue('--color-primary')).toBe('#7b6df6');
        expect(document.documentElement.style.getPropertyValue('--color-secondary')).toBe('#10b981');
      });
    });

    it('sets data-theme attribute on document element', async () => {
      renderHook(() => useThemeConfig(), { wrapper });

      await waitFor(() => {
        expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
      });
    });

    it('sets document title from config appName', async () => {
      renderHook(() => useThemeConfig(), { wrapper });

      await waitFor(() => {
        expect(document.title).toBe('Zerve Data AI');
      });
    });
  });

  describe('localStorage restoration', () => {
    it('loads theme config from localStorage', async () => {
      const storedConfig = {
        colors: { primary: '#ff0000', secondary: '#00ff00' },
        appName: 'Stored Theme',
      };
      localStorage.setItem('themeConfig', JSON.stringify(storedConfig));

      const { result } = renderHook(() => useThemeConfig(), { wrapper });

      expect(result.current.config.colors.primary).toBe('#ff0000');
      expect(result.current.config.colors.secondary).toBe('#00ff00');
      expect(result.current.config.appName).toBe('Stored Theme');
    });

    it('loads theme mode from localStorage', async () => {
      localStorage.setItem('themeMode', 'light');

      const { result } = renderHook(() => useThemeConfig(), { wrapper });

      expect(result.current.mode).toBe('light');
    });

    it('falls back to defaults when localStorage has invalid JSON', async () => {
      localStorage.setItem('themeConfig', 'not-valid-json');

      const { result } = renderHook(() => useThemeConfig(), { wrapper });

      expect(result.current.config.colors.primary).toBe('#7b6df6');
      expect(result.current.config.appName).toBe('Zerve Data AI');
    });

    it('falls back to defaults when stored config lacks colors.primary', async () => {
      localStorage.setItem('themeConfig', JSON.stringify({ appName: 'No Colors' }));

      const { result } = renderHook(() => useThemeConfig(), { wrapper });

      expect(result.current.config.colors.primary).toBe('#7b6df6');
    });
  });

  describe('toggleMode', () => {
    it('toggles from dark to light', async () => {
      const { result } = renderHook(() => useThemeConfig(), { wrapper });

      expect(result.current.mode).toBe('dark');

      act(() => {
        result.current.toggleMode();
      });

      expect(result.current.mode).toBe('light');
      expect(localStorage.getItem('themeMode')).toBe('light');
    });

    it('toggles from light back to dark', async () => {
      localStorage.setItem('themeMode', 'light');
      const { result } = renderHook(() => useThemeConfig(), { wrapper });

      expect(result.current.mode).toBe('light');

      act(() => {
        result.current.toggleMode();
      });

      expect(result.current.mode).toBe('dark');
      expect(localStorage.getItem('themeMode')).toBe('dark');
    });

    it('updates data-theme attribute on toggle', async () => {
      const { result } = renderHook(() => useThemeConfig(), { wrapper });

      act(() => {
        result.current.toggleMode();
      });

      await waitFor(() => {
        expect(document.documentElement.getAttribute('data-theme')).toBe('light');
      });
    });
  });

  describe('setColors', () => {
    it('merges partial color updates into config', async () => {
      const { result } = renderHook(() => useThemeConfig(), { wrapper });

      act(() => {
        result.current.setColors({ primary: '#ff0000' });
      });

      expect(result.current.config.colors.primary).toBe('#ff0000');
      // Secondary should remain unchanged
      expect(result.current.config.colors.secondary).toBe('#10b981');
    });

    it('persists updated colors to localStorage', async () => {
      const { result } = renderHook(() => useThemeConfig(), { wrapper });

      act(() => {
        result.current.setColors({ primary: '#abcdef', secondary: '#fedcba' });
      });

      const stored = JSON.parse(localStorage.getItem('themeConfig')!);
      expect(stored.colors.primary).toBe('#abcdef');
      expect(stored.colors.secondary).toBe('#fedcba');
    });

    it('updates CSS custom properties after setColors', async () => {
      const { result } = renderHook(() => useThemeConfig(), { wrapper });

      act(() => {
        result.current.setColors({ primary: '#123456' });
      });

      await waitFor(() => {
        expect(document.documentElement.style.getPropertyValue('--color-primary')).toBe('#123456');
      });
    });
  });

  describe('setBranding', () => {
    it('updates appName in config', async () => {
      const { result } = renderHook(() => useThemeConfig(), { wrapper });

      act(() => {
        result.current.setBranding({ appName: 'New App Name' });
      });

      expect(result.current.config.appName).toBe('New App Name');
    });

    it('updates logo and favicon in config', async () => {
      const { result } = renderHook(() => useThemeConfig(), { wrapper });

      act(() => {
        result.current.setBranding({ logo: 'https://example.com/logo.png', favicon: 'https://example.com/favicon.ico' });
      });

      expect(result.current.config.logo).toBe('https://example.com/logo.png');
      expect(result.current.config.favicon).toBe('https://example.com/favicon.ico');
    });

    it('persists branding changes to localStorage', async () => {
      const { result } = renderHook(() => useThemeConfig(), { wrapper });

      act(() => {
        result.current.setBranding({ appName: 'Persisted Name' });
      });

      const stored = JSON.parse(localStorage.getItem('themeConfig')!);
      expect(stored.appName).toBe('Persisted Name');
    });

    it('updates document title when appName changes', async () => {
      const { result } = renderHook(() => useThemeConfig(), { wrapper });

      act(() => {
        result.current.setBranding({ appName: 'Title Test' });
      });

      await waitFor(() => {
        expect(document.title).toBe('Title Test');
      });
    });
  });

  describe('API fetch on mount', () => {
    it('normalizes flat API response to nested ThemeConfig', async () => {
      mockGetThemeConfig.mockResolvedValue({
        data: {
          primaryColor: '#aabbcc',
          secondaryColor: '#ccddee',
          appName: 'API Theme',
        },
      });

      const { result } = renderHook(() => useThemeConfig(), { wrapper });

      await waitFor(() => {
        expect(result.current.config.colors.primary).toBe('#aabbcc');
      });
      expect(result.current.config.colors.secondary).toBe('#ccddee');
      expect(result.current.config.appName).toBe('API Theme');
    });

    it('passes through already-nested API response', async () => {
      mockGetThemeConfig.mockResolvedValue({
        data: {
          colors: { primary: '#111111', secondary: '#222222' },
          appName: 'Nested Theme',
        },
      });

      const { result } = renderHook(() => useThemeConfig(), { wrapper });

      await waitFor(() => {
        expect(result.current.config.colors.primary).toBe('#111111');
      });
      expect(result.current.config.colors.secondary).toBe('#222222');
      expect(result.current.config.appName).toBe('Nested Theme');
    });

    it('preserves defaults when API call fails', async () => {
      mockGetThemeConfig.mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useThemeConfig(), { wrapper });

      // Should still have defaults after API failure
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      expect(result.current.config.colors.primary).toBe('#7b6df6');
      expect(result.current.config.appName).toBe('Zerve Data AI');
    });

    it('updates localStorage after successful API fetch', async () => {
      mockGetThemeConfig.mockResolvedValue({
        data: {
          primaryColor: '#998877',
          secondaryColor: '#776655',
          appName: 'Cached Theme',
        },
      });

      renderHook(() => useThemeConfig(), { wrapper });

      await waitFor(() => {
        const stored = JSON.parse(localStorage.getItem('themeConfig')!);
        expect(stored.colors.primary).toBe('#998877');
      });
    });
  });

  describe('saveToAPI', () => {
    it('calls apiService.saveThemeConfig with flattened config', async () => {
      mockSaveThemeConfig.mockResolvedValue({});

      const { result } = renderHook(() => useThemeConfig(), { wrapper });

      await act(async () => {
        await result.current.saveToAPI();
      });

      expect(mockSaveThemeConfig).toHaveBeenCalledWith(
        expect.objectContaining({
          primaryColor: '#7b6df6',
          secondaryColor: '#10b981',
          appName: 'Zerve Data AI',
        })
      );
    });

    it('includes optional fields in flattened config when present', async () => {
      mockSaveThemeConfig.mockResolvedValue({});

      const storedConfig = {
        colors: {
          primary: '#111111',
          secondary: '#222222',
          tertiary: '#333333',
          background: '#444444',
          paper: '#555555',
        },
        appName: 'Full Config',
        logo: 'https://example.com/logo.png',
        favicon: 'https://example.com/favicon.ico',
      };
      localStorage.setItem('themeConfig', JSON.stringify(storedConfig));

      const { result } = renderHook(() => useThemeConfig(), { wrapper });

      await act(async () => {
        await result.current.saveToAPI();
      });

      expect(mockSaveThemeConfig).toHaveBeenCalledWith({
        primaryColor: '#111111',
        secondaryColor: '#222222',
        tertiaryColor: '#333333',
        backgroundColor: '#444444',
        paperColor: '#555555',
        appName: 'Full Config',
        logoUrl: 'https://example.com/logo.png',
        faviconUrl: 'https://example.com/favicon.ico',
      });
    });
  });
});
