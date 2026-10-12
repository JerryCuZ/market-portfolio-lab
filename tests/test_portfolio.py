"""Hand-calculated accounting and timing checks (no market downloads)."""
import sys
import unittest
from pathlib import Path
import pandas as pd
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from portfolio import simulate, reconcile


def frame(dates, prices, dividends=None):
    return pd.DataFrame({'Open': prices, 'Close': prices,
                         'Dividends': dividends if dividends is not None else 0},
                        index=pd.to_datetime(dates))


class PortfolioTests(unittest.TestCase):
    def test_initial_cost_and_reconciliation(self):
        f = frame(['2020-01-02','2020-01-03'], [100,100])
        r = simulate({'A':f}, {'A':1}, initial_cash=1000, cost_bps=100)
        self.assertAlmostEqual(r.daily.nav.iloc[-1], 1000/1.01)
        self.assertAlmostEqual(r.trades.fee.sum(), 1000-1000/1.01)
        reconcile(r)

    def test_ex_dividend_old_holders_not_new_buyers(self):
        f = frame(['2020-01-31','2020-02-03','2020-02-04'], [100,95,95], [0,5,0])
        r = simulate({'A':f},{'A':1}, initial_cash=1000,cost_bps=0)
        self.assertAlmostEqual(r.distributions.amount.sum(), 50)
        np.testing.assert_allclose(r.daily.nav, 1000)
        new = simulate({'A': f.iloc[1:]},{'A':1},initial_cash=1000,cost_bps=0)
        self.assertEqual(len(new.distributions),0)
        reconcile(r)

    def test_cash_distribution_not_double_counted(self):
        f = frame(['2020-01-02','2020-01-03'],[100,95],[0,5])
        r = simulate({'A':f},{'A':1},initial_cash=1000,cost_bps=0,monthly=False)
        self.assertAlmostEqual(r.daily.cash.iloc[-1],50)
        self.assertAlmostEqual(r.daily.nav.iloc[-1],1000)
        reconcile(r)

    def test_drift_and_next_month_open(self):
        dates = ['2020-01-30','2020-01-31','2020-02-03']
        a, b = frame(dates,[100,200,200]), frame(dates,[100,100,100])
        r = simulate({'A':a,'B':b},{'A':.5,'B':.5},initial_cash=1000,cost_bps=0)
        self.assertAlmostEqual(r.daily.A_weight.iloc[1],2/3)
        self.assertAlmostEqual(r.daily.A_weight.iloc[2],.5)
        self.assertEqual(r.trades.iloc[-1].decision_date,pd.Timestamp('2020-01-31'))
        self.assertEqual(r.trades.iloc[-1].date,pd.Timestamp('2020-02-03'))
        self.assertAlmostEqual(r.daily.nav.iloc[-1],1500)
        reconcile(r)

    def test_future_price_change_cannot_change_past_trades(self):
        dates = ['2020-01-31','2020-02-03','2020-03-02']
        f = frame(dates,[100,110,120])
        r = simulate({'A':f},{'A':.5},cost_bps=5)
        changed = f.copy()
        changed.iloc[-1, :2] = 500
        other = simulate({'A':changed},{'A':.5},cost_bps=5)
        pd.testing.assert_frame_equal(r.trades.iloc[:-1],other.trades.iloc[:-1])

    def test_bad_calendar_and_unsupported_action_rejected(self):
        f = frame(['2020-01-02','2020-01-03'],[100,100])
        with self.assertRaises(ValueError):
            simulate({'A':f,'B':f.iloc[1:]},{'A':.5,'B':.5})
        f['Stock Splits']=[0,2]
        with self.assertRaises(ValueError):
            simulate({'A':f},{'A':1})


if __name__ == '__main__':
    unittest.main()
