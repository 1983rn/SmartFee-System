import React from 'react';
import { Box, Card, CardContent, Typography, Grid, Chip, Stack, Paper } from '@mui/material';
import { AccountBalance, TrendingUp, Business, AttachMoney } from '@mui/icons-material';

// Mock data representing the enhanced income management
const mockIncomeData = {
  pta_total: 2450000,
  sdf_total: 850000,
  boarding_total: 1200000,
  other_income_total: 450000,
  other_incomes: [
    {
      id: 1,
      date: '2024-01-15',
      customer_name: 'ABC Construction Ltd',
      income_type: 'Class rooms',
      total_charge: 150000,
      amount_paid: 150000,
      balance: 0
    },
    {
      id: 2,
      date: '2024-01-10',
      customer_name: 'John Banda',
      income_type: 'Chairs',
      total_charge: 75000,
      amount_paid: 50000,
      balance: 25000
    },
    {
      id: 3,
      date: '2024-01-08',
      customer_name: 'Grace Phiri',
      income_type: 'House rentals',
      total_charge: 200000,
      amount_paid: 200000,
      balance: 0
    }
  ]
};

const IncomeCard = ({ title, amount, color, icon: Icon }) => (
  <Card sx={{ height: '100%', background: `linear-gradient(135deg, ${color}20 0%, ${color}10 100%)` }}>
    <CardContent>
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Box>
          <Typography variant="h6" color={color} fontWeight="bold">
            {title}
          </Typography>
          <Typography variant="h4" fontWeight="bold" color="text.primary">
            MK{amount.toLocaleString()}
          </Typography>
        </Box>
        <Icon sx={{ fontSize: 40, color: `${color}80` }} />
      </Stack>
    </CardContent>
  </Card>
);

const OtherIncomeRow = ({ income }) => (
  <Paper sx={{ p: 2, mb: 2, border: '1px solid', borderColor: 'divider' }}>
    <Grid container spacing={2} alignItems="center">
      <Grid item xs={12} sm={2}>
        <Typography variant="body2" color="text.secondary">
          {income.date}
        </Typography>
      </Grid>
      <Grid item xs={12} sm={3}>
        <Typography variant="body1" fontWeight="bold">
          {income.customer_name}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Customer
        </Typography>
      </Grid>
      <Grid item xs={12} sm={2}>
        <Typography variant="body1" fontWeight="bold">
          {income.income_type}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Type of Income
        </Typography>
      </Grid>
      <Grid item xs={12} sm={2}>
        <Typography variant="body2">
          MK{income.total_charge.toLocaleString()}
        </Typography>
      </Grid>
      <Grid item xs={12} sm={2}>
        <Typography variant="body2" color="success.main">
          MK{income.amount_paid.toLocaleString()}
        </Typography>
      </Grid>
      <Grid item xs={12} sm={1}>
        <Chip 
          label={income.balance === 0 ? 'Paid' : `MK${income.balance.toLocaleString()}`}
          color={income.balance === 0 ? 'success' : 'warning'}
          size="small"
        />
      </Grid>
    </Grid>
  </Paper>
);

const BudgetNote = () => (
  <Paper sx={{ p: 2, mb: 3, bgcolor: 'info.light', color: 'info.contrastText' }}>
    <Typography variant="body2">
      <strong>Note:</strong> Budget items can now be repeated as needed - duplicate entries are allowed for flexible budget planning.
    </Typography>
  </Paper>
);

export default function IncomeEnhancementsPreview() {
  const totalIncome = mockIncomeData.pta_total + mockIncomeData.sdf_total + 
                     mockIncomeData.boarding_total + mockIncomeData.other_income_total;

  return (
    <Box sx={{ p: 3, bgcolor: 'background.default', minHeight: '100vh' }}>
      <Typography variant="h4" gutterBottom fontWeight="bold" color="primary">
        Enhanced Income Management System
      </Typography>
      
      {/* Income Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <IncomeCard 
            title="PTA Fund Total" 
            amount={mockIncomeData.pta_total} 
            color="#1976d2"
            icon={AccountBalance}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <IncomeCard 
            title="SDF Total" 
            amount={mockIncomeData.sdf_total} 
            color="#0288d1"
            icon={TrendingUp}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <IncomeCard 
            title="Boarding Fee Total" 
            amount={mockIncomeData.boarding_total} 
            color="#2e7d32"
            icon={Business}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <IncomeCard 
            title="Other Income Total" 
            amount={mockIncomeData.other_income_total} 
            color="#ed6c02"
            icon={AttachMoney}
          />
        </Grid>
      </Grid>

      {/* Total Income Summary */}
      <Paper sx={{ p: 3, mb: 4, bgcolor: 'success.light' }}>
        <Typography variant="h5" fontWeight="bold" color="success.contrastText">
          Total Income: MK{totalIncome.toLocaleString()}
        </Typography>
        <Typography variant="body2" color="success.contrastText" sx={{ mt: 1 }}>
          Includes: Student fees + Other Income (Complete income picture)
        </Typography>
      </Paper>

      {/* Other Income Section */}
      <Typography variant="h5" gutterBottom fontWeight="bold" sx={{ mb: 3 }}>
        Other Income Records
      </Typography>
      
      {/* Column Headers */}
      <Paper sx={{ p: 2, mb: 2, bgcolor: 'grey.100' }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={2}>
            <Typography variant="subtitle2" fontWeight="bold">Date</Typography>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Typography variant="subtitle2" fontWeight="bold">Customer</Typography>
          </Grid>
          <Grid item xs={12} sm={2}>
            <Typography variant="subtitle2" fontWeight="bold">Type of Income</Typography>
          </Grid>
          <Grid item xs={12} sm={2}>
            <Typography variant="subtitle2" fontWeight="bold">Total Charge</Typography>
          </Grid>
          <Grid item xs={12} sm={2}>
            <Typography variant="subtitle2" fontWeight="bold">Amount Paid</Typography>
          </Grid>
          <Grid item xs={12} sm={1}>
            <Typography variant="subtitle2" fontWeight="bold">Status</Typography>
          </Grid>
        </Grid>
      </Paper>

      {/* Other Income Rows */}
      {mockIncomeData.other_incomes.map((income) => (
        <OtherIncomeRow key={income.id} income={income} />
      ))}

      {/* Budget Enhancement Note */}
      <Typography variant="h5" gutterBottom fontWeight="bold" sx={{ mt: 4, mb: 2 }}>
        Budget Management Enhancement
      </Typography>
      <BudgetNote />

      {/* Key Features */}
      <Paper sx={{ p: 3, mt: 4 }}>
        <Typography variant="h6" gutterBottom fontWeight="bold" color="primary">
          ✅ Enhancements Implemented
        </Typography>
        <Stack spacing={1}>
          <Typography variant="body2">
            • <strong>Other Income Total:</strong> Now displayed alongside PTA, SDF, and Boarding totals
          </Typography>
          <Typography variant="body2">
            • <strong>Enhanced Display:</strong> Customer and Type of Income clearly labeled with descriptions
          </Typography>
          <Typography variant="body2">
            • <strong>Dashboard Integration:</strong> Complete income picture including all sources
          </Typography>
          <Typography variant="body2">
            • <strong>Budget Flexibility:</strong> Duplicate budget items now allowed without constraints
          </Typography>
          <Typography variant="body2">
            • <strong>Visual Consistency:</strong> Maintains existing design while adding new functionality
          </Typography>
        </Stack>
      </Paper>
    </Box>
  );
}