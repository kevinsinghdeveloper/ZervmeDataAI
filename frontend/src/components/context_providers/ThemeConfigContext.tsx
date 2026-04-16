import React, { createContext, useContext, useState, useEffect } from 'react';
import { ThemeConfig } from '../../types';
import apiService from '../../utils/api.service';

const DEFAULT_THEME: ThemeConfig = {
  colors: { primary: '#7b6df6', secondary: '#10b981' },
  appName: 'Zerve Data AI',
};

interface ThemeConfigContextType {
  config: ThemeConfig;
  mode: 'dark' | 'light';
  toggleMode: () => void;
  setColors: (colors: Partial<ThemeConfig['colors']>) => void;
  setBranding: (data: Partial<ThemeConfig>) => void;
  saveToAPI: () => Promise<void>;
  isLoading: boolean;
}

const ThemeConfigContext = createContext<ThemeConfigContextType | undefined>(undefined);

export const useThemeConfig = () => {
  const context = useContext(ThemeConfigContext);
  if (!context) throw new Error('useThemeConfig must be used within ThemeConfigProvider');
  return context;
};

export const ThemeConfigProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [config, setConfig] = useState<ThemeConfig>(() => {
    try {
      const stored = localStorage.getItem('themeConfig');
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed.colors?.primary) return parsed;
      }
    } catch { /* ignore bad localStorage */ }
    return DEFAULT_THEME;
  });
  const [isLoading, setIsLoading] = useState(false);
  const [mode, setMode] = useState<'dark' | 'light'>(() => {
    try {
      const stored = localStorage.getItem('themeMode');
      if (stored === 'light' || stored === 'dark') return stored;
    } catch { /* ignore */ }
    return 'dark';
  });

  const toggleMode = () => {
    setMode((prev) => {
      const next = prev === 'dark' ? 'light' : 'dark';
      localStorage.setItem('themeMode', next);
      return next;
    });
  };

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', mode);
  }, [mode]);

  useEffect(() => {
    const normalizeTheme = (data: any): ThemeConfig => {
      if (data.colors?.primary) return data as ThemeConfig;
      return {
        colors: {
          primary: data.primaryColor || DEFAULT_THEME.colors.primary,
          secondary: data.secondaryColor || DEFAULT_THEME.colors.secondary,
          tertiary: data.tertiaryColor,
          background: data.backgroundColor,
          paper: data.paperColor,
        },
        appName: data.appName || DEFAULT_THEME.appName,
        logo: data.logoUrl || data.logo,
        favicon: data.faviconUrl || data.favicon,
      };
    };

    const fetchTheme = async () => {
      setIsLoading(true);
      try {
        const response = await apiService.getThemeConfig();
        if (response.data) {
          const theme = normalizeTheme(response.data);
          setConfig(theme);
          localStorage.setItem('themeConfig', JSON.stringify(theme));
        }
      } catch {
        // Use local/default theme
      } finally {
        setIsLoading(false);
      }
    };
    fetchTheme();
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    root.style.setProperty('--color-primary', config.colors.primary);
    root.style.setProperty('--color-secondary', config.colors.secondary);
    if (config.colors.tertiary) root.style.setProperty('--color-tertiary', config.colors.tertiary);
  }, [config.colors]);

  useEffect(() => {
    if (config.favicon) {
      let link = document.querySelector<HTMLLinkElement>("link[rel~='icon']");
      if (!link) {
        link = document.createElement('link');
        link.rel = 'icon';
        document.head.appendChild(link);
      }
      link.href = config.favicon;
    }
  }, [config.favicon]);

  useEffect(() => {
    document.title = config.appName || 'Zerve Data AI';
  }, [config.appName]);

  const setColors = (colors: Partial<ThemeConfig['colors']>) => {
    setConfig((prev) => {
      const updated = { ...prev, colors: { ...prev.colors, ...colors } };
      localStorage.setItem('themeConfig', JSON.stringify(updated));
      return updated;
    });
  };

  const setBranding = (data: Partial<ThemeConfig>) => {
    setConfig((prev) => {
      const updated = { ...prev, ...data };
      localStorage.setItem('themeConfig', JSON.stringify(updated));
      return updated;
    });
  };

  const saveToAPI = async () => {
    const flat: Record<string, string> = {
      primaryColor: config.colors.primary,
      secondaryColor: config.colors.secondary,
      appName: config.appName,
    };
    if (config.colors.tertiary) flat.tertiaryColor = config.colors.tertiary;
    if (config.colors.background) flat.backgroundColor = config.colors.background;
    if (config.colors.paper) flat.paperColor = config.colors.paper;
    if (config.logo) flat.logoUrl = config.logo;
    if (config.favicon) flat.faviconUrl = config.favicon;
    await apiService.saveThemeConfig(flat);
  };

  return (
    <ThemeConfigContext.Provider value={{ config, mode, toggleMode, setColors, setBranding, saveToAPI, isLoading }}>
      {children}
    </ThemeConfigContext.Provider>
  );
};
