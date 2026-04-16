import React, { useState, useRef, useEffect } from 'react';
import {
  Box, Typography, TextField, IconButton, CircularProgress, Paper,
} from '@mui/material';
import { Send, SmartToy, Person } from '@mui/icons-material';
import { AIChatMessage } from '../../types';

interface ChatPanelProps {
  messages: AIChatMessage[];
  onSend: (content: string) => void;
  isLoading: boolean;
}

const ChatPanel: React.FC<ChatPanelProps> = ({ messages, onSend, isLoading }) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const isUser = (msg: AIChatMessage) => msg.role === 'user';

  const getSenderIcon = (role: string) => {
    switch (role) {
      case 'assistant':
      case 'system':
        return <SmartToy sx={{ fontSize: 18 }} />;
      default:
        return <Person sx={{ fontSize: 18 }} />;
    }
  };

  const getSenderLabel = (role: string) => {
    switch (role) {
      case 'assistant': return 'Assistant';
      case 'system': return 'System';
      default: return 'You';
    }
  };

  const formatTime = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 300 }}>
      {/* Messages area */}
      <Box sx={{
        flex: 1, overflowY: 'auto', p: 2, display: 'flex', flexDirection: 'column', gap: 1.5,
        maxHeight: 400, minHeight: 200,
      }}>
        {messages.length === 0 ? (
          <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              No messages yet. Ask a question to get started.
            </Typography>
          </Box>
        ) : (
          messages.map((msg) => {
            const self = isUser(msg);
            return (
              <Box
                key={msg.id}
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: self ? 'flex-end' : 'flex-start',
                  maxWidth: '85%',
                  alignSelf: self ? 'flex-end' : 'flex-start',
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.25 }}>
                  {!self && getSenderIcon(msg.role)}
                  <Typography variant="caption" color="text.secondary">
                    {self ? 'You' : getSenderLabel(msg.role)}
                  </Typography>
                </Box>
                <Paper
                  elevation={0}
                  sx={{
                    px: 2, py: 1, borderRadius: 2,
                    bgcolor: self
                      ? 'primary.main'
                      : msg.role === 'assistant'
                        ? 'rgba(123, 109, 246, 0.1)'
                        : 'background.default',
                    color: self ? 'primary.contrastText' : 'text.primary',
                    border: self ? 'none' : '1px solid',
                    borderColor: self ? 'transparent' : 'divider',
                  }}
                >
                  <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                    {msg.content}
                  </Typography>
                </Paper>
                <Typography variant="caption" color="text.disabled" sx={{ mt: 0.25, px: 0.5 }}>
                  {formatTime(msg.createdAt)}
                </Typography>
              </Box>
            );
          })
        )}
        {isLoading && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, alignSelf: 'flex-start' }}>
            <CircularProgress size={16} />
            <Typography variant="caption" color="text.secondary">Sending...</Typography>
          </Box>
        )}
        <div ref={messagesEndRef} />
      </Box>

      {/* Input area */}
      <Box sx={{
        display: 'flex', gap: 1, p: 2, borderTop: 1, borderColor: 'divider',
        bgcolor: 'background.paper',
      }}>
        <TextField
          fullWidth
          size="small"
          placeholder="Type a message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          multiline
          maxRows={3}
          disabled={isLoading}
        />
        <IconButton
          color="primary"
          onClick={handleSend}
          disabled={!input.trim() || isLoading}
        >
          <Send />
        </IconButton>
      </Box>
    </Box>
  );
};

export default ChatPanel;
