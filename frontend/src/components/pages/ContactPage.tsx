import React, { useState } from 'react';
import {
  Container, Typography, Grid, Card, CardContent, TextField,
  Button, MenuItem, Alert,
} from '@mui/material';
import { Send } from '@mui/icons-material';

const ContactPage: React.FC = () => {
  const [form, setForm] = useState({ name: '', email: '', phone: '', inquiryType: 'Question', message: '' });
  const [submitted, setSubmitted] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Contact form:', form);
    setSubmitted(true);
  };

  return (
    <Container maxWidth="md" sx={{ py: 6 }}>
      <Typography variant="h4" fontWeight={700} gutterBottom textAlign="center">Contact Us</Typography>
      <Typography variant="body1" color="text.secondary" textAlign="center" sx={{ mb: 4 }}>
        Have questions? We'd love to hear from you.
      </Typography>

      {submitted ? (
        <Alert severity="success" sx={{ mb: 3 }}>Thank you for reaching out! We'll get back to you soon.</Alert>
      ) : (
        <Card variant="outlined" sx={{ borderRadius: 3 }}>
          <CardContent sx={{ p: 4 }}>
            <form onSubmit={handleSubmit}>
              <Grid container spacing={2.5}>
                <Grid item xs={12} sm={6}>
                  <TextField label="Name" name="name" fullWidth required value={form.name} onChange={handleChange} />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField label="Email" name="email" type="email" fullWidth required value={form.email} onChange={handleChange} />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField label="Phone" name="phone" type="tel" fullWidth value={form.phone} onChange={handleChange} />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField label="Inquiry Type" name="inquiryType" select fullWidth value={form.inquiryType} onChange={handleChange}>
                    <MenuItem value="Question">Question</MenuItem>
                    <MenuItem value="Request">Request</MenuItem>
                    <MenuItem value="Support">Support</MenuItem>
                    <MenuItem value="Partnership">Partnership</MenuItem>
                  </TextField>
                </Grid>
                <Grid item xs={12}>
                  <TextField label="Message" name="message" multiline rows={4} fullWidth required value={form.message} onChange={handleChange} />
                </Grid>
                <Grid item xs={12}>
                  <Button type="submit" variant="contained" size="large" endIcon={<Send />} sx={{ px: 4 }}>Submit</Button>
                </Grid>
              </Grid>
            </form>
          </CardContent>
        </Card>
      )}
    </Container>
  );
};

export default ContactPage;
