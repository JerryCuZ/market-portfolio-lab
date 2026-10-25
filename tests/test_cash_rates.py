import unittest
import numpy as np
import pandas as pd
from test_portfolio import frame
from cash_rates import rate_schedule,parse_rates
from portfolio import simulate,reconcile

class CashRateTests(unittest.TestCase):
    def test_units_lag_weekend_and_future_invariance(self):
        raw=b'observation_date,DFF\n2020-01-01,3.6\n2020-01-02,4.0\n2020-01-03,5.0\n2020-01-04,6.0\n2020-01-05,7.0\n2020-01-06,8.0\n'
        rates=parse_rates(raw)
        self.assertAlmostEqual(rates.iloc[0],.036)
        dates=pd.to_datetime(['2020-01-10','2020-01-13'])
        s=rate_schedule(rates,dates,lag_days=7)
        self.assertEqual(s.observation_date.iloc[1],pd.Timestamp('2020-01-03'))
        self.assertEqual(s.days.iloc[1],3)
        changed=rates.copy();changed.loc['2020-01-04':]=.9
        pd.testing.assert_frame_equal(s,rate_schedule(changed,dates,lag_days=7))
        self.assertEqual(rate_schedule(rates,dates,spread_bps=1000).annual_rate.max(),0)

    def test_cash_interest_calendar_days_and_compounding(self):
        dates=pd.to_datetime(['2020-01-10','2020-01-13','2020-01-14'])
        f=frame(dates,[100]*3)
        rates=pd.DataFrame({'annual_rate':.036,'assumed_available_date':pd.Timestamp('2020-01-01')},index=dates)
        r=simulate({'A':f},{'A':0},initial_cash=1000,cash_rates=rates)
        np.testing.assert_allclose(r.daily.interest,[0,.3,1000.3*.036/360])
        self.assertAlmostEqual(r.daily.nav.iloc[-1],1000.3*1.0001)
        reconcile(r)
        r.interest_events.loc[0,'principal']+=100
        with self.assertRaises(AssertionError):reconcile(r)

    def test_sale_today_does_not_earn_prior_interval_interest(self):
        dates=pd.to_datetime(['2020-01-02','2020-02-03','2020-02-04'])
        f=frame(dates,[100]*3,[0,2,0])
        s=pd.DataFrame({'A':[1,0], 'decision_date':pd.to_datetime(['2020-01-01','2020-01-31'])},index=dates[:2])
        rates=pd.DataFrame({'annual_rate':.036,'assumed_available_date':pd.Timestamp('2019-12-01')},index=dates)
        r=simulate({'A':f},{'A':1},initial_cash=1000,cost_bps=0,target_schedule=s,cash_rates=rates)
        self.assertAlmostEqual(r.daily.interest.iloc[1],0)
        self.assertAlmostEqual(r.daily.interest.iloc[2],1020*.036/360)
        reconcile(r)

    def test_zero_rate_compatibility_and_missing_rejection(self):
        dates=pd.to_datetime(['2020-01-02','2020-02-03'])
        f=frame(dates,[100,110]);rates=pd.DataFrame({'annual_rate':0.,'assumed_available_date':pd.Timestamp('2019-12-01')},index=dates)
        a=simulate({'A':f},{'A':.5});b=simulate({'A':f},{'A':.5},cash_rates=rates)
        pd.testing.assert_frame_equal(a.daily,b.daily);pd.testing.assert_frame_equal(a.trades,b.trades)
        rates.loc[dates[1],'assumed_available_date']=dates[1]
        with self.assertRaises(ValueError):simulate({'A':f},{'A':.5},cash_rates=rates)
        with self.assertRaises(ValueError):rate_schedule(pd.Series([.03],index=pd.to_datetime(['2010-01-01'])),dates)
