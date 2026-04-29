# -*- coding: utf-8 -*-
"""
Created on Tue Apr 28 11:06:30 2026

@author: coleb
"""

import json

def setconfig(file):
    with open(file) as f:
        config = json.load(f)
        return config

def apply_config(obj, cfg):
    for key, value in cfg.items():
        setattr(obj, key, value[0])
        
