import React, { useState, useMemo, useEffect, useCallback } from 'react';
import {
  Container, Typography, Grid, Card, CardContent, CardActionArea, Box,
  Button, TextField, InputAdornment, Chip, Dialog, DialogTitle,
  DialogContent, DialogActions,
} from '@mui/material';
import {
  Add, Search, FolderOpen, CalendarToday,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { useNotification } from '../context_providers/NotificationContext';
import { Project, ProjectStatus } from '../../types';
import apiService from '../../utils/api.service';
import LoadingSpinner from '../shared/LoadingSpinner';

const STATUS_OPTIONS: { label: string; value: ProjectStatus | 'all' }[] = [
  { label: 'All', value: 'all' },
  { label: 'Active', value: 'active' },
  { label: 'Archived', value: 'archived' },
  { label: 'Completed', value: 'completed' },
];

const STATUS_COLORS: Record<ProjectStatus, 'success' | 'default' | 'info'> = {
  active: 'success',
  archived: 'default',
  completed: 'info',
};

interface NewProjectForm {
  name: string;
  description: string;
  projectType: string;
}

const emptyForm: NewProjectForm = {
  name: '', description: '', projectType: '',
};

const ProjectsPage: React.FC = () => {
  const { showSuccess, showError } = useNotification();

  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<ProjectStatus | 'all'>('all');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState<NewProjectForm>(emptyForm);
  const [submitting, setSubmitting] = useState(false);

  const fetchProjects = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await apiService.listProjects();
      const data = res?.data?.projects || res?.data || res?.projects || [];
      setProjects(Array.isArray(data) ? data : []);
    } catch {
      setProjects([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const filteredProjects = useMemo(() => {
    return projects.filter(p => {
      const matchesSearch = !searchQuery ||
        p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (p.description || '').toLowerCase().includes(searchQuery.toLowerCase());
      const matchesStatus = statusFilter === 'all' || p.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [projects, searchQuery, statusFilter]);

  const handleSubmit = async () => {
    if (!form.name.trim()) return;
    setSubmitting(true);
    try {
      await apiService.createProject({
        name: form.name.trim(),
        description: form.description.trim() || undefined,
        projectType: form.projectType.trim() || undefined,
      });
      showSuccess('Project created successfully');
      setForm(emptyForm);
      setDialogOpen(false);
      fetchProjects();
    } catch (err: any) {
      showError(err.message || 'Failed to create project');
    } finally {
      setSubmitting(false);
    }
  };

  if (isLoading) return <LoadingSpinner message="Loading projects..." />;

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Typography variant="h4" fontWeight={700}>Projects</Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mt: 0.5 }}>
            {projects.length} project{projects.length !== 1 ? 's' : ''} total
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<Add />} onClick={() => setDialogOpen(true)}>
          New Project
        </Button>
      </Box>

      {/* Toolbar */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap', alignItems: 'center' }}>
        <TextField
          size="small"
          placeholder="Search projects..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start"><Search fontSize="small" /></InputAdornment>
            ),
          }}
          sx={{ minWidth: 240 }}
        />
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          {STATUS_OPTIONS.map(opt => (
            <Chip
              key={opt.value}
              label={opt.label}
              variant={statusFilter === opt.value ? 'filled' : 'outlined'}
              color={statusFilter === opt.value ? 'primary' : 'default'}
              onClick={() => setStatusFilter(opt.value)}
              size="small"
            />
          ))}
        </Box>
      </Box>

      {/* Project Grid */}
      {filteredProjects.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <FolderOpen sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No projects found
          </Typography>
          <Typography variant="body2" color="text.disabled" sx={{ mb: 3 }}>
            {projects.length === 0 ? 'Create your first project to get started.' : 'Try adjusting your filters.'}
          </Typography>
          {projects.length === 0 && (
            <Button variant="contained" startIcon={<Add />} onClick={() => setDialogOpen(true)}>
              Create Project
            </Button>
          )}
        </Box>
      ) : (
        <Grid container spacing={3}>
          {filteredProjects.map(project => (
            <Grid item xs={12} sm={6} md={4} key={project.id}>
              <Card sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                border: '1px solid rgba(148, 163, 184, 0.08)',
                transition: 'all 0.2s ease',
                overflow: 'hidden',
                '&:hover': { transform: 'translateY(-2px)', boxShadow: '0 8px 32px rgba(0,0,0,0.15)' },
              }}>
                <CardActionArea
                  sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', alignItems: 'stretch' }}
                >
                  <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                    {/* Status */}
                    <Box sx={{ display: 'flex', gap: 1, mb: 1.5, alignItems: 'center' }}>
                      <Chip
                        label={project.status}
                        size="small"
                        color={STATUS_COLORS[project.status]}
                        variant="outlined"
                      />
                      {project.projectType && (
                        <Chip label={project.projectType} size="small" variant="outlined"
                          sx={{ fontSize: '0.7rem' }} />
                      )}
                    </Box>

                    {/* Name */}
                    <Typography variant="h6" fontWeight={600} sx={{ mb: 0.5, lineHeight: 1.3 }}>
                      {project.name}
                    </Typography>

                    {/* Description */}
                    {project.description && (
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                        {project.description}
                      </Typography>
                    )}

                    {/* Footer */}
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 'auto', pt: 2, borderTop: '1px solid rgba(148,163,184,0.08)' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <CalendarToday sx={{ fontSize: 14, color: 'text.disabled' }} />
                        <Typography variant="caption" color="text.disabled">
                          {format(new Date(project.createdAt), 'MMM d, yyyy')}
                        </Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </CardActionArea>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* New Project Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>New Project</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, pt: '16px !important' }}>
          <TextField
            label="Project Name"
            required
            fullWidth
            value={form.name}
            onChange={(e) => setForm(prev => ({ ...prev, name: e.target.value }))}
            autoFocus
          />
          <TextField
            label="Project Type"
            fullWidth
            value={form.projectType}
            onChange={(e) => setForm(prev => ({ ...prev, projectType: e.target.value }))}
            helperText="e.g. Competitive Intelligence, Brand Analysis"
          />
          <TextField
            label="Description"
            fullWidth
            multiline
            rows={3}
            value={form.description}
            onChange={(e) => setForm(prev => ({ ...prev, description: e.target.value }))}
          />
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={!form.name.trim() || submitting}
          >
            {submitting ? 'Creating...' : 'Create Project'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default ProjectsPage;
