import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from risk_models import equal_risk_weights, equal_risk_schedule, risk_contributions


class EqualRiskTests(unittest.TestCase):
    def test_diagonal_matches_inverse_vol(self):
        vol=np.array([.2,.1,.15])
        c=pd.DataFrame(np.diag(vol**2),index=list('ABC'),columns=list('ABC'))
        w,_=equal_risk_weights(c)
        np.testing.assert_allclose(w,(1/vol)/(1/vol).sum(),atol=1e-8)

    def test_correlated_three_asset_solution(self):
        c=pd.DataFrame([[1,.8,0],[.8,1,0],[0,0,1]],index=list('ABC'),columns=list('ABC'))
        w,_=equal_risk_weights(c)
        expected=np.array([1,1,np.sqrt(1.8)])/(2+np.sqrt(1.8))
        np.testing.assert_allclose(w,expected,atol=1e-8)
        np.testing.assert_allclose(risk_contributions(w,c)[0].risk_share,1/3,atol=1e-9)
        other,_=equal_risk_weights(c.loc[list('CBA'),list('CBA')]*100)
        np.testing.assert_allclose(w,other.reindex(w.index),atol=1e-8)

    def test_invalid_and_nonconvergent_fail_closed(self):
        c=pd.DataFrame([[1,1],[1,1]],index=list('AB'),columns=list('AB'))
        with self.assertRaises(ValueError): equal_risk_weights(c)
        c.iloc[0,1]=float('nan')
        with self.assertRaises(ValueError): equal_risk_weights(c)
        c=pd.DataFrame([[1,.8,0],[.8,1,0],[0,0,1]],index=list('ABC'),columns=list('ABC'))
        with self.assertRaises(RuntimeError): equal_risk_weights(c,max_iterations=1)

    def test_future_prices_do_not_change_earlier_targets(self):
        rng=np.random.default_rng(8)
        p=pd.DataFrame(100*np.exp(rng.normal(0,.01,(110,3)).cumsum(axis=0)),
                       index=pd.bdate_range('2020-01-01',periods=110),columns=list('ABC'))
        s,_=equal_risk_schedule(p,10)
        date=s.index[1]
        q=p.copy(); q.loc[date:,'A']*=1.8
        t,_=equal_risk_schedule(q,10)
        pd.testing.assert_frame_equal(s.loc[:date],t.loc[:date])


if __name__ == '__main__': unittest.main()
