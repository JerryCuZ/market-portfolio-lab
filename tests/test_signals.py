"""Hand-calculated trend rules and all-cash account transitions."""
import unittest
import numpy as np
import pandas as pd
from test_portfolio import frame
from signals import trend_filter_schedule
from portfolio import simulate, reconcile


class SignalTests(unittest.TestCase):
    def fixture(self):
        dates = pd.bdate_range('2020-01-01', periods=6)
        prices = pd.DataFrame({'A':[10,10,12,8,7,15], 'B':[10]*6},index=dates)
        schedule = pd.DataFrame({'A':[.4,.4], 'B':[.6,.6],
            'decision_date':dates[[2,4]]},index=dates[[3,5]])
        return prices,schedule

    def test_hand_signal_equality_cash_and_input_unchanged(self):
        prices,schedule = self.fixture(); original=schedule.copy(deep=True)
        target,audit=trend_filter_schedule(prices,schedule,2)
        np.testing.assert_allclose(target[['A','B']],[[.4,0],[0,0]])
        np.testing.assert_allclose(audit.sma,[11,10,7.5,10])
        np.testing.assert_allclose(audit.cash_target,[.6,.6,1,1])
        pd.testing.assert_frame_equal(schedule,original)

    def test_future_prices_and_scaling_do_not_change_prior_signals(self):
        prices,schedule=self.fixture()
        a,aa=trend_filter_schedule(prices,schedule,2)
        changed=prices.copy(); changed.loc[schedule.index[0]:,'A'] *= 100
        b,bb=trend_filter_schedule(changed,schedule,2)
        pd.testing.assert_series_equal(a.iloc[0],b.iloc[0])
        pd.testing.assert_frame_equal(aa.iloc[:2],bb.iloc[:2])
        c,_=trend_filter_schedule(prices*7,schedule,2)
        pd.testing.assert_frame_equal(a,c)

    def test_reject_warmup_same_day_and_invalid_input(self):
        prices,schedule=self.fixture()
        with self.assertRaises(ValueError): trend_filter_schedule(prices,schedule,4)
        bad=schedule.copy(); bad['decision_date']=bad.index
        with self.assertRaises(ValueError): trend_filter_schedule(prices,bad,2)
        bad=prices.copy();bad.iloc[0,0]=np.nan
        with self.assertRaises(ValueError): trend_filter_schedule(bad,schedule,2)

    def test_all_cash_entire_run(self):
        f=frame(['2020-01-02','2020-02-03'],[100,150],[0,5])
        r=simulate({'A':f},{'A':0},initial_cash=1000)
        np.testing.assert_allclose(r.daily.nav,1000)
        self.assertTrue(r.trades.empty);self.assertTrue(r.distributions.empty)
        self.assertEqual(r.metrics()['fees_paid'],0)
        self.assertEqual(r.metrics()['max_drawdown'],0)
        reconcile(r)

    def test_liquidate_and_reenter_with_fees_and_dividend_entitlement(self):
        dates=pd.to_datetime(['2020-01-02','2020-02-03','2020-03-02'])
        f=frame(dates,[100,100,100],[0,2,3])
        s=pd.DataFrame({'A':[1.,0.,1.],
            'decision_date':pd.to_datetime(['2020-01-01','2020-01-31','2020-02-28'])},index=dates)
        r=simulate({'A':f},{'A':1},initial_cash=1010,cost_bps=100,target_schedule=s)
        # Initial 10 shares; liquidation earns $20 entitlement, pays $10 fee.
        self.assertAlmostEqual(r.daily.cash.iloc[1],1010)
        self.assertAlmostEqual(r.daily.A_shares.iloc[1],0)
        self.assertAlmostEqual(r.daily.A_shares.iloc[2],10)
        self.assertAlmostEqual(r.distributions.amount.sum(),20)
        self.assertAlmostEqual(r.trades.fee.sum(),30)
        reconcile(r)
