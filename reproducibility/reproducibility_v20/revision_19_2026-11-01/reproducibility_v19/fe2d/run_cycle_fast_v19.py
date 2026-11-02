"""Resume full-geometry cycles with full-step iteration and damped fallback."""
import argparse,json
import cycle_contact_v19 as base
from fast_inverse_contact_v19 import FastOperator

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--step',type=float,default=.04);p.add_argument('--h',type=float,default=.5);a=p.parse_args()
    base.Operator=FastOperator
    base.campaign(a.step,a.h)
