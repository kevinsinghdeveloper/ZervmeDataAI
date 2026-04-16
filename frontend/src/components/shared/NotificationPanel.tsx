import React, { useState, useEffect, useCallback } from 'react';
import {
  Popover, Box, Typography, List, ListItemButton,
  ListItemText, Button, Divider, CircularProgress,
} from '@mui/material';
import {
  DoneAll as DoneAllIcon,
  Circle as CircleIcon,
} from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';
import { AppNotification } from '../../types';
import { useNotification } from '../context_providers/NotificationContext';
import apiService from '../../utils/api.service';

interface NotificationPanelProps {
  anchorEl: HTMLElement | null;
  onClose: () => void;
  onCountChange: (count: number) => void;
}

const NotificationPanel: React.FC<NotificationPanelProps> = ({ anchorEl, onClose, onCountChange }) => {
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [loading, setLoading] = useState(false);
  const { showError } = useNotification();

  const fetchNotifications = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiService.listNotifications();
      const data = res.data || res;
      const items: AppNotification[] = Array.isArray(data) ? data : (data?.notifications || data?.items || []);
      setNotifications(items);
      const unread = items.filter((n) => !n.isRead).length;
      onCountChange(unread);
    } catch {
      // Non-critical
    } finally {
      setLoading(false);
    }
  }, [onCountChange]);

  useEffect(() => {
    if (anchorEl) {
      fetchNotifications();
    }
  }, [anchorEl, fetchNotifications]);

  const handleMarkRead = async (id: string) => {
    try {
      await apiService.markNotificationRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, isRead: true } : n))
      );
      const remaining = notifications.filter((n) => !n.isRead && n.id !== id).length;
      onCountChange(remaining);
    } catch {
      showError('Failed to mark notification as read');
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await apiService.markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, isRead: true })));
      onCountChange(0);
    } catch {
      showError('Failed to mark all as read');
    }
  };

  const handleClick = (notif: AppNotification) => {
    if (!notif.isRead) {
      handleMarkRead(notif.id);
    }
    if (notif.actionUrl) {
      window.location.href = notif.actionUrl;
      onClose();
    }
  };

  const unreadCount = notifications.filter((n) => !n.isRead).length;

  return (
    <Popover
      open={Boolean(anchorEl)}
      anchorEl={anchorEl}
      onClose={onClose}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      transformOrigin={{ vertical: 'top', horizontal: 'right' }}
      slotProps={{ paper: { sx: { width: 360, maxHeight: 480, mt: 1 } } }}
    >
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', px: 2, py: 1.5 }}>
        <Typography variant="subtitle1" fontWeight={600}>Notifications</Typography>
        {unreadCount > 0 && (
          <Button size="small" startIcon={<DoneAllIcon />} onClick={handleMarkAllRead}>
            Mark all read
          </Button>
        )}
      </Box>
      <Divider />

      {/* Content */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress size={24} />
        </Box>
      ) : notifications.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="body2" color="text.secondary">No notifications</Typography>
        </Box>
      ) : (
        <List dense sx={{ overflow: 'auto', maxHeight: 380, py: 0 }}>
          {notifications.map((notif) => (
            <ListItemButton
              key={notif.id}
              onClick={() => handleClick(notif)}
              sx={{
                py: 1.5,
                px: 2,
                bgcolor: notif.isRead ? 'transparent' : 'rgba(123, 109, 246, 0.04)',
                borderLeft: notif.isRead ? 'none' : '3px solid',
                borderColor: 'primary.main',
              }}
            >
              {!notif.isRead && (
                <CircleIcon sx={{ fontSize: 8, color: 'primary.main', mr: 1.5, flexShrink: 0 }} />
              )}
              <ListItemText
                primary={
                  <Typography variant="body2" fontWeight={notif.isRead ? 400 : 600} noWrap>
                    {notif.title}
                  </Typography>
                }
                secondary={
                  <Box>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                      {notif.message}
                    </Typography>
                    <Typography variant="caption" color="text.disabled">
                      {formatDistanceToNow(new Date(notif.createdAt), { addSuffix: true })}
                    </Typography>
                  </Box>
                }
                sx={{ ml: notif.isRead ? 2.5 : 0 }}
              />
            </ListItemButton>
          ))}
        </List>
      )}
    </Popover>
  );
};

export default NotificationPanel;
