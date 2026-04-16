import React, { useState, useEffect } from 'react';
import {
  Container, Typography, Grid, Card, CardContent, Box, Chip,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Avatar,
} from '@mui/material';
import { Groups, Person } from '@mui/icons-material';
import { useNotification } from '../context_providers/NotificationContext';
import { User } from '../../types';
import apiService from '../../utils/api.service';
import LoadingSpinner from '../shared/LoadingSpinner';

const CHART_COLORS = {
  primary: '#7b6df6',
  secondary: '#10b981',
};

interface TeamMemberData {
  id: string;
  name: string;
  firstName: string;
  lastName: string;
  email: string;
  avatarUrl?: string;
  orgRole: string;
  status: string;
}

const getInitials = (firstName: string, lastName: string): string => {
  return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase();
};

const getRoleColor = (role: string): 'primary' | 'secondary' | 'default' | 'success' | 'warning' => {
  switch (role) {
    case 'owner':
      return 'warning';
    case 'admin':
      return 'secondary';
    case 'manager':
      return 'primary';
    default:
      return 'default';
  }
};

const TeamPage: React.FC = () => {
  const { showError } = useNotification();
  const [members, setMembers] = useState<TeamMemberData[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchTeamData = async () => {
      setIsLoading(true);
      try {
        const membersResp = await apiService.listOrgMembers();
        const rawMembersData = membersResp?.data || membersResp || [];
        const rawMembers: User[] = Array.isArray(rawMembersData)
          ? rawMembersData
          : (rawMembersData?.members || []);

        const activeMembers = (Array.isArray(rawMembers) ? rawMembers : [])
          .filter((m) => m.status === 'active' || m.isActive);

        const teamMembers: TeamMemberData[] = activeMembers.map((m) => ({
          id: m.id,
          name: `${m.firstName} ${m.lastName}`,
          firstName: m.firstName,
          lastName: m.lastName,
          email: m.email,
          avatarUrl: m.avatarUrl,
          orgRole: m.orgRole,
          status: m.status,
        }));

        teamMembers.sort((a, b) => a.name.localeCompare(b.name));
        setMembers(teamMembers);
      } catch (err: any) {
        showError(err.message || 'Failed to load team data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchTeamData();
  }, [showError]);

  if (isLoading) return <LoadingSpinner message="Loading team data..." />;

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700}>Team Overview</Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mt: 0.5 }}>
          Manage and view your organization's team members.
        </Typography>
      </Box>

      {/* Summary Card */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{
            background: `linear-gradient(135deg, ${CHART_COLORS.primary}20, ${CHART_COLORS.primary}08)`,
            border: '1px solid rgba(148, 163, 184, 0.08)',
            transition: 'all 0.3s ease',
            '&:hover': { transform: 'translateY(-2px)', boxShadow: '0 8px 32px rgba(0,0,0,0.15)' },
          }}>
            <CardContent sx={{ py: 3 }}>
              <Box sx={{
                width: 44, height: 44, borderRadius: '12px', bgcolor: `${CHART_COLORS.primary}25`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                mb: 2, color: CHART_COLORS.primary,
              }}>
                <Groups sx={{ fontSize: 24 }} />
              </Box>
              <Typography variant="h3" fontWeight={700} sx={{ mb: 0.5 }}>{members.length}</Typography>
              <Typography variant="body2" color="text.secondary">Total Members</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Team Members Table */}
      <Card sx={{ overflow: 'hidden' }}>
        <Box sx={{ px: 3, pt: 3, pb: 1 }}>
          <Typography variant="h6" fontWeight={600}>
            Team Members
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Active members in your organization
          </Typography>
        </Box>
        {members.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 8 }}>
            <Person sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No team members found
            </Typography>
            <Typography variant="body2" color="text.disabled">
              Invite team members to get started.
            </Typography>
          </Box>
        ) : (
          <TableContainer sx={{ mt: 1 }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Member</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell>Role</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {members.map((member) => (
                  <TableRow
                    key={member.id}
                    sx={{ '&:hover': { bgcolor: 'rgba(123, 109, 246, 0.04)' } }}
                  >
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                        <Avatar
                          src={member.avatarUrl}
                          sx={{
                            width: 36, height: 36,
                            bgcolor: CHART_COLORS.primary + '30',
                            color: CHART_COLORS.primary,
                            fontSize: 14, fontWeight: 600,
                          }}
                        >
                          {getInitials(member.firstName, member.lastName)}
                        </Avatar>
                        <Typography variant="body2" fontWeight={600}>
                          {member.name}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {member.email}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={member.orgRole}
                        size="small"
                        color={getRoleColor(member.orgRole)}
                        variant="outlined"
                        sx={{ textTransform: 'capitalize', fontSize: 12 }}
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={member.status}
                        size="small"
                        color={member.status === 'active' ? 'success' : 'default'}
                        variant="outlined"
                        sx={{ textTransform: 'capitalize', fontSize: 12 }}
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Card>
    </Container>
  );
};

export default TeamPage;
