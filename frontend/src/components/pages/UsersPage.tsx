import React, { useState, useEffect, useCallback } from 'react';
import {
  Container, Typography, Box, Paper, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Chip, Button, TextField, InputAdornment, TablePagination,
} from '@mui/material';
import { Search, PersonAdd } from '@mui/icons-material';
import { useNotification } from '../context_providers/NotificationContext';
import { User } from '../../types';
import apiService from '../../utils/api.service';
import LoadingSpinner from '../shared/LoadingSpinner';

const UsersPage: React.FC = () => {
  const { showInfo, showError } = useNotification();
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(20);

  const fetchUsers = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await apiService.listOrgMembers();
      const data = response.data || response;
      const memberList: User[] = Array.isArray(data) ? data : (data.members || data.users || []);
      setUsers(memberList);
    } catch (err: any) {
      showError(err.message || 'Failed to load team members');
    } finally {
      setIsLoading(false);
    }
  }, [showError]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const getRoleColor = (role: string): 'primary' | 'secondary' | 'warning' | 'default' | 'info' => {
    switch (role) {
      case 'owner': return 'primary';
      case 'admin': return 'secondary';
      case 'manager': return 'warning';
      case 'member': return 'default';
      default: return 'info';
    }
  };

  const getStatusColor = (status: string): 'success' | 'warning' | 'error' | 'default' => {
    switch (status) {
      case 'active': return 'success';
      case 'invited': return 'warning';
      case 'deactivated': return 'error';
      default: return 'default';
    }
  };

  const filteredUsers = users.filter((u) => {
    if (!search) return true;
    const term = search.toLowerCase();
    return (
      u.firstName?.toLowerCase().includes(term) ||
      u.lastName?.toLowerCase().includes(term) ||
      u.email?.toLowerCase().includes(term)
    );
  });

  const paginatedUsers = filteredUsers.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  if (isLoading && users.length === 0) return <LoadingSpinner message="Loading team members..." />;

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" fontWeight={600}>Team Members</Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mt: 0.5 }}>
            View and manage your organization's members.
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<PersonAdd />}
          onClick={() => showInfo('Invite flow coming soon. Use the organization settings to invite members.')}
        >
          Invite Member
        </Button>
      </Box>

      <Box sx={{ mb: 3 }}>
        <TextField
          placeholder="Search by name or email..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(0); }}
          size="small"
          sx={{ minWidth: 320 }}
          InputProps={{
            startAdornment: <InputAdornment position="start"><Search /></InputAdornment>,
          }}
        />
      </Box>

      <TableContainer component={Paper} variant="outlined">
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Org Role</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Joined</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedUsers.map((user) => (
              <TableRow key={user.id} hover>
                <TableCell>{user.firstName} {user.lastName}</TableCell>
                <TableCell>{user.email}</TableCell>
                <TableCell>
                  <Chip
                    label={user.orgRole || 'member'}
                    size="small"
                    color={getRoleColor(user.orgRole || 'member')}
                    variant="outlined"
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={user.status || 'active'}
                    size="small"
                    color={getStatusColor(user.status || 'active')}
                  />
                </TableCell>
                <TableCell>
                  {user.createdAt ? new Date(user.createdAt).toLocaleDateString() : '-'}
                </TableCell>
              </TableRow>
            ))}
            {paginatedUsers.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                  <Typography color="text.secondary">
                    {search ? 'No members match your search.' : 'No team members found.'}
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
        <TablePagination
          component="div"
          count={filteredUsers.length}
          page={page}
          onPageChange={(_, p) => setPage(p)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => { setRowsPerPage(parseInt(e.target.value, 10)); setPage(0); }}
        />
      </TableContainer>
    </Container>
  );
};

export default UsersPage;
