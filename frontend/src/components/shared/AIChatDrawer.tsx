import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Drawer, Box, Typography, IconButton, TextField, Chip, Paper,
  List, ListItemButton, ListItemText, ListItemSecondaryAction,
  Collapse, CircularProgress, Tooltip, useTheme, useMediaQuery, Divider,
} from '@mui/material';
import {
  Close as CloseIcon,
  Add as AddIcon,
  Send as SendIcon,
  ExpandLess,
  ExpandMore,
  Delete as DeleteIcon,
  Chat as ChatIcon,
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip as RechartsTooltip,
  PieChart, Pie, Cell, Legend,
} from 'recharts';
import { AIChatSession, AIChatMessage } from '../../types';
import { useNotification } from '../context_providers/NotificationContext';
import apiService from '../../utils/api.service';

const DRAWER_WIDTH = 400;

const CHART_COLORS = ['#7b6df6', '#10b981', '#f59e0b', '#ef4444', '#3b82f6', '#8b5cf6'];

const SUGGESTION_CHIPS = [
  'Hours this week',
  'Budget status',
  'Suggest entry',
  'Team utilization',
];

interface AIChatDrawerProps {
  open: boolean;
  onClose: () => void;
}

const ChartInChat: React.FC<{ config: Record<string, any> }> = ({ config }) => {
  if (!config || !config.data || !Array.isArray(config.data)) return null;

  if (config.type === 'bar') {
    return (
      <Box sx={{ mt: 1, mb: 1 }}>
        {config.title && (
          <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
            {config.title}
          </Typography>
        )}
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={config.data}>
            <XAxis dataKey="name" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <RechartsTooltip />
            <Bar dataKey="value" fill="#7b6df6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Box>
    );
  }

  if (config.type === 'pie') {
    return (
      <Box sx={{ mt: 1, mb: 1 }}>
        {config.title && (
          <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
            {config.title}
          </Typography>
        )}
        <ResponsiveContainer width="100%" height={200}>
          <PieChart>
            <Pie
              data={config.data}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={70}
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
            >
              {config.data.map((_: any, index: number) => (
                <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
              ))}
            </Pie>
            <Legend />
            <RechartsTooltip />
          </PieChart>
        </ResponsiveContainer>
      </Box>
    );
  }

  return null;
};

