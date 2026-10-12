import unittest
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from risk_models import risk_contributions, inverse_vol_schedule
from portfolio import simulate, reconcile


class RiskTests(unittest.TestCase):
    def test_hand_calculated_risk_and_inverse_vol(self):
        cov = pd.DataFrame(np.diag([.2**2,.1**2]),index=['A','B'],columns=['A','B'])
        rc, vol = risk_contributions({'A':.5,'B':.5},cov)
        self.assertAlmostEqual(vol,np.sqrt(.0125))
        np.testing.assert_allclose(rc.risk_share,[.8,.2])
        rc, vol = risk_contributions({'A':1/3,'B':2/3},cov)
        np.testing.assert_allclose(rc.risk_share,[.5,.5])
        self.assertAlmostEqual(rc.volatility_contribution.sum(),vol)

    def test_inverse_vol_not_equal_risk_with_three_correlated_assets(self):
        cov = pd.DataFrame([[1,.8,0],[.8,1,0],[0,0,1]],index=list('ABC'),columns=list('ABC'))
        rc,_ = risk_contributions(dict.fromkeys('ABC',1/3),cov)
        self.assertFalse(np.allclose(rc.risk_share,1/3))
        self.assertAlmostEqual(rc.risk_share.sum(),1)

    def test_negative_risk_contribution_is_valid(self):
        cov = pd.DataFrame([[.04,-.015],[-.015,.01]],index=list('AB'),columns=list('AB'))
        rc,_ = risk_contributions({'A':.8,'B':.2},cov)
        self.assertLess(rc.loc['B','risk_share'],0)
        self.assertAlmostEqual(rc.risk_share.sum(),1)

    def test_signal_unchanged_by_execution_and_future_prices(self):
        dates = pd.bdate_range('2020-01-01',periods=100)
        rng = np.random.default_rng(42)
        p = pd.DataFrame(100*np.exp(np.cumsum(rng.normal(0,.01,(100,2)),axis=0)),index=dates,columns=list('AB'))
        s,_ = inverse_vol_schedule(p,lookback=10)
        execution = s.index[1]
        altered = p.copy()
        altered.loc[execution:,'A'] *= 2
        other,_ = inverse_vol_schedule(altered,lookback=10)
        pd.testing.assert_frame_equal(s.loc[:execution],other.loc[:execution])
        self.assertTrue((s.decision_date.to_numpy()<s.index.to_numpy()).all())

    def test_schedule_and_fixed_policy_match_and_same_day_rejected(self):
        dates = pd.to_datetime(['2020-01-02','2020-01-31','2020-02-03'])
        f = pd.DataFrame({'Open':[100,105,103],'Close':[101,105,106],'Dividends':0},index=dates)
        schedule = pd.DataFrame({'A':[.6,.6],'decision_date':pd.to_datetime(['2020-01-01','2020-01-31'])},index=dates[[0,2]])
        fixed = simulate({'A':f},{'A':.6})
        dynamic = simulate({'A':f},{'A':.6},target_schedule=schedule)
        pd.testing.assert_frame_equal(fixed.daily,dynamic.daily)
        reconcile(dynamic)
        schedule.loc[dates[2],'decision_date'] = dates[2]
        with self.assertRaises(ValueError):
            simulate({'A':f},{'A':.6},target_schedule=schedule)


if __name__ == '__main__': unittest.main()
