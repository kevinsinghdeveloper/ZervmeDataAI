import React, { useState, useEffect, useCallback } from 'react';
import {
  Container, Typography, Grid, Card, CardContent, Box,
  Button, TextField, InputAdornment, Chip, Dialog, DialogTitle,
  DialogContent, DialogActions, IconButton,
} from '@mui/material';
import {
  Add, Search, Hub, Edit as EditIcon, Delete, SmartToy,
} from '@mui/icons-material';
import { useNotification } from '../context_providers/NotificationContext';
import { ModelConfig } from '../../types';
import apiService from '../../utils/api.service';
import LoadingSpinner from '../shared/LoadingSpinner';

const ModelsPage: React.FC = () => {
  const { showSuccess, showError } = useNotification();
  const [models, setModels] = useState<ModelConfig[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingModel, setEditingModel] = useState<ModelConfig | null>(null);
  const [form, setForm] = useState({ name: '', modelTypeId: '', modelConfig: '{}' });
  const [submitting, setSubmitting] = useState(false);

  const fetchModels = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await apiService.listModelConfigs();
      const data = res?.data?.model_configs || res?.data || res?.model_configs || [];
      setModels(Array.isArray(data) ? data : []);
    } catch { setModels([]); }
    finally { setIsLoading(false); }
  }, []);

  useEffect(() => { fetchModels(); }, [fetchModels]);

  const filteredModels = models.filter(m =>
    !searchQuery || m.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleOpenDialog = (model?: ModelConfig) => {
    if (model) {
      setEditingModel(model);
      setForm({ name: model.name, modelTypeId: model.modelTypeId || '', modelConfig: model.modelConfig || '{}' });
    } else {
      setEditingModel(null);
      setForm({ name: '', modelTypeId: '', modelConfig: '{}' });
    }
    setDialogOpen(true);
  };

  const handleSubmit = async () => {
    if (!form.name.trim()) return;
    setSubmitting(true);
    try {
      if (editingModel) {
        await apiService.updateModelConfig(editingModel.id, form);
        showSuccess('Model updated');
      } else {
        await apiService.createModelConfig(form);
        showSuccess('Model created');
      }
      setDialogOpen(false);
      fetchModels();
    } catch (err: any) { showError(err.message || 'Failed to save model'); }
    finally { setSubmitting(false); }
  };

  const handleDelete = async (model: ModelConfig) => {
    try {
      await apiService.deleteModelConfig(model.id);
      showSuccess('Model deleted');
      fetchModels();
    } catch (err: any) { showError(err.message || 'Failed to delete'); }
  };

  if (isLoading) return <LoadingSpinner message="Loading models..." />;

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Typography variant="h4" fontWeight={700}>AI Models</Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mt: 0.5 }}>
            {models.length} model configuration{models.length !== 1 ? 's' : ''}
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<Add />} onClick={() => handleOpenDialog()}>New Model</Button>
      </Box>

      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <TextField
          size="small" placeholder="Search models..." value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{ startAdornment: <InputAdornment position="start"><Search fontSize="small" /></InputAdornment> }}
          sx={{ minWidth: 240 }}
        />
        <Chip label={`${filteredModels.length} model${filteredModels.length !== 1 ? 's' : ''}`} size="small" color="primary" variant="outlined" />
      </Box>

      {filteredModels.length === 0 ? (
        <Card variant="outlined" sx={{ borderRadius: 3 }}>
          <CardContent sx={{ textAlign: 'center', py: 8 }}>
            <Hub sx={{ fontSize: 56, color: 'text.disabled', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>No models configured</Typography>
            <Typography variant="body2" color="text.disabled" sx={{ mb: 3 }}>Create your first model to get started</Typography>
            <Button variant="contained" startIcon={<Add />} onClick={() => handleOpenDialog()}>Add Your First Model</Button>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={2.5}>
          {filteredModels.map(model => (
            <Grid item xs={12} md={6} lg={4} key={model.id}>
              <Card variant="outlined" sx={{
                height: '100%', borderRadius: 3, transition: 'all 0.2s',
                opacity: model.status === 'active' ? 1 : 0.65,
                '&:hover': { transform: 'translateY(-2px)', borderColor: 'primary.main', boxShadow: '0 8px 24px rgba(0,0,0,0.2)' },
              }}>
                <CardContent sx={{ p: 2.5 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box sx={{ width: 48, height: 48, borderRadius: 2, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'primary.main', color: 'white' }}>
                      <SmartToy />
                    </Box>
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      <IconButton size="small" onClick={() => handleOpenDialog(model)} sx={{ '&:hover': { color: 'primary.main' } }}>
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton size="small" onClick={() => handleDelete(model)} sx={{ '&:hover': { color: 'error.main' } }}>
                        <Delete fontSize="small" />
                      </IconButton>
                    </Box>
                  </Box>
                  <Typography variant="subtitle1" fontWeight={600} sx={{ mb: 0.5 }}>{model.name}</Typography>
                  {model.modelTypeId && (
                    <Typography variant="caption" sx={{ fontFamily: 'monospace', color: 'text.secondary', display: 'block', mb: 1.5 }}>{model.modelTypeId}</Typography>
                  )}
                  <Box sx={{ display: 'flex', gap: 0.75, flexWrap: 'wrap' }}>
                    <Chip label={model.status} size="small" color={model.status === 'active' ? 'success' : 'default'} />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingModel ? 'Edit Model' : 'New Model'}</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, pt: '16px !important' }}>
          <TextField label="Name" required fullWidth value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} autoFocus />
          <TextField label="Model Type ID" fullWidth value={form.modelTypeId} onChange={(e) => setForm({ ...form, modelTypeId: e.target.value })} helperText="e.g. openai, anthropic" />
          <TextField label="Configuration (JSON)" fullWidth multiline rows={4} value={form.modelConfig} onChange={(e) => setForm({ ...form, modelConfig: e.target.value })} />
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSubmit} disabled={!form.name.trim() || submitting}>
            {submitting ? 'Saving...' : (editingModel ? 'Update' : 'Create')}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default ModelsPage;