const AIChatDrawer: React.FC<AIChatDrawerProps> = ({ open, onClose }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const { showError } = useNotification();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const [sessions, setSessions] = useState<AIChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<AIChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionsOpen, setSessionsOpen] = useState(false);
  const [sessionsLoading, setSessionsLoading] = useState(false);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const fetchSessions = useCallback(async () => {
    setSessionsLoading(true);
    try {
      const res = await apiService.listChatSessions();
      const data = res.data || res;
      setSessions(Array.isArray(data) ? data : (data?.sessions || data?.items || []));
    } catch {
      // Silently fail - sessions list is not critical
    } finally {
      setSessionsLoading(false);
    }
  }, []);

  const fetchMessages = useCallback(async (sessionId: string) => {
    try {
      const res = await apiService.listChatMessages(sessionId);
      const data = res.data || res;
      setMessages(Array.isArray(data) ? data : (data?.messages || data?.items || []));
    } catch {
      showError('Failed to load chat messages');
    }
  }, [showError]);

  useEffect(() => {
    if (open) {
      fetchSessions();
    }
  }, [open, fetchSessions]);

  useEffect(() => {
    if (activeSessionId) {
      fetchMessages(activeSessionId);
    }
  }, [activeSessionId, fetchMessages]);

  const handleSelectSession = (sessionId: string) => {
    setActiveSessionId(sessionId);
    setMessages([]);
    setSessionsOpen(false);
  };

  const handleNewChat = async () => {
    try {
      const res = await apiService.createChatSession('New Chat');
      const session = res.data || res;
      setSessions((prev) => [session, ...prev]);
      setActiveSessionId(session.id);
      setMessages([]);
      setSessionsOpen(false);
    } catch {
      showError('Failed to create chat session');
    }
  };

  const handleDeleteSession = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    try {
      await apiService.deleteChatSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      if (activeSessionId === sessionId) {
        setActiveSessionId(null);
        setMessages([]);
      }
    } catch {
      showError('Failed to delete chat session');
    }
  };

  const sendMessage = async (content: string) => {
    if (!content.trim() || isLoading) return;

    let sessionId = activeSessionId;

    // Auto-create session if none selected
    if (!sessionId) {
      try {
        const res = await apiService.createChatSession(content.slice(0, 50));
        const session = res.data || res;
        sessionId = session.id;
        setSessions((prev) => [session, ...prev]);
        setActiveSessionId(sessionId);
      } catch {
        showError('Failed to create chat session');
        return;
      }
    }

    // Append user message optimistically
    const userMessage: AIChatMessage = {
      sessionId: sessionId!,
      id: `temp-${Date.now()}`,
      role: 'user',
      content,
      createdAt: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const res = await apiService.sendChatMessage(sessionId!, content);
      const data = res.data || res;

      // The response should contain the assistant message
      const assistantMessage: AIChatMessage = data.assistantMessage || data.message || data;
      setMessages((prev) => [...prev, assistantMessage]);

      // Update session list with latest message timestamp
      setSessions((prev) =>
        prev.map((s) =>
          s.id === sessionId
            ? { ...s, messageCount: s.messageCount + 2, lastMessageAt: new Date().toISOString() }
            : s
        )
      );
    } catch (err: any) {
      showError(err.message || 'Failed to send message');
      // Add an error message in chat
      setMessages((prev) => [
        ...prev,
        {
          sessionId: sessionId!,
          id: `error-${Date.now()}`,
          role: 'system',
          content: 'Failed to get a response. Please try again.',
          createdAt: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = () => {
    sendMessage(input);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleChipClick = (text: string) => {
    sendMessage(text);
  };

  const renderMessage = (msg: AIChatMessage) => {
    if (msg.role === 'system') {
      return (
        <Box key={msg.id} sx={{ display: 'flex', justifyContent: 'center', my: 1 }}>
          <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic' }}>
            {msg.content}
          </Typography>
        </Box>
      );
    }

    const isUser = msg.role === 'user';

    return (
      <Box
        key={msg.id}
        sx={{
          display: 'flex',
          justifyContent: isUser ? 'flex-end' : 'flex-start',
          mb: 1.5,
        }}
      >
        <Paper
          elevation={0}
          sx={{
            px: 2,
            py: 1.5,
            maxWidth: '85%',
            borderRadius: 2,
            bgcolor: isUser ? 'primary.main' : 'background.paper',
            color: isUser ? 'primary.contrastText' : 'text.primary',
            border: isUser ? 'none' : `1px solid ${theme.palette.divider}`,
          }}
        >
          {isUser ? (
            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
              {msg.content}
            </Typography>
          ) : (
            <Box
              sx={{
                '& p': { m: 0, mb: 1, '&:last-child': { mb: 0 } },
                '& ul, & ol': { pl: 2, my: 0.5 },
                '& code': {
                  bgcolor: 'action.hover',
                  px: 0.5,
                  py: 0.25,
                  borderRadius: 0.5,
                  fontSize: '0.85em',
                  fontFamily: 'monospace',
                },
                '& pre': {
                  bgcolor: 'action.hover',
                  p: 1.5,
                  borderRadius: 1,
                  overflow: 'auto',
                  '& code': { bgcolor: 'transparent', p: 0 },
                },
                '& a': { color: 'primary.main' },
                '& table': {
                  borderCollapse: 'collapse',
                  width: '100%',
                  my: 1,
                  '& th, & td': {
                    border: `1px solid ${theme.palette.divider}`,
                    px: 1,
                    py: 0.5,
                    fontSize: '0.85em',
                  },
                },
              }}
            >
              <ReactMarkdown>{msg.content}</ReactMarkdown>
            </Box>
          )}
          {msg.chartConfig && <ChartInChat config={msg.chartConfig} />}
        </Paper>
      </Box>
    );
  };

  const drawerContent = (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          px: 2,
          py: 1.5,
          borderBottom: `1px solid ${theme.palette.divider}`,
          minHeight: 56,
        }}
      >
        <ChatIcon sx={{ mr: 1, color: 'primary.main' }} />
        <Typography variant="h6" sx={{ flex: 1, fontWeight: 600 }}>
          AI Assistant
        </Typography>
        <Tooltip title="New Chat">
          <IconButton size="small" onClick={handleNewChat} sx={{ mr: 0.5 }}>
            <AddIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title="Close">
          <IconButton size="small" onClick={onClose}>
            <CloseIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Sessions list (collapsible) */}
      <Box sx={{ borderBottom: `1px solid ${theme.palette.divider}` }}>
        <ListItemButton onClick={() => setSessionsOpen(!sessionsOpen)} sx={{ py: 0.75 }}>
          <ListItemText
            primary={
              <Typography variant="body2" color="text.secondary">
                Chat History ({sessions.length})
              </Typography>
            }
          />
          {sessionsOpen ? <ExpandLess fontSize="small" /> : <ExpandMore fontSize="small" />}
        </ListItemButton>
        <Collapse in={sessionsOpen} timeout="auto" unmountOnExit>
          {sessionsLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
              <CircularProgress size={20} />
            </Box>
          ) : sessions.length === 0 ? (
            <Typography variant="caption" color="text.secondary" sx={{ px: 2, py: 1, display: 'block' }}>
              No chat sessions yet
            </Typography>
          ) : (
            <List dense sx={{ maxHeight: 200, overflow: 'auto', pt: 0 }}>
              {sessions.map((session) => (
                <ListItemButton
                  key={session.id}
                  selected={session.id === activeSessionId}
                  onClick={() => handleSelectSession(session.id)}
                  sx={{ py: 0.5, pl: 3 }}
                >
                  <ListItemText
                    primary={session.title || 'Untitled'}
                    primaryTypographyProps={{ variant: 'body2', noWrap: true }}
                    secondary={session.messageCount ? `${session.messageCount} messages` : undefined}
                    secondaryTypographyProps={{ variant: 'caption' }}
                  />
                  <ListItemSecondaryAction>
                    <IconButton
                      edge="end"
                      size="small"
                      onClick={(e) => handleDeleteSession(e, session.id)}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItemButton>
              ))}
            </List>
          )}
        </Collapse>
      </Box>

      {/* Messages area */}
      <Box
        sx={{
          flex: 1,
          overflow: 'auto',
          px: 2,
          py: 2,
        }}
      >
        {messages.length === 0 && !isLoading && (
          <Box sx={{ textAlign: 'center', mt: 8 }}>
            <ChatIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
            <Typography variant="body1" color="text.secondary" gutterBottom>
              How can I help you?
            </Typography>
            <Typography variant="body2" color="text.disabled">
              Ask about your hours, budgets, team activity, or get suggestions for time entries.
            </Typography>
          </Box>
        )}
        {messages.map(renderMessage)}
        {isLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 1.5 }}>
            <Paper
              elevation={0}
              sx={{
                px: 2,
                py: 1.5,
                borderRadius: 2,
                bgcolor: 'background.paper',
                border: `1px solid ${theme.palette.divider}`,
                display: 'flex',
                alignItems: 'center',
                gap: 1,
              }}
            >
              <CircularProgress size={16} />
              <Typography variant="body2" color="text.secondary">
                Thinking...
              </Typography>
            </Paper>
          </Box>
        )}
        <div ref={messagesEndRef} />
      </Box>

      {/* Suggestion chips */}
      {messages.length === 0 && (
        <>
          <Divider />
          <Box sx={{ px: 2, py: 1, display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
            {SUGGESTION_CHIPS.map((chip) => (
              <Chip
                key={chip}
                label={chip}
                size="small"
                variant="outlined"
                onClick={() => handleChipClick(chip)}
                sx={{
                  cursor: 'pointer',
                  '&:hover': { bgcolor: 'primary.main', color: 'primary.contrastText', borderColor: 'primary.main' },
                }}
              />
            ))}
          </Box>
        </>
      )}

      {/* Input area */}
      <Box
        sx={{
          px: 2,
          py: 1.5,
          borderTop: `1px solid ${theme.palette.divider}`,
          display: 'flex',
          gap: 1,
          alignItems: 'flex-end',
        }}
      >
        <TextField
          inputRef={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything..."
          size="small"
          fullWidth
          multiline
          maxRows={4}
          disabled={isLoading}
          sx={{
            '& .MuiOutlinedInput-root': {
              borderRadius: 2,
            },
          }}
        />
        <IconButton
          color="primary"
          onClick={handleSend}
          disabled={!input.trim() || isLoading}
          sx={{
            bgcolor: 'primary.main',
            color: 'primary.contrastText',
            '&:hover': { bgcolor: 'primary.dark' },
            '&.Mui-disabled': { bgcolor: 'action.disabledBackground' },
            width: 40,
            height: 40,
          }}
        >
          <SendIcon fontSize="small" />
        </IconButton>
      </Box>
    </Box>
  );

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      variant={isMobile ? 'temporary' : 'persistent'}
      sx={{
        '& .MuiDrawer-paper': {
          width: isMobile ? '100%' : DRAWER_WIDTH,
          maxWidth: '100%',
          boxSizing: 'border-box',
          mt: isMobile ? 0 : '64px',
          height: isMobile ? '100%' : 'calc(100% - 64px)',
        },
      }}
    >
      {drawerContent}
    </Drawer>
  );
};

export default AIChatDrawer;
