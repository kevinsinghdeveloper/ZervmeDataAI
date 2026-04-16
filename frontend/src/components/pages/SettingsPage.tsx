import React, { useState, useEffect, useCallback } from 'react';
import {
  Container, Typography, Box, Grid, Card, CardContent, CardActions, Button,
  TextField, Divider, Tabs, Tab, Switch, FormControlLabel, Paper, CircularProgress,
  Dialog, DialogTitle, DialogContent, DialogActions, Chip, IconButton,
  FormControl, InputLabel, Select, MenuItem, InputAdornment, Checkbox, Slider,
} from '@mui/material';
import {
  Save, Palette, Settings, Security, CloudUpload, Delete, SmartToy, Psychology,
  Edit as EditIcon, Add, Search, Hub, SettingsApplications,
} from '@mui/icons-material';
import { useThemeConfig } from '../context_providers/ThemeConfigContext';
import { useNotification } from '../context_providers/NotificationContext';
import { DEFAULT_BG, DEFAULT_PAPER } from '../../theme/theme';
import apiService from '../../utils/api.service';
import { AIModelConfig, AIModelProvider } from '../../types';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div role="tabpanel" hidden={value !== index}>
    {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
  </div>
);

const SettingsPage: React.FC = () => {
  const { config, setColors, setBranding } = useThemeConfig();
  const { showSuccess, showError } = useNotification();
  const [tab, setTab] = useState(0);
  const [appName, setAppName] = useState(config.appName);
  const [primaryColor, setPrimaryColor] = useState(config.colors.primary);
  const [secondaryColor, setSecondaryColor] = useState(config.colors.secondary);
  const [bgColor, setBgColor] = useState(config.colors.background || DEFAULT_BG);
  const [paperColor, setPaperColor] = useState(config.colors.paper || DEFAULT_PAPER);
  const [logoFile, setLogoFile] = useState<File | null>(null);
  const [logoPreview, setLogoPreview] = useState<string>(config.logo || '');
  const [faviconFile, setFaviconFile] = useState<File | null>(null);
  const [faviconPreview, setFaviconPreview] = useState<string>(config.favicon || '');
  const [uploading, setUploading] = useState(false);

  // General settings state
  const [generalSettings, setGeneralSettings] = useState({
    allowPublicChat: true,
    requireEmailVerification: true,
    maintenanceMode: false,
    defaultUserRole: 'viewer',
    maxUploadSizeMb: 50,
    defaultModel: 'gpt-4',
    enableAuditLogging: true,
  });

  // Chatbot settings state
  const [chatbotPrompt, setChatbotPrompt] = useState(
    'You are a helpful assistant for Zerve Direct. Help lendees with questions about the document submission process.'
  );

  // Security settings state
  const [securitySettings, setSecuritySettings] = useState({
    jwtExpiryHours: 24,
    maxLoginAttempts: 5,
    lockoutDurationMinutes: 30,
    enableRateLimiting: true,
    enableTwoFactor: false,
    corsOrigins: '*',
  });

  // AI Models state
  const [aiModels, setAiModels] = useState<AIModelConfig[]>([]);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [modelDialogOpen, setModelDialogOpen] = useState(false);
  const [editingModel, setEditingModel] = useState<AIModelConfig | null>(null);
  const [modelSaving, setModelSaving] = useState(false);
  const [modelSearch, setModelSearch] = useState('');
  const [modelProviderFilter, setModelProviderFilter] = useState<'all' | AIModelProvider>('all');
  const [modelFormData, setModelFormData] = useState({
    name: '',
    modelId: '',
    provider: 'openai' as AIModelProvider,
    apiKey: '',
    temperature: 0.7,
    maxTokens: 4096,
    isActive: true,
    isDefault: false,
  });

  const fetchAIModels = useCallback(async () => {
    setModelsLoading(true);
    try {
      const response = await apiService.listAIModels();
      const data = response.data || response;
      setAiModels(Array.isArray(data) ? data : (data?.models || []));
    } catch {
      // Use empty on error
    } finally {
      setModelsLoading(false);
    }
  }, []);

  const filteredModels = aiModels.filter((model) => {
    const matchesSearch = model.name.toLowerCase().includes(modelSearch.toLowerCase()) ||
      model.modelId.toLowerCase().includes(modelSearch.toLowerCase());
    const matchesProvider = modelProviderFilter === 'all' || model.provider === modelProviderFilter;
    return matchesSearch && matchesProvider;
  });

  const getProviderConfig = (provider: string) => {
    switch (provider) {
      case 'openai':
        return {
          icon: <SmartToy sx={{ fontSize: 28 }} />,
          gradient: 'linear-gradient(135deg, #10a37f 0%, #1a7f5a 100%)',
          glowColor: 'rgba(16, 163, 127, 0.3)',
          color: '#10a37f',
        };
      case 'anthropic':
        return {
          icon: <Psychology sx={{ fontSize: 28 }} />,
          gradient: 'linear-gradient(135deg, #d4a574 0%, #c4956a 100%)',
          glowColor: 'rgba(212, 165, 116, 0.3)',
          color: '#d4a574',
        };
      default:
        return {
          icon: <SettingsApplications sx={{ fontSize: 28 }} />,
          gradient: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
          glowColor: 'rgba(99, 102, 241, 0.3)',
          color: '#818cf8',
        };
    }
  };

  const handleOpenModelDialog = (model?: AIModelConfig) => {
    if (model) {
      setEditingModel(model);
      setModelFormData({
        name: model.name,
        modelId: model.modelId,
        provider: model.provider,
        apiKey: model.config.hasApiKey ? '••••••••' : '',
        temperature: model.config.temperature,
        maxTokens: model.config.maxTokens,
        isActive: model.isActive,
        isDefault: model.isDefault,
      });
    } else {
      setEditingModel(null);
      setModelFormData({
        name: '',
        modelId: '',
        provider: 'openai',
        apiKey: '',
        temperature: 0.7,
        maxTokens: 4096,
        isActive: true,
        isDefault: false,
      });
    }
    setModelDialogOpen(true);
  };

  const handleSaveModel = async () => {
    setModelSaving(true);
    try {
      const configObj: Record<string, any> = {
        temperature: modelFormData.temperature,
        max_tokens: modelFormData.maxTokens,
      };
      // Only send API key if it was changed (not the masked placeholder)
      if (modelFormData.apiKey && modelFormData.apiKey !== '••••••••') {
        configObj.api_key = modelFormData.apiKey;
      }
      const payload: any = {
        modelId: editingModel ? editingModel.id : modelFormData.modelId,
        name: modelFormData.name,
        provider: modelFormData.provider,
        model_name: modelFormData.modelId,
        isActive: modelFormData.isActive,
        isDefault: modelFormData.isDefault,
        config: JSON.stringify(configObj),
      };
      await apiService.updateAIModel(payload);
      showSuccess(editingModel ? `Model ${modelFormData.name} updated` : `Model ${modelFormData.name} created`);
      setModelDialogOpen(false);
      fetchAIModels();
    } catch (err: any) {
      showError(err.message || 'Failed to save model');
    } finally {
      setModelSaving(false);
    }
  };

  const handleDeleteModel = async (model: AIModelConfig) => {
    if (!window.confirm(`Are you sure you want to delete "${model.name}"? This will reset it to registry defaults or remove it entirely.`)) return;
    try {
      await apiService.deleteAIModelConfig(model.id);
      showSuccess(`Model ${model.name} deleted`);
      fetchAIModels();
    } catch (err: any) {
      showError(err.message || 'Failed to delete model');
    }
  };

  // Sync previews when config loads from API
  useEffect(() => {
    if (config.logo) setLogoPreview(config.logo);
    if (config.favicon) setFaviconPreview(config.favicon);
  }, [config.logo, config.favicon]);

  const handleLogoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setLogoFile(file);
      setLogoPreview(URL.createObjectURL(file));
    }
  };

  const handleFaviconChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFaviconFile(file);
      setFaviconPreview(URL.createObjectURL(file));
    }
  };

  const handleRemoveLogo = () => {
    setLogoFile(null);
    setLogoPreview('');
    setBranding({ logo: '' });
  };

  const handleRemoveFavicon = () => {
    setFaviconFile(null);
    setFaviconPreview('');
    setBranding({ favicon: '' });
  };

  // Fetch AI models when Chatbot or AI Models tab is selected
  useEffect(() => {
    if (tab === 3 || tab === 4) {
      fetchAIModels();
    }
  }, [tab, fetchAIModels]);

  // Fetch settings on mount
  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const response = await apiService.getSettings();
        const data = response.data || response;
        setGeneralSettings((prev) => ({
          ...prev,
          allowPublicChat: data.allowPublicChat ?? prev.allowPublicChat,
          requireEmailVerification: data.requireEmailVerification ?? prev.requireEmailVerification,
          maintenanceMode: data.maintenanceMode ?? prev.maintenanceMode,
          defaultUserRole: data.defaultUserRole ?? prev.defaultUserRole,
          maxUploadSizeMb: data.maxUploadSizeMb ?? prev.maxUploadSizeMb,
          defaultModel: data.defaultModel ?? prev.defaultModel,
          enableAuditLogging: data.enableAuditLogging ?? prev.enableAuditLogging,
        }));
        setSecuritySettings((prev) => ({
          ...prev,
          jwtExpiryHours: data.jwtExpiryHours ?? prev.jwtExpiryHours,
          maxLoginAttempts: data.maxLoginAttempts ?? prev.maxLoginAttempts,
          lockoutDurationMinutes: data.lockoutDurationMinutes ?? prev.lockoutDurationMinutes,
          enableRateLimiting: data.enableRateLimiting ?? prev.enableRateLimiting,
          enableTwoFactor: data.enableTwoFactor ?? prev.enableTwoFactor,
          corsOrigins: data.corsOrigins ?? prev.corsOrigins,
        }));
        if (data.chatbotSystemPrompt) setChatbotPrompt(data.chatbotSystemPrompt);
      } catch {
        // Use defaults on error
      }
    };
    fetchSettings();
  }, []);

  const handleSaveTheme = async () => {
    try {
      setUploading(true);

      let logoUrl = logoPreview;
      let faviconUrl = faviconPreview;

      // TODO: Implement asset upload via S3 presigned URL when backend endpoint is ready
      if (logoFile) {
        // For now, use the local preview URL; actual upload TBD
        setLogoFile(null);
      }

      if (faviconFile) {
        // For now, use the local preview URL; actual upload TBD
        setFaviconFile(null);
      }

      // Update context state
      setColors({ primary: primaryColor, secondary: secondaryColor, background: bgColor, paper: paperColor });
      setBranding({ appName, logo: logoUrl || undefined, favicon: faviconUrl || undefined });

      // Send flat payload directly to avoid stale closure issue
      const flat: Record<string, string> = {
        primaryColor,
        secondaryColor,
        backgroundColor: bgColor,
        paperColor,
        appName,
      };
      if (logoUrl) flat.logoUrl = logoUrl;
      if (faviconUrl) flat.faviconUrl = faviconUrl;
      await apiService.saveThemeConfig(flat);

      showSuccess('Theme settings saved successfully');
    } catch (err: any) {
      showError(err.message || 'Failed to save theme settings');
    } finally {
      setUploading(false);
    }
  };

  const handleSaveGeneral = async () => {
    try {
      await apiService.saveSettings(generalSettings);
      showSuccess('General settings saved successfully');
    } catch (err: any) {
      showError(err.message || 'Failed to save general settings');
    }
  };

  const handleSaveSecurity = async () => {
    try {
      await apiService.saveSettings(securitySettings);
      showSuccess('Security settings saved successfully');
    } catch (err: any) {
      showError(err.message || 'Failed to save security settings');
    }
  };

  const handleSaveChatbot = async () => {
    if (!generalSettings.defaultModel) {
      showError('Please select a default model before saving.');
      return;
    }
    const selectedModel = aiModels.find((m) => m.id === generalSettings.defaultModel);
    if (!selectedModel) {
      showError('Selected model not found. Please choose a valid model.');
      return;
    }
    if (!selectedModel.isActive) {
      showError(`"${selectedModel.name}" is inactive. Please activate it in the AI Models tab or choose a different model.`);
      return;
    }
    if (!selectedModel.config.hasApiKey) {
      showError(`"${selectedModel.name}" has no API key configured. Add one in the AI Models tab before setting it as default.`);
      return;
    }
    try {
      await apiService.saveSettings({ chatbotSystemPrompt: chatbotPrompt, defaultModel: generalSettings.defaultModel });
      showSuccess('Chatbot settings saved successfully');
    } catch (err: any) {
      showError(err.message || 'Failed to save chatbot settings');
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={600}>Settings</Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mt: 0.5 }}>
          Manage application configuration, theme, and security settings.
        </Typography>
      </Box>

      <Paper variant="outlined">
        <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ borderBottom: 1, borderColor: 'divider', px: 2 }}>
          <Tab icon={<Palette />} label="Theme" iconPosition="start" />
          <Tab icon={<Settings />} label="General" iconPosition="start" />
          <Tab icon={<Security />} label="Security" iconPosition="start" />
          <Tab icon={<SmartToy />} label="Chatbot" iconPosition="start" />
          <Tab icon={<Psychology />} label="AI Models" iconPosition="start" />
        </Tabs>

        {/* Theme Tab */}
        <TabPanel value={tab} index={0}>
          <Box sx={{ px: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Branding</Typography>
                    <Divider sx={{ mb: 2 }} />
                    <TextField
                      label="Application Name"
                      fullWidth
                      value={appName}
                      onChange={(e) => setAppName(e.target.value)}
                      sx={{ mb: 3 }}
                    />

                    {/* Logo Upload */}
                    <Typography variant="subtitle2" sx={{ mb: 1 }}>Logo</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                      <Box
                        sx={{
                          width: 64, height: 64, border: '1px dashed', borderColor: 'divider',
                          borderRadius: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
                          overflow: 'hidden', bgcolor: 'background.default',
                        }}
                      >
                        {logoPreview ? (
                          <img src={logoPreview} alt="Logo" style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }} onError={() => { setLogoPreview(''); setBranding({ logo: '' }); }} />
                        ) : (
                          <Typography variant="caption" color="text.secondary">No logo</Typography>
                        )}
                      </Box>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                        <Button component="label" size="small" variant="outlined" startIcon={<CloudUpload />}>
                          Upload Logo
                          <input type="file" hidden accept="image/*" onChange={handleLogoChange} />
                        </Button>
                        {logoPreview && (
                          <Button size="small" color="error" startIcon={<Delete />} onClick={handleRemoveLogo}>
                            Remove
                          </Button>
                        )}
                      </Box>
                    </Box>

                    {/* Favicon Upload */}
                    <Typography variant="subtitle2" sx={{ mb: 1 }}>Favicon</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Box
                        sx={{
                          width: 32, height: 32, border: '1px dashed', borderColor: 'divider',
                          borderRadius: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
                          overflow: 'hidden', bgcolor: 'background.default',
                        }}
                      >
                        {faviconPreview ? (
                          <img src={faviconPreview} alt="Favicon" style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }} onError={() => { setFaviconPreview(''); setBranding({ favicon: '' }); }} />
                        ) : (
                          <Typography variant="caption" color="text.secondary" fontSize={8}>ico</Typography>
                        )}
                      </Box>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                        <Button component="label" size="small" variant="outlined" startIcon={<CloudUpload />}>
                          Upload Favicon
                          <input type="file" hidden accept="image/*,.ico" onChange={handleFaviconChange} />
                        </Button>
                        {faviconPreview && (
                          <Button size="small" color="error" startIcon={<Delete />} onClick={handleRemoveFavicon}>
                            Remove
                          </Button>
                        )}
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Colors</Typography>
                    <Divider sx={{ mb: 2 }} />
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <input type="color" value={primaryColor} onChange={(e) => setPrimaryColor(e.target.value)} style={{ width: 48, height: 48, border: 'none', cursor: 'pointer' }} />
                        <TextField label="Primary Color" value={primaryColor} onChange={(e) => setPrimaryColor(e.target.value)} size="small" fullWidth />
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <input type="color" value={secondaryColor} onChange={(e) => setSecondaryColor(e.target.value)} style={{ width: 48, height: 48, border: 'none', cursor: 'pointer' }} />
                        <TextField label="Secondary Color" value={secondaryColor} onChange={(e) => setSecondaryColor(e.target.value)} size="small" fullWidth />
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <input type="color" value={bgColor} onChange={(e) => setBgColor(e.target.value)} style={{ width: 48, height: 48, border: 'none', cursor: 'pointer' }} />
                        <TextField label="Background Color" value={bgColor} onChange={(e) => setBgColor(e.target.value)} size="small" fullWidth />
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <input type="color" value={paperColor} onChange={(e) => setPaperColor(e.target.value)} style={{ width: 48, height: 48, border: 'none', cursor: 'pointer' }} />
                        <TextField label="Panel Color" value={paperColor} onChange={(e) => setPaperColor(e.target.value)} size="small" fullWidth />
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="contained"
                startIcon={uploading ? <CircularProgress size={18} color="inherit" /> : <Save />}
                onClick={handleSaveTheme}
                disabled={uploading}
              >
                {uploading ? 'Saving...' : 'Save Theme Settings'}
              </Button>
            </Box>
          </Box>
        </TabPanel>

        {/* General Tab */}
        <TabPanel value={tab} index={1}>
          <Box sx={{ px: 3 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>General Settings</Typography>
                <Divider sx={{ mb: 2 }} />
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <FormControlLabel
                    control={<Switch checked={generalSettings.allowPublicChat} onChange={(e) => setGeneralSettings((p) => ({ ...p, allowPublicChat: e.target.checked }))} />}
                    label="Enable public chat"
                  />
                  <FormControlLabel
                    control={<Switch checked={generalSettings.requireEmailVerification} onChange={(e) => setGeneralSettings((p) => ({ ...p, requireEmailVerification: e.target.checked }))} />}
                    label="Require email verification"
                  />
                  <FormControlLabel
                    control={<Switch checked={generalSettings.maintenanceMode} onChange={(e) => setGeneralSettings((p) => ({ ...p, maintenanceMode: e.target.checked }))} />}
                    label="Enable maintenance mode"
                  />
                  <FormControlLabel
                    control={<Switch checked={generalSettings.enableAuditLogging} onChange={(e) => setGeneralSettings((p) => ({ ...p, enableAuditLogging: e.target.checked }))} />}
                    label="Enable audit logging"
                  />
                  <TextField
                    label="Default user role"
                    value={generalSettings.defaultUserRole}
                    onChange={(e) => setGeneralSettings((p) => ({ ...p, defaultUserRole: e.target.value }))}
                    fullWidth
                    size="small"
                  />
                  <TextField
                    label="Max upload size (MB)"
                    value={generalSettings.maxUploadSizeMb}
                    onChange={(e) => setGeneralSettings((p) => ({ ...p, maxUploadSizeMb: parseInt(e.target.value, 10) || 0 }))}
                    fullWidth
                    size="small"
                    type="number"
                  />
                  <Typography variant="caption" color="text.secondary">
                    Default AI model is configured in the Chatbot tab.
                  </Typography>
                </Box>
              </CardContent>
              <CardActions sx={{ justifyContent: 'flex-end', p: 2 }}>
                <Button variant="contained" startIcon={<Save />} onClick={handleSaveGeneral}>Save General Settings</Button>
              </CardActions>
            </Card>
          </Box>
        </TabPanel>

        {/* Security Tab */}
        <TabPanel value={tab} index={2}>
          <Box sx={{ px: 3 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Security Settings</Typography>
                <Divider sx={{ mb: 2 }} />
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <TextField
                    label="JWT Token Expiry (hours)"
                    value={securitySettings.jwtExpiryHours}
                    onChange={(e) => setSecuritySettings((p) => ({ ...p, jwtExpiryHours: parseInt(e.target.value, 10) || 0 }))}
                    fullWidth
                    size="small"
                    type="number"
                  />
                  <TextField
                    label="Max login attempts"
                    value={securitySettings.maxLoginAttempts}
                    onChange={(e) => setSecuritySettings((p) => ({ ...p, maxLoginAttempts: parseInt(e.target.value, 10) || 0 }))}
                    fullWidth
                    size="small"
                    type="number"
                  />
                  <TextField
                    label="Account lockout duration (minutes)"
                    value={securitySettings.lockoutDurationMinutes}
                    onChange={(e) => setSecuritySettings((p) => ({ ...p, lockoutDurationMinutes: parseInt(e.target.value, 10) || 0 }))}
                    fullWidth
                    size="small"
                    type="number"
                  />
                  <FormControlLabel
                    control={<Switch checked={securitySettings.enableRateLimiting} onChange={(e) => setSecuritySettings((p) => ({ ...p, enableRateLimiting: e.target.checked }))} />}
                    label="Enable rate limiting"
                  />
                  <FormControlLabel
                    control={<Switch checked={securitySettings.enableTwoFactor} onChange={(e) => setSecuritySettings((p) => ({ ...p, enableTwoFactor: e.target.checked }))} />}
                    label="Enable two-factor authentication"
                  />
                  <TextField
                    label="Allowed CORS origins"
                    value={securitySettings.corsOrigins}
                    onChange={(e) => setSecuritySettings((p) => ({ ...p, corsOrigins: e.target.value }))}
                    fullWidth
                    size="small"
                    helperText="Comma-separated list of allowed origins"
                  />
                </Box>
              </CardContent>
              <CardActions sx={{ justifyContent: 'flex-end', p: 2 }}>
                <Button variant="contained" startIcon={<Save />} onClick={handleSaveSecurity}>Save Security Settings</Button>
              </CardActions>
            </Card>
          </Box>
        </TabPanel>

        {/* Chatbot Tab */}
        <TabPanel value={tab} index={3}>
          <Box sx={{ px: 3 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Chatbot Configuration</Typography>
                <Divider sx={{ mb: 2 }} />
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Configure the AI chatbot behavior — select the default model and customize the system prompt.
                </Typography>
                <FormControl fullWidth sx={{ mb: 3 }}>
                  <InputLabel>Default Model</InputLabel>
                  <Select
                    value={generalSettings.defaultModel}
                    label="Default Model"
                    onChange={(e) => setGeneralSettings((p) => ({ ...p, defaultModel: e.target.value }))}
                  >
                    {aiModels.filter((m) => m.isActive).map((model) => (
                      <MenuItem key={model.id} value={model.id}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {model.name}
                          <Chip label={model.provider} size="small" variant="outlined" sx={{ textTransform: 'capitalize', height: 20, fontSize: '0.7rem' }} />
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <TextField
                  label="System Prompt"
                  multiline
                  rows={6}
                  fullWidth
                  value={chatbotPrompt}
                  onChange={(e) => setChatbotPrompt(e.target.value)}
                  placeholder="Enter the system prompt for the chatbot..."
                  helperText="This prompt guides how the chatbot responds to user questions."
                />
              </CardContent>
              <CardActions sx={{ justifyContent: 'flex-end', p: 2 }}>
                <Button variant="contained" startIcon={<Save />} onClick={handleSaveChatbot}>Save Chatbot Settings</Button>
              </CardActions>
            </Card>
          </Box>
        </TabPanel>
        {/* AI Models Tab */}
        <TabPanel value={tab} index={4}>
          <Box sx={{ px: 3 }}>
            {/* Header with Add Model button */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
              <Box>
                <Typography variant="h6" gutterBottom>AI Model Configuration</Typography>
                <Typography variant="body2" color="text.secondary">
                  Configure and manage AI model connections for the chat assistant.
                </Typography>
              </Box>
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={() => handleOpenModelDialog()}
                sx={{ borderRadius: '10px', px: 3 }}
              >
                Add Model
              </Button>
            </Box>

            {/* Search and Filters */}
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 3, alignItems: 'center' }}>
              <TextField
                placeholder="Search models..."
                value={modelSearch}
                onChange={(e) => setModelSearch(e.target.value)}
                size="small"
                sx={{ minWidth: 250 }}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Search fontSize="small" color="action" />
                    </InputAdornment>
                  ),
                }}
              />
              <FormControl size="small" sx={{ minWidth: 150 }}>
                <InputLabel>Provider</InputLabel>
                <Select
                  value={modelProviderFilter}
                  label="Provider"
                  onChange={(e) => setModelProviderFilter(e.target.value as any)}
                >
                  <MenuItem value="all">All Providers</MenuItem>
                  <MenuItem value="openai">OpenAI</MenuItem>
                  <MenuItem value="anthropic">Anthropic</MenuItem>
                  <MenuItem value="custom">Custom</MenuItem>
                </Select>
              </FormControl>
              <Chip
                label={`${filteredModels.length} model${filteredModels.length !== 1 ? 's' : ''}`}
                size="small"
                color="primary"
                variant="outlined"
              />
            </Box>

            {/* Models Grid or Loading/Empty */}
            {modelsLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
                <CircularProgress />
              </Box>
            ) : filteredModels.length === 0 ? (
              <Card variant="outlined" sx={{ borderRadius: '16px' }}>
                <CardContent sx={{ textAlign: 'center', py: 8 }}>
                  <Hub sx={{ fontSize: 56, color: 'text.disabled', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary" gutterBottom>
                    {modelSearch || modelProviderFilter !== 'all' ? 'No models match your filters' : 'No models configured yet'}
                  </Typography>
                  <Typography variant="body2" color="text.disabled" sx={{ mb: 3 }}>
                    Create your first model configuration to get started
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<Add />}
                    onClick={() => handleOpenModelDialog()}
                    sx={{ borderRadius: '10px' }}
                  >
                    Add Your First Model
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <Grid container spacing={2.5}>
                {filteredModels.map((model) => {
                  const pConfig = getProviderConfig(model.provider);
                  return (
                    <Grid item xs={12} md={6} lg={4} key={model.id}>
                      <Card
                        variant="outlined"
                        sx={{
                          height: '100%',
                          borderRadius: '16px',
                          transition: 'all 0.2s ease',
                          opacity: model.isActive ? 1 : 0.65,
                          '&:hover': {
                            transform: 'translateY(-2px)',
                            borderColor: 'primary.main',
                            boxShadow: '0 8px 24px rgba(0,0,0,0.2)',
                          },
                        }}
                      >
                        <CardContent sx={{ p: 2.5 }}>
                          {/* Provider icon + edit/delete */}
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                            <Box
                              sx={{
                                width: 48,
                                height: 48,
                                borderRadius: '12px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                background: pConfig.gradient,
                                boxShadow: `0 6px 16px ${pConfig.glowColor}`,
                                color: 'white',
                              }}
                            >
                              {pConfig.icon}
                            </Box>
                            <Box sx={{ display: 'flex', gap: 0.5 }}>
                              <IconButton
                                size="small"
                                onClick={() => handleOpenModelDialog(model)}
                                sx={{ '&:hover': { color: 'primary.main' } }}
                              >
                                <EditIcon fontSize="small" />
                              </IconButton>
                              <IconButton
                                size="small"
                                onClick={() => handleDeleteModel(model)}
                                sx={{ '&:hover': { color: 'error.main' } }}
                              >
                                <Delete fontSize="small" />
                              </IconButton>
                            </Box>
                          </Box>

                          {/* Name + model ID */}
                          <Typography variant="subtitle1" fontWeight={600} sx={{ mb: 0.5 }}>
                            {model.name}
                          </Typography>
                          <Typography variant="caption" sx={{ fontFamily: 'monospace', color: 'text.secondary', display: 'block', mb: 1.5 }}>
                            {model.modelId}
                          </Typography>

                          {/* Chips */}
                          <Box sx={{ display: 'flex', gap: 0.75, flexWrap: 'wrap', mb: 2 }}>
                            <Chip
                              label={model.provider}
                              size="small"
                              sx={{
                                background: `${pConfig.color}20`,
                                color: pConfig.color,
                                fontWeight: 500,
                                textTransform: 'capitalize',
                              }}
                            />
                            <Chip
                              label={model.isActive ? 'Active' : 'Inactive'}
                              size="small"
                              sx={{
                                background: model.isActive ? 'rgba(34, 197, 94, 0.15)' : 'rgba(107, 114, 128, 0.15)',
                                color: model.isActive ? '#4ade80' : '#9ca3af',
                                fontWeight: 500,
                              }}
                            />
                            {model.isDefault && (
                              <Chip label="Default" size="small" color="success" />
                            )}
                            {!model.config.hasApiKey && (
                              <Chip label="No API Key" size="small" color="warning" variant="outlined" />
                            )}
                          </Box>

                          {/* Stats panel */}
                          <Box sx={{ p: 1.5, borderRadius: '10px', bgcolor: 'action.hover' }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                              <Typography variant="caption" color="text.secondary">Temperature</Typography>
                              <Typography variant="caption" fontWeight={600}>{model.config.temperature}</Typography>
                            </Box>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                              <Typography variant="caption" color="text.secondary">Max Tokens</Typography>
                              <Typography variant="caption" fontWeight={600}>{model.config.maxTokens.toLocaleString()}</Typography>
                            </Box>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                              <Typography variant="caption" color="text.secondary">Context Window</Typography>
                              <Typography variant="caption" fontWeight={600}>{(model.maxContext / 1000).toFixed(0)}k</Typography>
                            </Box>
                          </Box>
                        </CardContent>
                      </Card>
                    </Grid>
                  );
                })}
              </Grid>
            )}
          </Box>
        </TabPanel>

        {/* AI Model Create/Edit Dialog */}
        <Dialog open={modelDialogOpen} onClose={() => setModelDialogOpen(false)} maxWidth="md" fullWidth>
          <DialogTitle>
            {editingModel ? 'Edit Model Configuration' : 'Create New Model'}
          </DialogTitle>
          <DialogContent>
            <Box sx={{ pt: 1, display: 'flex', flexDirection: 'column', gap: 2.5 }}>
              <TextField
                label="Model Name"
                fullWidth
                required
                value={modelFormData.name}
                onChange={(e) => setModelFormData({ ...modelFormData, name: e.target.value })}
                placeholder="e.g. GPT-4 Production"
              />
              <TextField
                label="Model ID"
                fullWidth
                required
                value={modelFormData.modelId}
                onChange={(e) => setModelFormData({ ...modelFormData, modelId: e.target.value })}
                placeholder="e.g. gpt-4o, claude-sonnet-4-5-20250929"
                helperText="The specific model identifier from the provider"
              />
              <FormControl fullWidth required>
                <InputLabel>Provider</InputLabel>
                <Select
                  value={modelFormData.provider}
                  label="Provider"
                  onChange={(e) => setModelFormData({ ...modelFormData, provider: e.target.value as AIModelProvider })}
                >
                  <MenuItem value="openai">OpenAI</MenuItem>
                  <MenuItem value="anthropic">Anthropic</MenuItem>
                  <MenuItem value="custom">Custom</MenuItem>
                </Select>
              </FormControl>
              <TextField
                label="API Key"
                fullWidth
                type="password"
                value={modelFormData.apiKey}
                onChange={(e) => setModelFormData({ ...modelFormData, apiKey: e.target.value })}
                placeholder={modelFormData.provider === 'openai' ? 'sk-...' : 'sk-ant-...'}
                helperText={editingModel?.config.hasApiKey ? 'Leave as-is to keep existing key, or enter a new one' : 'Required to activate this model'}
              />
              <Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Temperature: {modelFormData.temperature}
                </Typography>
                <Slider
                  value={modelFormData.temperature}
                  onChange={(_, v) => setModelFormData({ ...modelFormData, temperature: v as number })}
                  min={0}
                  max={2}
                  step={0.1}
                  marks={[{ value: 0, label: '0' }, { value: 0.7, label: '0.7' }, { value: 2, label: '2' }]}
                  valueLabelDisplay="auto"
                  sx={{ mx: 1 }}
                />
              </Box>
              <TextField
                label="Max Tokens"
                fullWidth
                type="number"
                value={modelFormData.maxTokens}
                onChange={(e) => setModelFormData({ ...modelFormData, maxTokens: parseInt(e.target.value) || 4096 })}
                helperText="Maximum response length in tokens"
              />
              <Box sx={{ display: 'flex', gap: 3 }}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={modelFormData.isActive}
                      onChange={(e) => setModelFormData({ ...modelFormData, isActive: e.target.checked })}
                    />
                  }
                  label="Active (available in chat)"
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={modelFormData.isDefault}
                      onChange={(e) => setModelFormData({ ...modelFormData, isDefault: e.target.checked })}
                    />
                  }
                  label="Set as default model"
                />
              </Box>
            </Box>
          </DialogContent>
          <DialogActions sx={{ p: 2 }}>
            <Button onClick={() => setModelDialogOpen(false)}>Cancel</Button>
            <Button
              variant="contained"
              onClick={handleSaveModel}
              disabled={modelSaving || !modelFormData.name || !modelFormData.modelId}
              startIcon={modelSaving ? <CircularProgress size={18} color="inherit" /> : <Save />}
            >
              {modelSaving ? 'Saving...' : (editingModel ? 'Update' : 'Create')}
            </Button>
          </DialogActions>
        </Dialog>
      </Paper>
    </Container>
  );
};

export default SettingsPage;
